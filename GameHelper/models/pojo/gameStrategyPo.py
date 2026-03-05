from typing import Optional, List
from pydantic import Field, BaseModel


class GameStrategyPO(BaseModel):
    """
    游戏攻略数据对象
    """
    id: Optional[int] = Field(None, description="主键 ID")
    title: str = Field(..., description="攻略标题")
    content: Optional[str] = Field(None, description="攻略正文内容")
    source_url: Optional[str] = Field(None, description="来源链接")
    game_name: str = Field(..., description="游戏名称")
    strategy_type: str = Field(..., description="攻略类型")
    status: int = Field(1, description="状态：0-禁用，1-启用")
    entity_names: Optional[List[str]] = Field(None, description="关联的实体名称列表")

    class Config:
        from_attributes = True


class GameStrategyCreateRequest(BaseModel):
    """
    攻略创建请求对象
    """
    title: str = Field(..., description="攻略标题")
    content: Optional[str] = Field(None, description="攻略正文内容")
    source_url: Optional[str] = Field(None, description="来源链接")
    game_name: str = Field(..., description="游戏名称")
    strategy_type: str = Field(..., description="攻略类型")
    entity_names: Optional[List[str]] = Field(None, description="关联的实体名称列表")


class GameStrategyUpdateRequest(BaseModel):
    """
    攻略更新请求对象
    """
    title: Optional[str] = Field(None, description="攻略标题")
    content: Optional[str] = Field(None, description="攻略正文内容")
    source_url: Optional[str] = Field(None, description="来源链接")
    strategy_type: Optional[str] = Field(None, description="攻略类型")
    status: Optional[int] = Field(None, description="状态")
    entity_names: Optional[List[str]] = Field(None, description="关联的实体名称列表")


class GameStrategyResponse(BaseModel):
    """
    攻略响应对象
    """
    id: int = Field(..., description="主键 ID")
    title: str = Field(..., description="攻略标题")
    content: Optional[str] = Field(None, description="攻略正文内容")
    source_url: Optional[str] = Field(None, description="来源链接")
    game_name: str = Field(..., description="游戏名称")
    strategy_type: str = Field(..., description="攻略类型")
    status: int = Field(..., description="状态")
    entities: Optional[List[str]] = Field(None, description="关联的实体名称列表")

    class Config:
        from_attributes = True
