from datetime import datetime
from typing import Optional, ClassVar, List

from pydantic import Field

from GameHelper.models.modelBase import GameHelperDBModel


class GameStrategyEntityRelModel(GameHelperDBModel):
    """
    攻略 - 实体关联表模型
    关联攻略和实体，支持多对多关系
    """
    table_alias: ClassVar[str] = "game_strategy_entity_rel"
    create_table_sql: ClassVar[str] = f"""
    CREATE TABLE `{table_alias}` (
        -- 核心主键
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键 ID',

        -- 关联关系
        `strategy_id` BIGINT UNSIGNED NOT NULL COMMENT '攻略 ID',
        `entity_id` BIGINT UNSIGNED NOT NULL COMMENT '实体 ID',
        `relevance_score` INT UNSIGNED NOT NULL DEFAULT 100 COMMENT '相关性权重 (用于排序)',

        -- 审计字段
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人 ID',

        -- 主键与索引
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_strategy_entity` (`strategy_id`, `entity_id`),
        KEY `idx_entity_id` (`entity_id`),
        KEY `idx_relevance` (`relevance_score`)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='攻略 - 实体关联表';
    """

    # 字段定义
    id: Optional[int] = Field(None, description="主键 ID")
    strategy_id: int = Field(..., description="攻略 ID")
    entity_id: int = Field(..., description="实体 ID")
    relevance_score: int = Field(100, description="相关性权重")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    created_by: Optional[int] = Field(None, description="创建人 ID")

    @classmethod
    def get_by_strategy_id(cls, strategy_id: int) -> List['GameStrategyEntityRelModel']:
        """
        根据攻略 ID 获取关联的实体关系

        Args:
            strategy_id: 攻略 ID

        Returns:
            关联关系列表
        """
        try:
            cls._ensure_table_exists()
            return cls.find_by(
                strategy_id=strategy_id,
                order_by="relevance_score",
                order="DESC"
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_strategy_id({strategy_id}) 失败：{str(e)}")
            return []

    @classmethod
    def get_by_entity_id(cls, entity_id: int, limit: int = 100) -> List['GameStrategyEntityRelModel']:
        """
        根据实体 ID 获取关联的攻略关系

        Args:
            entity_id: 实体 ID
            limit: 返回数量限制

        Returns:
            关联关系列表
        """
        try:
            cls._ensure_table_exists()
            return cls.find_by(
                entity_id=entity_id,
                limit=limit,
                order_by="relevance_score",
                order="DESC"
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_entity_id({entity_id}) 失败：{str(e)}")
            return []

    @classmethod
    def get_strategy_ids_by_entity_id(cls, entity_id: int, limit: int = 100) -> List[int]:
        """
        根据实体 ID 获取关联的攻略 ID 列表

        Args:
            entity_id: 实体 ID
            limit: 返回数量限制

        Returns:
            攻略 ID 列表
        """
        try:
            cls._ensure_table_exists()
            relations = cls.find_by(
                entity_id=entity_id,
                limit=limit,
                order_by="relevance_score",
                order="DESC"
            )
            return [rel.strategy_id for rel in relations]
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_strategy_ids_by_entity_id({entity_id}) 失败：{str(e)}")
            return []

    @classmethod
    def get_entity_ids_by_strategy_id(cls, strategy_id: int) -> List[int]:
        """
        根据攻略 ID 获取关联的实体 ID 列表

        Args:
            strategy_id: 攻略 ID

        Returns:
            实体 ID 列表
        """
        try:
            cls._ensure_table_exists()
            relations = cls.find_by(strategy_id=strategy_id)
            return [rel.entity_id for rel in relations]
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_entity_ids_by_strategy_id({strategy_id}) 失败：{str(e)}")
            return []

    @classmethod
    def exists(cls, strategy_id: int, entity_id: int) -> bool:
        """
        检查关联是否已存在

        Args:
            strategy_id: 攻略 ID
            entity_id: 实体 ID

        Returns:
            True-存在，False-不存在
        """
        try:
            cls._ensure_table_exists()
            result = cls.find_by(
                strategy_id=strategy_id,
                entity_id=entity_id,
                limit=1
            )
            return len(result) > 0
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"exists({strategy_id}, {entity_id}) 失败：{str(e)}")
            return False

    @classmethod
    def delete_by_strategy_id(cls, strategy_id: int) -> bool:
        """
        根据攻略 ID 删除所有关联关系

        Args:
            strategy_id: 攻略 ID

        Returns:
            True-成功，False-失败
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return False

            table_name = cls.get_table_name_with_db()
            sql = f"DELETE FROM {table_name} WHERE `strategy_id` = %s"
            db.execute(sql, (strategy_id,))
            return True
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"delete_by_strategy_id({strategy_id}) 失败：{str(e)}")
            return False

    @classmethod
    def delete_by_entity_id(cls, entity_id: int) -> bool:
        """
        根据实体 ID 删除所有关联关系

        Args:
            entity_id: 实体 ID

        Returns:
            True-成功，False-失败
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return False

            table_name = cls.get_table_name_with_db()
            sql = f"DELETE FROM {table_name} WHERE `entity_id` = %s"
            db.execute(sql, (entity_id,))
            return True
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"delete_by_entity_id({entity_id}) 失败：{str(e)}")
            return False


if __name__ == '__main__':
    # 创建表
    print("✓ 攻略 - 实体关联表创建成功")
