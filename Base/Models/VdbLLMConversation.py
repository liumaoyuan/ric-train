from typing import Optional, List

from Base.Ai.service.commonService import RewriteQuestionParams
from Base.Repository.base.baseVDB import BaseVDBModel
from pydantic import Field


class VdbLLMConversation(BaseVDBModel):
    collection_alias = "llm_conversation"
    description = "LLM 对话记录表"

    id: Optional[int] = Field(
        default=0,  # auto_id 时提供默认值，避免校验失败
        json_schema_extra={
            'is_primary': True,
            'auto_id': True
        }
    )

    db_id: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 64
        }
    )

    session_id: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 64
        }
    )

    user_id: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 64
        }
    )

    question: Optional[str] = Field(
        default='',
        json_schema_extra={
            'enable_match': True,
            'enable_analyzer': True,
            'max_length': 65535
        }
    )

    rewrite_question: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 65535
        }
    )

    answer: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 65535
        }
    )

    embedding: Optional[List[float]] = Field(
        default_factory=list,
        json_schema_extra={
            'dim': 1024
        }
    )

    # 稀疏向量字段（基于 BM25 文本字段生成）
    content_sparse: Optional[List[float]] = Field(
        default_factory=list,
        json_schema_extra={
            'is_sparse_vector': True,
            'bm25_source_field': 'question'
        }
    )


if __name__ == '__main__':
    VdbLLMConversation()
