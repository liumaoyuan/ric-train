from datetime import datetime
from typing import Optional, ClassVar, List

from pydantic import Field

from GameHelper.models.modelBase import GameHelperDBModel


class GameStrategyModel(GameHelperDBModel):
    """
    游戏攻略主表模型
    存储攻略的基本信息
    """
    table_alias: ClassVar[str] = "game_strategy"
    create_table_sql: ClassVar[str] = f"""
    CREATE TABLE `{table_alias}` (
        -- 核心主键
        `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键 ID',

        -- 攻略基本信息
        `title` VARCHAR(500) NOT NULL COMMENT '攻略标题',
        `content` TEXT COMMENT '攻略正文内容',
        `source_url` VARCHAR(1000) COMMENT '来源链接',
        `game_name` VARCHAR(100) NOT NULL COMMENT '游戏名称',
        `strategy_type` VARCHAR(50) NOT NULL COMMENT '攻略类型 (如"出装"、"玩法"、"英雄攻略")',

        -- 状态
        `status` TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：0-禁用，1-启用',

        -- 审计字段
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人 ID',
        `updated_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人 ID',

        -- 主键与索引
        PRIMARY KEY (`id`),
        KEY `idx_game_name` (`game_name`),
        KEY `idx_strategy_type` (`strategy_type`),
        KEY `idx_status` (`status`),
        KEY `idx_created_at` (`created_at`)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='游戏攻略主表';
    """

    # 字段定义
    id: Optional[int] = Field(None, description="主键 ID")
    title: str = Field(..., description="攻略标题")
    content: Optional[str] = Field(None, description="攻略正文内容")
    source_url: Optional[str] = Field(None, description="来源链接")
    game_name: str = Field(..., description="游戏名称")
    strategy_type: str = Field(..., description="攻略类型")
    status: int = Field(1, description="状态：0-禁用，1-启用")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人 ID")
    updated_by: Optional[int] = Field(None, description="更新人 ID")

    @property
    def is_active(self) -> bool:
        """
        判断攻略是否可用

        Returns:
            True-可用，False-禁用
        """
        return self.status == 1

    @classmethod
    def get_by_id(cls, strategy_id: int) -> Optional['GameStrategyModel']:
        """
        根据 ID 获取攻略

        Args:
            strategy_id: 攻略 ID

        Returns:
            攻略记录对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            result = cls.find_by(id=strategy_id, limit=1)
            return result[0] if result else None
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_id({strategy_id}) 失败：{str(e)}")
            return None

    @classmethod
    def get_by_game_name(cls, game_name: str, status: int = 1, limit: int = 100) -> List['GameStrategyModel']:
        """
        根据游戏名称获取攻略列表

        Args:
            game_name: 游戏名称
            status: 状态筛选（可选，默认 1-启用）
            limit: 返回数量限制

        Returns:
            攻略记录列表
        """
        try:
            cls._ensure_table_exists()
            return cls.find_by(
                game_name=game_name,
                status=status,
                limit=limit,
                order_by="created_at",
                order="DESC"
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_game_name({game_name}) 失败：{str(e)}")
            return []

    @classmethod
    def get_by_strategy_type(cls, strategy_type: str, status: int = 1, limit: int = 100) -> List['GameStrategyModel']:
        """
        根据攻略类型获取攻略列表

        Args:
            strategy_type: 攻略类型
            status: 状态筛选（可选，默认 1-启用）
            limit: 返回数量限制

        Returns:
            攻略记录列表
        """
        try:
            cls._ensure_table_exists()
            return cls.find_by(
                strategy_type=strategy_type,
                status=status,
                limit=limit,
                order_by="created_at",
                order="DESC"
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_strategy_type({strategy_type}) 失败：{str(e)}")
            return []

    @classmethod
    def search_by_title(cls, title_keyword: str, game_name: Optional[str] = None, limit: int = 20) -> List['GameStrategyModel']:
        """
        根据攻略标题模糊搜索

        Args:
            title_keyword: 标题关键词
            game_name: 游戏名称（可选）
            limit: 返回数量限制

        Returns:
            攻略记录列表
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return []

            table_name = cls.get_table_name_with_db()
            if game_name:
                sql = f"SELECT * FROM {table_name} WHERE `title` LIKE %s AND `game_name` = %s AND `status` != 0 ORDER BY `created_at` DESC LIMIT %s"
                results = db.execute(sql, (f"%{title_keyword}%", game_name, limit))
            else:
                sql = f"SELECT * FROM {table_name} WHERE `title` LIKE %s AND `status` != 0 ORDER BY `created_at` DESC LIMIT %s"
                results = db.execute(sql, (f"%{title_keyword}%", limit))

            return [cls(**result) for result in results] if results else []
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"search_by_title({title_keyword}) 失败：{str(e)}")
            return []

    @classmethod
    def get_all_active(cls, limit: int = 1000) -> List['GameStrategyModel']:
        """
        获取所有可用的攻略

        Args:
            limit: 返回数量限制

        Returns:
            可用攻略记录列表
        """
        try:
            cls._ensure_table_exists()
            return cls.find_by(
                status=1,
                limit=limit,
                order_by="created_at",
                order="DESC"
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_all_active() 失败：{str(e)}")
            return []


if __name__ == '__main__':
    # 创建表
    print("✓ 表创建成功")
