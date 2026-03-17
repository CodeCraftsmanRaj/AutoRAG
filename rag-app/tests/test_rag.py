import json
import os
from importlib import import_module
from pathlib import Path

import pytest

from app.rag import query_rag

THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))
DATASET_PATH = Path(__file__).resolve().parents[1] / "golden_dataset.json"


@pytest.mark.rag_eval
def test_rag_golden_dataset_quality_gate() -> None:
	try:
		deepeval_mod = import_module("deepeval")
		metrics_mod = import_module("deepeval.metrics")
		test_case_mod = import_module("deepeval.test_case")
	except Exception:
		pytest.skip("DeepEval is not installed in this environment.")

	assert_test = getattr(deepeval_mod, "assert_test")
	FaithfulnessMetric = getattr(metrics_mod, "FaithfulnessMetric")
	AnswerRelevancyMetric = getattr(metrics_mod, "AnswerRelevancyMetric")
	ContextualPrecisionMetric = getattr(metrics_mod, "ContextualPrecisionMetric")
	ContextualRecallMetric = getattr(metrics_mod, "ContextualRecallMetric")
	ContextualRelevancyMetric = getattr(metrics_mod, "ContextualRelevancyMetric")
	LLMTestCase = getattr(test_case_mod, "LLMTestCase")

	dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
	metrics = [
		FaithfulnessMetric(threshold=THRESHOLD),
		AnswerRelevancyMetric(threshold=THRESHOLD),
		ContextualPrecisionMetric(threshold=THRESHOLD),
		ContextualRecallMetric(threshold=THRESHOLD),
		ContextualRelevancyMetric(threshold=THRESHOLD),
	]

	failures = []
	for item in dataset:
		result = query_rag(item["question"], top_k=4, namespace="default")
		case = LLMTestCase(
			input=item["question"],
			expected_output=item["expected_answer"],
			actual_output=result["answer"],
			retrieval_context=result["contexts"],
		)
		try:
			assert_test(case, metrics)
		except AssertionError as exc:
			failures.append({"id": item["id"], "question": item["question"], "error": str(exc)})

	assert not failures, f"RAG quality gate failed: {json.dumps(failures, ensure_ascii=False)}"

