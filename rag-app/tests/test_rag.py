import json
import os
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.metrics import (
	AnswerRelevancyMetric,
	ContextualPrecisionMetric,
	ContextualRecallMetric,
	ContextualRelevancyMetric,
	FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

from app.rag import query_rag

THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))
DATASET_PATH = Path(__file__).resolve().parents[1] / "golden_dataset.json"


@pytest.mark.rag_eval
def test_rag_golden_dataset_quality_gate() -> None:
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

