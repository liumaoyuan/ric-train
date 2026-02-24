import json
import time
from typing import Optional, Any, Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from Base.Ai.base.baseEnum import LLMTypeEnum
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Models.BaseLLMConversationModel import BaseLLMConversationModel
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

    def to_log_instance(self) -> BaseLLMConversationModel:
        return BaseLLMConversationModel(
            question=self.query,
            user_id=self.user_id,
            session_id=self.session_id,
            ai_model=self.model_type.value,
            stream_mode="1" if self.is_stream else "0"
        )


router = APIRouter()


def _generate_sse_response_with_save(stream, is_thinking: bool, conversation: BaseLLMConversationModel, llm, start_time: float) -> Generator[str, None, None]:
    """
    生成 SSE 格式的流式响应，完成后自动保存到数据库

    Args:
        stream: 流式输出对象
        is_thinking: 是否启用思考模式
        conversation: 会话记录对象
        llm: LLM 实例
        start_time: 开始时间戳（用于计算耗时）

    Yields:
        SSE 格式的字符串
    """
    content_parts = []
    for chunk in stream:
        content_parts.append(chunk)
        if is_thinking:
            # 思考模式：chunk 是字典 {"type": "reasoning"/"content", "content": "..."}
            data = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {data}\n\n"
        else:
            # 普通模式：chunk 是字符串
            data = json.dumps({"type": "content", "content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"

    # 流式输出完成后，组装完整内容并保存
    if is_thinking:
        # 思考模式：组装 reasoning 和 content
        reasoning_parts = [c.get('content', '') for c in content_parts if c.get('type') == 'reasoning']
        content_parts_list = [c.get('content', '') for c in content_parts if c.get('type') == 'content']
        full_content = {'reasoning': ''.join(reasoning_parts), 'content': ''.join(content_parts_list)}
        conversation.answer = json.dumps(full_content, ensure_ascii=False)
    else:
        # 普通模式：拼接所有字符串
        conversation.answer = ''.join(content_parts)

    conversation.ai_model = llm.model_name
    # 计算总耗时（毫秒）
    conversation.duration_ms = int((time.time() - start_time) * 1000)

    try:
        conversation.save()
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.error(f"保存对话记录失败：{str(e)}")


#  这里为啥没写 async 呢？
@router.post("/chat-v1")
def chat(params: ChatParams):
    llm = get_default_qwen_llm()

    conversation = params.to_log_instance()
    conversation.ai_model = llm.model_name
    conversation.source = "base_chat_api"

    # 记录开始时间
    start_time = time.time()

    try:
        if params.is_stream:
            # 流式输出：启用思考模式和流式传输
            stream = llm.invoke(
                prompt=params.query,
                enable_thinking=params.is_thinking,
                stream=True,
                **params.invoke_params
            )
            return StreamingResponse(
                _generate_sse_response_with_save(stream, params.is_thinking, conversation, llm, start_time),
                media_type="text/event-stream"
            )
        else:
            # 非流式输出
            result = llm.invoke(prompt=params.query, **params.invoke_params)
            conversation.answer = result
            # 计算总耗时（毫秒）
            conversation.duration_ms = int((time.time() - start_time) * 1000)
            conversation.save()
            return HttpResponse.ok(result)
    except Exception as e:
        conversation.status = 'failed'
        conversation.error_msg = str(e)
        # 计算总耗时（毫秒）
        conversation.duration_ms = int((time.time() - start_time) * 1000)
        conversation.save()
        return HttpResponse.error(str(e))


def register_ai_chat_router(app):
    app.include_router(router)
