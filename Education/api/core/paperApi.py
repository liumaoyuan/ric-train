import logging
from typing import Optional

from fastapi import APIRouter, Query

from Base.RicUtils.httpUtils import HttpResponse
from Education.services.paperService import get_paper_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/education/paper")


@router.get("/{paper_id}")
def get_paper_detail(paper_id: int):
    """
    获取试卷详情（学生答题用）

    Args:
        paper_id: 试卷 ID

    Returns:
        试卷详情，包含题目列表
    """
    try:
        detail = get_paper_service().get_paper_detail(paper_id)
        return HttpResponse.ok(detail)
    except ValueError as e:
        return HttpResponse.error(str(e))
    except Exception as e:
        logger.error(f"获取试卷详情失败：{str(e)}")
        return HttpResponse.error(f"获取试卷详情失败：{str(e)}")


@router.post("")
def create_paper(
    paper_name: str = Query(..., description="试卷名称"),
    question_ids: str = Query(..., description="题目 ID 列表（逗号分隔）"),
    scores: Optional[str] = Query(None, description="每题分值（逗号分隔）"),
    description: Optional[str] = Query(None, description="试卷描述"),
    subject: Optional[str] = Query(None, description="科目"),
    duration_minutes: Optional[int] = Query(30, description="考试时长（分钟）"),
    created_by: Optional[int] = Query(505, description="创建者 ID")
):
    """
    创建试卷

    Args:
        paper_name: 试卷名称
        question_ids: 题目 ID 列表（逗号分隔）
        scores: 每题分值（逗号分隔，可选）
        description: 试卷描述
        subject: 科目
        duration_minutes: 考试时长
        created_by: 创建者 ID

    Returns:
        创建的试卷信息
    """
    try:
        # 解析逗号分隔的 ID 列表
        q_ids = [int(x.strip()) for x in question_ids.split(',') if x.strip()]
        score_list = None
        if scores:
            score_list = [float(x.strip()) for x in scores.split(',') if x.strip()]

        service = get_paper_service()
        paper = service.create_paper(
            paper_name=paper_name,
            question_ids=q_ids,
            scores=score_list,
            description=description,
            subject=subject,
            duration_minutes=duration_minutes,
            created_by=created_by
        )

        return HttpResponse.ok({
            'paper_id': paper.id,
            'paper_uuid': paper.paper_uuid,
            'paper_name': paper.paper_name,
            'total_score': paper.total_score
        })
    except Exception as e:
        logger.error(f"创建试卷失败：{str(e)}")
        return HttpResponse.error(f"创建试卷失败：{str(e)}")


@router.get("/{paper_id}/versions")
def get_paper_versions(paper_id: int):
    """
    获取试卷版本历史

    Args:
        paper_id: 试卷 ID

    Returns:
        版本历史列表
    """
    try:
        versions = get_paper_service().get_paper_versions(paper_id)
        return HttpResponse.ok(versions)
    except ValueError as e:
        return HttpResponse.error(str(e))
    except Exception as e:
        logger.error(f"获取版本历史失败：{str(e)}")
        return HttpResponse.error(f"获取版本历史失败：{str(e)}")


@router.put("/{paper_id}/publish")
def publish_paper(paper_id: int):
    """
    发布试卷

    Args:
        paper_id: 试卷 ID

    Returns:
        操作结果
    """
    try:
        success = get_paper_service().publish_paper(paper_id)
        if success:
            return HttpResponse.ok({'message': '试卷发布成功'})
        else:
            return HttpResponse.error('试卷发布失败')
    except Exception as e:
        logger.error(f"发布试卷失败：{str(e)}")
        return HttpResponse.error(f"发布试卷失败：{str(e)}")


@router.delete("/{paper_id}")
def delete_paper(paper_id: int):
    """
    删除试卷（软删除）

    Args:
        paper_id: 试卷 ID

    Returns:
        操作结果
    """
    try:
        success = get_paper_service().delete_paper(paper_id)
        if success:
            return HttpResponse.ok({'message': '试卷删除成功'})
        else:
            return HttpResponse.error('试卷删除失败')
    except Exception as e:
        logger.error(f"删除试卷失败：{str(e)}")
        return HttpResponse.error(f"删除试卷失败：{str(e)}")
