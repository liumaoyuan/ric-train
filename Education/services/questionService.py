import json
import logging
import random
from typing import List

from pydantic import BaseModel, Field

from Base.Ai.base import SystemMessages, UserMessages
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Models.BaseParamsModel import BaseParamsModel
from Education.prompts.common import prompt_render
from Education.prompts.questionPrompts import ai_judge_prompt, SM_QUESTION_GENERATE_PROMPT
from Education.models.pojo.answerPo import AnswerPo
from Education.models.pojo.questionBo import QuestionRandomBo, AiJudgeQuestionBo
from Education.models.pojo.questionPo import QuestionPo

logger = logging.getLogger(__name__)


class QuestionService(BaseModel):
    subjects: List[str] = Field([], description="科目列表")
    question_types: List[str] = Field([], description="题型列表")
    difficulty_levels: List[str] = Field([], description="难度等级列表")
    knowledge_points: dict = Field({}, description="知识点字典")

    def generate_question_by_prompt(self):
        # TODO : 根据用户自然语言输入的提示生成题目 ， 如"帮我生成一道困难的高三几何相关的数学题"
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

    def get_knowledge_points(self, grade: str, subject: str):
        """
        根据年级和学科获取知识点列表

        Args:
            grade: 年级（小学|初中|高中|大学）
            subject: 学科（chinese|math|english|physics|chemistry|biology|history|geography|politics）

        Returns:
            知识点字符串（逗号分隔的知识点列表）
        """
        # 生成 code: grade_subject (例如: 小学_chinese)
        code = f'{grade}_{subject}'

        # 检查缓存
        if not self.knowledge_points.get(code):
            # 从数据库查询知识点
            try:
                knowledge_point = BaseParamsModel.get_param_by_code(code=code, type='Education',
                                                                    parent_code='edu_knowledge_point')
                if knowledge_point:
                    self.knowledge_points[code] = knowledge_point.get('value', '')
                    logger.info(f"成功获取知识点: {code}, 值: {self.knowledge_points[code][:50]}...")
                else:
                    self.knowledge_points[code] = ''
                    logger.warning(f"未找到知识点: code={code}, type=Education, parent_code=edu_knowledge_point")
            except Exception as e:
                logger.error(f"查询知识点失败: code={code}, 错误: {str(e)}")
                self.knowledge_points[code] = ''

        return self.knowledge_points.get(code, '')

    @staticmethod
    def sample_knowledge_points(knowledge_points_str: str, count: int = 5) -> List[str]:
        """
        从逗号分隔的知识点字符串中随机抽取指定数量的知识点

        Args:
            knowledge_points_str: 知识点字符串（逗号分隔）
            count: 抽取数量，默认为5

        Returns:
            知识点列表（随机抽取的列表）

        示例:
            >>> points = "名词单复数,冠词用法,人称代词,物主代词,动词时态"
            >>> QuestionService.sample_knowledge_points(points, 3)
            ["人称代词", "动词时态", "冠词用法"]
        """
        if not knowledge_points_str:
            return []

        # 分割知识点字符串，去除空格
        points_list = [point.strip() for point in knowledge_points_str.split(',') if point.strip()]

        if not points_list:
            return []

        # 如果知识点数量不足，全部返回
        if len(points_list) <= count:
            return points_list

        # 随机抽取指定数量的知识点
        return random.sample(points_list, count)

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
        self.knowledge_points = {}

    def random_generate_question(self, question_random_bo: QuestionRandomBo):
        """
        随机生成一道题目
        """
        subject = question_random_bo.subject or random.choice(self.get_subjects()).get('value')
        question_type = question_random_bo.question_type or random.choice(self.get_question_types()).get('value')
        difficulty_level = (question_random_bo.difficulty_level or
                            random.choice(self.get_difficulty_levels()).get('value'))
        grade_type = question_random_bo.grade_type or random.choice(['小学', '初中', '高中'])
        knowledge_points = self.sample_knowledge_points(self.get_knowledge_points(grade_type, subject))

        user_prompt = f"""帮我出一道题目，根据提供的知识点任选一个或多个进行出题：
        科目：{subject}
        题型：{question_type}
        难度：{difficulty_level}
        年级：{grade_type}
        知识点：{knowledge_points} """

        system_msg = prompt_render(SM_QUESTION_GENERATE_PROMPT, {"subject": self.get_subjects(),
                                                                 "append": self.get_question_rule(question_type),
                                                                 "question_type": self.get_question_types()})

        messages = [SystemMessages(prompt=system_msg), UserMessages(prompt=user_prompt)]

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
                          ai_model=llm.model_name, ai_prompt=str(messages), source=params.source, **response)
        answer.save()
        return response

    @staticmethod
    def judge_question(params: AiJudgeQuestionBo):
        """
        人工判题
        """
        # 获取题目
        question = QuestionPo.get_by_id(params.question_id)
        if not question:
            raise ValueError(f"题目不存在：{params.question_id}")

        true_answer = question.answer
        user_answer = params.answer

        # 标准化答案：去除首尾空格，转为小写
        def normalize_answer(answer):
            if answer is None:
                return ""
            if isinstance(answer, (bool, int, float)):
                return str(answer).lower().strip()
            return str(answer).lower().strip()

        norm_true = normalize_answer(true_answer)
        norm_user = normalize_answer(user_answer)

        # 根据题型进行判题
        score = 0
        ai_result = ""

        if question.question_type == 'judgement':
            # 判断题：比较 true/false 字符串
            is_correct = norm_true == norm_user
            score = 1 if is_correct else 0
            ai_result = "✓ 正确" if is_correct else "✗ 错误"

        elif question.question_type in ['single_choice', 'multiple_choice']:
            # 选择题：比较选项字母
            # 处理多选题答案（可能是逗号分隔或逗号+空格分隔）
            norm_true = ','.join(sorted([opt.strip() for opt in norm_true.replace(' ', ',').split(',') if opt.strip()]))
            norm_user = ','.join(sorted([opt.strip() for opt in norm_user.replace(' ', ',').split(',') if opt.strip()]))

            is_correct = norm_true == norm_user
            score = 1 if is_correct else 0
            ai_result = f"✓ 正确" if is_correct else f"✗ 错误。正确答案：{true_answer}"

        else:
            # 填空题、简答题、论述题：直接字符串比较
            is_correct = norm_true == norm_user
            score = 1 if is_correct else 0
            ai_result = f"✓ 正确" if is_correct else f"✗ 错误。正确答案：{true_answer}"

        return {'score': score, 'ai_result': ai_result}


question_service = QuestionService()


def get_question_service():
    return question_service


if __name__ == '__main__':
    question_service = QuestionService()
    res = QuestionPo.get_random_question(num=1)
    # res = question_service.random_generate_question(QuestionRandomBo())
    # res = question_service.judge_question(
    #     AiJudgeQuestionBo(question_id=1239, user_id='test', answer="false", source='test'))
    if isinstance(res, list):
        for i in res:
            print(res)
    else:
        print(res)
