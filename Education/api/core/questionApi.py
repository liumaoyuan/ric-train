import threading
import uuid
import io
import logging
from datetime import datetime
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, Response, UploadFile, File

from Base.RicUtils.dataUtils import remove_none
from Base.RicUtils.excelUtils import dict_list_to_excel, excel_to_dict_list
from Base.RicUtils.httpUtils import HttpResponse
from Education.models.pojo.questionBo import AiJudgeQuestionBo, QuestionRandomBo
from Education.models.pojo.questionPo import QuestionPo
from Education.models.pojo.questionVo import QuestionRandomParamVo
from Education.services.questionService import get_question_service

logger = logging.getLogger(__name__)

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

    # 字段名映射（英文 -> 中文），从模型中获取
    field_name_map = QuestionPo.get_field_mapping()
    # 额外添加一些自定义映射（覆盖或补充模型定义）
    field_name_map.update({
        'id': 'ID',
        'question_uuid': '题目UUID',
    })

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


@router.post("/excel_import")
async def excel_import_question(file: UploadFile = File(...)):
    """
    Excel 导入题目接口

    支持上传 Excel 文件批量导入题目。
    Excel 格式应与导出格式保持一致，但可以省略 ID 和 UUID 字段（自动生成）。

    Args:
        file: 上传的 Excel 文件

    Returns:
        导入结果信息

    Example:
        使用 curl 上传：
        curl -X POST "http://localhost:8000/education/question/excel_import" \
             -F "file=@questions.xlsx"

        使用 Postman：
        1. 选择 POST 方法
        2. URL: http://localhost:8000/education/question/excel_import
        3. Body -> form-data
        4. Key: file, Type: File, Value: 选择 Excel 文件
    """
    import io

    # 检查文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return HttpResponse.error("文件格式错误，请上传 Excel 文件（.xlsx 或 .xls）")

    try:
        # 读取文件内容
        file_content = await file.read()
        file_obj = io.BytesIO(file_content)

        # 字段名映射（中文 -> 英文），从模型中获取并反转
        field_mapping_en_to_cn = QuestionPo.get_field_mapping()
        field_name_map = {cn: en for en, cn in field_mapping_en_to_cn.items()}
        # 额外添加一些自定义映射
        field_name_map.update({
            'ID': 'id',
            '题目UUID': 'question_uuid',
        })

        # 解析 Excel
        data_list = excel_to_dict_list(
            file_obj=file_obj,
            field_name_map=field_name_map
        )

        if not data_list:
            return HttpResponse.error("Excel 文件为空或格式不正确")

        # 转换为 QuestionPo 对象列表
        questions = []
        created_by = 505  # 默认创建人 ID（可根据实际需求修改）

        for data in data_list:
            # 过滤掉空值字段
            data = {key: value for key, value in data.items() if value}

            # 自动生成 question_uuid
            data['question_uuid'] = str(uuid.uuid4())

            # 设置默认创建人
            if 'created_by' not in data or not data['created_by']:
                data['created_by'] = created_by

            # 处理类型转换问题

            # 1. 处理布尔值转字符串（如 answer: False -> "False"）
            if 'answer' in data and isinstance(data['answer'], bool):
                data['answer'] = str(data['answer'])

            # 2. 处理 datetime 字段（created_at, updated_at 为 None）
            if 'created_at' in data and data['created_at'] is None:
                data['created_at'] = datetime.now()
            if 'updated_at' in data and data['updated_at'] is None:
                data['updated_at'] = datetime.now()

            # 3. 处理整数类型（created_by, updated_by）
            if 'created_by' in data and isinstance(data['created_by'], str):
                try:
                    data['created_by'] = int(data['created_by'])
                except (ValueError, TypeError):
                    data['created_by'] = created_by
            if 'updated_by' in data and isinstance(data['updated_by'], str):
                try:
                    data['updated_by'] = int(data['updated_by'])
                except (ValueError, TypeError):
                    data['updated_by'] = None  # updated_by 是 Optional[int]

            # 4. 验证必需字段（过滤后可能被移除）
            required_fields = ['question_text', 'grade', 'subject', 'question_type', 'question_uuid', 'created_by']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                logger.warning(f"跳过缺少必需字段的数据行：缺少 {missing_fields}, 数据：{data}")
                continue

            # 5. 保留所有字段，不强制转换为None（让Pydantic根据Optional定义处理）

            # 创建 QuestionPo 对象
            try:
                question = QuestionPo(**data)
                questions.append(question)
            except Exception as e:
                logger.warning(f"跳过无效数据行：{data}, 错误：{str(e)}")
                continue

        if not questions:
            return HttpResponse.error("没有有效的题目数据可导入")

        # 批量插入
        inserted_ids = QuestionPo.bulk_insert(questions, batch_size=100)

        return HttpResponse.ok({
            "message": f"成功导入 {len(inserted_ids)} 道题目",
            "total_rows": len(data_list),
            "valid_rows": len(questions),
            "inserted_rows": len(inserted_ids),
            "skipped_rows": len(data_list) - len(questions)
        })

    except ValueError as e:
        return HttpResponse.error(f"读取 Excel 失败：{str(e)}")
    except Exception as e:
        logger.error(f"导入题目失败：{str(e)}")
        return HttpResponse.error(f"导入失败：{str(e)}")
