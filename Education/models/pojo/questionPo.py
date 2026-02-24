from datetime import datetime
from typing import Optional, ClassVar, List
import json
from pydantic import field_serializer, field_validator, Field
from Base.Repository.models.defaultDbModel import DefaultDbModel


class QuestionPo(DefaultDbModel):
    table_alias: ClassVar[str] = 'questions'
    create_table_sql = f"""
                       -- 题目表
                       CREATE TABLE IF NOT EXISTS `{table_alias}`
                       (
                           -- 核心ID
                           `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '题目ID',
                           `question_uuid`       VARCHAR(36) NOT NULL DEFAULT (UUID()) COMMENT '题目UUID（用于外部引用）',

                           -- 题目内容
                           `question_text`       TEXT        NOT NULL COMMENT '题干（纯文本）',
                           `question_html`       TEXT COMMENT '题干（HTML格式，支持公式、图片等）',
                           `question_markdown`   TEXT COMMENT '题干（Markdown格式）',

                           -- 答案与解析
                           `answer`              TEXT COMMENT '标准答案',
                           `analysis`            TEXT COMMENT '题目解析',
                           `hint`                VARCHAR(500) COMMENT '解题提示',
                           `ai_judge_prompt`     TEXT COMMENT 'AI判题时提示词',
                           `solution_steps`      TEXT COMMENT '解题步骤',
                           `knowledge_points`    VARCHAR(500) COMMENT '知识点',

                           -- 题目元数据
                           `grade`               TINYINT UNSIGNED NOT NULL COMMENT '年级：1-12, 1-6小学 7-9初中 10-12高中',
                           `subject`             VARCHAR(20) NOT NULL COMMENT '科目：chinese|math|english|physics|chemistry|biology|history|geography|politics',
                           `question_type`       VARCHAR(20) NOT NULL COMMENT '题型：single_choice|multiple_choice|fill_blank|short_answer|essay|judgement',

                           -- 难度与评分
                           `difficulty_level`    TINYINT UNSIGNED DEFAULT 3 COMMENT '难度等级：1-5（1最简单，5最难）',
                           `difficulty_label`    VARCHAR(10) COMMENT '难度标签：easy|medium|hard',

                           -- 多媒体资源
                           `images`              TEXT COMMENT '图片资源URL列表',
                           `audio_url`           VARCHAR(500) COMMENT '音频资源URL',
                           `video_url`           VARCHAR(500) COMMENT '视频解析URL',

                           -- AI生成信息
                           `ai_model`            VARCHAR(50) COMMENT 'AI模型名称：gpt-4|claude|文心一言等 如果Null 表示非AI生成题目',
                           `ai_prompt`           TEXT COMMENT '生成时使用的prompt',
                           `ai_params`           TEXT COMMENT '其他AI参数',

                           -- 版本控制
                           `version`             INT UNSIGNED DEFAULT 1 COMMENT '版本号',
                           `previous_version_id` BIGINT UNSIGNED COMMENT '上一版本ID',
                           `change_log`          TEXT COMMENT '变更说明',

                           -- 时间戳
                           `created_at`          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                           `updated_at`          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

                           -- 创建者信息
                           `created_by`          BIGINT UNSIGNED NOT NULL COMMENT '创建者ID',
                           `updated_by`          BIGINT UNSIGNED COMMENT '更新者ID',
                           `status`              BIGINT UNSIGNED COMMENT '状态：0-正常 1-删除',

                           -- 主键
                           PRIMARY KEY (`id`),

                           -- 索引
                           UNIQUE KEY `uk_question_uuid` (`question_uuid`),
                           KEY                   `idx_grade_subject` (`grade`, `subject`),
                           KEY                   `idx_question_type` (`question_type`),
                           KEY                   `idx_difficulty` (`difficulty_level`),
                           KEY                   `idx_ai_model` (`ai_model`),
                           KEY                   `idx_created_at` (`created_at`),
                           KEY                   `idx_created_by` (`created_by`),
                           KEY                   `idx_subject_type` (`subject`, `question_type`)

                       ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目表';
                       """

    # 字段类型注解
    id: Optional[int] = Field(None, description="题目ID")
    question_uuid: str = Field(None, description="题目UUID")
    question_text: str = Field(None, description="题干")
    question_html: Optional[str] = Field(None, description="题干（HTML格式）")
    question_markdown: Optional[str] = Field(None, description="题干（Markdown格式）")
    answer: Optional[str | dict | list | bool] = Field(None, description="标准答案")
    analysis: Optional[str] = Field(None, description="题目解析")
    hint: Optional[str] = Field(None, description="解题提示")
    ai_judge_prompt: Optional[str] = Field(None, description="AI判题时提示词")
    solution_steps: Optional[str | dict | list] = Field(None, description="解题步骤")
    knowledge_points: Optional[str] = Field(None, description="知识点")
    grade: int = Field(None, description="年级")
    subject: str = Field(None, description="科目")
    question_type: str = Field(None, description="题型")
    difficulty_level: Optional[int] = Field(None, description="难度等级")
    difficulty_label: Optional[str] = Field(None, description="难度标签")
    images: Optional[str] = Field(None, description="图片资源URL列表")
    audio_url: Optional[str] = Field(None, description="音频资源URL")
    video_url: Optional[str] = Field(None, description="视频解析URL")
    ai_model: Optional[str] = Field(None, description="AI模型名称")
    ai_prompt: Optional[str] = Field(None, description="生成时使用的prompt")
    ai_params: Optional[str] = Field(None, description="其他AI参数")
    version: Optional[int] = Field(None, description="版本号")
    previous_version_id: Optional[int] = Field(None, description="上一版本ID")
    change_log: Optional[str] = Field(None, description="变更说明")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: int = Field(None, description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")
    status: Optional[int] = Field(None, description="状态")

    @staticmethod
    def get_field_mapping() -> dict:
        """
        获取字段名到中文描述的映射

        Returns:
            dict: 字段名到中文描述的映射字典
        """
        field_mapping = {}
        for field_name, field_info in QuestionPo.model_fields.items():
            # 获取 Field 的 description 属性
            if hasattr(field_info, 'description') and field_info.description:
                field_mapping[field_name] = field_info.description
        return field_mapping

    # 字段验证器 - 将 bool 转换为 str
    @field_validator('answer', mode='before')
    @classmethod
    def validate_answer_field(cls, v):
        """验证并转换 answer 字段值，支持 bool 类型自动转换为 str"""
        if isinstance(v, bool):
            return str(v)
        return v

    # JSON 字段序列化器 - 将 dict/list 转换为 JSON 字符串
    @field_serializer('answer', 'solution_steps', 'images', 'ai_params')
    def serialize_json_fields(self, value, _info):
        """将 dict 或 list 类型的字段序列化为 JSON 字符串"""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    @property
    def mini_dict(self):
        return {'id': self.id,
                'question_uuid': self.question_uuid,
                'question_text': self.question_text,
                'question_type': self.question_type,
                'grade': self.grade,
                'subject': self.subject,
                'difficulty_level': self.difficulty_level}

    @classmethod
    def get_random_question(cls,
                          subject: Optional[str] = None,
                          question_type: Optional[str] = None,
                          difficulty_level: Optional[int] = None,
                          grade: Optional[int] = None) -> Optional['QuestionPo']:
        """
        根据条件随机查询一个题目

        Args:
            subject: 科目（可选）
            question_type: 题型（可选）
            difficulty_level: 难度等级 1-5（可选）
            grade: 年级 1-12（可选）

        Returns:
            随机题目对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                return None

            table_name = cls.get_table_name()

            # 构建查询条件
            where_clauses = []
            params = []

            if subject:
                where_clauses.append("`subject` = %s")
                params.append(subject)

            if question_type:
                where_clauses.append("`question_type` = %s")
                params.append(question_type)

            if difficulty_level:
                where_clauses.append("`difficulty_level` = %s")
                params.append(difficulty_level)

            if grade:
                where_clauses.append("`grade` = %s")
                params.append(grade)

            # 构建 SQL
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            sql = f"SELECT * FROM `{table_name}` WHERE {where_sql} ORDER BY RAND() LIMIT 1"

            result = db.execute(sql, tuple(params))
            if result:
                return cls(**result[0])
            return None
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"get_random_question 失败：{str(e)}")
            return None

    @classmethod
    def get_by_id(cls, id_val) -> Optional['QuestionPo']:
        """
        根据 ID 或 UUID 查询记录

        Args:
            id_val: 题目 ID（整数）或 UUID（字符串）

        Returns:
            题目对象，未找到返回 None
        """
        try:
            cls._ensure_table_exists()
            db = cls.get_db_connection()
            if db is None:
                logger = __import__('logging').getLogger(__name__)
                logger.warning(f"{cls.__name__}.get_by_id({id_val}) 失败：数据库连接未设置")
                return None

            table_name = cls.get_table_name()

            sql = f"SELECT * FROM `{table_name}` WHERE `id` = %s or `question_uuid` = %s limit 1"
            params = (id_val,str(id_val))

            result = db.execute(sql, params)

            if not result:
                return None

            return cls(**result[0])
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"{cls.__name__}.get_by_id({id_val}) 失败：{str(e)}")
            return None




if __name__ == '__main__':
    po = QuestionPo()
    po.create_table()

    print("\n=== 测试随机题目查询 ===")

    # 测试1：无条件随机查询
    question = QuestionPo.get_random_question()
    if question:
        print(f"✓ 随机题目（无筛选）: ID={question.id}, UUID={question.question_uuid}")
    else:
        print("✗ 未找到题目")

    # 测试2：按科目随机查询
    question = QuestionPo.get_random_question(subject="math")
    if question:
        print(f"✓ 随机数学题: ID={question.id}, 题型={question.question_type}")
    else:
        print("✗ 未找到数学题目")

    # 测试3：按科目和题型随机查询
    question = QuestionPo.get_random_question(subject="math", question_type="single_choice")
    if question:
        print(f"✓ 随机数学单选题: ID={question.id}, 难度={question.difficulty_level}")
    else:
        print("✗ 未找到符合条件的题目")

    # 测试4：按难度随机查询
    question = QuestionPo.get_random_question(difficulty_level=3)
    if question:
        print(f"✓ 随机中等难度题: ID={question.id}, 科目={question.subject}")
    else:
        print("✗ 未找到中等难度题目")
