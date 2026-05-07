from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Wolin.db.connectionInit import WolinModuleDBModel


class InterviewDialoguePo(WolinModuleDBModel):
    """
    面试对话记录表 —— 一场面试包含多轮对话，一条数据对应一轮问答。
    通过 record_uuid 关联 interview_records 表。
    """
    table_alias: ClassVar[str] = 'interview_dialogues'
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_alias}` (
            `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '对话记录 ID',
            `record_uuid` VARCHAR(36) NOT NULL COMMENT '关联面试记录 UUID',
            `dialogue_order` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '对话轮次序号',
            `question_text` TEXT COMMENT '面试官问题文本',
            `question_tts_path` VARCHAR(500) COMMENT '问题对应的 TTS 音频文件路径',
            `answer_text` TEXT COMMENT '求职者回答文本（ASR 转写）',
            `answer_audio_path` VARCHAR(500) COMMENT '求职者回答的原始音频路径',
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

            PRIMARY KEY (`id`),
            KEY `idx_record_uuid` (`record_uuid`),
            KEY `idx_dialogue_order` (`dialogue_order`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面试对话记录表';
        """

    id: Optional[int] = Field(None, description="对话记录 ID")
    record_uuid: str = Field(..., description="关联面试记录 UUID")
    dialogue_order: int = Field(0, description="对话轮次序号")
    question_text: Optional[str] = Field(None, description="面试官问题文本")
    question_tts_path: Optional[str] = Field(None, description="问题对应的 TTS 音频文件路径")
    answer_text: Optional[str] = Field(None, description="求职者回答文本")
    answer_audio_path: Optional[str] = Field(None, description="求职者回答的原始音频路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    @classmethod
    def create_dialogue(cls, record_uuid: str, question_text: str, answer_text: str,
                        question_tts_path: Optional[str] = None,
                        answer_audio_path: Optional[str] = None) -> "InterviewDialoguePo":
        """
        创建一轮面试对话记录，自动计算轮次序号。
        """
        max_order = cls.find_by(record_uuid=record_uuid, order_by="dialogue_order", order="DESC", limit=1)
        next_order = (max_order[0].dialogue_order + 1) if max_order else 1

        dialogue = cls(
            record_uuid=record_uuid,
            dialogue_order=next_order,
            question_text=question_text,
            answer_text=answer_text,
            question_tts_path=question_tts_path,
            answer_audio_path=answer_audio_path,
        )
        dialogue.save()
        return dialogue


if __name__ == '__main__':
    po = InterviewDialoguePo()
    po.create_table()
    print("面试对话记录表创建成功")
