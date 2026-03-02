from datetime import datetime
from typing import Optional, ClassVar
from pydantic import Field
from Base.Repository.models.defaultDbModel import DefaultDbModel


class PaperPo(DefaultDbModel):
    """
    试卷表实体类
    """
    table_alias: ClassVar[str] = 'papers'
    create_table_sql = f"""
        -- 试卷表
        CREATE TABLE IF NOT EXISTS `{table_alias}` (
            `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '试卷 ID',
            `paper_uuid` VARCHAR(36) NOT NULL DEFAULT (UUID()) COMMENT '试卷 UUID',
            `parent_id` BIGINT UNSIGNED COMMENT '父版本 ID（用于版本控制）',

            -- 试卷基本信息
            `paper_name` VARCHAR(200) NOT NULL COMMENT '试卷名称',
            `description` TEXT COMMENT '试卷描述',
            `subject` VARCHAR(50) COMMENT '科目',

            -- 题目配置
            `question_ids` VARCHAR(500) NOT NULL COMMENT '题目 ID 列表（逗号分隔，有序）',
            `scores` VARCHAR(500) COMMENT '每题分值（逗号分隔，为空则使用默认分值）',
            `default_score_type` VARCHAR(50) DEFAULT 'uniform_1' COMMENT '默认分值类型：uniform_1=每题 1 分',

            -- 考试配置
            `duration_minutes` INT DEFAULT 30 COMMENT '考试时长（分钟）',

            -- 状态管理
            `status` VARCHAR(20) DEFAULT 'draft' COMMENT '状态：draft|published|archived',
            `is_public` TINYINT DEFAULT 1 COMMENT '是否公开：0-私有，1-公开',

            -- 审计字段
            `created_by` BIGINT UNSIGNED NOT NULL COMMENT '创建者 ID',
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

            PRIMARY KEY (`id`),
            KEY `idx_paper_uuid` (`paper_uuid`),
            KEY `idx_parent_id` (`parent_id`),
            KEY `idx_subject` (`subject`),
            KEY `idx_status` (`status`),
            KEY `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试卷表';
        """

    # 字段定义
    id: Optional[int] = Field(None, description="试卷 ID")
    paper_uuid: Optional[str] = Field(None, description="试卷 UUID")
    parent_id: Optional[int] = Field(None, description="父版本 ID")

    # 试卷基本信息
    paper_name: str = Field(..., description="试卷名称")
    description: Optional[str] = Field(None, description="试卷描述")
    subject: Optional[str] = Field(None, description="科目")

    # 题目配置
    question_ids: str = Field(..., description="题目 ID 列表（逗号分隔）")
    scores: Optional[str] = Field(None, description="每题分值（逗号分隔）")
    default_score_type: str = Field('uniform_1', description="默认分值类型")

    # 考试配置
    duration_minutes: Optional[int] = Field(30, description="考试时长（分钟）")

    # 状态管理
    status: str = Field('draft', description="状态：draft|published|archived")
    is_public: Optional[int] = Field(1, description="是否公开：0-私有，1-公开")

    # 审计字段
    created_by: int = Field(..., description="创建者 ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @property
    def get_question_id_list(self) -> list:
        """获取题目 ID 列表"""
        if not self.question_ids:
            return []
        return [int(x.strip()) for x in self.question_ids.split(',') if x.strip()]

    @property
    def get_score_list(self) -> list:
        """获取分值列表"""
        if not self.scores:
            return []
        return [float(x.strip()) for x in self.scores.split(',') if x.strip()]

    @property
    def total_score(self) -> float:
        """计算总分"""
        score_list = self.get_score_list
        if score_list:
            return sum(score_list)
        # 使用默认分值（每题 1 分）
        return len(self.get_question_id_list) * 1.0

    def get_score_for_question(self, question_index: int) -> float:
        """
        获取指定题目的分值

        Args:
            question_index: 题目索引（从 0 开始）

        Returns:
            题目分值，默认为 1 分
        """
        score_list = self.get_score_list
        if score_list and question_index < len(score_list):
            return score_list[question_index]
        return 1.0  # 默认分值

    @classmethod
    def get_by_uuid(cls, paper_uuid: str) -> Optional['PaperPo']:
        """
        根据 UUID 查询试卷

        Args:
            paper_uuid: 试卷 UUID

        Returns:
            试卷对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return None

            table_name = cls.get_table_name()
            sql = f"SELECT * FROM `{table_name}` WHERE `paper_uuid` = %s LIMIT 1"
            result = db.execute(sql, (paper_uuid,))

            if not result:
                return None

            return cls(**result[0])
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_by_uuid({paper_uuid}) 失败：{str(e)}")
            return None

    @classmethod
    def get_versions(cls, parent_id: int) -> list:
        """
        获取某个试卷的所有版本

        Args:
            parent_id: 父版本 ID

        Returns:
            试卷版本列表，按创建时间倒序排列
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return []

            table_name = cls.get_table_name()
            sql = f"""
                SELECT * FROM `{table_name}`
                WHERE `parent_id` = %s OR `id` = %s
                ORDER BY `created_at` DESC
            """
            results = db.execute(sql, (parent_id, parent_id))

            if not results:
                return []

            return [cls(**row) for row in results]
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_versions({parent_id}) 失败：{str(e)}")
            return []


if __name__ == '__main__':
    po = PaperPo()
    po.create_table()
    print("试卷表创建成功")
