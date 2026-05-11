import requests
import dataclasses
import hashlib
import json
import os
import sys
import certifi
import datetime
import copy
import shutil
from models import Ship
from typing import Optional
from dataclasses import asdict
from PySide6.QtCore import QObject, Signal
from utils import resource_path

SALT = "AzurLaneDex_Salt_2025"

def hash_password(password: str) -> str:
    """对密码进行 SHA256 哈希，返回十六进制字符串"""
    if not password:
        return ""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

class ShipManager(QObject):
    data_changed = Signal()
    REQUIRED_FIELDS = set(Ship.__dataclass_fields__.keys())
    USER_STATE_FIELDS = {
        'owned', 'breakthrough', 'remodeled', 'oath', 'level_120', 
        'special_gear_obtained'
    }
    attr_map = [
        ("耐久", "durability"),
        ("炮击", "firepower"),
        ("雷击", "torpedo"),
        ("防空", "aa"),
        ("航空", "aviation"),
        ("命中", "accuracy"),
        ("装填", "reload"),
        ("机动", "mobility"),
        ("反潜", "antisub")
    ]

    def __init__(self, account_manager, dev_mode=False):
        super().__init__()
        self.account_manager = account_manager
        self.dev_mode = dev_mode
        # 确定用户数据根目录（可执行文件所在目录）
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.abspath(".")
        self.data_dir = os.path.join(base_dir, "data")
        self.static_dir = os.path.join(self.data_dir, "static")
        self.user_dir = os.path.join(self.data_dir, "users")
        self.log_dir = os.path.join(self.data_dir, "log")
        # 静态数据文件路径
        self.static_path = os.path.join(self.static_dir, "ships_static.json")
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.user_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        # 用户状态文件路径（动态）
        current_user = account_manager.get_current_account()
        if current_user:
            self.state_path = os.path.join(self.user_dir, current_user, "ships_state.json")
        else:
            self.state_path = None
        self.config_file = "config.json"
        self.config = self.load_config()
        self.version = "0.0"
        self.ships = []
        #theme_mode = self.config.get("theme_mode", "system")
        #if theme_mode == "system":
        #self.current_theme = "light"
        #elif self.current_theme == "light":
        #   self.current_theme = "light"
        #elif self.current_theme == "dark":
        #   self.current_theme = "dark"
        #else:
        #    self.current_theme = theme_mode
        #   self.current_theme = "light"
        self.load()

    def load(self):
        """加载 JSON，若不存在则创建示例数据"""
        if os.path.exists("ships.json") and not os.path.exists(self.static_path):
            self._migrate_old_data()
            current_user = self.account_manager.get_current_account()
            if current_user:
                self.state_path = os.path.join(self.user_dir, current_user, "ships_state.json")
            else:
                self.state_path = None

                # 尝试从打包资源中复制默认静态文件
                default_static = resource_path("data/static/ships_static.json")
                if os.path.exists(default_static):
                    os.makedirs(os.path.dirname(self.static_path), exist_ok=True)
                    shutil.copy2(default_static, self.static_path)
                    print(f"已复制默认静态数据到 {self.static_path}")
                else:
                    # 如果没有默认静态文件，则创建示例（开发模式）
                    if self.dev_mode:
                        self._create_sample_static()
                    else:
                        raise FileNotFoundError("缺少静态数据文件")

        with open(self.static_path, 'r', encoding='utf-8') as f:
            static_data = json.load(f)
        self.version = static_data.get("version", "0.0")
        static_ships = static_data.get("ships", [])
        
        for ship_dict in static_ships:
                self._migrate_old_bonus(ship_dict)

        # 2. 加载用户状态
        state_dict = {}
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            state_dict = {item['id']: item for item in state_data.get('states', [])}

         # 3. 合并
        self.ships = []
        for static in static_ships:
            ship_id = static['id']
            state = state_dict.get(ship_id, {})
            merged = {**static, **state}
            self._clean_ship_dict(merged)
            try:
                ship = Ship.from_dict(merged)
                self.ships.append(ship)
            except Exception as e:
                print(f"创建 Ship 对象失败，ID={ship_id}: {e}")

        self._auto_assign_game_order()
        print(f"[INFO] 成功加载 {len(self.ships)} 条舰船，版本 {self.version}")
                    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except (json.JSONDecodeError, IOError):
                pass
        default_config = {"edit_password": "", "log_edits": True}
        self.save_config(default_config)
        return default_config
        #else:
        #    return {"edit_password": "", "log_edits": True}

    def save_config(self, config=None):
        if config is not None:
            self.config = config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def set_edit_password(self, password: str):
        """设置编辑密码（哈希后存储）"""
        self.config["edit_password"] = hash_password(password)
        self.save_config()
    
    def verify_edit_password(self, password: str) -> bool:
        """验证输入的密码是否正确"""
        stored_hash = self.config.get("edit_password", "")
        if not stored_hash:
            # 没有设置密码，视为验证通过（即不需要密码）
            return True
        return hash_password(password) == stored_hash

    #def get_edit_password(self):
    #    return self.config.get("edit_password", "")

    def need_password_for_edit(self) -> bool:
        """是否需要密码才能编辑"""
        return bool(self.config.get("edit_password", ""))
    
    def log_edit(self, ship_id, changes, password_used):
        """记录修改日志"""
        if not self.config.get("log_edits", True):
            return
        log_dir = "data/log"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "edit_log.json")
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "ship_id": ship_id,
            "password_used": password_used,
            "changes": changes
        }
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


    def _migrate_old_tech_fields(self, item: dict):
        """
        将旧版本的单字段科技点（如 tech_durability）转换为三阶段字段
        （获得阶段赋原值，满破和120阶段置0）
        """
        tech_bases = [
            "tech_durability", "tech_firepower", "tech_torpedo", "tech_aa",
            "tech_aviation", "tech_accuracy", "tech_reload", "tech_mobility", "tech_antisub"
        ]
        for base in tech_bases:
            old_key = base
            if old_key in item and isinstance(item[old_key], (int, float)):
                # 将原值赋给获得阶段
                item[f"{base}_obtain"] = int(item[old_key])
                # 如果满破/120阶段不存在，则设为0
                if f"{base}_max" not in item:
                    item[f"{base}_max"] = 0
                if f"{base}_120" not in item:
                    item[f"{base}_120"] = 0
                # 删除旧字段
                del item[old_key]

    def save(self):
        """保存到 JSON，包含版本号，使用原子写入防止文件损坏"""
        state_list = []
        for ship in self.ships:
            state_item = {
                "id": ship.id,
                "owned": ship.owned,
                "breakthrough": ship.breakthrough,
                "remodeled": ship.remodeled,
                "oath": ship.oath,
                "level_120": ship.level_120,
                "special_gear_obtained": ship.special_gear_obtained,
            }
            state_list.append(state_item)
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump({"states": state_list}, f, indent=2, ensure_ascii=False)
        self.data_changed.emit()
        print(f"[保存成功] 用户状态已保存至 {self.state_path}")

    def _create_sample_static(self):
        """生成示例静态数据（仅开发模式）"""
            # 示例船只（只包含静态字段）
        sample_ships = [
            {
                "id": 1,
                "name": "泛用型布里",
                "faction": "其他",
                "ship_class": "驱逐",
                "rarity": "精锐",
                "game_order": 1,
                "can_remodel": False,
                "remodel_date": "",
                "acquire_main": "兑换、赠送",
                "acquire_detail": "日/周常任务、月度签到、活动任务、商店兑换、主线普通关卡三星奖励、新兵训练、礼包购买",
                "build_time": "",
                "drop_locations": [],
                "shop_exchange": "勋章、演习",
                "is_permanent": True,
                "debut_event": "",
                "release_date": "2017-05-25",
                "notes": "无法建造",
                "tech_points_obtain": 0,
                "tech_points_max": 0,
                "tech_points_120": 0,
                "tech_durability_obtain": 0,
                "tech_durability_max": 0,
                "tech_durability_120": 0,
                "tech_firepower_obtain": 0,
                "tech_firepower_max": 0,
                "tech_firepower_120": 0,
                "tech_torpedo_obtain": 0,
                "tech_torpedo_max": 0,
                "tech_torpedo_120": 0,
                "tech_aa_obtain": 0,
                "tech_aa_max": 0,
                "tech_aa_120": 0,
                "tech_aviation_obtain": 0,
                "tech_aviation_max": 0,
                "tech_aviation_120": 0,
                "tech_accuracy_obtain": 0,
                "tech_accuracy_max": 0,
                "tech_accuracy_120": 0,
                "tech_reload_obtain": 0,
                "tech_reload_max": 0,
                "tech_reload_120": 0,
                "tech_mobility_obtain": 0,
                "tech_mobility_max": 0,
                "tech_mobility_120": 0,
                "tech_antisub_obtain": 0,
                "tech_antisub_max": 0,
                "tech_antisub_120": 0,
                "special_gear_name": "",
                "special_gear_date": "",
                "special_gear_acquire": "",
                "can_special_gear": False,
                "image_path": "images/bulin.png"
            }   
        ]
        static_data = {
            "version": "0.1",
            "ships": sample_ships
        }
        os.makedirs(os.path.dirname(self.static_path), exist_ok=True)
        with open(self.static_path, 'w', encoding='utf-8') as f:
            json.dump(static_data, f, indent=2)
        print(f"已创建示例静态数据文件: {self.static_path}")
        # self._save_static()
        # self.save()

    def filter(self, criteria: dict) -> list[Ship]:
        result = self.ships[:]
        for field, value in criteria.items():
            if value is None or value == "":
                continue
            if field == "ship_class":
                if isinstance(value, list):
                    # 处理特殊索引 "前排先锋"、"后排主力" 等
                    new_result = []
                    for ship in result:
                        for cls in value:
                            if self._match_ship_class(ship, cls):
                                new_result.append(ship)
                                break
                    result = new_result
                else:
                    result = [s for s in result if s.ship_class == value]
            # 阵营（多选）
            elif field == "faction":
                if isinstance(value, list):
                    result = [s for s in result if s.faction in value]
                else:
                    result = [s for s in result if s.faction == value]
            # 稀有度（多选）
            elif field == "rarity":
                if isinstance(value, list):
                    result = [s for s in result if s.rarity in value]
                else:
                    result = [s for s in result if s.rarity == value]
            # 附加状态
            elif field == "can_remodel" and value:
                result = [s for s in result if s.can_remodel]
            elif field == "can_remodel_not" and value:
                result = [s for s in result if s.can_remodel and not s.remodeled]
            elif field == "remodeled" and value:
                result = [s for s in result if s.remodeled]
            elif field == "max_breakthrough" and value:
                result = [s for s in result if s.is_max_breakthrough()]
            elif field == "not_max" and value:
                result = [s for s in result if s.owned and not s.is_max_breakthrough()]
            elif field == "level_120" and value:
                result = [s for s in result if s.level_120]
            elif field == "not_level120" and value:
                result = [s for s in result if s.owned and not s.level_120]
            elif field == "is_special" and value:
                result = [s for s in result if "μ" in s.name or "（μ" in s.name or s.name.startswith("小")]
            elif field == "can_special_gear" and value:
                result = [s for s in result if s.can_special_gear]
            elif field == "can_special_gear_not_obtained" and value:
                result = [s for s in result if s.can_special_gear and not s.special_gear_obtained]
            elif field == "special_gear_obtained" and value:
                result = [s for s in result if s.special_gear_obtained]
            elif field == "not_oath" and value:
                result = [s for s in result if not s.oath]
            elif field == "oath" and value:
                result = [s for s in result if s.oath]
            elif field == "is_permanent" and value:
                result = [s for s in result if s.is_permanent]
            elif field == "not_permanent" and value:
                result = [s for s in result if not s.is_permanent]
            # 属性加成（筛选出拥有任意一项选中属性的船）
            elif field == "attributes" and isinstance(value, list):
                new_result = []
                for ship in result:
                    for attr in value:
                        # 根据属性名获取对应的科技点数值（获得+120级）
                        if self._has_attr_bonus(ship, attr):
                            new_result.append(ship)
                            break
                result = new_result
            elif field == "can_remodel" and value:
                result = [s for s in result if s.can_remodel]
            elif field == "remodeled" and value:
                result = [s for s in result if s.remodeled]
            elif field == "oath" and value:
                result = [s for s in result if s.oath]
            elif field == "owned" and value:
                result = [s for s in result if s.owned]
            elif field == "max_breakthrough" and value:
                result = [s for s in result if s.is_max_breakthrough()]
            elif field == "level_120" and value:
                result = [s for s in result if s.level_120]
            elif field == "not_level120" and value:
                result = [s for s in result if not s.level_120]
            elif field == "is_special" and value:
                # 判断是否为μ兵装或小船
                result = [s for s in result if ("μ" in s.name or "（μ" in s.name or s.name.startswith("小"))]
            elif field == "name_contains" and value:
                lower_value = value.lower()
                result = [s for s in result if 
                          lower_value in s.name.lower() 
                          or (s.alt_name and lower_value in s.alt_name.lower())
                          or (s.special_gear_name and lower_value in s.special_gear_name.lower())
                          or (s.debut_event and lower_value in s.debut_event.lower())
                          or (s.acquire_detail and lower_value in s.acquire_detail.lower())
                          or (s.acquire_main and lower_value in s.acquire_main.lower())]
            elif field == "not_owned" and value:
                result = [s for s in result if not s.owned]
            elif field == "not_max" and value:
                result = [s for s in result if s.owned and not s.is_max_breakthrough()]
            elif field == "not_level120" and value:
                result = [s for s in result if s.owned and not s.level_120]
            elif field == "can_remodel_not" and value:
                result = [s for s in result if s.owned and s.can_remodel and not s.remodeled]
            elif field == "can_special_gear" and value:
                result = [s for s in result if s.can_special_gear]
            elif field == "special_gear_obtained" and value:
                result = [s for s in result if s.can_special_gear and s.special_gear_obtained]
            elif field == "special_gear_not_obtained" and value:
                result = [s for s in result if s.owned and s.can_special_gear and not s.special_gear_obtained]
        return result

    def _match_index(self, ship, index):
        """根据索引名称判断舰船是否匹配"""
        if index == "前排先锋":
            return ship.ship_class in ["驱逐", "轻巡", "重巡", "超巡", "重炮", "维修"]
        elif index == "后排主力":
            return ship.ship_class in ["战列", "战巡", "航战", "航母", "轻航"]
        elif index == "驱逐":
            return ship.ship_class == "驱逐"
        elif index == "轻巡":
            return ship.ship_class == "轻巡"
        elif index == "重巡":
            return ship.ship_class in ["重巡", "超巡"]
        elif index == "战列":
            return ship.ship_class in ["战列", "战巡", "航战"]
        elif index == "航母":
            return ship.ship_class in ["航母", "轻航"]
        elif index == "维修":
            return ship.ship_class == "维修"
        elif index == "潜艇":
            return ship.ship_class in ["潜艇", "潜母"]
        elif index == "其他":
            # 其他未分类的舰种，例如运输、风帆等
            other_classes = ["运输", "风帆"]
            return ship.ship_class in other_classes
        return False
    
    def _has_attr_bonus(self, ship, attr):
        """检查舰船是否拥有指定属性加成（获得+120级）"""
        attr_map = {
            "炮击": "firepower",
            "航空": "aviation",
            "机动": "mobility",
            "防空": "aa",
            "雷击": "torpedo",
            "装填": "reload",
            "耐久": "durability",
            "反潜": "antisub"
        }
        base = attr_map.get(attr)
        if not base:
            return False
        obtain = getattr(ship, f"tech_{base}_obtain", 0)
        val120 = getattr(ship, f"tech_{base}_120", 0)
        return (obtain + val120) > 0

    def sort(self, ships: list[Ship], key: str, reverse: bool = False) -> list[Ship]:
        if key == "id":
            return sorted(ships, key=lambda s: s.id, reverse=reverse)
        elif key == "game_order":
            return sorted(ships, key=lambda s: s.game_order, reverse=reverse)
        elif key == "name":
            return sorted(ships, key=lambda s: s.name, reverse=reverse)
        elif key == "rarity":
            rarity_order = {"普通":1, "稀有":2, "精锐":3, "超稀有":4, "海上传奇":5}
            return sorted(ships, key=lambda s: rarity_order.get(s.rarity, 0), reverse=reverse)
        elif key == "oath":
            # 按誓约状态排序，True 排在前还是后取决于 reverse
            return sorted(ships, key=lambda s: s.oath, reverse=reverse)
        elif key == "release_date":
        # 将空字符串视为极大值，以便排在最后
            def date_key(s):
                date = s.release_date
                if not date:
                    return "9999-99-99"  # 极大字符串
                return date
            return sorted(ships, key=date_key, reverse=reverse)
        elif key == "remodel_date":
            def remodel_key(s):
                return s.remodel_date if s.remodel_date else "9999-99-99"
            return sorted(ships, key=remodel_key, reverse=reverse)
        elif key == "oath":
            return sorted(ships, key=lambda s: s.oath, reverse=reverse)
        elif key == "level_120":
            return sorted(ships, key=lambda s: s.level_120, reverse=reverse)
        elif key == "total_attr_bonus":
            # 按属性加成总和排序（所有科技点获得+120级之和）
            def total_attr(s):
                total = 0
                for base in ["durability", "firepower", "torpedo", "aa", "aviation",
                             "accuracy", "reload", "mobility", "antisub"]:
                    total += getattr(s, f"tech_{base}_obtain", 0)
                    total += getattr(s, f"tech_{base}_120", 0)
                return total
            return sorted(ships, key=total_attr, reverse=reverse)
        return ships
    
    def calculate_fleet_tech(self):
        """
        计算所有已获得舰船的科技点总和
        返回: (camp_tech, global_bonus)
            camp_tech: dict, 键为阵营，值为该阵营各项科技点总和（字典）
            global_bonus: dict, 键为科技属性，值为全舰队加成总和（获得+120级）
        """
        # 初始化数据结构
        camps = set(s.faction for s in self.ships)
        camp_tech = {camp: {
            'durability': 0, 'firepower': 0, 'torpedo': 0, 'aa': 0,
            'aviation': 0, 'accuracy': 0, 'reload': 0, 'mobility': 0, 'antisub': 0
        } for camp in camps}

        global_bonus = {
            'durability': 0, 'firepower': 0, 'torpedo': 0, 'aa': 0,
            'aviation': 0, 'accuracy': 0, 'reload': 0, 'mobility': 0, 'antisub': 0
        }

        for ship in self.ships:
            if not ship.owned:
                continue
            faction = ship.faction
            # 科技点累加（三阶段全加）
            camp_tech[faction]['durability'] += ship.tech_durability_obtain + ship.tech_durability_max + ship.tech_durability_120
            camp_tech[faction]['firepower']   += ship.tech_firepower_obtain + ship.tech_firepower_max + ship.tech_firepower_120
            camp_tech[faction]['torpedo']     += ship.tech_torpedo_obtain + ship.tech_torpedo_max + ship.tech_torpedo_120
            camp_tech[faction]['aa']          += ship.tech_aa_obtain + ship.tech_aa_max + ship.tech_aa_120
            camp_tech[faction]['aviation']    += ship.tech_aviation_obtain + ship.tech_aviation_max + ship.tech_aviation_120
            camp_tech[faction]['accuracy']    += ship.tech_accuracy_obtain + ship.tech_accuracy_max + ship.tech_accuracy_120
            camp_tech[faction]['reload']      += ship.tech_reload_obtain + ship.tech_reload_max + ship.tech_reload_120
            camp_tech[faction]['mobility']    += ship.tech_mobility_obtain + ship.tech_mobility_max + ship.tech_mobility_120
            camp_tech[faction]['antisub']     += ship.tech_antisub_obtain + ship.tech_antisub_max + ship.tech_antisub_120

            # 全舰队加成（获得 + 120级）
            global_bonus['durability'] += ship.tech_durability_obtain + ship.tech_durability_120
            global_bonus['firepower']   += ship.tech_firepower_obtain + ship.tech_firepower_120
            global_bonus['torpedo']     += ship.tech_torpedo_obtain + ship.tech_torpedo_120
            global_bonus['aa']          += ship.tech_aa_obtain + ship.tech_aa_120
            global_bonus['aviation']    += ship.tech_aviation_obtain + ship.tech_aviation_120
            global_bonus['accuracy']    += ship.tech_accuracy_obtain + ship.tech_accuracy_120
            global_bonus['reload']      += ship.tech_reload_obtain + ship.tech_reload_120
            global_bonus['mobility']    += ship.tech_mobility_obtain + ship.tech_mobility_120
            global_bonus['antisub']     += ship.tech_antisub_obtain + ship.tech_antisub_120

        return camp_tech, global_bonus
    
    def calculate_camp_tech_points(self):
        """计算每个阵营的科技点总和（所有已拥有船的三阶段科技点之和）"""
        camp_tech = {}
        for ship in self.ships:
            if ship.owned:
                faction = ship.faction
                if faction not in camp_tech:
                    camp_tech[faction] = {'obtain': 0, 'max': 0, 'level120': 0}
                camp_tech[faction]['obtain'] += ship.tech_points_obtain
                if ship.is_max_breakthrough():
                    camp_tech[faction]['max'] += ship.tech_points_max
                if ship.level_120:
                    camp_tech[faction]['level120'] += ship.tech_points_120
        return camp_tech
    
    def calculate_global_bonuses(self):
        """
        计算全舰队属性加成
        返回字典：{(舰种, 属性): 总值}
        加成规则：
            - 获得时加成（tech_xxx_obtain）作用于 obtain_affects 中的舰种
            - 120级时加成（tech_xxx_120）作用于 level120_affects 中的舰种
            - 若对应列表为空，则该项不生效
        """
        bonuses = {}
        # 属性映射（中文 -> 用于存储的 key，可选）
        for ship in self.ships:
            if not ship.owned:
                continue

            # 获得时加成
            if ship.obtain_bonus_attr and ship.obtain_bonus_value != 0 and ship.obtain_affects:
                for sc in ship.obtain_affects:
                    key = (sc, ship.obtain_bonus_attr)
                    bonuses[key] = bonuses.get(key, 0) + ship.obtain_bonus_value

            # 120级时加成
            if ship.level120_bonus_attr and ship.level120_bonus_value != 0 and ship.level120_affects:
                for sc in ship.level120_affects:
                    key = (sc, ship.level120_bonus_attr)
                    bonuses[key] = bonuses.get(key, 0) + ship.level120_bonus_value
        return bonuses

    def _parse_and_add_bonus(self, bonuses_dict, bonus_str):
        """
        解析加成字符串，如 "驱逐耐久+1"，并累加到 bonuses_dict
        格式：舰种属性+数值
        """
        import re
        # 简单解析：假设格式为 "舰种属性+数值"，例如 "驱逐耐久+1"
        match = re.match(r'([^\d]+)([+-]?\d+)', bonus_str)
        if match:
            key_part = match.group(1)  # 例如 "驱逐耐久"
            value = int(match.group(2))
            # 进一步分离舰种和属性：可以约定舰种和属性之间无分隔，需要预定义列表
            # 但为了简单，我们暂时将整个 key_part 作为标识，或者由用户输入时直接分两部分
            # 建议在对话框中使用两个下拉框选择舰种和属性，然后自动生成字符串
            # 这里我们简化处理：直接存储字符串，显示时原样显示
            bonuses_dict[key_part] = bonuses_dict.get(key_part, 0) + value

    def stats(self):
        total = len(self.ships)
        owned = [s for s in self.ships if s.owned]
        not_owned = [s for s in self.ships if not s.owned]
        max_break = [s for s in owned if s.is_max_breakthrough()]
        not_max = [s for s in owned if not s.is_max_breakthrough()]
        oath = [s for s in self.ships if s.oath]
        remodeled = [s for s in self.ships if s.remodeled]
        can_remodel_not = [s for s in self.ships if s.can_remodel and not s.remodeled]
        level120 = [s for s in self.ships if s.level_120]
        can_remodel_total = [s for s in self.ships if s.can_remodel]
        can_special_gear = [s for s in self.ships if s.can_special_gear]
        special_gear_obtained = [s for s in self.ships if s.can_special_gear and s.special_gear_obtained]
        special_gear_not_obtained = [s for s in self.ships if s.can_special_gear and not s.special_gear_obtained]
        return {
            'total': total,
            'owned': len(owned),
            'not_owned': len(not_owned),
            'max_break': len(max_break),
            'not_max': len(not_max),
            'oath': len(oath),
            'remodeled': len(remodeled),
            'can_remodel_not': len(can_remodel_not),
            'level120': len(level120),
            'can_remodel_total': len(can_remodel_total),
            'can_special_gear': len(can_special_gear),
            'special_gear_obtained': len(special_gear_obtained),
            'special_gear_not_obtained': len(special_gear_not_obtained)
        }
    
    def add_ship(self, ship: Ship):
        if not self.dev_mode or not self.account_manager.is_developer():
            raise PermissionError("只有开发者模式下的开发者账户才能新增舰船")
        existing_ids = {s.id for s in self.ships}
        # 处理 game_order
        if ship.game_order != 0:
            existing = next((s for s in self.ships if s.game_order == ship.game_order), None)
            if existing:
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    None, "图鉴顺序冲突",
                    f"图鉴顺序 {ship.game_order} 已被 {existing.name} 占用。\n"
                    f"是否自动将 {ship.game_order} 及之后的船顺序向后延后一位？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    # 延后冲突及之后的船
                    for s in self.ships:
                        if s.game_order >= ship.game_order:
                            s.game_order += 1
                    # 新船使用原顺序
                    ship.game_order = ship.game_order
                    # 重新排序
                    self.ships.sort(key=lambda s: s.game_order)
                else:
                    print("用户取消添加")
                    return None
        else:
            # 自动分配：取最大 game_order + 1
            max_order = max((s.game_order for s in self.ships), default=0)
            ship.game_order = max_order + 1
            """添加新船，若 ship.id 为 0 则自动分配，否则检查冲突并可能自动调整"""
        
        if ship.id == 0:
            # 自动分配：取最大 ID + 1
            max_id = max(existing_ids, default=0)
            new_id = max_id + 1
            # 确保新 ID 不冲突（如果 max_id+1 意外被占用？但理论上不会，因为 existing_ids 已包含所有）
            while new_id in existing_ids:
                new_id += 1  # 极罕见情况，但保留
            ship.id = new_id
        else:
            # 手动指定 ID，检查是否冲突
            if ship.id in existing_ids:
                # 冲突处理：弹窗询问用户是否自动分配新 ID，或抛出异常
                # 这里我们选择自动分配新 ID 并给出警告
                print(f"警告：ID {ship.id} 已存在，将自动分配新 ID")
                max_id = max(existing_ids, default=0)
                new_id = max_id + 1
                while new_id in existing_ids:
                    new_id += 1
                ship.id = new_id
                # 可选：通过信号或返回值通知用户
            # 如果未冲突，直接使用 ship.id

        if not ship.can_remodel:
            ship.remodel_date = ""

        self.ships.append(ship)
        self.ships.sort(key=lambda s: s.game_order)
        #self.save()
        self._bump_version()
        self._save_static()
        self.data_changed.emit()
        #print(f"保存的 can_special_gear: {ship.can_special_gear}")
        print(f"已添加舰船 ID={ship.id}, 当前总数为 {len(self.ships)}")
        return ship.id
    
    def update_ship(self, old_id, new_ship):
        """
        更新指定 ID 的舰船数据
        :param ship_id: 原舰船的 ID
        :param old_id: 原舰船的 ID
        :param new_ship: 新的 Ship 对象（应包含更新后的所有字段）
        :return: 是否成功
        """
        if not self.dev_mode or not self.account_manager.is_developer():
            raise PermissionError("只有开发者模式下的开发者账户才能编辑静态数据")
        # 1. 处理 ID 变更
        new_ship = copy.deepcopy(new_ship)
        #print(f"[1] 传入 new_ship 的 special_gear_name: {new_ship.special_gear_name}")
        #print(f"更新前 ID: {old_id}, 新 ID: {new_ship.id}")
        # 查找所有匹配的索引（理论上只有一个）
        indices = [i for i, s in enumerate(self.ships) if s.id == old_id]
        if not indices:
            return False
        # 替换所有匹配的项（通常只有一个）
        for i in indices:
            self.ships[i] = new_ship
        # 如果存在重复，删除多余的（这里简单处理：保留最后一个替换的，删除其他）
        # 但更推荐在数据加载时保证 ID 唯一性。
        # 去重
        seen = set()
        unique_ships = []
        for s in self.ships:
            if s.id not in seen:
                seen.add(s.id)
                unique_ships.append(s)
            else:
                print(f"警告：发现重复 ID {s.id}，已跳过")
        self.ships = unique_ships
        #print(f"[2] 替换后列表中对应 ID 的船的 special_gear_name: {self.ships[-1].special_gear_name}")
        #if new_ship.id != old_id:
        #    conflict = next((s for s in self.ships if s.id == new_ship.id), None)
            #print(f"用户输入的 ID: {self.id_spin.value()}")
        #    if conflict:
        #        from PySide6.QtWidgets import QMessageBox
        #        reply = QMessageBox.question(
        #            None, "ID 冲突",
        #            f"ID {new_ship.id} 已被 {conflict.name} 占用。\n"
        #            f"是否自动分配新 ID？",
        #            QMessageBox.Yes | QMessageBox.No
        #        )
        #        if reply == QMessageBox.No:
        #            return False
        #        else:
        #            # 自动分配新 ID
        #            max_id = max((s.id for s in self.ships), default=0)
        #            new_ship.id = max_id + 1
        #        # 移除旧船，添加新船
        #        self.ships = [s for s in self.ships if s.id != old_id]
        #        self.ships.append(new_ship)
        #        print(f"[2] 替换后列表中对应 ID 的船的 special_gear_name: {self.ships[-1].special_gear_name}")
        #    else:
        #        # ID 未变，直接替换
        #        for i, s in enumerate(self.ships):
        #            if s.id == old_id:
        #                self.ships[i] = new_ship
        #                print(f"[2] 替换后列表中索引 {i} 的船的 special_gear_name: {self.ships[i].special_gear_name}")
        #                break

        # 2. 处理 game_order 冲突（如果需要）
        # 如果 game_order 发生变化，检查冲突
        # 注意：new_ship 可能已经在上面的分支中更新了 ID，但 game_order 可能已由用户修改
        # 我们检测是否有其他船占用相同的 game_order（排除自身）
        #print(f"[3] 处理 game_order 冲突前，new_ship 的 special_gear_name: {new_ship.special_gear_name}")
        conflict_order = next((s for s in self.ships if s.id != new_ship.id and s.game_order == new_ship.game_order), None)
        if conflict_order:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                None, "图鉴顺序冲突",
                f"图鉴顺序 {new_ship.game_order} 已被 {conflict_order.name} 占用。\n"
                f"是否自动将 {new_ship.game_order} 及之后的船顺序向后延后一位？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                for s in self.ships:
                    if s.id != new_ship.id and s.game_order >= new_ship.game_order:
                        s.game_order += 1
            else:
                return False  # 用户取消更新
            
        if not new_ship.can_remodel:
            new_ship.remodel_date = ""

        # 替换列表中的对象
        #print(f"[4] 处理 game_order 冲突后，new_ship 的 special_gear_name: {new_ship.special_gear_name}")
        temp = new_ship
        self.ships.sort(key=lambda s: s.game_order)
        #print(f"[5] 排序后，temp 的 special_gear_name: {temp.special_gear_name}")
        #print(f"[5] 排序后，列表中 ID {new_ship.id} 的船的 special_gear_name: {next(s for s in self.ships if s.id == new_ship.id).special_gear_name}")
        self._bump_version()
        self._save_static()
        self.data_changed.emit()
        #self.save()
        updated = next((s for s in self.ships if s.id == new_ship.id), None)
        print(f"更新后，列表中 ID {new_ship.id} 的对象: {updated}")
        return True
    
    def _bump_version(self):
        """增加版本号（次版本号+1，超过99则主版本号+1，次版本号归零）"""
        try:
            major, minor = map(int, self.version.split('.'))
        except:
            major, minor = 0, 1
        minor += 1
        if minor >= 100:
            major += 1
            minor = 0
        self.version = f"{major}.{minor}"
        print(f"[版本] 数据版本已更新至 {self.version}")
        # 注意：这里不保存，由调用者保存静态数据

    def _save_static(self):
        """保存静态数据到文件（开发模式专用）"""
        if not self.dev_mode or not self.account_manager.is_developer():
            raise PermissionError("只有开发者模式下的开发者账户才能保存静态数据")
        static_ships = []
        for ship in self.ships:
            ship_dict = ship.to_dict()
            for field in self.USER_STATE_FIELDS:
                ship_dict.pop(field, None)
            static_ships.append(ship_dict)
        os.makedirs(os.path.dirname(self.static_path), exist_ok=True)
        with open(self.static_path, 'w', encoding='utf-8') as f:
            json.dump({"version": self.version, "ships": static_ships}, f, indent=2, ensure_ascii=False)
        print(f"[静态数据] 已保存至 {self.static_path}")

    def switch_account(self, new_account):
        """切换账户，重新加载状态文件"""
        self.state_path = f"data/users/{new_account}/ships_state.json"
        self.load()  # 重新加载数据
        self.data_changed.emit()

    def export_static(self, export_path):
        """将当前内存中的静态数据导出到指定文件（仅开发模式可用）"""
        if not self.dev_mode:
            raise PermissionError("非开发模式不能导出静态数据")
        static_ships = []
        for ship in self.ships:
            # 排除用户状态字段
            ship_dict = ship.to_dict()
            for field in self.USER_STATE_FIELDS:
                ship_dict.pop(field, None)
            static_ships.append(ship_dict)
        export_data = {
            "version": self.version,
            "ships": static_ships
        }
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"静态数据已导出至 {export_path}")

    def export_csv(self, path):
        import pandas as pd
        # 将每个 ship 的复杂字段转换为 JSON 字符串，避免 pandas 生成 NaN
        export_data = []
        for ship in self.ships:
            d = ship.to_dict()
            # 将列表和字典字段转为 JSON 字符串
            for field in ['drop_locations', 'tech_affects', 'bonus_obtain', 'bonus_120']:
                if field in d:
                    d[field] = json.dumps(d[field], ensure_ascii=False)
            # 将日期字段空值转为空字符串
            for field in ['remodel_date', 'release_date', 'special_gear_date']:
                if d.get(field) is None:
                    d[field] = ""
            export_data.append(d)
        df = pd.DataFrame(export_data)
        df.to_csv(path, index=False, encoding='utf-8-sig', quoting=1)

    def export_excel(self, path):
        import pandas as pd
        df = pd.DataFrame([s.to_dict() for s in self.ships])
        df.to_excel(path, index=False)

    def import_csv(self, path):
        import pandas as pd
        import ast
        import dataclasses
        from models import Ship

        try:
            # 读取 CSV，指定所有列为字符串类型，避免 pandas 自动转换
            df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[''], encoding='utf-8-sig')
        except Exception as e:
            raise Exception(f"CSV 文件读取失败: {e}")

        ships = []
        required_fields = self.REQUIRED_FIELDS

        for idx, row in df.iterrows():
            data = row.to_dict()
            data = {k.strip(): v for k, v in data.items()}
            # 1. 修复版本号：如果 CSV 中的 version 列存在，但不应覆盖 ships.json 的版本号，我们忽略它。
            # 实际导入时，版本号保持原 manager 的版本，不依赖 CSV。

            # 2. 处理特殊字段：列表、字典、日期等
            for field in required_fields:
                if field not in data or data[field] in (None, "", "nan", "NaN", "null"):
                    default = Ship.__dataclass_fields__[field].default
                    if default is dataclasses._MISSING_TYPE:
                        field_type = Ship.__dataclass_fields__[field].type
                        if field_type == int:
                            data[field] = 0
                        elif field_type == str:
                            data[field] = ""
                        elif field_type == bool:
                            data[field] = False
                        elif field_type == list:
                            data[field] = []
                        elif field_type == dict:
                            data[field] = {}
                        else:
                            data[field] = None
                    else:
                        data[field] = default
                    continue

                val = data[field]
                
                if field in ('drop_locations', 'tech_affects'):
                    if isinstance(val, str):
                        # 尝试 JSON 解析
                        try:
                            parsed = json.loads(val)
                            data[field] = parsed if isinstance(parsed, list) else []
                        except:
                            # 尝试 Python 字面量解析（如 "['a','b']"）
                            try:
                                parsed = ast.literal_eval(val)
                                data[field] = parsed if isinstance(parsed, list) else []
                            except:
                                # 最后尝试按逗号分割（如果看起来像列表）
                                if val.startswith('[') and val.endswith(']'):
                                    data[field] = [s.strip() for s in val[1:-1].split(',') if s.strip()]
                                else:
                                    data[field] = []
                    else:
                        data[field] = val if isinstance(val, list) else []

                # 字典字段
                elif field in ('bonus_obtain', 'bonus_120'):
                    if isinstance(val, str):
                        try:
                            parsed = json.loads(val)
                            data[field] = parsed if isinstance(parsed, dict) else {}
                        except:
                            try:
                                parsed = ast.literal_eval(val)
                                data[field] = parsed if isinstance(parsed, dict) else {}
                            except:
                                data[field] = {}
                    else:
                        data[field] = val if isinstance(val, dict) else {}

                # 布尔字段
                elif field in ('owned', 'remodeled', 'oath', 'level_120', 'can_remodel',
                               'can_special_gear', 'special_gear_obtained', 'is_permanent'):
                    if isinstance(val, bool):
                        data[field] = val
                    else:
                        # 将字符串 "True"/"true"/"1" 转为 True，其余为 False
                        data[field] = val.lower() in ('true', '1', 'yes')
                
                # 整数字段（包括 id, game_order, breakthrough, tech_points_* 以及所有 tech_*_obtain 等，但这里只列出一部分，其他会在循环外处理？）
                elif field in ('id', 'game_order', 'breakthrough',
                            'tech_points_obtain', 'tech_points_max', 'tech_points_120'):
                    try:
                        data[field] = int(float(val))
                    except:
                        data[field] = 0

                # 日期字段（保持字符串）
                elif field in ('remodel_date', 'release_date', 'special_gear_date'):
                    data[field] = str(val) if val else ""

                # 其他字符串字段
                else:
                    data[field] = str(val)

            # 额外处理：所有 tech_xxx_obtain, tech_xxx_max, tech_xxx_120 字段（属性加成）
            # 这些字段的数量很多，我们动态检测并转换为整数
            for key in list(data.keys()):
                if key.startswith('tech_') and (key.endswith('_obtain') or key.endswith('_max') or key.endswith('_120')):
                    try:
                        data[key] = int(float(data[key]))
                    except:
                        data[key] = 0

            # 过滤出合法字段（只保留 Ship 类中定义的字段）
            filtered_item = {k: v for k, v in data.items() if k in required_fields}
            try:
                ship = Ship.from_dict(filtered_item)
                ships.append(ship)
            except Exception as e:
                print(f"警告: 第 {idx+2} 行数据转换失败，已跳过: {e}")
                continue

        if not ships:
            raise Exception("CSV 文件中没有有效的舰船数据")
        self.ships = ships
        if self.dev_mode:
            self._save_static()
        self.save()

    def update_from_github(self, url: str, backup: bool = True) -> bool:
        """
        从远程 URL 更新舰船数据
        :param url: 远程 JSON 文件的 URL
        :param backup: 是否在更新前备份当前文件
        :return: 是否成功
        """
        import requests
        import os
        import shutil
        try:
            print(f"正在从 {url} 获取最新数据...")
            resp = requests.get(url, timeout=10, verify=certifi.where())
            resp.raise_for_status()
            remote_data = resp.json()

            # 验证数据格式（至少包含一条记录，且每条记录有 id 和 name）
            if isinstance(remote_data, dict) and "version" in remote_data and "ships" in remote_data:
                remote_version = remote_data.get("version", "0.0")
                remote_ships = remote_data.get("ships", [])
            elif isinstance(remote_data, list):
                remote_version = "0.0"   # 假设旧格式版本为1.0
                remote_ships = remote_data
            else:
                raise ValueError("远程数据格式错误")
            
            # 比较版本
            if self._version_compare(remote_version, self.version) <= 0:
                print("远程版本不高于本地版本，无需更新")
                return False

            # 备份当前文件
            if backup and os.path.exists(self.static_path):
                shutil.copy2(self.static_path, self.static_path + ".bak")
            with open(self.static_path, 'w', encoding='utf-8') as f:
                json.dump(remote_data, f, indent=2, ensure_ascii=False)

            self.version = remote_version
            self.save()
            self.load()
            print("数据更新成功！")
            return True

        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            raise Exception(f"网络更新失败: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            raise Exception(f"远程数据格式错误: {e}")
        except Exception as e:
            print(f"更新过程中发生错误: {e}")
            raise

    def _version_compare(self, v1, v2):
        """比较两个版本号，v1 > v2 返回正数，相等返回0，v1 < v2 返回负数"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        v1_parts = normalize(v1)
        v2_parts = normalize(v2)
        # 补零使长度相同
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        if v1_parts > v2_parts:
            return 1
        elif v1_parts < v2_parts:
            return -1
        else:
            return 0

    def _merge_user_data(self, new_ships: list):
        """
        将当前用户数据（拥有状态、突破数等）合并到新数据中
        策略：以新数据为基础，如果旧数据中有相同 ID 的船，则保留用户的 owned、breakthrough、oath、level_120 等状态
        """
        # 建立旧数据字典，以 ID 为键
        old_dict = {s.id: s for s in self.ships}

        for new_ship in new_ships:
            old_ship = old_dict.get(new_ship.id)
            if old_ship:
                # 保留用户的自定义状态
                new_ship.owned = old_ship.owned
                new_ship.breakthrough = old_ship.breakthrough
                new_ship.oath = old_ship.oath
                new_ship.level_120 = old_ship.level_120
                # 如果还保留了其他状态（如改造、誓约等），也可一并合并
                new_ship.remodeled = old_ship.remodeled
                # 注意：科技点数值以新数据为准（因为可能修正了数值）

    def _auto_assign_game_order(self):
        """如果所有船的 game_order 都是 0，则根据当前列表顺序自动分配"""
        if not self.ships:
            return
        if any(ship.game_order != 0 for ship in self.ships):
            print("已有非零 game_order，跳过自动分配")
            return
        print("开始自动分配 game_order")
        for idx, ship in enumerate(self.ships, start=1):
            ship.game_order = idx
        self._save_static()
        print(f"已自动分配 game_order，范围 1-{len(self.ships)}")

    def get_latest_version(self):
        """从GitHub获取最新版本号"""
        try:
            url = "https://api.github.com/repos/xiwangzaiqianfang/AzurLane-Dex/releases/latest"
            resp = requests.get(url, timeout=10, verify=certifi.where())
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "")
                if tag.startswith("v"):
                    tag = tag[1:]
                return tag
        except Exception as e:
            print(f"获取版本失败: {e}")
        return None
    
    def get_program_version(self):
        """读取程序版本号"""
        version_file = (resource_path("version.json"))
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("version", "0.0.0")
            except:
                return "0.0.0"
        return "0.0.0"
    
    def _match_ship_class(self, ship, cls):
        """根据舰种分类匹配"""
        if cls == "前排先锋":
            return ship.ship_class in ["驱逐", "轻巡", "重巡", "超巡", "重炮", "维修"]
        elif cls == "后排主力":
            return ship.ship_class in ["战列", "战巡", "航战", "航母", "轻航"]
        elif cls == "驱逐":
            return ship.ship_class == "驱逐"
        elif cls == "轻巡":
            return ship.ship_class == "轻巡"
        elif cls == "重巡":
            return ship.ship_class in ["重巡", "超巡"]
        elif cls == "战列":
            return ship.ship_class in ["战列", "战巡", "航战"]
        elif cls == "航母":
            return ship.ship_class in ["航母", "轻航"]
        elif cls == "维修":
            return ship.ship_class == "维修"
        elif cls == "潜艇":
            return ship.ship_class in ["潜艇", "潜母"]
        elif cls == "其他":
            return ship.ship_class in ["运输", "风帆", "工作舰"]
        return False

    def _has_attr_bonus(self, ship, attr):
        """检查舰船是否拥有指定属性加成（获得+120级）"""
        attr_map = {
            "炮击": "firepower",
            "航空": "aviation",
            "机动": "mobility",
            "防空": "aa",
            "雷击": "torpedo",
            "装填": "reload",
            "耐久": "durability",
            "反潜": "antisub"
        }
        base = attr_map.get(attr)
        if not base:
            return False
        obtain = getattr(ship, f"tech_{base}_obtain", 0)
        val120 = getattr(ship, f"tech_{base}_120", 0)
        return (obtain + val120) > 0
    
    def get_total_tech_points(self):
        """计算所有舰船（无论是否拥有）的科技点总和（获得+满破+120级）"""
        total = 0
        for ship in self.ships:
            total += ship.tech_points_obtain + ship.tech_points_max + ship.tech_points_120
        return total
    
    def get_owned_tech_points(self):
        """计算已拥有舰船的科技点总和"""
        total = 0
        for ship in self.ships:
            if ship.owned:
                total += ship.tech_points_obtain
                if ship.is_max_breakthrough():
                    total += ship.tech_points_max
                if ship.level_120:
                    total += ship.tech_points_120
        return total

    def _migrate_old_data(self):
        """将旧的 ships.json 拆分为静态数据和用户状态文件"""
        if not os.path.exists("ships.json"):
            return
        print("检测到旧数据文件 ships.json，正在自动迁移...")
        try:
            with open("ships.json", 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 兼容旧格式
            if isinstance(data, dict) and "version" in data and "ships" in data:
                version = data["version"]
                ships = data["ships"]
            elif isinstance(data, list):
                version = "0.0"
                ships = data
            else:
                raise ValueError("无法识别的 ships.json 格式")

            ship_fields = Ship.__dataclass_fields__
            static_ships = []
            state_list = []

            for ship in ships:
                self._clean_ship_dict(ship)   # 注意：ship 是字典，会被原地修改
                
                # 分离数据
                # 静态数据：复制所有字段，然后移除用户状态字段
                static = ship.copy()
                for field in self.USER_STATE_FIELDS:
                    static.pop(field, None)
                static_ships.append(static)

                # 用户状态：只保留 id 和状态字段
                state = {"id": ship["id"]}
                for field in self.USER_STATE_FIELDS:
                    if field in ship:
                        state[field] = ship[field]
                state_list.append(state)

            static_data = {"version": version, "ships": static_ships}
            state_data = {"states": state_list}

            # 确保静态数据目录存在
            os.makedirs(os.path.dirname(self.static_path), exist_ok=True)
            with open(self.static_path, 'w', encoding='utf-8') as f:
                json.dump(static_data, f, indent=2, ensure_ascii=False)

            # 用户状态：需要确定当前账户名。如果没有账户，先创建默认账户
            current_user = self.account_manager.get_current_account()
            if not current_user:
                current_user = "default"
                self.account_manager.add_account(current_user, password="")
                self.account_manager.set_current_account(current_user)
            self.state_path = self._get_state_path()   # 获取正确路径
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            # 备份旧文件
            backup_path = "ships.json.bak"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename("ships.json", backup_path)
            print("数据迁移成功！原文件已备份为 ships.json.bak")
        except Exception as e:
            print(f"数据迁移失败: {e}")
            raise

        # 迁移 accounts.json
        if os.path.exists("accounts.json"):
            print("检测到旧账户文件 accounts.json，正在迁移...")
            try:
                with open("accounts.json", 'r', encoding='utf-8') as f:
                    accounts_data = json.load(f)
                # 新路径
                new_accounts_path = "data/users/accounts.json"
                os.makedirs(os.path.dirname(new_accounts_path), exist_ok=True)
                with open(new_accounts_path, 'w', encoding='utf-8') as f:
                    json.dump(accounts_data, f, indent=2, ensure_ascii=False)
                # 备份旧文件
                backup_accounts = "accounts.json.bak"
                if os.path.exists(backup_accounts):
                    os.remove(backup_accounts)
                os.rename("accounts.json", backup_accounts)
                print("accounts.json 迁移成功")
            except Exception as e:
                print(f"accounts.json 迁移失败: {e}")

        # 迁移 edit_log.json
        if os.path.exists("edit_log.json"):
            print("检测到旧日志文件 edit_log.json，正在迁移...")
            try:
                log_dir = "data/log"
                os.makedirs(log_dir, exist_ok=True)
                new_log_path = os.path.join(log_dir, "edit_log.json")
                shutil.copy2("edit_log.json", new_log_path)
                backup_log = "edit_log.json.bak"
                if os.path.exists(backup_log):
                    os.remove(backup_log)
                os.rename("edit_log.json", backup_log)
                print("edit_log.json 迁移成功")
            except Exception as e:
                print(f"edit_log.json 迁移失败: {e}")

        #self._save_static()
        #self.save()

    def import_user_state(self, import_path, as_new_account=False, new_account_name=None):
        """
        导入用户状态文件
        :param import_path: 要导入的文件路径
        :param as_new_account: 是否创建新账户
        :param new_account_name: 新账户名称（当 as_new_account=True 时必填）
        """
        if not os.path.exists(import_path):
            raise FileNotFoundError("导入文件不存在")

        if as_new_account:
            if not new_account_name:
                raise ValueError("创建新账户需要提供账户名")
            # 创建新账户（密码可选，这里设为空）
            success = self.account_manager.add_account(new_account_name, password="")
            if not success:
                raise Exception(f"账户 {new_account_name} 已存在")
            # 复制状态文件到新账户的状态文件路径
            new_state_path = f"ships_state_{new_account_name}.json"
            shutil.copy2(import_path, new_state_path)
            # 切换到新账户
            self.account_manager.set_current_account(new_account_name)
            self.state_path = new_state_path
            self.load()
        else:
            # 覆盖当前账户
            shutil.copy2(import_path, self.state_path)
            self.load()

        self.data_changed.emit()

    def _get_state_path(self):
        current_user = self.account_manager.get_current_account()
        if current_user:
            user_folder = os.path.join(self.user_dir, current_user)
            os.makedirs(user_folder, exist_ok=True)
            return os.path.join(user_folder, "ships_state.json")
        return None
    
    def _clean_field_value(self, value, field_type):
        """清洗单个字段的值，返回清洗后的值或 None（应使用默认值）"""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in ("nan", "null", "none", "na", ""):
                return None
            if field_type == int:
                try:
                    return int(float(stripped))
                except:
                    return 0
            elif field_type == bool:
                return stripped.lower() in ("true", "1", "yes")
            elif field_type == list:
                # 尝试解析 JSON 数组
                if stripped.startswith('[') and stripped.endswith(']'):
                    try:
                        import json
                        parsed = json.loads(stripped)
                        return parsed if isinstance(parsed, list) else []
                    except:
                        return []
                return []
            elif field_type == dict:
                if stripped.startswith('{') and stripped.endswith('}'):
                    try:
                        import json
                        parsed = json.loads(stripped)
                        return parsed if isinstance(parsed, dict) else {}
                    except:
                        return {}
                return {}
            else:
                return stripped
        return value

    def _clean_ship_dict(self, ship_dict):
        """清洗单个舰船字典（原地修改）"""
        for field, value in list(ship_dict.items()):
            if field == 'id':
                continue
            field_info = Ship.__dataclass_fields__.get(field)
            if field_info is None:
                # 如果字段不在模型中，删除它
                del ship_dict[field]
                continue
            field_type = field_info.type
            cleaned = self._clean_field_value(value, field_type)
            if cleaned is None:
                # 设置默认值
                if field_type == int:
                    ship_dict[field] = 0
                elif field_type == str:
                    ship_dict[field] = ""
                elif field_type == bool:
                    ship_dict[field] = False
                elif field_type == list:
                    ship_dict[field] = []
                elif field_type == dict:
                    ship_dict[field] = {}
                else:
                    ship_dict[field] = None
            else:
                ship_dict[field] = cleaned
        # 特殊联动：如果不可改造，清空改造日期
        if not ship_dict.get("can_remodel", False):
            ship_dict["remodel_date"] = ""
        return ship_dict
    
    def _migrate_old_bonus(self, ship_dict):
        """将旧的多个属性加成字段转换为单一属性加成（原地修改 ship 对象）"""
        attr_map = [
            ("耐久", "durability"),
            ("炮击", "firepower"),
            ("雷击", "torpedo"),
            ("防空", "aa"),
            ("航空", "aviation"),
            ("命中", "accuracy"),
            ("装填", "reload"),
            ("机动", "mobility"),
            ("反潜", "antisub")
        ]
        
        # 获得时加成
        if "obtain_bonus_attr" not in ship_dict or not ship_dict.get("obtain_bonus_attr"):
            for attr_name, base in attr_map:
                val = ship_dict.get(f"tech_{base}_obtain", 0)
                if val != 0:
                    ship_dict["obtain_bonus_attr"] = attr_name
                    ship_dict["obtain_bonus_value"] = val
                    break
            else:
                # 没有非零加成，设置空值
                ship_dict.setdefault("obtain_bonus_attr", "")
                ship_dict.setdefault("obtain_bonus_value", 0)

        # 120级时加成
        if "level120_bonus_attr" not in ship_dict or not ship_dict.get("level120_bonus_attr"):
            for attr_name, base in attr_map:
                val = ship_dict.get(f"tech_{base}_120", 0)
                if val != 0:
                    ship_dict["level120_bonus_attr"] = attr_name
                    ship_dict["level120_bonus_value"] = val
                    break
            else:
                ship_dict.setdefault("level120_bonus_attr", "")
                ship_dict.setdefault("level120_bonus_value", 0)

        # 适用舰种迁移（如果旧的 tech_affects 存在且新列表为空）
        if (not ship_dict.get("obtain_affects") and 
            "tech_affects" in ship_dict and ship_dict["tech_affects"]):
            ship_dict["obtain_affects"] = ship_dict["tech_affects"].copy()
        if (not ship_dict.get("level120_affects") and 
            "tech_affects" in ship_dict and ship_dict["tech_affects"]):
            ship_dict["level120_affects"] = ship_dict["tech_affects"].copy()

        # 可选：删除旧字段，保持数据干净
        for _, base in attr_map:
            ship_dict.pop(f"tech_{base}_obtain", None)
            ship_dict.pop(f"tech_{base}_max", None)
            ship_dict.pop(f"tech_{base}_120", None)
        ship_dict.pop("tech_affects", None)