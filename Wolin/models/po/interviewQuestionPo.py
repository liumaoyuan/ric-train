from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Wolin.db.connectionInit import WolinModuleDBModel


class InterviewQuestionPo(WolinModuleDBModel):
    """
    模拟面试问题表 —— 存储基于简历生成的面试问题及其 TTS 音频路径。
    """
    table_alias: ClassVar[str] = 'interview_questions'
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_alias}` (
            `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '问题 ID',
            `record_uuid` VARCHAR(36) NOT NULL COMMENT '关联面试记录 UUID',
            `question_text` VARCHAR(500) NOT NULL COMMENT '问题文本',
            `question_order` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '问题排序序号',
            `tts_audio_path` VARCHAR(500) COMMENT 'TTS 音频文件路径',
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

            PRIMARY KEY (`id`),
            KEY `idx_record_uuid` (`record_uuid`),
            KEY `idx_question_order` (`question_order`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模拟面试问题表';
        """

    id: Optional[int] = Field(None, description="问题 ID")
    record_uuid: str = Field(..., description="关联面试记录 UUID")
    question_text: str = Field(..., description="问题文本")
    question_order: int = Field(0, description="问题排序序号")
    tts_audio_path: Optional[str] = Field(None, description="TTS 音频文件路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def find_by_record_uuid(cls, record_uuid: str) -> list["InterviewQuestionPo"]:
        """根据面试记录 UUID 查询问题列表，按 question_order 升序排序。"""
        return cls.find_by(record_uuid=record_uuid, order_by="question_order", order="ASC")


if __name__ == '__main__':
    po = InterviewQuestionPo()
    po.create_table()
    print("模拟面试问题表创建成功")
