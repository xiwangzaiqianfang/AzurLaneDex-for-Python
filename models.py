from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class Ship:
    # 基本信息
    id: int
    name: str
    faction: str
    ship_class: str
    rarity: str
    alt_name: str = ""
    game_order: int = 0

    # 状态信息
    owned: bool = False
    breakthrough: int = 0
    can_remodel: bool = False
    remodel_date: str = ""
    remodeled: bool = False
    oath: bool = False
    level_120: bool = False
    can_special_gear: bool = False
    special_gear_obtained: bool = False

    # 获取方式
    acquire_main: str = ""
    acquire_detail: str = ""
    build_time: str = ""
    drop_locations: List[str] = field(default_factory=list)
    shop_exchange: str = ""
    is_permanent: bool = True

    # 实装活动
    debut_event: str = ""
    release_date: str = ""
    notes: str = ""
    
    special_gear_name: str = ""          # 特殊兵装名称
    special_gear_date: str = ""          # 实装日期
    special_gear_acquire: str = ""       # 特殊兵装获取方式

    # 科技点数据（每个属性三阶段：获得、满破、120级）
    tech_points_obtain: int = 0
    tech_points_max: int = 0
    tech_points_120: int = 0

    tech_affects: List[str] = field(default_factory=list)  # 科技点适用舰种列表
    obtain_affects: List[str] = field(default_factory=list)
    level120_affects: List[str] = field(default_factory=list)
    
    # 获得时加成（单一属性）
    obtain_bonus_attr: str = ""      # 属性名，如 "耐久"、"炮击"等
    obtain_bonus_value: int = 0      # 加成数值
    obtain_affects: List[str] = field(default_factory=list)   # 适用舰种列表

    # 120级时加成（单一属性）
    level120_bonus_attr: str = ""    # 属性名
    level120_bonus_value: int = 0    # 加成数值
    level120_affects: List[str] = field(default_factory=list)  # 适用舰种列表

    # 加成属性（每个属性三阶段：获得、满破、120级）
    tech_durability_obtain: int = 0
    tech_durability_max: int = 0
    tech_durability_120: int = 0

    tech_firepower_obtain: int = 0
    tech_firepower_max: int = 0
    tech_firepower_120: int = 0

    tech_torpedo_obtain: int = 0
    tech_torpedo_max: int = 0
    tech_torpedo_120: int = 0

    tech_aa_obtain: int = 0
    tech_aa_max: int = 0
    tech_aa_120: int = 0

    tech_aviation_obtain: int = 0
    tech_aviation_max: int = 0
    tech_aviation_120: int = 0

    tech_accuracy_obtain: int = 0
    tech_accuracy_max: int = 0
    tech_accuracy_120: int = 0

    tech_reload_obtain: int = 0
    tech_reload_max: int = 0
    tech_reload_120: int = 0

    tech_mobility_obtain: int = 0
    tech_mobility_max: int = 0
    tech_mobility_120: int = 0

    tech_antisub_obtain: int = 0
    tech_antisub_max: int = 0
    tech_antisub_120: int = 0

    # 立绘路径
    image_path: str = ""

    def is_max_breakthrough(self) -> bool:
        """是否满破 (突破3次)"""
        return self.breakthrough == 3

    def get_tech_total(self, base_attr: str) -> int:
        """
        根据舰船当前状态计算某科技属性的总和
        base_attr: 属性前缀，如 'tech_durability'
        """
        total = 0
        if self.owned:
            total += getattr(self, f"{base_attr}_obtain", 0)
            if self.is_max_breakthrough():
                total += getattr(self, f"{base_attr}_max", 0)
            if self.level_120:
                total += getattr(self, f"{base_attr}_120", 0)
        return total

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        # 处理 drop_locations 可能是字符串的情况
        if 'drop_locations' in data and isinstance(data['drop_locations'], str):
            data['drop_locations'] = data['drop_locations'].split(';') if data['drop_locations'] else []
        return cls(**data)