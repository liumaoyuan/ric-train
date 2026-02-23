import json
import logging
import random
from typing import List

from pydantic import BaseModel, Field

from Base.Ai.base import SystemMessages, UserMessages
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Models.BaseParamsModel import BaseParamsModel
from Education.Models.pojo.answerPo import AnswerPo
from Education.Models.pojo.questionBo import QuestionRandomBo, AiJudgeQuestionBo
from Education.Models.pojo.questionPo import QuestionPo
from Education.Prompts.common import prompt_render
from Education.Prompts.questionPrompts import get_generate_question_prompt, ai_judge_prompt

logger = logging.getLogger(__name__)


class QuestionService(BaseModel):
    subjects: List[str] = Field([], description="科目列表")
    question_types: List[str] = Field([], description="题型列表")
    difficulty_levels: List[str] = Field([], description="难度等级列表")

    def generate_question_by_prompt(self):
        # TODO : 根据用户自然语言输入的提示生成题目 ， 如“帮我生成一道困难的高三几何相关的数学题”
        #       顺便做成接口
        pass

    def get_subjects(self):
        if not self.subjects:
            self.subjects = BaseParamsModel.get_params_by_parent_code('edu_subject', 'Education') or []
        return self.subjects

    def get_question_types(self):
        if not self.question_types:
            self.question_types = BaseParamsModel.get_params_by_parent_code('edu_question_type', 'Education') or []
        return self.question_types

    def get_difficulty_levels(self):
        if not self.difficulty_levels:
            self.difficulty_levels = BaseParamsModel.get_params_by_parent_code('edu_difficulty_label',
                                                                               'Education') or []
        return self.difficulty_levels

    @staticmethod
    def get_question_rule(question_type: str):
        """
        根据题目类型查询出题规则

        Args:
            question_type: 题目类型（single_choice|multiple_choice|fill_blank|short_answer|essay|judgement）

        Returns:
            包含 code、value、desc 的字典，未找到返回 None
        """
        result = ''
        try:
            result = BaseParamsModel.get_param_by_code(question_type, 'Education')
        except Exception as e:
            logger.error(f"获取题目生成规则失败 get_question_rule({question_type}) 失败：{str(e)}")
        return str(result.get('value'))

    def clear_instance_cache(self):
        """
        清理实例缓存
        :return:
        """
        self.subjects = []
        self.question_types = []
        self.difficulty_levels = []


    def random_generate_question(self, question_random_bo: QuestionRandomBo):
        """
        随机生成一道题目
        """
        subject = question_random_bo.subject or random.choice(self.get_subjects()).get('value')
        question_type = question_random_bo.question_type or random.choice(self.get_question_types()).get('value')
        difficulty_level = (question_random_bo.difficulty_level or
                            random.choice(self.get_difficulty_levels()).get('value'))
        grade_type = question_random_bo.grade_type or random.choice(['小学', '初中', '高中'])

        user_prompt = f"""帮我出一道题目：
        科目：{subject}
        题型：{question_type}
        难度：{difficulty_level}
        年级：{grade_type}"""

        messages = get_generate_question_prompt(user_prompt, system_prompt_append=self.get_question_rule(question_type))

        llm = get_default_qwen_llm()
        response = llm.chat(messages)
        response = json.loads(response)
        question = QuestionPo(ai_model=llm.model_name, ai_prompt=str(messages), created_by=505, **response)
        question.save()
        return response

    @staticmethod
    def ai_judge_question(params: AiJudgeQuestionBo):
        """
        AI判题
        """
        question = QuestionPo.get_by_id(params.question_id)
        if not question:
            raise ValueError(f"题目不存在：{params.question_id}")

        system_prompt = prompt_render(ai_judge_prompt, question.model_dump())
        user_prompt = f"""我的答案是：{params.answer}"""

        messages = [SystemMessages(prompt=system_prompt), UserMessages(prompt=user_prompt)]

        llm = get_default_qwen_llm()
        response = llm.chat(messages)
        response = json.loads(response)

        answer = AnswerPo(user_id=params.user_id, question_id=params.question_id, user_answer=params.answer,
                          ai_model=llm.model_name, ai_prompt=str(messages),source=params.source, **response)
        answer.save()
        return response


question_service = QuestionService()


def get_question_service():
    return question_service


if __name__ == '__main__':
    question_service = QuestionService()
    res = question_service.ai_judge_question(AiJudgeQuestionBo(question_id=1, user_id='test', answer="B",source='test'))
    print(res)
