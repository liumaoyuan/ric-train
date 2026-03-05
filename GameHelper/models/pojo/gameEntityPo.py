from typing import Optional, List
from pydantic import Field, BaseModel


class GameEntityPO(BaseModel):
    """
    游戏实体数据对象
    """
    id: Optional[int] = Field(None, description="主键 ID")
    entity_name: str = Field(..., description="实体名称")
    entity_code: str = Field(..., description="实体编码")
    entity_type: str = Field(..., description="实体类型")
    game_name: str = Field(..., description="所属游戏")
    aliases: Optional[str] = Field(None, description="别名/外号列表")
    description: Optional[str] = Field(None, description="实体描述")
    status: int = Field(1, description="状态")

    class Config:
        from_attributes = True

    def get_aliases_list(self) -> List[str]:
        """获取别名列表"""
        if not self.aliases:
            return []
        return [a.strip() for a in self.aliases.split(',') if a.strip()]


class GameEntityCreateRequest(BaseModel):
    """
    实体创建请求对象
    """
    entity_name: str = Field(..., description="实体名称")
    entity_code: str = Field(..., description="实体编码")
    entity_type: str = Field(..., description="实体类型")
    game_name: str = Field(..., description="所属游戏")
    aliases: Optional[str] = Field(None, description="别名/外号列表")
    description: Optional[str] = Field(None, description="实体描述")


class GameEntityUpdateRequest(BaseModel):
    """
    实体更新请求对象
    """
    entity_name: Optional[str] = Field(None, description="实体名称")
    aliases: Optional[str] = Field(None, description="别名/外号列表")
    description: Optional[str] = Field(None, description="实体描述")
    status: Optional[int] = Field(None, description="状态")


class GameEntityResponse(BaseModel):
    """
    实体响应对象
    """
    id: int = Field(..., description="主键 ID")
    entity_name: str = Field(..., description="实体名称")
    entity_code: str = Field(..., description="实体编码")
    entity_type: str = Field(..., description="实体类型")
    game_name: str = Field(..., description="所属游戏")
    aliases: Optional[List[str]] = Field(None, description="别名列表")
    description: Optional[str] = Field(None, description="实体描述")

    class Config:
        from_attributes = True
