import logging
from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Base.Repository.models.defaultDbModel import DefaultDbModel

logger = logging.getLogger(__name__)


class SysMenu(DefaultDbModel):
    """菜单权限表（树形结构）"""
    table_alias: ClassVar[str] = "sys_menu"
    create_table_sql: ClassVar[str] = f"""CREATE TABLE `{table_alias}` (
        `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
        `parent_id`       BIGINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '父菜单ID（0表示根节点）',
        `menu_name`       VARCHAR(100)    NOT NULL                 COMMENT '菜单名称',
        `menu_type`       TINYINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '类型: 0=目录, 1=菜单, 2=按钮',
        `permission_code` VARCHAR(100)    DEFAULT NULL             COMMENT '权限标识（如 sys:user:add）',
        `path`            VARCHAR(200)    DEFAULT NULL             COMMENT '前端路由路径',
        `component`       VARCHAR(200)    DEFAULT NULL             COMMENT '前端组件路径',
        `icon`            VARCHAR(100)    DEFAULT NULL             COMMENT '菜单图标',
        `sort_order`      INT UNSIGNED    NOT NULL DEFAULT 0       COMMENT '排序序号（同级排序）',
        `status`          TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '状态: 0=禁用, 1=启用',
        `visible`         TINYINT UNSIGNED NOT NULL DEFAULT 1      COMMENT '显示: 0=隐藏, 1=显示',
        `created_at`      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_at`      DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `created_by`      BIGINT UNSIGNED DEFAULT NULL             COMMENT '创建人ID',
        `updated_by`      BIGINT UNSIGNED DEFAULT NULL             COMMENT '更新人ID',
        PRIMARY KEY (`id`),
        KEY `idx_parent_id` (`parent_id`),
        KEY `idx_menu_type` (`menu_type`),
        KEY `idx_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='菜单权限表';
    """

    id: Optional[int] = Field(None, description="菜单ID")
    parent_id: int = Field(0, description="父菜单ID(0表示根)")
    menu_name: str = Field(..., description="菜单名称")
    menu_type: int = Field(0, description="类型: 0目录 1菜单 2按钮")
    permission_code: Optional[str] = Field(None, description="权限标识")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    sort_order: int = Field(0, description="排序序号")
    status: int = Field(1, description="状态: 0禁用 1启用")
    visible: int = Field(1, description="显示: 0隐藏 1显示")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")

    @classmethod
    def delete_cascade(cls, menu_id: int) -> dict:
        """删除菜单及其关联（检查子节点 + 删除角色关联）"""
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return {"success": False, "message": "数据库连接失败"}

            from .sysRoleMenu import SysRoleMenu

            children = cls.find_by(parent_id=menu_id)
            if children:
                return {"success": False, "message": f"该菜单下存在 {len(children)} 个子节点，请先删除子节点"}

            rm_table = SysRoleMenu.get_table_name_with_db()
            db.execute(f"DELETE FROM {rm_table} WHERE `menu_id` = %s", (menu_id,), commit=True)

            cls.delete_by_id(menu_id)
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除菜单失败: {e}")
            return {"success": False, "message": f"删除失败: {e}"}
