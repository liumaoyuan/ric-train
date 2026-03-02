# Education 考试模块开发总结

## 已完成的功能

### 1. 数据库实体类

#### PaperPo - 试卷表实体类
**文件位置**: `Education/models/pojo/paperPo.py`

**核心字段**:
- `id`, `paper_uuid`: 主键
- `parent_id`: 父版本 ID（用于版本控制）
- `paper_name`: 试卷名称
- `description`: 试卷描述
- `subject`: 科目
- `question_ids`: 题目 ID 列表（逗号分隔）
- `scores`: 每题分值（逗号分隔）
- `default_score_type`: 默认分值类型（uniform_1=每题 1 分）
- `duration_minutes`: 考试时长
- `status`: draft|published|archived
- `is_public`: 是否公开
- `created_by`, `created_at`: 创建者/时间

**主要方法**:
- `get_question_id_list()`: 获取题目 ID 列表
- `get_score_list()`: 获取分值列表
- `total_score`: 计算总分
- `get_score_for_question(index)`: 获取指定题目分值
- `get_by_uuid()`: 根据 UUID 查询
- `get_versions()`: 获取版本历史

---

#### ExamPo - 考试记录表实体类
**文件位置**: `Education/models/pojo/examPo.py`

**核心字段**:
- `id`, `exam_uuid`: 主键
- `paper_id`: 试卷 ID
- `user_id`: 考生姓名/ID
- `start_time`, `end_time`: 考试起止时间
- `user_ip`: 用户 IP 地址
- `answers`: 用户答案（JSON 格式）
- `total_score`: 总分
- `score_details`: 得分详情（JSON 格式）
- `ai_summary`: AI 考试总结
- `ai_scoring_basis`: AI 打分依据
- `teacher_review`: 教师复核意见（保留字段）
- `status`: ongoing|submitted|graded

**主要方法**:
- `get_answers_dict()`: 获取答案字典
- `get_score_details_dict()`: 获取得分详情
- `get_by_uuid()`: 根据 UUID 查询
- `check_user_exam_exists()`: 检查用户是否已参加考试
- `get_by_user_id()`: 查询用户历史考试

---

### 2. Service 服务层

#### PaperService - 试卷服务
**文件位置**: `Education/services/paperService.py`

**主要方法**:
- `create_paper()`: 创建试卷
- `update_paper()`: 更新试卷（创建新版本）
- `get_paper_detail()`: 获取试卷详情（含题目信息）
- `get_paper_versions()`: 获取版本历史
- `delete_paper()`: 删除试卷（软删除）
- `publish_paper()`: 发布试卷

---

#### ExamService - 考试服务
**文件位置**: `Education/services/examService.py`

**主要方法**:
- `start_exam()`: 开始考试
- `submit_exam()`: 提交试卷
- `grade_exam()`: 判卷（固定逻辑 + AI）
- `judge_single_question()`: 判单道题
- `generate_ai_summary()`: 生成 AI 考试总结
- `get_exam_result()`: 获取考试结果
- `get_user_history()`: 查询用户历史

---

### 3. Prompt 模板

**文件位置**: `Education/prompts/examPrompts.py`

**模板列表**:
- `EXAM_AI_SUMMARY_PROMPT`: AI 考试总结 Prompt
- `EXAM_AI_JUDGE_PROMPT`: AI 判题 Prompt
- `EXAM_CHEATING_DETECTION_PROMPT`: 作弊检测 Prompt（预留）

---

### 4. API 接口

#### Paper API - 试卷接口
**文件位置**: `Education/api/core/paperApi.py`

**接口列表**:
- `GET /education/paper/{paper_id}`: 获取试卷详情
- `POST /education/paper`: 创建试卷
- `GET /education/paper/{paper_id}/versions`: 获取版本历史
- `PUT /education/paper/{paper_id}/publish`: 发布试卷
- `DELETE /education/{paper_id}`: 删除试卷

---

#### Exam API - 考试接口
**文件位置**: `Education/api/core/examApi.py`

**接口列表**:
- `POST /education/exam/start`: 开始考试
- `POST /education/exam/{exam_id}/submit`: 提交试卷
- `GET /education/exam/{exam_id}/result`: 获取考试结果
- `GET /education/exam/history`: 查询历史答题
- `POST /education/exam/{exam_id}/grade`: 手动判卷

---

### 5. 前端页面

**文件位置**: `Education/frontend/`

**页面列表**:

| 页面 | 文件 | 路由 | 功能 |
|------|------|------|------|
| 考试页面 | `exam.html` | `/edu/exam` | 根据试卷 ID 渲染题目，倒计时，提交答案 |
| 结果页面 | `exam_result.html` | `/edu/exam-result` | 显示成绩、AI 总结、学习建议 |
| 历史页面 | `history.html` | `/edu/history` | 输入名字查询历史答题记录 |

**前端功能**:
- 学生输入姓名即可开始考试
- 倒计时功能（默认 30 分钟）
- 支持多种题型：单选题、多选题、判断题、填空题、简答题、论述题
- 超时自动交卷
- AI 判卷和总结展示

---

## 使用方式

### 1. 创建试卷

```python
from Education.services.paperService import get_paper_service

service = get_paper_service()
paper = service.create_paper(
    paper_name="Python 基础测试",
    question_ids=[1, 2, 3, 4, 5],
    scores=[2, 2, 2, 2, 2],  # 每题 2 分
    subject="python",
    duration_minutes=30,
    created_by=505
)
```

### 2. 开始考试

**前端访问**: `/edu/exam?paper_id={试卷 ID}`

学生输入姓名后点击"开始考试"，系统会：
1. 检查用户是否已参加过该试卷
2. 创建考试记录
3. 渲染题目
4. 开始倒计时

### 3. 提交试卷

学生完成答题后点击"提交试卷"，系统会：
1. 客观题（选择、判断）使用固定逻辑判卷
2. 主观题（简答、论述）使用 AI 判卷
3. 生成 AI 考试总结（含学习建议）
4. 保存判卷结果

### 4. 查看结果

提交后自动跳转到结果页，或访问 `/edu/exam-result?exam_id={考试 ID}`

### 5. 查看历史

访问 `/edu/history`，输入姓名查询历史考试记录

---

## 技术要点

### 1. 答案存储方案
使用 JSON 格式存储每题答案，避免逗号冲突问题：
```json
{
    "1": "A",
    "2": "A,C",
    "3": "北京",
    "4": "简述..."
}
```

### 2. 判卷逻辑
- **客观题**: 复用 `questionService.judge_question()` 固定逻辑
- **主观题**: 使用 AI 判卷，支持部分得分

### 3. AI 总结生成
调用大模型生成三部分内容：
- 成绩总结（鼓励性语言）
- 知识点梳理
- 学习建议（2-3 条具体建议）

### 4. 版本控制
通过 `parent_id` 字段实现试卷版本管理，每次更新创建新记录

---

## 待扩展功能

1. **手动选题组卷**: 目前只支持指定题目 ID 创建试卷，可扩展前端手动选题界面
2. **随机出题组卷**: 可按规则随机选题生成试卷
3. **教师复核功能**: 已有 `teacher_review` 字段，可实现修改分数功能
4. **防作弊检测**: 预留了 `EXAM_CHEATING_DETECTION_PROMPT`，可实现异常检测
5. **题目解析展示**: 考后可显示题目解析

---

## 文件清单

```
Education/
├── api/
│   ├── core/
│   │   ├── paperApi.py       # 试卷 API
│   │   └── examApi.py        # 考试 API
│   └── router.py             # 路由注册（已更新）
├── frontend/
│   ├── exam.html             # 考试页面
│   ├── exam_result.html      # 结果页面
│   ├── history.html          # 历史页面
│   └── register.py           # 前端路由注册（已更新）
├── models/
│   └── pojo/
│       ├── paperPo.py        # 试卷实体类
│       └── examPo.py         # 考试记录实体类
├── prompts/
│   └── examPrompts.py        # 考试相关 Prompt
├── services/
│   ├── paperService.py       # 试卷服务
│   └── examService.py        # 考试服务
└── plan.md                   # 开发计划文档
```
