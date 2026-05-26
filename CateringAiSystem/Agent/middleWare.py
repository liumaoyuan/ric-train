"""聊天助手 Agent - 运行时上下文工具

ChatMemoryMiddleware 已由 graph.py 中的 summary_node 替代。
本模块仅保留 session_id / user_id 的 contextvars 工具，
供 chatService 等外部模块在调用 Agent 前设置会话上下文。
"""
import contextvars

_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="")
_user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")


def set_session_context(session_id: str, user_id: str):
    """设置当前会话上下文（每次调用 Agent 前由 ChatAgent 设置）"""
    _session_id_var.set(session_id)
    _user_id_var.set(user_id)


def get_session_id() -> str:
    return _session_id_var.get()


def get_user_id() -> str:
    return _user_id_var.get()
