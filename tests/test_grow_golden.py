"""Golden-set growth from live spans. No API calls."""

from scripts.grow_golden import candidates_from_spans


def test_grow_golden_adds_new_inputs_only_and_never_labels():
    span = lambda text, tid: {"attributes": {"input.value": text}, "context": {"trace_id": tid}}  # noqa: E731
    spans = [span("Cheap hotel in Rome?", "t1"), span("cheap hotel in rome?", "t2"), span("known", "t3"), span("", "t4")]
    new = candidates_from_spans(spans, {"known"})
    assert len(new) == 1
    c = new[0]
    assert c["status"] == "needs_label" and c["expected_behavior"] == "" and c["trace_id"] == "t1" and c["split"] in ("train", "test")
