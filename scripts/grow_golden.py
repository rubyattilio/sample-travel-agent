"""Add live production inputs that failed a live eval to data/golden_candidates.json, for labelling.

    ax spans export travel-agent --space $ARIZE_SPACE_ID --days 7 --stdout \
        --filter "name = 'travel_agent' AND <failed-eval filter>" > failing_spans.json
    uv run python scripts/grow_golden.py failing_spans.json

Only adds inputs. Expected answers are never written automatically: a candidate stays "needs_label"
until a person fills in expected_tools / expected_facts / expected_behavior. Labelled candidates become
the next dataset version (golden_v2); the gate keeps comparing on one version, and the headline
before/after numbers stay pinned to v1.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden_v1.json"
CANDIDATES = ROOT / "data" / "golden_candidates.json"


def candidates_from_spans(spans, known_inputs):
    out = {}
    for span in spans:
        text = (span["attributes"].get("input.value") or "").strip()
        if not text or text.lower() in known_inputs:
            continue
        digest = hashlib.sha256(text.lower().encode()).hexdigest()
        out.setdefault(text.lower(), {
            "example_key": f"live-{digest[:8]}",
            "category": "unlabeled",
            "input": text,
            "turns": [text],
            "expected_tools": [], "expected_facts": {}, "must_not": [], "expected_behavior": "",
            "split": "test" if int(digest, 16) % 3 == 0 else "train",  # stable random third held out
            "source": "live",
            "status": "needs_label",
            "trace_id": span["context"]["trace_id"],
        })
    return list(out.values())


def main():
    spans = json.loads(Path(sys.argv[1]).read_text())
    existing = json.loads(CANDIDATES.read_text()) if CANDIDATES.exists() else []
    known = {r["input"].strip().lower() for r in json.loads(GOLDEN.read_text()) + existing}
    new = candidates_from_spans(spans, known)
    CANDIDATES.write_text(json.dumps(existing + new, indent=2, ensure_ascii=False) + "\n")
    print(f"Added {len(new)} candidates ({len(existing) + len(new)} waiting for labels) to {CANDIDATES.name}")


if __name__ == "__main__":
    main()
