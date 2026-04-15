import requests
import dataclasses
import hashlib
import json
import os
import certifi
import datetime
import copy
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

    def __init__(self, filepath="ships.json"):
        super().__init__()
        self.filepath = filepath
        self.config_file = "config.json"
        self.config = self.load_config()
        self.version = "0.9.5"
        self.ships: list[Ship] = []
        #theme_mode = self.config.get("theme_mode", "system")
        #if theme_mode == "system":
        #    self.current_theme = "light"
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
        if not os.path.exists(self.filepath):
            self._create_sample_data()
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 文件损坏: {e}")

        print(f"[DEBUG] 原始数据类型: {type(raw_data)}")
        if isinstance(raw_data, dict):
            print(f"[DEBUG] 字典键: {list(raw_data.keys())}")

            # 兼容旧版本：如果 data 是列表，则包装成新格式
            if isinstance(raw_data, dict) and "version" in raw_data and "ships" in raw_data:
                self.version = raw_data.get("version", "0.0")
                ships_data = raw_data["ships"]
                print(f"[DEBUG] 新版格式，version={self.version}, ships_data 类型={type(ships_data)}")
            elif isinstance(raw_data, list):
                # 旧版格式：直接是数组
                self.version = "0.0"
                ships_data = raw_data
                print(f"[DEBUG] 旧版格式，直接数组，长度={len(ships_data)}")
            else:
                # 未知格式，尝试补救
                print("[ERROR] 无法识别的数据格式，将重置为空")
                self.version = "0.0"
                ships_data = []

        # 确保 ships_data 是列表
        if not isinstance(ships_data, list):
            ships_data = []  # 如果意外不是列表，重置为空

        ship_fields = set(Ship.__dataclass_fields__.keys())
        migrated = []

        for item in ships_data:
            # 旧数据迁移：如果存在旧式单字段科技点，将其转换为三阶段字段
            #self._migrate_old_tech_fields(item)
            if not isinstance(item, dict):
                print(f"警告: 遇到非字典数据，已跳过: {item}")
                continue
                
            # 补全所有缺失字段
            for field in ship_fields:
                if field not in item:
                    default_val = Ship.__dataclass_fields__[field].default
                    if default_val is dataclasses._MISSING_TYPE:
                        # 必需字段缺失，根据类型设置合理的默认值
                        field_type = Ship.__dataclass_fields__[field].type
                        if field_type == int:
                            item[field] = 0          # 例如 id 默认 0
                        elif field_type == str:
                            item[field] = ""          # 名称等默认空字符串
                        elif field_type == bool:
                            item[field] = False
                        elif field_type == list:
                            item[field] = []           # drop_locations 等列表
                        else:
                            item[field] = None
                    else:
                        item[field] = default_val  

            # 处理 drop_locations 字符串转列表
            if isinstance(item.get('drop_locations'), str):
                item['drop_locations'] = item['drop_locations'].split(';') if item['drop_locations'] else []

            # 仅保留合法字段
            filtered_item = {k: v for k, v in item.items() if k in ship_fields}
            migrated.append(filtered_item)


        # 转换为 Ship 对象
        self.ships = [Ship.from_dict(item) for item in migrated]
        print(f"[INFO] 成功加载 {len(self.ships)} 条舰船，版本 {self.version}")
        #self.version = version   # 可以在类中保存版本号
        for ship in self.ships:
        # 修复布尔字段
            for field_name, field_info in Ship.__dataclass_fields__.items():
                value = getattr(ship, field_name)
                field_type = field_info.type
    
                # 修复布尔字段
                if field_type == bool and isinstance(value, str):
                    setattr(ship, field_name, value.lower() == 'true')
                # 修复整数字段
                elif field_type == int and isinstance(value, str):
                    try:
                        setattr(ship, field_name, int(value))
                    except:
                        setattr(ship, field_name, 0)
                # 修复列表字段（可选）
                elif field_type == list and isinstance(value, str):
                    # 如果字符串是 JSON 数组格式，解析它
                    if value.startswith('[') and value.endswith(']'):
                        try:
                            setattr(ship, field_name, json.loads(value))
                        except:
                            setattr(ship, field_name, [])
                    else:
                        setattr(ship, field_name, [])
                elif field_type == str and not isinstance(value, str):
                    setattr(ship, field_name, str(value) if value is not None else "")
        self._auto_assign_game_order()
            
        #如果检测到旧格式，立即保存为新格式（可选）
        if isinstance(raw_data, list):
            self.save()   # 这会以新格式保存
                    
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
        log_file = "edit_log.json"
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
        # 检查 self.ships 是否全部是 Ship 对象
        for i, s in enumerate(self.ships):
            d = s.to_dict()
            for k, v in d.items():
                if hasattr(v, '__class__') and v.__class__.__name__ == '_MISSING_TYPE':
                    print(f"发现 _MISSING_TYPE 在 ship[{i}], 字段 {k}, 值 {v}")
                    # 可以在这里将该字段设为默认值，避免崩溃
                    # d[k] = 0  # 或根据类型设置
                    # 但更好的是在数据源头修复
            if not isinstance(s, Ship):
                print(f"错误: ships[{i}] 不是 Ship 对象: {s}")
                # 这里可以选择抛出异常或尝试修复
                raise TypeError(f"ships[{i}] 不是 Ship 对象")
    
        data_to_save = {
            "version": self.version,
            "ships": [s.to_dict() for s in self.ships]
        }
    
        # 先写入临时文件，再替换原文件
        temp_file = self.filepath + ".tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.filepath)
            self.data_changed.emit()
            print(f"[保存成功] {self.filepath} 版本 {self.version}，舰船数 {len(self.ships)}")
        except Exception as e:
            print(f"[保存失败] {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

        self.data_changed.emit()


    def _create_sample_data(self):
        sample = [
            Ship(
                id=1, name="泛用型布里", faction="其他", ship_class="驱逐", rarity="精锐",
                owned=False, breakthrough=0, oath=False, level_120=False, acquire_main="兑换、赠送", acquire_detail="日/周常任务、月度签到、活动任务、商店兑换、主线普通关卡三星奖励、新兵训练、礼包购买", shop_exchange="勋章、演习", release_date="2017年05月25日", notes="无法建造",
                tech_durability_obtain=0, tech_durability_max=0, tech_durability_120=0,
                tech_firepower_obtain=0, tech_firepower_max=0, tech_firepower_120=0,
                tech_torpedo_obtain=0, tech_torpedo_max=0, tech_torpedo_120=0,
                tech_aa_obtain=0, tech_aa_max=0, tech_aa_120=0,
                tech_aviation_obtain=0, tech_aviation_max=0, tech_aviation_120=0,
                tech_accuracy_obtain=0, tech_accuracy_max=0, tech_accuracy_120=0,
                tech_reload_obtain=0, tech_reload_max=0, tech_reload_120=0,
                tech_mobility_obtain=0, tech_mobility_max=0, tech_mobility_120=0,
                tech_antisub_obtain=0, tech_antisub_max=0, tech_antisub_120=0,
                bonus_obtain=[], bonus_120=[], tech_affects=["驱逐"],
                image_path="images/bulin.png"
            ),
            Ship(
                id=2, name="试作型布里MKII", faction="其他", ship_class="驱逐", rarity="超稀有",
                owned=False, breakthrough=0, oath=False, level_120=False, acquire_main="兑换、赠送", acquire_detail="日/周常任务、月度签到、活动任务、商店兑换、主线普通关卡三星奖励、新兵训练、礼包购买", shop_exchange="勋章、演习", release_date="2017年05月25日", notes="无法建造",
                tech_durability_obtain=0, tech_durability_max=0, tech_durability_120=0,
                tech_firepower_obtain=0, tech_firepower_max=0, tech_firepower_120=0,
                tech_torpedo_obtain=0, tech_torpedo_max=0, tech_torpedo_120=0,
                tech_aa_obtain=0, tech_aa_max=0, tech_aa_120=0,
                tech_aviation_obtain=0, tech_aviation_max=0, tech_aviation_120=0,
                tech_accuracy_obtain=0, tech_accuracy_max=0, tech_accuracy_120=0,
                tech_reload_obtain=0, tech_reload_max=0, tech_reload_120=0,
                tech_mobility_obtain=0, tech_mobility_max=0, tech_mobility_120=0,
                tech_antisub_obtain=0, tech_antisub_max=0, tech_antisub_120=0,
                bonus_obtain=[], bonus_120=[], tech_affects=["驱逐"],
                image_path="images/trial_bulin_mkii.png"
            ),
            Ship(
                id=3, name="特装型布里MKIII", faction="其他", ship_class="驱逐", rarity="海上传奇",
                owned=False, breakthrough=0, oath=False, level_120=False, acquire_main="兑换、赠送", acquire_detail="世界巡游赠送、带有UR的大型EX活动累计PT获取、布里支援计划、商店兑换", shop_exchange="原型商店", debut_event="蝶海梦花", release_date="2020年09月17日", notes="无法建造",
                tech_durability_obtain=0, tech_durability_max=0, tech_durability_120=0,
                tech_firepower_obtain=0, tech_firepower_max=0, tech_firepower_120=0,
                tech_torpedo_obtain=0, tech_torpedo_max=0, tech_torpedo_120=0,
                tech_aa_obtain=0, tech_aa_max=0, tech_aa_120=0,
                tech_aviation_obtain=0, tech_aviation_max=0, tech_aviation_120=0,
                tech_accuracy_obtain=0, tech_accuracy_max=0, tech_accuracy_120=0,
                tech_reload_obtain=0, tech_reload_max=0, tech_reload_120=0,
                tech_mobility_obtain=0, tech_mobility_max=0, tech_mobility_120=0,
                tech_antisub_obtain=0, tech_antisub_max=0, tech_antisub_120=0,
                bonus_obtain=[], bonus_120=[], tech_affects=["驱逐"],
                image_path="images/specialized_bulin_mkiii.png"
            )
        ]
        self.ships = sample
        self.version = "0.1"
        self.save()

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
                result = [s for s in result if lower_value in s.name.lower() or (s.special_gear_name and lower_value in s.special_gear_name.lower())]
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
        """
        bonuses = {}
        for ship in self.ships:
            if not ship.owned:
                continue
            affects = ship.tech_affects if ship.tech_affects else []
            if not affects:
                continue
            # 遍历九个属性
            for base_display, base_key in [
                ("耐久", "durability"), ("炮击", "firepower"), ("雷击", "torpedo"),
                ("防空", "aa"), ("航空", "aviation"), ("命中", "accuracy"),
                ("装填", "reload"), ("机动", "mobility"), ("反潜", "antisub")
            ]:
                # 获得时加成
                obtain = getattr(ship, f"tech_{base_key}_obtain", 0)
                val_120 = getattr(ship, f"tech_{base_key}_120", 0)
                # 强制转换
                try:
                    obtain = int(obtain)
                    val_120 = int(val_120)
                except:
                    obtain = 0
                    val_120 = 0
                if obtain != 0:
                    for sc in affects:
                        key = (sc, base_display)
                        bonuses[key] = bonuses.get(key, 0) + obtain
                # 120级加成
                if val_120 != 0:
                    for sc in affects:
                        key = (sc, base_display)
                        bonuses[key] = bonuses.get(key, 0) + val_120
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

        self.ships.append(ship)
        self.ships.sort(key=lambda s: s.game_order)
        self.save()
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

        # 替换列表中的对象
        #print(f"[4] 处理 game_order 冲突后，new_ship 的 special_gear_name: {new_ship.special_gear_name}")
        temp = new_ship
        self.ships.sort(key=lambda s: s.game_order)
        #print(f"[5] 排序后，temp 的 special_gear_name: {temp.special_gear_name}")
        #print(f"[5] 排序后，列表中 ID {new_ship.id} 的船的 special_gear_name: {next(s for s in self.ships if s.id == new_ship.id).special_gear_name}")
        self.save()
        updated = next((s for s in self.ships if s.id == new_ship.id), None)
        print(f"更新后，列表中 ID {new_ship.id} 的对象: {updated}")
        return True

    def switch_file(self, new_path):
        self.filepath = new_path
        self.load()

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
            if backup and os.path.exists(self.filepath):
                backup_path = self.filepath + ".bak"
                shutil.copy2(self.filepath, backup_path)
                print(f"已备份当前数据到 {backup_path}")

            # 数据迁移：确保新数据包含所有必要字段
            ship_fields = set(Ship.__dataclass_fields__.keys())
            migrated = []
            for item in remote_ships:
                # 补全缺失字段
                for field in ship_fields:
                    if field not in item:
                        default_val = Ship.__dataclass_fields__[field].default
                        item[field] = default_val
                # 处理 drop_locations 字符串转列表
                if isinstance(item.get('drop_locations'), str):
                    item['drop_locations'] = item['drop_locations'].split(';') if item['drop_locations'] else []
                # 仅保留合法字段
                filtered_item = {k: v for k, v in item.items() if k in ship_fields}
                migrated.append(filtered_item)

            # 将新数据转换为 Ship 对象列表
            new_ships = [Ship.from_dict(item) for item in migrated]

            # **重要：合并用户数据**（保留用户的拥有状态、突破数等）
            self._merge_user_data(new_ships)

            # 替换当前数据
            self.ships = new_ships
            self.version = remote_version
            self.save()
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
        self.save()
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