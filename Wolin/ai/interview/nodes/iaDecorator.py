import logging
from functools import wraps
from Wolin.ai.interview.iaState import IAState
from Wolin.service.interviewRecordService import get_interview_record_service

logger = logging.getLogger(__name__)


def capture_node_error(node_name: str = None):
    """
    工作流节点错误捕获装饰器

    功能：
    1. 自动捕获节点执行过程中的异常
    2. 记录错误日志
    3. 保存错误信息到数据库
    4. 重新抛出异常，让工作流知道节点失败

    使用方式：
        @graph_node
        @capture_node_error('extract_resume')
        def extract_resume(state: IAState):
            ...

    或者（自动获取函数名）：
        @graph_node
        @capture_node_error()
        def extract_resume(state: IAState):
            ...

    Args:
        node_name: 节点名称，如果为 None 则自动使用函数名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state: IAState, *args, **kwargs):
            # 自动获取节点名称
            actual_node_name = node_name or func.__name__

            try:
                return func(state, *args, **kwargs)
            except Exception as e:
                # 记录错误日志
                logger.error(f"{actual_node_name} 节点失败：{e}", exc_info=True)

                # 保存错误信息到数据库
                try:
                    get_interview_record_service().save_with_error(state, str(e), actual_node_name)
                except Exception as save_error:
                    # 如果保存失败也记录下来，但不掩盖原始错误
                    logger.error(f"{actual_node_name} 节点保存错误记录失败：{save_error}", exc_info=True)

                # 重新抛出异常，让工作流知道节点失败
                raise

        return wrapper
    return decorator
