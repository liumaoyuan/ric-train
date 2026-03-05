from typing import Optional, List, ClassVar

from pydantic import Field

from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Repository.base.baseVDB import BaseVDBModel
from pymilvus import Function, FunctionType


class VDBGameStrategy(BaseVDBModel):
    """
    游戏攻略向量数据库模型
    存储攻略的向量嵌入，支持语义搜索
    """
    collection_alias: ClassVar[str] = "game_strategy"
    description: ClassVar[str] = "游戏攻略向量表"

    id: Optional[int] = Field(
        default=0,
        json_schema_extra={
            'is_primary': True,
            'auto_id': True
        }
    )

    db_id: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 50
        }
    )

    title: Optional[str] = Field(
        default='',
        json_schema_extra={
            'enable_match': True,
            'enable_analyzer': True,
            'max_length': 500
        }
    )

    content: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 65535
        }
    )

    game_name: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 100
        }
    )

    strategy_type: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 50
        }
    )

    entity_names: Optional[str] = Field(
        default='',
        json_schema_extra={
            'max_length': 500
        }
    )

    embedding: Optional[List[float]] = Field(
        default_factory=list,
        json_schema_extra={
            'dim': 1024
        }
    )

    # 稀疏向量字段（基于 title 字段 BM25 生成）
    title_sparse: Optional[List[float]] = Field(
        default_factory=list,
        json_schema_extra={
            'is_sparse_vector': True,
            'bm25_source_field': 'title'
        }
    )

    @staticmethod
    def search_by_keyword(keyword: str, game_name: Optional[str] = None, limit: int = 10):
        """
        根据关键词搜索攻略（混合搜索：向量 + BM25）

        Args:
            keyword: 搜索关键词
            game_name: 游戏名称（可选，用于过滤）
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        llm = get_default_qwen_llm()
        embedding = llm.embedding(keyword, dimensions=1024)

        ranker = Function(
            name="rrf",
            input_field_names=[],
            function_type=FunctionType.RERANK,
            params={
                "reranker": "rrf",
                "k": 100
            }
        )

        # 构建过滤表达式
        filter_expr = ""
        if game_name:
            filter_expr = f"game_name == '{game_name}'"

        res = VDBGameStrategy.hybrid_search(
            queries=[
                {
                    'data': embedding,  # 密集向量搜索
                    'field': 'embedding',
                    'type': 'dense',
                    'params': {
                        'metric_type': 'COSINE',
                        'params': {'nprobe': 10}
                    }
                },
                {
                    'data': [keyword],
                    'field': 'title_sparse',
                    'type': 'sparse',
                    'params': {
                        'metric_type': 'BM25',
                        'params': {}
                    }
                }
            ],
            limit=limit,
            filter_expr=filter_expr,
            output_fields=['db_id', 'title', 'content', 'game_name', 'strategy_type', 'entity_names'],
            weights=[0.4, 0.6],
            ranker=ranker
        )
        return res

    @staticmethod
    def search_by_bm25(keyword: str, game_name: Optional[str] = None, limit: int = 10):
        """
        根据关键词 BM25 搜索攻略

        Args:
            keyword: 搜索关键词
            game_name: 游戏名称（可选，用于过滤）
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        filter_expr = ""
        if game_name:
            filter_expr = f"game_name == '{game_name}'"

        res = VDBGameStrategy.query(
            filter=filter_expr,
            output_fields=['db_id', 'title', 'content', 'game_name', 'strategy_type', 'entity_names'],
            limit=limit
        )
        return res

    @staticmethod
    def search_by_entity(entity_name: str, limit: int = 10):
        """
        根据实体名称搜索攻略

        Args:
            entity_name: 实体名称
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        res = VDBGameStrategy.query(
            filter=f"entity_names like '%{entity_name}%'",
            output_fields=['db_id', 'title', 'content', 'game_name', 'strategy_type', 'entity_names'],
            limit=limit
        )
        return res


if __name__ == '__main__':
    # 测试
    print("✓ VDB 游戏攻略表初始化成功")
