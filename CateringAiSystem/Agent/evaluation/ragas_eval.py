"""RAG 质量评估（RAGAS）

基于 RAGAS 框架量化评估知识库检索与生成质量。
支持作为独立脚本运行和程序化调用。

用法:
    # 程序化调用
    from CateringAiSystem.Agent.evaluation.ragas_eval import RAGEvaluator
    report = await RAGEvaluator.evaluate()
    print(report["summary"])

    # 命令行
    python -m CateringAiSystem.Agent.evaluation.ragas_eval

    # 评估指定文档
    python -m CateringAiSystem.Agent.evaluation.ragas_eval --doc-id 1

目标值:
    - Hit Rate (context_recall):        > 90%
    - MRR (context_precision):          > 0.85
    - Faithfulness:                     > 85%
    - Answer Relevancy:                 > 90%
"""
import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── 默认测试用例（用户应根据实际知识库内容增删改） ──

DEFAULT_TEST_CASES = [
    # 公司制度
    {"question": "公司年假有多少天？", "ground_truth": "公司年假根据工龄计算，满1年5天，满10年10天，满20年15天。"},
    {"question": "员工迟到怎么处理？", "ground_truth": "员工迟到30分钟内扣款20元，超过30分钟按事假处理，月度累计3次以上给予书面警告。"},
    {"question": "请病假需要什么材料？", "ground_truth": "请病假需提供二级以上医院开具的诊断证明或病历，请假时长超过3天需提前报部门主管审批。"},
    {"question": "公司报销流程是什么？", "ground_truth": "报销流程：员工填写报销单→部门主管审核→财务审核→出纳付款。单笔超过2000元需总经理审批。"},
    # 菜品知识
    {"question": "招牌红烧肉的标准化配料有哪些？", "ground_truth": "招牌红烧肉的标准配料：五花肉500g、冰糖30g、生抽20ml、老抽10ml、料酒15ml、八角2个、桂皮1段、姜片5片。"},
    {"question": "酸辣土豆丝的切制标准是什么？", "ground_truth": "酸辣土豆丝切制标准：土豆丝粗细2-3mm，长度5-8cm，切好后立即浸泡在清水中去除淀粉，浸泡时间不少于5分钟。"},
    # 运营流程
    {"question": "门店每日开业流程是什么？", "ground_truth": "每日开业流程：1) 检查设备运行状态 2) 验收食材到货 3) 按照备菜清单准备当日食材 4) 开市前30分钟完成所有准备工作 5) 召开班前会。"},
    {"question": "外卖订单出现漏送怎么处理？", "ground_truth": "外卖漏送处理流程：1) 确认漏送菜品及金额 2) 立即联系顾客致歉 3) 安排补送或退款 4) 记录至客诉台账 5) 查找原因避免再犯。"},
    # SOP标准
    {"question": "炒锅的温度控制标准是多少？", "ground_truth": "炒锅温度控制标准：滑炒180-200°C，爆炒220-240°C，炸制160-180°C，炖煮保持微沸状态95-100°C。"},
    {"question": "食材验收的标准流程是什么？", "ground_truth": "食材验收标准流程：1) 核对送货单与订单 2) 检查食材外观、色泽、气味 3) 测量中心温度（冷链食品≤4°C）4) 称重核实数量 5) 填写验收记录 6) 分类入库。"},
]


class RAGEvaluator:
    """RAG 质量评估器（RAGAS）

    提供检索质量（Hit Rate、MRR）和生成质量（Faithfulness、Answer Relevancy）评估。
    """

    TEST_CASES = DEFAULT_TEST_CASES

    @classmethod
    async def evaluate(cls, doc_id: Optional[int] = None,
                       test_cases: Optional[list] = None,
                       permission_scope: str = "all",
                       top_k: int = 5) -> dict:
        """执行 RAGAS 评估

        Args:
            doc_id: 限定评估的文档 ID（None 表示全库评估）
            test_cases: 自定义测试用例，默认使用 DEFAULT_TEST_CASES
            permission_scope: 检索权限范围
            top_k: 检索返回条数

        Returns:
            dict: 包含各项指标得分和评估报告的字典
        """
        cases = test_cases or cls.TEST_CASES
        if not cases:
            return {"error": "没有测试用例", "scores": {}, "summary": ""}

        questions = [c["question"] for c in cases]
        ground_truths = [c["ground_truth"] for c in cases]

        logger.info("RAGAS 评估开始 | 测试用例数: %d | doc_id: %s | top_k: %d",
                    len(cases), doc_id or "全库", top_k)

        # Step 1: 对每个问题执行 RAG 流水线
        answers = []
        contexts_list = []

        for i, q in enumerate(questions):
            answer, contexts = await cls._run_rag_pipeline(
                question=q, permission_scope=permission_scope, top_k=top_k,
            )
            answers.append(answer)
            contexts_list.append(contexts)

        # Step 2: 计算 RAGAS 指标
        scores = await cls._compute_ragas_scores(questions, answers, contexts_list, ground_truths)

        # Step 3: 补充 Hit Rate 和 MRR 计算
        hit_rate, mrr = cls._compute_retrieval_metrics(questions, contexts_list, ground_truths)
        scores["hit_rate"] = hit_rate
        scores["mrr"] = mrr

        # Step 4: 生成报告
        summary = cls._format_report(scores, len(cases))
        report = {
            "scores": scores,
            "summary": summary,
            "test_case_count": len(cases),
            "passed": cls._check_targets(scores),
        }

        logger.info("RAGAS 评估完成\n%s", summary)
        return report

    @classmethod
    async def _run_rag_pipeline(cls, question: str, permission_scope: str = "all",
                                 top_k: int = 5) -> tuple:
        """对单个问题执行 RAG 检索 + LLM 生成

        Returns:
            (answer: str, contexts: list[str])
        """
        from CateringAiSystem.Service.knowledgeService import KnowledgeService
        from CateringAiSystem.Utils.llm_models import get_qian_wen

        # 检索
        results = KnowledgeService.search(query=question, permission_scope=permission_scope, top_k=top_k)
        contexts = [r["text"] for r in results if r.get("text")] if results else []

        if not contexts:
            return "暂无相关检索结果", []

        # LLM 生成回答
        context_str = "\n\n---\n\n".join(contexts)
        llm = get_qian_wen(temperature=0.3, max_tokens=1024)
        prompt = (
            f"请基于以下参考内容回答问题。如果参考内容不足以回答，请如实说明。\n\n"
            f"参考内容：\n{context_str}\n\n"
            f"问题：{question}\n\n"
            f"请给出简洁准确的回答。"
        )
        try:
            resp = await llm.ainvoke(prompt)
            answer = resp.content if hasattr(resp, "content") else str(resp)
        except Exception as e:
            logger.error("LLM 生成回答失败: %s", e)
            answer = "生成回答失败"

        return answer, contexts

    @classmethod
    async def _compute_ragas_scores(cls, questions: list, answers: list,
                                     contexts_list: list, ground_truths: list) -> dict:
        """使用 RAGAS 框架计算评估指标"""
        try:
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision,
            )
            from datasets import Dataset
        except ImportError:
            logger.warning("RAGAS 或 datasets 未安装，跳过 RAGAS 指标计算")
            return {"faithfulness": 0, "answer_relevancy": 0, "context_recall": 0, "context_precision": 0}

        try:
            dataset = Dataset.from_dict({
                "question": questions,
                "answer": answers,
                "contexts": contexts_list,
                "ground_truth": ground_truths,
            })

            result = evaluate(
                dataset=dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_recall,
                    context_precision,
                ],
            )

            scores = {}
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
                for key in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
                    scores[key] = round(result_dict.get(key, 0), 4)
            else:
                scores = {
                    "faithfulness": round(float(result.get("faithfulness", 0)), 4),
                    "answer_relevancy": round(float(result.get("answer_relevancy", 0)), 4),
                    "context_recall": round(float(result.get("context_recall", 0)), 4),
                    "context_precision": round(float(result.get("context_precision", 0)), 4),
                }
            return scores
        except Exception as e:
            logger.error("RAGAS 评估计算失败: %s", e)
            return {"faithfulness": 0, "answer_relevancy": 0, "context_recall": 0, "context_precision": 0}

    @classmethod
    def _compute_retrieval_metrics(cls, questions: list, contexts_list: list,
                                    ground_truths: list) -> tuple:
        """计算检索层面的 Hit Rate 和 MRR

        将 ground_truth 拆分为关键词，判断检索结果中是否包含这些关键词。
        """
        import jieba

        hit_count = 0
        reciprocal_ranks = []

        for contexts, gt in zip(contexts_list, ground_truths):
            if not contexts:
                reciprocal_ranks.append(0)
                continue

            # 分词
            gt_keywords = set(jieba.lcut(gt))
            # 过滤单字和过短的词
            gt_keywords = {kw for kw in gt_keywords if len(kw) >= 2}

            if not gt_keywords:
                hit_count += 1
                reciprocal_ranks.append(1)
                continue

            found_rank = None
            for rank, ctx in enumerate(contexts):
                ctx_keywords = set(jieba.lcut(ctx))
                overlap = gt_keywords & ctx_keywords
                if len(overlap) / len(gt_keywords) >= 0.3:
                    if found_rank is None:
                        found_rank = rank
                    break

            if found_rank is not None:
                hit_count += 1
                reciprocal_ranks.append(1.0 / (found_rank + 1))
            else:
                reciprocal_ranks.append(0)

        n = len(questions)
        hit_rate = round(hit_count / n, 4) if n > 0 else 0
        mrr = round(sum(reciprocal_ranks) / n, 4) if n > 0 else 0
        return hit_rate, mrr

    @staticmethod
    def _format_report(scores: dict, case_count: int) -> str:
        """格式化评估报告"""
        lines = [
            "=" * 60,
            "RAG 质量评估报告",
            "=" * 60,
            f"测试用例数: {case_count}",
            "-" * 60,
        ]

        metric_names = {
            "faithfulness": ("Faithfulness（忠实度）", "> 85%", 0.85),
            "answer_relevancy": ("Answer Relevancy（回答相关性）", "> 90%", 0.90),
            "context_recall": ("Hit Rate（检索命中率）", "> 90%", 0.90),
            "context_precision": ("MRR（平均倒数排名）", "> 0.85", 0.85),
            "hit_rate": ("Hit Rate（关键词命中率）", "> 90%", 0.90),
            "mrr": ("MRR（关键词平均倒数排名）", "> 0.85", 0.85),
        }

        all_passed = True
        for key, (label, target_str, threshold) in metric_names.items():
            value = scores.get(key, 0)
            passed = value >= threshold
            if not passed:
                all_passed = False
            status = "✓ PASS" if passed else "✗ FAIL"
            lines.append(f"  {label:30s} | {value:.2%}  | 目标: {target_str:8s} | {status}")

        lines.append("-" * 60)
        lines.append(f"总体评估: {'✓ 通过' if all_passed else '✗ 未通过'}")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _check_targets(scores: dict) -> bool:
        """检查是否全部达标"""
        thresholds = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.90,
            "context_recall": 0.90,
            "context_precision": 0.85,
            "hit_rate": 0.90,
            "mrr": 0.85,
        }
        for key, threshold in thresholds.items():
            if scores.get(key, 0) < threshold:
                return False
        return True


# ═══════════════════════════════════════════
# 知识库更新后自动触发评估
# ═══════════════════════════════════════════

async def evaluate_after_vectorize(doc_id: int) -> dict:
    """向量化完成后自动执行 RAGAS 评估

    由 knowledgeService.confirm_vectorize 在向量化完成后调用。
    """
    logger.info("知识库文档向量化完成，触发 RAGAS 评估 (doc_id=%s)", doc_id)
    report = await RAGEvaluator.evaluate(doc_id=doc_id)
    return report


# ═══════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="RAGAS 质量评估")
    parser.add_argument("--doc-id", type=int, default=None, help="限定评估的文档ID")
    parser.add_argument("--top-k", type=int, default=5, help="检索返回条数")
    parser.add_argument("--output", type=str, default=None, help="结果输出文件路径（JSON）")
    args = parser.parse_args()

    async def main():
        report = await RAGEvaluator.evaluate(doc_id=args.doc_id, top_k=args.top_k)
        print("\n" + report["summary"])

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n报告已保存至: {args.output}")

        # 非零退出码表示评估未通过
        if not report.get("passed", False):
            exit(1)

    asyncio.run(main())
