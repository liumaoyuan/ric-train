import threading
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Response

from Base.RicUtils.dataUtils import remove_none
from Base.RicUtils.excelUtils import dict_list_to_excel
from Base.RicUtils.httpUtils import HttpResponse
from Education.Models.pojo.questionBo import AiJudgeQuestionBo, QuestionRandomBo
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


@router.post("/excel_export")
async def excel_export_question(params: QuestionRandomBo):
    """
    导出题目到Excel接口

    支持根据参数筛选导出：
    - subject: 科目筛选（可选）
    - question_type: 题型筛选（可选）
    - difficulty_level: 难度筛选（可选）
    - grade_type: 年级筛选（可选）

    返回 Excel 文件下载
    """
    # 查询题目数据
    questions = QuestionPo.find_by(**remove_none(params.model_dump()))

    # 转换为字典列表（使用 model_dump 返回所有字段，包括空值）
    data_list = [q.model_dump() for q in questions]

    # 如果没有数据
    if not data_list:
        return HttpResponse.error("没有可导出的题目数据")

    # 字段名映射（英文 -> 中文）
    field_name_map = {
        'id': 'ID',
        'question_uuid': '题目UUID',
        'question_text': '题干',
        'question_html': '题干HTML',
        'question_markdown': '题干Markdown',
        'answer': '标准答案',
        'analysis': '答案解析',
        'hint': '提示',
        'ai_judge_prompt': 'AI判题提示词',
        'solution_steps': '解题步骤',
        'knowledge_points': '知识点',
        'grade': '年级',
        'subject': '科目',
        'question_type': '题型',
        'difficulty_level': '难度等级',
        'difficulty_label': '难度标签',
        'images': '图片',
        'audio_url': '音频URL',
        'video_url': '视频URL',
        'ai_model': 'AI模型',
        'ai_prompt': 'AI提示词',
        'ai_params': 'AI参数',
        'version': '版本',
        'previous_version_id': '上一版本ID',
        'change_log': '变更日志',
        'created_at': '创建时间',
        'updated_at': '更新时间',
        'created_by': '创建人',
        'updated_by': '更新人',
        'status': '状态'
    }

    # 排除字段（敏感或不必要的字段）
    exclude_fields = [
        'ai_judge_prompt',
        'ai_prompt',
        'ai_params',
        'change_log',
        'previous_version_id'
    ]

    # 生成 Excel 文件
    filename = f"题目导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    # 对文件名进行 URL 编码，支持中文
    encoded_filename = quote(filename)
    excel_bytes = dict_list_to_excel(
        data_list,
        sheet_name="题目列表",
        field_name_map=field_name_map,
        exclude_fields=exclude_fields,
        include_all_fields=True
    )

    # 返回 Excel 文件
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )
