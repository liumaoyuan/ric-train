import logging

from Base.Ai.base import AssistantMessages, UserMessages
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Models.BaseLLMConversationModel import BaseLLMConversationModel
from Base.Models.VdbLLMConversation import VdbLLMConversation

logger = logging.getLogger(__name__)


class MemoryV1Service:


    @staticmethod
    def get_n_high_similarity_item(question: str, user_id: str = None, session_id: str = None, n: int = 5):
        """
        获取与 query 最相似的 n 个对话
        使用混合搜索（密集向量 + 稀疏向量）
        可选择性地按 user_id 和 session_id 进行过滤
        """
        llm = get_default_qwen_llm()
        dense_vectors = llm.embedding(text=question, dimensions=1024)

        # 构建过滤表达式
        filter_conditions = []
        if user_id:
            filter_conditions.append(f"user_id == '{user_id}'")
        if session_id:
            filter_conditions.append(f"session_id == '{session_id}'")

        filter_expr = " and ".join(filter_conditions) if filter_conditions else ""

        res = VdbLLMConversation.hybrid_search(
            queries=[
                {
                    'data': dense_vectors,  # 密集向量搜索
                    'field': 'embedding',
                    'type': 'dense',
                    'params': {
                        'metric_type': 'COSINE',
                        'params': {'nprobe': 10}
                    }
                },
                {
                    'data': [question],
                    'field': 'content_sparse',
                    'type': 'sparse',
                    'params': {
                        'metric_type': 'BM25',
                        'params': {}
                    }
                }
            ],
            limit=n,
            filter_expr=filter_expr,  # 添加过滤条件
            weights=[0.7, 0.3],  # 密集向量权重0.7，稀疏向量权重0.3
            output_fields=['db_id', 'session_id', 'user_id', 'question', 'answer']  # 返回需要的字段
        )
        return res

    @staticmethod
    def vdb_res_2_messages(res):
        """
        VDB 检索的会话结果 转换为 messages
        """
        result_list = []

        def dict_2_messages_join_list(dict_item: dict):
            result_list.append(UserMessages(prompt=dict_item.get('question')))
            result_list.append(AssistantMessages(prompt=dict_item.get('answer')))

        list(map(dict_2_messages_join_list, res))
        return result_list



    @staticmethod
    def get_simple_memory(question: str, user_id: str = None, session_id: str = None):
        """
        获取最简单的记忆
        """
        history = BaseLLMConversationModel.get_last_n_turns_context(user_id, session_id, 3)
        db_ids = [str(item.id) for item in history if isinstance(item, BaseLLMConversationModel)]
        history = BaseLLMConversationModel.db_res_2_messages(history)
        # 不做 user_id 和 session_id 的限制，  其他用户的优质提问也做参考
        similar_items = MemoryV1Service.get_n_high_similarity_item(question, n=10)
        logger.debug(f"【Simple Memory】DB近N轮已使用的 db_id: {db_ids}")
        logger.debug(f"【Simple Memory】VDB召回的 db_id: {[item.get('db_id') for item in similar_items]}")
        # 去重
        similar_items = [i for i in similar_items if i.get('db_id') not in db_ids]
        # todo:  相似度最低限制 做成 系统参数
        similar_items = [i for i in similar_items if i.get('distance') > 0.5]
        logger.debug(f"【Simple Memory】相似度筛选后的 db_id: {[item.get('db_id') for item in similar_items]}")

        similar_items = MemoryV1Service.vdb_res_2_messages(similar_items)

        return similar_items + history


if __name__ == '__main__':
    service = MemoryV1Service()
    context1 = service.get_simple_memory(question="你好", user_id="string", session_id="string")
    # context2 = service.get_n_high_similarity_item(question="五 加 六 等于几", n=5)
    # print(context1)
    # print(context2)
    for i1 in context1:
        print(i1)
