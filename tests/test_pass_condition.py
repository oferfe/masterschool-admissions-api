"""Tests for src/evaluators/pass_condition.py — all branches of evaluate()."""

import pytest

from src.evaluators.pass_condition import evaluate


class TestAlways:
    def test_always_passes(self):
        """'always' condition returns 'passed' with an empty payload."""
        assert evaluate("always", {}) == "passed"

    def test_always_passes_with_any_payload(self):
        """'always' condition returns 'passed' regardless of payload content."""
        assert evaluate("always", {"foo": "bar"}) == "passed"


class TestScoreGt75:
    def test_score_above_75_passes(self):
        """Score of 80 (> 75) returns 'passed'."""
        assert evaluate("score_gt_75", {"score": 80}) == "passed"

    def test_score_exactly_75_fails(self):
        """Score of exactly 75 (not > 75) returns 'failed'."""
        assert evaluate("score_gt_75", {"score": 75}) == "failed"

    def test_score_below_75_fails(self):
        """Score of 50 (< 75) returns 'failed'."""
        assert evaluate("score_gt_75", {"score": 50}) == "failed"

    def test_score_missing_fails(self):
        """Missing score defaults to 0, which returns 'failed'."""
        assert evaluate("score_gt_75", {}) == "failed"


class TestDecisionPassed:
    def test_decision_passed_interview(self):
        """Decision of 'passed_interview' returns 'passed'."""
        assert evaluate("decision_passed", {"decision": "passed_interview"}) == "passed"

    def test_decision_other_value_fails(self):
        """Any decision other than 'passed_interview' returns 'failed'."""
        assert evaluate("decision_passed", {"decision": "rejected"}) == "failed"

    def test_decision_missing_fails(self):
        """Missing decision field returns 'failed'."""
        assert evaluate("decision_passed", {}) == "failed"


class TestUnknownCondition:
    def test_unknown_raises_value_error(self):
        """An unrecognised pass condition raises ValueError."""
        with pytest.raises(ValueError, match="Unknown condition"):
            evaluate("unknown", {})
