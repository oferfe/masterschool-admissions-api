"""Tests for src/evaluators/unlock_condition.py — generic unlock evaluator."""

import pytest

from src.evaluators.unlock_condition import should_unlock


class TestShouldUnlock:
    def test_unknown_condition_raises_value_error(self):
        """Any arbitrary condition string raises ValueError (no conditions implemented)."""
        with pytest.raises(ValueError, match="Unknown unlock condition"):
            should_unlock("some_condition", {})

    def test_another_unknown_condition_raises(self):
        """Even a known-sounding condition raises ValueError when not implemented."""
        with pytest.raises(ValueError, match="Unknown unlock condition"):
            should_unlock("score_between_60_75", {"score": 70})

    def test_empty_string_raises(self):
        """An empty string condition raises ValueError."""
        with pytest.raises(ValueError, match="Unknown unlock condition"):
            should_unlock("", {})
