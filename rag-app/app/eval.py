import json
import os
import string
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from app.rag import query_rag

def _normalize(text: str) -> List[str]:
	strip_chars = string.punctuation + "`"
	return [
		token.strip(strip_chars).lower()
		for token in text.split()
		if token.strip(strip_chars)
	]


def _overlap_ratio(a: str, b: str) -> float:
	a_tokens = set(_normalize(a))
	b_tokens = set(_normalize(b))
	if not a_tokens or not b_tokens:
		return 0.0
	return len(a_tokens & b_tokens) / max(1, len(a_tokens))


def _max_context_overlap(text: str, contexts: List[str]) -> float:
	if not contexts:
		return 0.0
	return max(_overlap_ratio(text, context) for context in contexts)


def _score_case(item: Dict[str, str], result: Dict[str, Any]) -> Dict[str, float]:
	answer = result["answer"]
	question = item["question"]
	expected = item["expected_answer"]
	contexts = result["contexts"]

	faithfulness = _max_context_overlap(answer, contexts)
	answer_relevancy = (_overlap_ratio(answer, expected) + _overlap_ratio(answer, question)) / 2
	contextual_precision = _max_context_overlap(expected, contexts)
	contextual_recall = _overlap_ratio(expected, " ".join(contexts))
	contextual_relevancy = _max_context_overlap(question, contexts)

	return {
		"faithfulness": round(min(1.0, faithfulness), 4),
		"answer_relevancy": round(min(1.0, answer_relevancy), 4),
		"contextual_precision": round(min(1.0, contextual_precision), 4),
		"contextual_recall": round(min(1.0, contextual_recall), 4),
		"contextual_relevancy": round(min(1.0, contextual_relevancy), 4),
	}


def run_dataset_eval(dataset_path: str = "./golden_dataset.json", threshold: float = 0.75) -> Dict[str, float]:
	dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))

	faithfulness_scores: List[float] = []
	relevancy_scores: List[float] = []
	precision_scores: List[float] = []
	recall_scores: List[float] = []
	contextual_rel_scores: List[float] = []

	for item in dataset:
		result = query_rag(item["question"], top_k=4, use_llm=False)
		scores = _score_case(item, result)

		faithfulness_scores.append(scores["faithfulness"])
		relevancy_scores.append(scores["answer_relevancy"])
		precision_scores.append(scores["contextual_precision"])
		recall_scores.append(scores["contextual_recall"])
		contextual_rel_scores.append(scores["contextual_relevancy"])

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

