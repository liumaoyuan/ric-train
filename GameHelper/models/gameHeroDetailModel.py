from datetime import datetime
from typing import Optional, ClassVar, List, Dict, Any, Union
import json

from pydantic import Field, field_validator, field_serializer

from GameHelper.models.modelBase import GameHelperDBModel


class GameHeroDetailModel(GameHelperDBModel):
    """
    游戏英雄详情表模型
    存储英雄的详细信息，包括属性、技能、出装推荐等
    """
    table_alias: ClassVar[str] = "game_hero_detail"
    create_table_sql: ClassVar[str] = """
    CREATE TABLE `game_hero_detail` (
        -- 核心主键
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键 ID',
        `hero_id` VARCHAR(50) NOT NULL COMMENT '英雄 ID(关联 game_entity 表的 entity_code)',
        `game_name` VARCHAR(100) NOT NULL COMMENT '游戏名称',

        -- 英雄基本信息
        `hero_name` VARCHAR(100) NOT NULL COMMENT '英雄名称',
        `hero_alias` VARCHAR(100) COMMENT '英雄别名/英文名',
        `hero_title` VARCHAR(200) COMMENT '英雄称号',
        `roles` VARCHAR(100) COMMENT '角色定位 (逗号分隔，如：fighter,assassin)',
        `camp` VARCHAR(100) COMMENT '阵营',
        `damage_type` VARCHAR(20) COMMENT '伤害类型 (物理/魔法/混合)',

        -- 英雄属性 (基础值)
        `hp` DECIMAL(10,2) COMMENT '生命值',
        `hp_per_level` DECIMAL(10,2) COMMENT '生命成长',
        `mp` DECIMAL(10,2) COMMENT '法力值',
        `mp_per_level` DECIMAL(10,2) COMMENT '法力成长',
        `attack_damage` DECIMAL(10,2) COMMENT '攻击力',
        `attack_damage_per_level` DECIMAL(10,2) COMMENT '攻击成长',
        `attack_speed` DECIMAL(10,2) COMMENT '攻击速度',
        `attack_speed_per_level` DECIMAL(10,2) COMMENT '攻速成长',
        `armor` DECIMAL(10,2) COMMENT '护甲值',
        `armor_per_level` DECIMAL(10,2) COMMENT '护甲成长',
        `magic_resist` DECIMAL(10,2) COMMENT '魔法抗性',
        `magic_resist_per_level` DECIMAL(10,2) COMMENT '魔抗成长',
        `move_speed` INT COMMENT '移动速度',
        `attack_range` INT COMMENT '攻击距离',
        `hp_regen` DECIMAL(10,2) COMMENT '生命回复',
        `mp_regen` DECIMAL(10,2) COMMENT '法力回复',

        -- 英雄评分 (1-10)
        `attack_rating` INT COMMENT '攻击力评分',
        `defense_rating` INT COMMENT '防御力评分',
        `magic_rating` INT COMMENT '魔法评分',
        `difficulty_rating` INT COMMENT '难度评分',
        `mobility_rating` INT COMMENT '机动性评分',
        `utility_rating` INT COMMENT '功能性评分',
        `crowd_control_rating` INT COMMENT '控制能力评分',

        -- 出装推荐 (JSON 格式存储)
        `starting_items` JSON COMMENT '出门装推荐',
        `core_items` JSON COMMENT '核心装备推荐',
        `situational_items` JSON COMMENT ' situational 装备推荐',
        `boots_recommendation` JSON COMMENT '鞋子推荐',

        -- 符文推荐 (JSON 格式存储)
        `primary_runes` JSON COMMENT '主系符文',
        `secondary_runes` JSON COMMENT '副系符文',
        `shards` JSON COMMENT '符文碎片',

        -- 召唤师技能
        `summoner_spells` JSON COMMENT '召唤师技能推荐',

        -- 技能加点
        `skill_order` VARCHAR(50) COMMENT '技能加点顺序 (如：QWEQQQ)',
        `skill_max_order` VARCHAR(20) COMMENT '主副技能加点 (如：Q>E>W)',

        -- 对线技巧
        `ally_tips` JSON COMMENT '友方技巧',
        `enemy_tips` JSON COMMENT '敌方技巧',
        `strong_against` VARCHAR(200) COMMENT '优势对线',
        `weak_against` VARCHAR(200) COMMENT '劣势对线',

        -- 统计数据 (可以通过后续爬虫更新)
        `pick_rate` DECIMAL(5,2) COMMENT '登场率 (%%)',
        `win_rate` DECIMAL(5,2) COMMENT '胜率 (%%)',
        `ban_rate` DECIMAL(5,2) COMMENT '禁用率 (%%)',
        `games_played` INT COMMENT '出场次数',

        -- 皮肤数量
        `skin_count` INT DEFAULT 0 COMMENT '皮肤数量',

        -- 状态
        `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-可用',

        -- 审计字段
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人 ID',
        `updated_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人 ID',

        -- 主键与索引
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_hero_game` (`hero_id`, `game_name`),
        KEY `idx_hero_name` (`hero_name`),
        KEY `idx_roles` (`roles`(50)),
        KEY `idx_damage_type` (`damage_type`),
        KEY `idx_status` (`status`)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='游戏英雄详情表';
    """

    # 字段定义
    id: Optional[int] = Field(None, description="主键 ID")
    hero_id: str = Field(..., description="英雄 ID")
    game_name: str = Field(..., description="游戏名称")
    hero_name: str = Field(..., description="英雄名称")
    hero_alias: Optional[str] = Field(None, description="英雄别名")
    hero_title: Optional[str] = Field(None, description="英雄称号")
    roles: Optional[str] = Field(None, description="角色定位")
    camp: Optional[str] = Field(None, description="阵营")
    damage_type: Optional[str] = Field(None, description="伤害类型")

    # 英雄属性
    hp: Optional[float] = Field(None, description="生命值")
    hp_per_level: Optional[float] = Field(None, description="生命成长")
    mp: Optional[float] = Field(None, description="法力值")
    mp_per_level: Optional[float] = Field(None, description="法力成长")
    attack_damage: Optional[float] = Field(None, description="攻击力")
    attack_damage_per_level: Optional[float] = Field(None, description="攻击成长")
    attack_speed: Optional[float] = Field(None, description="攻击速度")
    attack_speed_per_level: Optional[float] = Field(None, description="攻速成长")
    armor: Optional[float] = Field(None, description="护甲值")
    armor_per_level: Optional[float] = Field(None, description="护甲成长")
    magic_resist: Optional[float] = Field(None, description="魔法抗性")
    magic_resist_per_level: Optional[float] = Field(None, description="魔抗成长")
    move_speed: Optional[int] = Field(None, description="移动速度")
    attack_range: Optional[int] = Field(None, description="攻击距离")
    hp_regen: Optional[float] = Field(None, description="生命回复")
    mp_regen: Optional[float] = Field(None, description="法力回复")

    # 英雄评分
    attack_rating: Optional[int] = Field(None, description="攻击力评分")
    defense_rating: Optional[int] = Field(None, description="防御力评分")
    magic_rating: Optional[int] = Field(None, description="魔法评分")
    difficulty_rating: Optional[int] = Field(None, description="难度评分")
    mobility_rating: Optional[int] = Field(None, description="机动性评分")
    utility_rating: Optional[int] = Field(None, description="功能性评分")
    crowd_control_rating: Optional[int] = Field(None, description="控制能力评分")

    # 出装推荐 (JSON)
    starting_items: Optional[Union[Dict[str, Any], str]] = Field(None, description="出门装推荐")
    core_items: Optional[Union[Dict[str, Any], str]] = Field(None, description="核心装备推荐")
    situational_items: Optional[Union[Dict[str, Any], str]] = Field(None, description=" situational 装备推荐")
    boots_recommendation: Optional[Union[Dict[str, Any], str]] = Field(None, description="鞋子推荐")

    # 符文推荐 (JSON)
    primary_runes: Optional[Union[Dict[str, Any], str]] = Field(None, description="主系符文")
    secondary_runes: Optional[Union[Dict[str, Any], str]] = Field(None, description="副系符文")
    shards: Optional[Union[Dict[str, Any], str]] = Field(None, description="符文碎片")

    # 召唤师技能
    summoner_spells: Optional[Union[Dict[str, Any], str]] = Field(None, description="召唤师技能推荐")

    # 技能加点
    skill_order: Optional[str] = Field(None, description="技能加点顺序")
    skill_max_order: Optional[str] = Field(None, description="主副技能加点")

    # 对线技巧
    ally_tips: Optional[Union[List[Any], str]] = Field(None, description="友方技巧")
    enemy_tips: Optional[Union[List[Any], str]] = Field(None, description="敌方技巧")
    strong_against: Optional[str] = Field(None, description="优势对线")
    weak_against: Optional[str] = Field(None, description="劣势对线")

    # 统计数据
    pick_rate: Optional[float] = Field(None, description="登场率")
    win_rate: Optional[float] = Field(None, description="胜率")
    ban_rate: Optional[float] = Field(None, description="禁用率")
    games_played: Optional[int] = Field(None, description="出场次数")

    skin_count: int = Field(0, description="皮肤数量")
    status: int = Field(1, description="状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人 ID")
    updated_by: Optional[int] = Field(None, description="更新人 ID")

    @classmethod
    def get_by_hero_id(cls, hero_id: str, game_name: str) -> Optional['GameHeroDetailModel']:
        """
        根据英雄 ID 获取详情

        Args:
            hero_id: 英雄 ID
            game_name: 游戏名称

        Returns:
            英雄详情对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            result = cls.find_by(hero_id=hero_id, game_name=game_name, limit=1)
            return result[0] if result else None
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_hero_id({hero_id}, {game_name}) 失败：{str(e)}")
            return None

    @classmethod
    def get_by_roles(cls, roles: str, game_name: str, limit: int = 50) -> List['GameHeroDetailModel']:
        """
        根据角色定位获取英雄列表

        Args:
            roles: 角色定位
            game_name: 游戏名称
            limit: 返回数量限制

        Returns:
            英雄详情列表
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return []

            table_name = cls.get_table_name_with_db()
            sql = f"SELECT * FROM {table_name} WHERE `roles` LIKE %s AND `game_name` = %s AND `status` = 1 ORDER BY `win_rate` DESC LIMIT %s"
            results = db.execute(sql, (f"%{roles}%", game_name, limit))
            return [cls(**result) for result in results] if results else []
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_roles({roles}) 失败：{str(e)}")
            return []

    @classmethod
    def get_high_winrate_heroes(cls, game_name: str, min_win_rate: float = 52.0, limit: int = 20) -> List['GameHeroDetailModel']:
        """
        获取高胜率英雄

        Args:
            game_name: 游戏名称
            min_win_rate: 最低胜率
            limit: 返回数量限制

        Returns:
            英雄详情列表
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return []

            table_name = cls.get_table_name_with_db()
            sql = f"SELECT * FROM {table_name} WHERE `game_name` = %s AND `win_rate` >= %s AND `status` = 1 ORDER BY `win_rate` DESC LIMIT %s"
            results = db.execute(sql, (game_name, min_win_rate, limit))
            return [cls(**result) for result in results] if results else []
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_high_winrate_heroes() 失败：{str(e)}")
            return []

    @property
    def is_high_winrate(self) -> bool:
        """判断是否为高胜率英雄"""
        return self.win_rate is not None and self.win_rate >= 52.0

    @property
    def is_popular(self) -> bool:
        """判断是否为热门英雄"""
        return self.pick_rate is not None and self.pick_rate >= 10.0


if __name__ == '__main__':
    print("✓ 英雄详情表模型加载成功")
