from typing import Optional, Literal

from pydantic import BaseModel, Field


class QuestionRandomBo(BaseModel):
    """
    随机出题函数的入参BO类
    """
    subject: Optional[str] = Field(None, description="科目")
    question_type: Optional[str] = Field(None, description="题型")
    difficulty_level: Optional[str] = Field(None, description="难度等级")
    grade_type: Optional[Literal["小学", "初中", "高中"]] = Field(None, description="年级类型")


class AiJudgeQuestionBo(BaseModel):
    """
    AI判题函数的入参BO类
    """
    user_id: Optional[int | str] = Field(None, description="用户ID")
    question_id: int | str = Field(..., description="题目文本")
    answer: str = Field(..., description="标准答案")
    source: Optional[str] = Field(None, description="来源")
