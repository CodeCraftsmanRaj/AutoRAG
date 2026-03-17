import json
import os
from importlib import import_module
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from app.rag import query_rag


DEFAULT_JUDGE_MODEL = os.getenv("EVAL_MODEL", os.getenv("LLM_MODEL", "gemini-2.0-flash"))


def _load_symbol(module_name: str, symbol_name: str):
	module = import_module(module_name)
	return getattr(module, symbol_name)


def _judge_client() -> Any:
	if os.getenv("GEMINI_API_KEY"):
		ChatGoogleGenerativeAI = _load_symbol("langchain_google_genai", "ChatGoogleGenerativeAI")
		return ChatGoogleGenerativeAI(
			model=DEFAULT_JUDGE_MODEL,
			temperature=0,
			google_api_key=os.getenv("GEMINI_API_KEY"),
		)
	if os.getenv("OPENAI_API_KEY"):
		ChatOpenAI = _load_symbol("langchain_openai", "ChatOpenAI")
		return ChatOpenAI(model=DEFAULT_JUDGE_MODEL, temperature=0)
	raise SystemExit("Set GEMINI_API_KEY in .env and recreate the container before running evaluation.")


def _extract_json(payload: str) -> Dict[str, Any]:
	text = payload.strip()
	if text.startswith("```"):
		parts = text.split("```")
		for part in parts:
			part = part.strip()
			if part.startswith("json"):
				part = part[4:].strip()
			if part.startswith("{"):
				text = part
				break
	return json.loads(text)


def _score_case(judge: Any, item: Dict[str, str], result: Dict[str, Any]) -> Dict[str, float]:
	prompt = f"""
You are grading a RAG system. Return only valid JSON.

Question: {item['question']}
Expected answer: {item['expected_answer']}
Actual answer: {result['answer']}
Retrieved contexts: {json.dumps(result['contexts'], ensure_ascii=False)}

Score each metric from 0.0 to 1.0:
- faithfulness: answer supported by retrieved context
- answer_relevancy: answer addresses the question
- contextual_precision: retrieved context is focused and useful
- contextual_recall: retrieved context covers needed facts
- contextual_relevancy: retrieved context is relevant overall

Return JSON exactly in this shape:
{{
  "faithfulness": 0.0,
  "answer_relevancy": 0.0,
  "contextual_precision": 0.0,
  "contextual_recall": 0.0,
  "contextual_relevancy": 0.0
}}
"""
	response = judge.invoke(prompt)
	content = response.content if hasattr(response, "content") else str(response)
	scores = _extract_json(content)
	return {
		"faithfulness": float(scores["faithfulness"]),
		"answer_relevancy": float(scores["answer_relevancy"]),
		"contextual_precision": float(scores["contextual_precision"]),
		"contextual_recall": float(scores["contextual_recall"]),
		"contextual_relevancy": float(scores["contextual_relevancy"]),
	}


def run_dataset_eval(dataset_path: str = "./golden_dataset.json", threshold: float = 0.75) -> Dict[str, float]:
	judge = _judge_client()
	dataset = json.loads(Path(dataset_path).read_text(encoding="utf-8"))

	faithfulness_scores: List[float] = []
	relevancy_scores: List[float] = []
	precision_scores: List[float] = []
	recall_scores: List[float] = []
	contextual_rel_scores: List[float] = []

	for item in dataset:
		result = query_rag(item["question"], top_k=4)
		scores = _score_case(judge, item, result)

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
	try:
		summary = run_dataset_eval(path, threshold)
	except Exception as exc:
		msg = str(exc)
		if "insufficient_quota" in msg or "RateLimitError" in msg or "429" in msg:
			raise SystemExit(
				"Evaluation failed due to provider quota/rate-limit (429). Check Gemini/OpenAI quota and recreate the container."
			)
		if "AuthenticationError" in msg or "401" in msg or "API key not valid" in msg:
			raise SystemExit(
				"Evaluation failed due to invalid/missing key in container. Check GEMINI_API_KEY in .env and recreate container."
			)
		raise
	print(json.dumps(summary, indent=2))
	if not summary["passed"]:
		raise SystemExit(1)

