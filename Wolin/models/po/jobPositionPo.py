from datetime import datetime
from typing import Optional, ClassVar

from pydantic import Field

from Wolin.db.connectionInit import WolinModuleDBModel


class JobPositionPo(WolinModuleDBModel):
    """
    岗位信息表 —— 存储 BOSS 直聘等招聘软件上的岗位信息。
    """
    table_alias: ClassVar[str] = 'job_positions'
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_alias}` (
            `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '岗位 ID',
            `position_name` VARCHAR(200) NOT NULL COMMENT '岗位名称',
            `company_name` VARCHAR(200) NOT NULL COMMENT '公司名称',
            `company_address` VARCHAR(500) COMMENT '公司地址',
            `salary_range` VARCHAR(100) COMMENT '薪资范围，如 15-30K',
            `job_responsibilities` TEXT COMMENT '岗位职责',
            `job_requirements` TEXT COMMENT '任职要求',
            `experience_required` VARCHAR(100) COMMENT '经验要求，如 3-5年',
            `education_required` VARCHAR(100) COMMENT '学历要求，如 本科',
            `company_industry` VARCHAR(200) COMMENT '公司行业',
            `company_size` VARCHAR(100) COMMENT '公司规模，如 100-499人',
            `job_url` VARCHAR(500) COMMENT '岗位链接',
            `source_platform` VARCHAR(50) DEFAULT 'boss' COMMENT '来源平台，如 boss、lagou',
            `raw_data` TEXT COMMENT '原始数据（JSON 字符串）',
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

            PRIMARY KEY (`id`),
            KEY `idx_position_name` (`position_name`),
            KEY `idx_company_name` (`company_name`),
            KEY `idx_source_platform` (`source_platform`),
            KEY `idx_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位信息表';
        """

    id: Optional[int] = Field(None, description="岗位 ID")
    position_name: str = Field(..., description="岗位名称")
    company_name: str = Field(..., description="公司名称")
    company_address: Optional[str] = Field(None, description="公司地址")
    salary_range: Optional[str] = Field(None, description="薪资范围，如 15-30K")
    job_responsibilities: Optional[str] = Field(None, description="岗位职责")
    job_requirements: Optional[str] = Field(None, description="任职要求")
    experience_required: Optional[str] = Field(None, description="经验要求，如 3-5年")
    education_required: Optional[str] = Field(None, description="学历要求，如 本科")
    company_industry: Optional[str] = Field(None, description="公司行业")
    company_size: Optional[str] = Field(None, description="公司规模，如 100-499人")
    job_url: Optional[str] = Field(None, description="岗位链接")
    source_platform: str = Field('boss', description="来源平台，如 boss、lagou")
    raw_data: Optional[str] = Field(None, description="原始数据（JSON 字符串）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @classmethod
    def find_by_company(cls, company_name: str) -> list["JobPositionPo"]:
        """根据公司名称查询岗位列表。"""
        return cls.find_by(company_name=company_name)

    @classmethod
    def find_by_platform(cls, platform: str) -> list["JobPositionPo"]:
        """根据来源平台查询岗位列表。"""
        return cls.find_by(source_platform=platform)


if __name__ == '__main__':
    po = JobPositionPo()
    po.create_table()
    print("岗位信息表创建成功")
