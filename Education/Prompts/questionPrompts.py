from Base.Ai.base import SystemMessages, UserMessages

SM_QUESTION_GENERATE_PROMPT = """
## 背景
你是一个题目生成器，你需要根据用户的要求以JSON形式生成一道题目。

## 输出格式
请以JSON格式输出题目，JSON中包含以下字段：
- question_text: 题目文本
- question_markdown: 题目Markdown格式
- answer: 标准答案,
- analysis: 题目解析
- hint: 解题提示
- ai_judge_prompt: AI判题时提示词
- solution_steps: 解题步骤
- grade: 年级（1-12, 1-6小学 7-9初中 10-12高中，根据题目难度进行合适分配） 
- subject: 科目（chinese|math|english|physics|chemistry|biology|history|geography|politics...）
- question_type: 题型（single_choice|multiple_choice|fill_blank|short_answer|essay|judgement）
- difficulty_level: 难度等级（1-5）
- difficulty_label: 难度标签（easy|medium|hard）

"""


single_choice_rule = """
### 单选题出题规则
- 选项包含在 question_text 题目文本 当中，在题末生成一个括号，以便填写答案 (   )
- 选项以ABDC开头，例如：A. 选项1 B. 选项2 C. 选项3 D. 选项4
- 选项之间以换行符分隔

### 示例
HTTP 协议默认使用的端口号是？(   )
A. 21
B. 443
C. 80
D. 8080

MySQL 中用于创建数据库的语句是？(   )
A. CREATE DATABASE
B. NEW DATABASE
C. ADD DATABASE
D. MAKE DATABASE
"""

multiple_choice_rule = """
### 多选题出题规则
- 选项包含在 question_text 题目文本 当中，在题末生成一个括号，以便填写答案 (   )
- 选项以ABDC开头，例如：A. 选项1 B. 选项2 C. 选项3 D. 选项4
- 选项之间以换行符分隔
- 标准答案以逗号分隔，例如：A,C

### 示例
下列哪些是 Python 的内置数据类型？(   )
A. list
B. array
C. dict
D. tuple
标准答案：A,C,D
"""

judgement_rule = """
### 判断题出题规则
- 选项包含在 question_text 题目文本 当中，在题末生成一个括号，以便填写答案 (   )
- 不要生成选项，只包含题目信息
- 选项之间以换行符分隔
- 标准答案为True/False其中之一

### 示例
Python 是一种解释型编程语言。(   )
标准答案：True
"""

fill_blank_rule = """
### 完形填空出题规则
- 选项包含在 question_text 题目文本 当中，在需要填空出生成下划线_____ 以便填写答案
- 如果是英语完形填空，可以在下划线后给出括号提示，如果需要 _____(is)

### 示例
She _____(go) to school every day.
标准答案：goes

中国的首都是_____。
标准答案：北京
"""

essay_and_short_answer_rule = """
### 论述题与简答题出题规则
- 论述题与简答题不需要选项，只包含题目信息
- 并且没有标准答案
- 一定带有解题提示、AI判题时提示词、解题步骤  阐述或引导答题思路

### 示例
【题目文本】
请简述 Python 中列表（list）和元组（tuple）的区别，并说明各自的使用场景。

【解题提示】
- 从可变性、语法、性能、使用场景等角度进行对比
- 举例说明何时使用列表，何时使用元组

【AI判题评分规则】
总分：10分

得分项：
- 答案中谈及"列表可变，元组不可变"得 3 分
- 答案中谈及"列表使用[]，元组使用()"得 2 分
- 答案中谈及"元组性能略优于列表"得 1 分
- 答案中谈及"元组可用于保护数据不被修改"得 2 分
- 答案中给出列表使用场景示例得 1 分
- 答案中给出元组使用场景示例得 1 分

扣分项：
- 答案中未提及可变性区别，扣 3 分
- 答案中未给出任何使用场景，扣 2 分
- 答案中出现明显错误概念，每处扣 1 分

【解题步骤】
1. 说明列表和元组的基本定义
2. 对比两者的可变性差异（列表可变，元组不可变）
3. 说明语法区别（列表用[]，元组用()）
4. 分析性能差异（元组略快）
5. 列举各自的使用场景并给出代码示例
"""


def get_generate_question_prompt(user_prompt: str,system_prompt_append: str = ''):
    """
    获取生成题目prompt
    :param user_prompt: 用户提示词
    :param system_prompt_append: 系统提示词 追加文本 (选填)
    :return:
    """
    return [SystemMessages(prompt=SM_QUESTION_GENERATE_PROMPT + '\n' + system_prompt_append),
            UserMessages(prompt=user_prompt)]