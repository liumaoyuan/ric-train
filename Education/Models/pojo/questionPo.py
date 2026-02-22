from typing import Optional, ClassVar
from Base.Repository.models.defaultDbModel import DefaultDbModel


class QuestionPo(DefaultDbModel):
    table_alias: ClassVar[str] = 'question'
    create_table_sql = """
                       -- 题目表
                       CREATE TABLE `questions`
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
                           `ai_judge_prompt`     VARCHAR(500) COMMENT 'AI判题时提示词',
                           `solution_steps`      JSON COMMENT '解题步骤（JSON数组）',

                           -- 题目元数据
                           `grade`               TINYINT UNSIGNED NOT NULL COMMENT '年级：1-9 对应一年级到九年级',
                           `subject`             VARCHAR(20) NOT NULL COMMENT '科目：chinese|math|english|physics|chemistry|biology|history|geography|politics',
                           `question_type`       VARCHAR(20) NOT NULL COMMENT '题型：single_choice|multiple_choice|fill_blank|short_answer|essay|true_false|matching',

                           -- 难度与评分
                           `difficulty_level`    TINYINT UNSIGNED DEFAULT 3 COMMENT '难度等级：1-5（1最简单，5最难）',
                           `difficulty_label`    VARCHAR(10) COMMENT '难度标签：easy|medium|hard',

                           -- 多媒体资源
                           `images`              JSON COMMENT '图片资源URL列表（JSON数组）',
                           `audio_url`           VARCHAR(500) COMMENT '音频资源URL',
                           `video_url`           VARCHAR(500) COMMENT '视频解析URL',

                           -- AI生成信息
                           `ai_model`            VARCHAR(50) COMMENT 'AI模型名称：gpt-4|claude|文心一言等 如果Null 表示非AI生成题目',
                           `ai_prompt`           TEXT COMMENT '生成时使用的prompt',
                           `ai_params`           JSON COMMENT '其他AI参数（JSON格式）',

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
    id: Optional[int] = None
    question_uuid: str = None
    question_text: str = None
    question_html: Optional[str] = None
    question_markdown: Optional[str] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    hint: Optional[str] = None
    ai_judge_prompt: Optional[str] = None
    solution_steps: Optional[str] = None
    grade: int = None
    subject: str = None
    question_type: str = None
    difficulty_level: Optional[int] = None
    difficulty_label: Optional[str] = None
    images: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_params: Optional[str] = None
    version: Optional[int] = None
    previous_version_id: Optional[int] = None
    change_log: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: int = None
    updated_by: Optional[int] = None




if __name__ == '__main__':
    po = QuestionPo()
    po.create_table()
