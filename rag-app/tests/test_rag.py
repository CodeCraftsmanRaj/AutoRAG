import json
import os
from pathlib import Path

import pytest

from app.eval import run_dataset_eval

THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.75"))
DATASET_PATH = Path(__file__).resolve().parents[1] / "golden_dataset.json"


@pytest.mark.rag_eval
def test_rag_golden_dataset_quality_gate() -> None:
	if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
		pytest.skip("No evaluation key is configured.")

	assert DATASET_PATH.exists(), json.dumps({"missing_dataset": str(DATASET_PATH)})
	summary = run_dataset_eval(str(DATASET_PATH), THRESHOLD)
	assert summary["passed"], json.dumps(summary, ensure_ascii=False)

