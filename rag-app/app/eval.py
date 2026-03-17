import json
import os
from importlib import import_module
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from app.rag import query_rag


def _load_deepeval() -> Dict[str, Any]:
	"""Lazy import to avoid editor import errors when DeepEval is not installed locally."""
	try:
		metrics_mod = import_module("deepeval.metrics")
		test_case_mod = import_module("deepeval.test_case")
	except Exception as exc:  # pragma: no cover
		raise RuntimeError(
			"DeepEval is required for evaluation. Install with: pip install -r requirements.txt"
		) from exc

	return {
		"AnswerRelevancyMetric": getattr(metrics_mod, "AnswerRelevancyMetric"),
		"ContextualPrecisionMetric": getattr(metrics_mod, "ContextualPrecisionMetric"),
		"ContextualRecallMetric": getattr(metrics_mod, "ContextualRecallMetric"),
		"ContextualRelevancyMetric": getattr(metrics_mod, "ContextualRelevancyMetric"),
		"FaithfulnessMetric": getattr(metrics_mod, "FaithfulnessMetric"),
		"LLMTestCase": getattr(test_case_mod, "LLMTestCase"),
	}


def run_dataset_eval(dataset_path: str = "./golden_dataset.json", threshold: float = 0.75) -> Dict[str, float]:
	deps = _load_deepeval()
	FaithfulnessMetric = deps["FaithfulnessMetric"]
	AnswerRelevancyMetric = deps["AnswerRelevancyMetric"]
	ContextualPrecisionMetric = deps["ContextualPrecisionMetric"]
	ContextualRecallMetric = deps["ContextualRecallMetric"]
	ContextualRelevancyMetric = deps["ContextualRelevancyMetric"]
	LLMTestCase = deps["LLMTestCase"]

	dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))

	faithfulness_scores: List[float] = []
	relevancy_scores: List[float] = []
	precision_scores: List[float] = []
	recall_scores: List[float] = []
	contextual_rel_scores: List[float] = []

	for item in dataset:
		result = query_rag(item["question"], top_k=4)
		case = LLMTestCase(
			input=item["question"],
			expected_output=item["expected_answer"],
			actual_output=result["answer"],
			retrieval_context=result["contexts"],
		)

		m1 = FaithfulnessMetric(threshold=threshold)
		m2 = AnswerRelevancyMetric(threshold=threshold)
		m3 = ContextualPrecisionMetric(threshold=threshold)
		m4 = ContextualRecallMetric(threshold=threshold)
		m5 = ContextualRelevancyMetric(threshold=threshold)

		for metric in [m1, m2, m3, m4, m5]:
			metric.measure(case)

		faithfulness_scores.append(float(m1.score))
		relevancy_scores.append(float(m2.score))
		precision_scores.append(float(m3.score))
		recall_scores.append(float(m4.score))
		contextual_rel_scores.append(float(m5.score))

	report = {
		"faithfulness": mean(faithfulness_scores) if faithfulness_scores else 0.0,
		"answer_relevancy": mean(relevancy_scores) if relevancy_scores else 0.0,
		"contextual_precision": mean(precision_scores) if precision_scores else 0.0,
		"contextual_recall": mean(recall_scores) if recall_scores else 0.0,
		"contextual_relevancy": mean(contextual_rel_scores) if contextual_rel_scores else 0.0,
	}
	report["rag_composite"] = mean(report.values()) if report else 0.0
	report["threshold"] = threshold
	report["passed"] = report["faithfulness"] >= threshold and report["rag_composite"] >= threshold
	return report


if __name__ == "__main__":
	path = os.getenv("GOLDEN_DATASET_PATH", "./golden_dataset.json")
	threshold = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))
	summary = run_dataset_eval(path, threshold)
	print(json.dumps(summary, indent=2))
	if not summary["passed"]:
		raise SystemExit(1)

