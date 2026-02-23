import threading

from fastapi import APIRouter

from Base.RicUtils.httpUtils import HttpResponse
from Education.Models.pojo.questionBo import AiJudgeQuestionBo
from Education.Models.pojo.questionPo import QuestionPo
from Education.Models.pojo.questionVo import QuestionRandomParamVo
from Education.Services.questionService import get_question_service

router = APIRouter(prefix="/education/question")

@router.get("/random_one")
def get_random_one_question():
    """
    随机返回一道题目
    """
    # todo: 不返回用户已经做过的题目
    res = QuestionPo.get_random_question()
    return HttpResponse.ok(res.mini_dict)

@router.post("/random_generate")
async def generate_random_question(params: QuestionRandomParamVo):
    """
    随机AI生成题目接口
    :param params:  如果不指定对应参数的值，对应参数将随机取值。 如 不指定 科目，将随机取一个科目
    :return:
    """

    # TODO: 改成多并发执行， 同时启动 多个线程（参数控制）并发生成，加快生成速度
    def generate_question():
        for i in range(params.num):
            get_question_service().random_generate_question(params)

    # 额外线程执行
    threading.Thread(target=generate_question).start()
    return HttpResponse.ok("正在生成中...")


@router.post("/ai_judge")
async def ai_judge_question(params: AiJudgeQuestionBo):
    """
    AI判题接口
    """
    res = get_question_service().ai_judge_question(params)
    return HttpResponse.ok(res)
