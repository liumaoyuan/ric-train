"""
答题记录 Mock 数据生成器
使用 LLM 生成真实的仿真答题数据
"""
import logging
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Ai.base import UserMessages

logger = logging.getLogger(__name__)


def _generate_single_record(_) -> Dict:
    """
    生成单条答题记录（供多线程使用）

    Args:
        _ : 占位符参数，用于 ThreadPoolExecutor.map

    Returns:
        Dict: 单条答题记录
    """
    llm = get_default_qwen_llm()

    # 基础数据池
    question_ids = [
        "q_uuid_001", "q_uuid_002", "q_uuid_003", "q_uuid_004", "q_uuid_005",
        "q_uuid_006", "q_uuid_007", "q_uuid_008", "q_uuid_009", "q_uuid_010"
    ]
    user_ids = [
        "user_001", "user_002", "user_003", "user_004", "user_005",
        "user_006", "user_007", "user_008", "user_009", "user_010"
    ]
    sources = ["daily_question", "exam", "homework", "practice"]
    question_types = ["single_choice", "multiple_choice", "fill_blank", "short_answer"]
    answer_pool = {
        "single_choice": ["A", "B", "C", "D"],
        "multiple_choice": ["AB", "AC", "ABC", "ABCD", "BCD"],
        "fill_blank": ["答案是 42", "结果为 100", "等于π", "x=5"],
        "short_answer": ["因为根据勾股定理...", "主要原因是...", "解：设 x 为未知数..."]
    }

    # 使用 LLM 生成单条数据的核心信息
    prompt = """请生成 1 条学生答题记录数据，包含：
1. 题目类型（single_choice/multiple_choice/fill_blank/short_answer）
2. 用户答案（符合题型）
3. 得分率 (0-1，要有变化)
4. AI 判题置信度 (0.7-0.99)
5. AI 判题简要评语

请以 JSON 格式返回：
{"question_type": "single_choice", "user_answer": "A", "score": 0.8, "ai_confidence": 0.95, "ai_comment": "回答正确"}
"""

    try:
        messages = [UserMessages(prompt=prompt)]
        response = llm.chat(messages)

        # 清理并解析 JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        result = json.loads(response)
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"LLM 生成失败，使用备用方案：{e}")
        result = {
            "question_type": random.choice(question_types),
            "user_answer": "A",
            "score": random.choice([0, 0.5, 0.7, 0.8, 1.0]),
            "ai_confidence": round(random.uniform(0.75, 0.99), 2),
            "ai_comment": "备用数据"
        }

    # 构建完整记录
    question_type = result.get("question_type", "single_choice")
    base_time = datetime.now()
    random_hours = random.randint(0, 168)
    created_at = base_time - timedelta(hours=random_hours)

    ai_result = {
        "correct": result.get("score", 1.0) >= 0.8,
        "confidence": result.get("ai_confidence", 0.9),
        "comment": result.get("ai_comment", ""),
        "question_type": question_type
    }

    record = {
        "question_id": random.choice(question_ids),
        "user_id": random.choice(user_ids),
        "user_answer": result.get("user_answer", random.choice(answer_pool[question_type])),
        "score": float(result.get("score", 1.0)),
        "ai_model": "qwen-max" if random.random() > 0.3 else None,
        "ai_prompt": f"请判断以下{question_type}的答案是否正确。",
        "ai_result": json.dumps(ai_result, ensure_ascii=False),
        "source": random.choice(sources),
        "connection_id": f"conn_{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
    }

    return record


def generate_mock_answer_data(num: int = 5, max_workers: int = 50) -> List[Dict]:
    """
    使用 LLM 生成真实的仿真答题数据（多线程并发）

    Args:
        num: 生成数据条数，默认 5 条
        max_workers: 最大并发数，默认 50

    Returns:
        List[Dict]: 答题记录列表
    """
    logger.info(f"开始生成 {num} 条答题记录，并发数：{max_workers}")

    records = []

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        futures = list(executor.map(_generate_single_record, range(num)))
        records.extend(futures)

    logger.info(f"成功生成 {len(records)} 条答题记录")
    return records


def insert_mock_answers_to_db(records: List[Dict]) -> int:
    """
    将生成的答题记录插入数据库

    Args:
        records: 答题记录列表

    Returns:
        int: 成功插入的记录数
    """
    from Education.models.pojo.answerPo import AnswerPo

    success_count = 0
    for record in records:
        try:
            answer = AnswerPo(**record)
            answer_id = answer.save()
            if answer_id > 0:
                success_count += 1
                logger.info(f"插入答题记录成功，ID={answer_id}, question_id={record.get('question_id')}")
        except Exception as e:
            logger.error(f"插入答题记录失败：{e}")

    return success_count


def create_and_insert_mock_answers(num: int = 5, max_workers: int = 50, show_progress: bool = True) -> dict:
    """
    一站式函数：生成并插入答题记录到数据库（多线程并发）

    Args:
        num: 要生成的答题记录数量
        max_workers: 最大并发数，默认 50
        show_progress: 是否显示进度日志，默认 True

    Returns:
        dict: 执行结果统计
            - total: 生成总数
            - success: 成功插入数
            - failed: 失败数
    """
    if show_progress:
        logger.info(f"开始生成并插入 {num} 条答题记录，并发数：{max_workers}...")

    # 1. 生成 Mock 数据（多线程）
    records = generate_mock_answer_data(num=num, max_workers=max_workers)

    if not records:
        logger.warning("未能生成任何答题记录")
        return {'total': 0, 'success': 0, 'failed': 0}

    # 2. 批量插入数据库
    success_count = insert_mock_answers_to_db(records)
    failed_count = num - success_count

    if show_progress:
        logger.info(f"完成：成功 {success_count}/{num} 条，失败 {failed_count} 条")

    return {'total': num, 'success': success_count, 'failed': failed_count}


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    create_and_insert_mock_answers(num=250,max_workers=50)