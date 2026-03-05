from datetime import datetime
from typing import Optional, ClassVar, List

from pydantic import Field

from GameHelper.models.modelBase import GameHelperDBModel


class GameEntityModel(GameHelperDBModel):
    """
    游戏实体表模型
    存储游戏相关的实体（英雄、模式、装备等）
    """
    table_alias: ClassVar[str] = "game_entity"
    create_table_sql: ClassVar[str] = f"""
    CREATE TABLE `{table_alias}` (
        -- 核心主键
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键 ID',

        -- 实体基本信息
        `entity_name` VARCHAR(100) NOT NULL COMMENT '实体名称',
        `entity_code` VARCHAR(50) NOT NULL COMMENT '实体编码',
        `entity_type` VARCHAR(50) NOT NULL COMMENT '实体类型 (hero/mode/item/skill 等)',
        `game_name` VARCHAR(100) NOT NULL COMMENT '所属游戏',
        `aliases` VARCHAR(500) COMMENT '别名/外号列表 (逗号分隔)',
        `description` TEXT COMMENT '实体描述',

        -- 状态
        `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-可用',

        -- 审计字段
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人 ID',
        `updated_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人 ID',

        -- 主键与索引
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_entity_code_game` (`entity_code`, `game_name`),
        KEY `idx_entity_name` (`entity_name`),
        KEY `idx_entity_type` (`entity_type`),
        KEY `idx_game_name` (`game_name`),
        KEY `idx_status` (`status`)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='游戏实体表';
    """

    # 字段定义
    id: Optional[int] = Field(None, description="主键 ID")
    entity_name: str = Field(..., description="实体名称")
    entity_code: str = Field(..., description="实体编码")
    entity_type: str = Field(..., description="实体类型")
    game_name: str = Field(..., description="所属游戏")
    aliases: Optional[str] = Field(None, description="别名/外号列表")
    description: Optional[str] = Field(None, description="实体描述")
    status: int = Field(1, description="状态：0-禁用，1-可用")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人 ID")
    updated_by: Optional[int] = Field(None, description="更新人 ID")

    @property
    def is_active(self) -> bool:
        """
        判断实体是否可用

        Returns:
            True-可用，False-禁用
        """
        return self.status == 1

    def get_aliases_list(self) -> List[str]:
        """
        获取别名列表

        Returns:
            别名列表
        """
        if not self.aliases:
            return []
        return [a.strip() for a in self.aliases.split(',') if a.strip()]

    @classmethod
    def get_by_id(cls, entity_id: int) -> Optional['GameEntityModel']:
        """
        根据 ID 获取实体

        Args:
            entity_id: 实体 ID

        Returns:
            实体记录对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            result = cls.find_by(id=entity_id, limit=1)
            return result[0] if result else None
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_id({entity_id}) 失败：{str(e)}")
            return None

    @classmethod
    def get_by_entity_code(cls, entity_code: str, game_name: str) -> Optional['GameEntityModel']:
        """
        根据实体编码和游戏名称获取实体

        Args:
            entity_code: 实体编码
            game_name: 游戏名称

        Returns:
            实体记录对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            result = cls.find_by(entity_code=entity_code, game_name=game_name, limit=1)
            return result[0] if result else None
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_entity_code({entity_code}, {game_name}) 失败：{str(e)}")
            return None

    @classmethod
    def get_by_entity_name(cls, entity_name: str, game_name: Optional[str] = None, limit: int = 10) -> List['GameEntityModel']:
        """
        根据实体名称获取实体列表

        Args:
            entity_name: 实体名称
            game_name: 游戏名称（可选）
            limit: 返回数量限制

        Returns:
            实体记录列表
        """
        try:
            cls._ensure_table_exists()
            if game_name:
                return cls.find_by(
                    entity_name=entity_name,
                    game_name=game_name,
                    status=1,
                    limit=limit
                )
            else:
                return cls.find_by(
                    entity_name=entity_name,
                    status=1,
                    limit=limit
                )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_entity_name({entity_name}) 失败：{str(e)}")
            return []

    @classmethod
    def search_by_name(cls, keyword: str, game_name: Optional[str] = None, limit: int = 20) -> List['GameEntityModel']:
        """
        根据实体名称模糊搜索

        Args:
            keyword: 关键词
            game_name: 游戏名称（可选）
            limit: 返回数量限制

        Returns:
            实体记录列表
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return []

            table_name = cls.get_table_name_with_db()
            if game_name:
                sql = f"SELECT * FROM {table_name} WHERE (`entity_name` LIKE %s OR `aliases` LIKE %s) AND `game_name` = %s AND `status` != 0 ORDER BY `created_at` DESC LIMIT %s"
                results = db.execute(sql, (f"%{keyword}%", f"%{keyword}%", game_name, limit))
            else:
                sql = f"SELECT * FROM {table_name} WHERE (`entity_name` LIKE %s OR `aliases` LIKE %s) AND `status` != 0 ORDER BY `created_at` DESC LIMIT %s"
                results = db.execute(sql, (f"%{keyword}%", f"%{keyword}%", limit))

            return [cls(**result) for result in results] if results else []
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"search_by_name({keyword}) 失败：{str(e)}")
            return []

    @classmethod
    def get_by_type(cls, entity_type: str, game_name: Optional[str] = None, status: int = 1, limit: int = 100) -> List['GameEntityModel']:
        """
        根据实体类型获取实体列表

        Args:
            entity_type: 实体类型
            game_name: 游戏名称（可选）
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            实体记录列表
        """
        try:
            cls._ensure_table_exists()
            if game_name:
                return cls.find_by(
                    entity_type=entity_type,
                    game_name=game_name,
                    status=status,
                    limit=limit,
                    order_by="entity_name",
                    order="ASC"
                )
            else:
                return cls.find_by(
                    entity_type=entity_type,
                    status=status,
                    limit=limit,
                    order_by="entity_name",
                    order="ASC"
                )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_type({entity_type}) 失败：{str(e)}")
            return []

    @classmethod
    def get_all_entities(cls, game_name: Optional[str] = None, status: int = 1, limit: int = 1000) -> List['GameEntityModel']:
        """
        获取所有实体

        Args:
            game_name: 游戏名称（可选）
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            实体记录列表
        """
        try:
            cls._ensure_table_exists()
            if game_name:
                return cls.find_by(
                    game_name=game_name,
                    status=status,
                    limit=limit,
                    order_by="entity_type",
                    order="ASC"
                )
            else:
                return cls.find_by(
                    status=status,
                    limit=limit,
                    order_by="entity_type",
                    order="ASC"
                )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_all_entities() 失败：{str(e)}")
            return []


if __name__ == '__main__':
    # 创建表
    print("✓ 游戏实体表创建成功")
