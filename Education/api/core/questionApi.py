import threading

from fastapi import APIRouter

from Base.RicUtils.httpUtils import HttpResponse
from Education.Models.pojo.questionVo import QuestionRandomParamVo
from Education.Services.questionService import get_question_service

router = APIRouter(prefix="/education/question")

@router.post("/random_generate")
def get_question(params: QuestionRandomParamVo):
    """
    随机出题接口
    :param params:  如果不指定对应参数的值，对应参数将随机取值。 如 不指定 科目，将随机取一个科目
    :return:
    """

    # TODO: 改成多并发执行， 同时启动 多个线程（参数控制）并发生成，加快生成速度, 需要考虑用户需要生成数量小于并发量时的情况
    def generate_question():
        for i in range(params.num):
            get_question_service().random_generate_question(params)

    # 额外线程执行
    threading.Thread(target=generate_question).start()
    return HttpResponse.ok("正在生成中...")