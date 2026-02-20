import json
from typing import Optional, Any, Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from Base.Ai.base.baseEnum import LLMTypeEnum
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.RicUtils.httpUtils import HttpResponse


class ChatParams(BaseModel):
    query: str = Field(..., description="用户问题")
    user_id: Optional[str] = Field(None, description="用户标识")
    model_type: LLMTypeEnum = Field(LLMTypeEnum.QWEN, description="模型类型")
    session_id: Optional[str] = Field(None, description="会话标识")
    is_stream: bool = Field(False, description="是否流式输出")
    is_thinking: bool = Field(False, description="是否思考")
    invoke_params: Optional[dict] = Field({}, description="调用参数")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.is_thinking:
            self.is_stream = True


router = APIRouter()


def _generate_sse_response(stream, is_thinking: bool) -> Generator[str, None, None]:
    """
    生成 SSE 格式的流式响应

    Args:
        stream: 流式输出对象
        is_thinking: 是否启用思考模式

    Yields:
        SSE 格式的字符串
    """
    for chunk in stream:
        if is_thinking:
            # 思考模式：chunk 是字典 {"type": "reasoning"/"content", "content": "..."}
            data = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {data}\n\n"
        else:
            # 普通模式：chunk 是字符串
            data = json.dumps({"type": "content", "content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"


#  这里为啥没写 async 呢？
@router.post("/chat-v1")
def chat(params: ChatParams):
    llm = get_default_qwen_llm()

    if params.is_stream:
        # 流式输出：启用思考模式和流式传输
        stream = llm.invoke(
            prompt=params.query,
            enable_thinking=params.is_thinking,
            stream=True,
            **params.invoke_params
        )
        return StreamingResponse(
            _generate_sse_response(stream, params.is_thinking),
            media_type="text/event-stream"
        )
    else:
        # 非流式输出
        result = llm.invoke(prompt=params.query, **params.invoke_params)
        return HttpResponse.ok(result)


def register_ai_chat_router(app):
    app.include_router(router)
