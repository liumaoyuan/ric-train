

from Base.Models.BaseParamsModel import BaseParamsModel
from Education.Models.pojo.questionPo import QuestionPo
from Education.Prompts.questionPrompts import (
    single_choice_rule,
    multiple_choice_rule,
    judgement_rule,
    fill_blank_rule,
    essay_and_short_answer_rule
)


def _init_params_with_parent(
    parent_code: str,
    parent_value: str,
    parent_desc: str,
    items: str,
    item_names: dict,
    item_prefix: str = '',
    item_desc_prefix: str = ''
):
    """
    通用参数初始化函数 - 支持父级参数和子参数的初始化

    Args:
        parent_code: 父级参数编码
        parent_value: 父级参数值
        parent_desc: 父级参数描述
        items: 子项列表，用 | 分隔
        item_names: 子项名称映射字典
        item_prefix: 子项编码前缀（默认为空）
        item_desc_prefix: 子项描述前缀（默认为空）
    """
    # 检查父级参数是否存在
    parent_param = BaseParamsModel.get_param_by_code(parent_code, 'Education')

    if parent_param is None:
        # 父级参数不存在，创建父级参数
        parent = BaseParamsModel(
            code=parent_code,
            value=parent_value,
            desc=parent_desc,
            type='Education',
        )
        parent.save()
        print(f"✓ 创建父级参数成功: {parent_code}")
    else:
        print(f"✓ 父级参数已存在: {parent_code}")

    # 检查子参数是否已存在
    existing_items = BaseParamsModel.get_params_by_parent_code(parent_code, 'Education')
    existing_codes = {s['code'] for s in existing_items}

    # 遍历所有子项并插入不存在的参数
    for item in items.split('|'):
        code = f'{item_prefix}{item}' if item_prefix else item
        if code in existing_codes:
            print(f"  跳过已存在: {item_names[item]} ({item})")
            continue

        params = BaseParamsModel(
            code=code,
            value=item,
            desc=f'{item_desc_prefix}{item_names[item]}',
            parent_code=parent_code,
            type='Education',
        )
        params.save()
        print(f"✓ 插入成功: {item_names[item]} ({item})")

    print(f"\n参数初始化完成！")


def init_question_subjects():
    """初始化教育项目的学科参数"""
    _init_params_with_parent(
        parent_code='edu_subject',
        parent_value='subject',
        parent_desc='教育项目-学科类别',
        items='chinese|math|english|physics|chemistry|biology|history|geography|politics',
        item_names={
            'chinese': '语文',
            'math': '数学',
            'english': '英语',
            'physics': '物理',
            'chemistry': '化学',
            'biology': '生物',
            'history': '历史',
            'geography': '地理',
            'politics': '政治'
        },
        item_prefix='subject_',
        item_desc_prefix='教育项目-学科类别-'
    )


def init_question_types():
    """初始化教育项目的题目类型参数"""
    _init_params_with_parent(
        parent_code='edu_question_type',
        parent_value='question_type',
        parent_desc='教育项目-题目类型',
        items='single_choice|multiple_choice|fill_blank|judgement|essay|short_answer',
        item_names={
            'single_choice': '单选题',
            'multiple_choice': '多选题',
            'fill_blank': '填空题',
            'judgement': '判断题',
            'essay': '论述题',
            'short_answer': '简答题'
        },
        item_prefix='question_type_',
        item_desc_prefix='教育项目-题目类型-'
    )


def init_question_difficulty_labels():
    """初始化教育项目的难度标签参数"""
    _init_params_with_parent(
        parent_code='edu_difficulty_label',
        parent_value='difficulty_label',
        parent_desc='教育项目-难度标签',
        items='easy|medium|hard',
        item_names={
            'easy': '简单',
            'medium': '中等',
            'hard': '困难'
        },
        item_prefix='difficulty_label_',
        item_desc_prefix='教育项目-难度标签-'
    )


def init_question_rules():
    """初始化教育项目的出题规则参数"""
    parent_code = 'edu_question_rule'
    parent_value = 'question_rule'
    parent_desc = '教育项目-出题规则'

    # 检查父级参数是否存在
    parent_param = BaseParamsModel.get_param_by_code(parent_code, 'Education')

    if parent_param is None:
        # 父级参数不存在，创建父级参数
        parent = BaseParamsModel(
            code=parent_code,
            value=parent_value,
            desc=parent_desc,
            type='Education',
        )
        parent.save()
        print(f"✓ 创建父级参数成功: {parent_code}")
    else:
        print(f"✓ 父级参数已存在: {parent_code}")

    # 从 questionPrompts 导入的规则常量
    rules = {
        'single_choice': single_choice_rule,
        'multiple_choice': multiple_choice_rule,
        'judgement': judgement_rule,
        'fill_blank': fill_blank_rule,
        'essay': essay_and_short_answer_rule,
        'short_answer': essay_and_short_answer_rule
    }

    # 检查子参数是否已存在
    existing_items = BaseParamsModel.get_params_by_parent_code(parent_code, 'Education')
    existing_codes = {s['code'] for s in existing_items}

    # 遍历所有规则并插入不存在的参数
    for code, value in rules.items():
        if code in existing_codes:
            print(f"  跳过已存在: {code}")
            continue

        params = BaseParamsModel(
            code=code,
            value=value,
            desc=f'教育项目-出题规则-{code}',
            parent_code=parent_code,
            type='Education',
        )
        params.save()
        print(f"✓ 插入成功: {code}")

    print(f"\n出题规则初始化完成！")


def question_db_init():
    QuestionPo.create_table()
    init_question_subjects()
    init_question_types()
    init_question_difficulty_labels()
    init_question_rules()

if __name__ == '__main__':
    question_db_init()