from typing import Optional

from pydantic import BaseModel, Field


class QuestionRandomBo(BaseModel):
    """
    随机出题函数的入参BO类
    """
    subject: Optional[str] = Field(None, description="科目")
    question_type: Optional[str] = Field(None, description="题型")
    difficulty_level: Optional[str] = Field(None, description="难度等级")