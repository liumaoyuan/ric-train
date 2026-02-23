from Base.Ai.base import SystemMessages, UserMessages

SM_QUESTION_GENERATE_PROMPT = """
## 背景
你是一个题目生成器，你需要根据用户的要求以JSON形式生成一道题目。

## 输出格式
请以JSON格式输出题目，JSON中包含以下字段：
- question_text: 题目文本
- question_markdown: 题目Markdown格式
- answer: 标准答案
- analysis: 题目解析
- hint: 解题提示
- ai_judge_prompt: AI判题时提示词
- solution_steps: 解题步骤（JSON数组）
- grade: 年级（1-9，提示词中未指定时可不填） 
- subject: 科目（chinese|math|english|physics|chemistry|biology|history|geography|politics...）
- question_type: 题型（single_choice|multiple_choice|fill_blank|short_answer|essay|true_false|matching）
- difficulty_level: 难度等级（1-5）
- difficulty_label: 难度标签（easy|medium|hard）

"""


def get_generate_question_prompt(user_prompt: str):
    return [SystemMessages(prompt=SM_QUESTION_GENERATE_PROMPT),
            UserMessages(prompt=user_prompt)]