from functools import lru_cache
from time import sleep

from Base.Ai.llms.qwenLlm import QwenLlm
from Base.RicUtils.decoratorUtils import timing_log

cache_dict = {}

@timing_log
@lru_cache(128)
def ask(query: str):
    if query in cache_dict:
        return cache_dict.get(query)

    sleep(10)
    qwen = QwenLlm()
    res = qwen.invoke(query)

    cache_dict[query] = res
    return res


if __name__ == '__main__':
    ask("今天天气怎么样")

    # ask("今天天气怎么样")
