from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.moduleDbModel import BaseModuleDBModel


class BaseLLMConversationModel(BaseModuleDBModel):
    """
    LLM 对话记录模型
    """
    table_alias: ClassVar[str] = "base_llm_conversation"
    create_table_sql: ClassVar[str] = f"""
                    CREATE TABLE `{table_alias}` (
                    -- 核心字段
                    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    `session_id` VARCHAR(64) COMMENT '会话ID',
                    `user_id` VARCHAR(64) COMMENT '用户ID',

                    -- 对话内容
                    `question` VARCHAR(2000) NOT NULL COMMENT '用户提问',
                    `answer` TEXT COMMENT 'AI 回答',
                    `context` TEXT COMMENT '完整上下文（JSON 格式或拼接文本）',

                    -- 模型与模式
                    `ai_model` VARCHAR(100) COMMENT 'AI 模型名称',
                    `ai_agent` VARCHAR(100) COMMENT 'AI Agent/助手名称',
                    `stream_mode` VARCHAR(20) DEFAULT '0' COMMENT '交互模式：0-非流式，1-流式，2-深度思考，3-embedding，4-asr，5-ocr',

                    -- 状态与错误
                    `status` VARCHAR(20) DEFAULT 'success' COMMENT '状态：success|failed|timeout',
                    `error_msg` TEXT COMMENT '错误信息',
                    `source` VARCHAR(50) COMMENT '请求来源：web|app|api|plugin',

                    -- 性能与时间
                    `duration_ms` INT UNSIGNED COMMENT '总耗时（毫秒）',
                    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

                    -- 主键与索引
                    PRIMARY KEY (`id`),
                    KEY `idx_session_id` (`session_id`),
                    KEY `idx_user_id` (`user_id`),
                    KEY `idx_created_at` (`created_at`),
                    KEY `idx_ai_model` (`ai_model`),
                    KEY `idx_status` (`status`),
                    KEY `idx_source` (`source`)

                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM 对话记录表';
                """

    # 字段定义
    id: Optional[int] = Field(None, description="主键ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    question: str = Field('', description="用户提问")
    answer: Optional[str] = Field(None, description="AI 回答")
    context: Optional[str] = Field(None, description="完整上下文（JSON 格式或拼接文本）")
    ai_model: Optional[str] = Field(None, description="AI 模型名称")
    ai_agent: Optional[str] = Field(None, description="AI Agent/助手名称")
    stream_mode: str = Field('0', description="交互模式：0-非流式，1-流式，2-深度思考，3-embedding，4-asr，5-ocr")
    status: str = Field('success', description="状态：success|failed|timeout")
    error_msg: Optional[str] = Field(None, description="错误信息")
    source: Optional[str] = Field(None, description="请求来源：web|app|api|plugin")
    duration_ms: Optional[int] = Field(None, description="总耗时（毫秒）")
    created_at: Optional[datetime] = Field(None, description="创建时间")



if __name__ == '__main__':
    BaseLLMConversationModel.create_table()
