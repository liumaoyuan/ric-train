import os

from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

from Base.Config.setting import settings


def get_qian_wen(temperature: float = 0.7, max_tokens: int = 2048, enable_search: bool = False):
    qwen_config = settings.dashscope
    extra_kwargs = {}
    if enable_search:
        extra_kwargs["extra_body"] = {"enable_search": True}
    model = ChatOpenAI(
        model=qwen_config.default_model,
        api_key=qwen_config.api_key,
        base_url=qwen_config.base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra_kwargs,
    )
    return model


def get_deepseek(temperature: float = 0.7, max_tokens: int = 2048):
    dp_config = settings.deepseek
    # 禁用 reasoning/thinking 模式，避免 reasoning_content 在序列化后丢失导致 API 报错
    extra_kwargs = {"extra_body": {"thinking": {"type": "disabled"}}}
    model = ChatOpenAI(
        model=dp_config.default_model,
        api_key=dp_config.api_key,
        base_url=dp_config.base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        **extra_kwargs,
    )
    return model


def get_embedding():
    model = SentenceTransformer("EMBEDDING_MODEL")
    return model
