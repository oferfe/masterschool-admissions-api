"""Tests for src/evaluators/unlock_condition.py — generic unlock evaluator."""

import pytest

from src.evaluators.unlock_condition import should_unlock


class TestShouldUnlock:
    def test_unknown_condition_raises_value_error(self):
        """An arbitrary condition string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown unlock condition"):
            should_unlock("some_condition", {})

    def test_score_between_60_75_true(self):
        """score_between_60_75 returns True for score in range."""
        assert should_unlock("score_between_60_75", {"score": 70}) is True

    def test_score_between_60_75_false_below(self):
        """score_between_60_75 returns False for score below 60."""
        assert should_unlock("score_between_60_75", {"score": 50}) is False

    def test_score_between_60_75_false_above(self):
        """score_between_60_75 returns False for score above 75."""
        assert should_unlock("score_between_60_75", {"score": 80}) is False

    def test_score_between_60_75_boundary_low(self):
        """score_between_60_75 returns True at exactly 60."""
        assert should_unlock("score_between_60_75", {"score": 60}) is True

    def test_score_between_60_75_boundary_high(self):
        """score_between_60_75 returns True at exactly 75."""
        assert should_unlock("score_between_60_75", {"score": 75}) is True

    def test_empty_string_raises(self):
        """An empty string condition raises ValueError."""
        with pytest.raises(ValueError, match="Unknown unlock condition"):
            should_unlock("", {})
