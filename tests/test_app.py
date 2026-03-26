"""Tests for src/app.py — FastAPI app configuration and lifespan."""

import pytest

from src.app import app, lifespan
from src.db.store import store


class TestAppConfig:
    """Verify the FastAPI application is wired correctly."""

    def test_app_title(self):
        """The FastAPI app has the correct title."""
        assert app.title == "Admissions System API"

    def test_app_has_routes(self):
        """The app has registered routes for all expected paths."""
        paths = [route.path for route in app.routes]
        assert "/users" in paths
        assert "/flow" in paths
        assert "/users/{user_id}/progress" in paths
        assert "/users/{user_id}/outcome" in paths
        assert "/users/{user_id}/tasks/{task_id}" in paths

    def test_root_route_exists(self):
        """The root '/' endpoint is registered."""
        paths = [route.path for route in app.routes]
        assert "/" in paths


class TestLifespan:
    """Verify the lifespan hook loads flow config into the store."""

    @pytest.mark.anyio
    async def test_lifespan_loads_flow_config(self):
        """Running the lifespan context manager populates the store."""
        assert len(store.flow_steps) == 0
        assert len(store.tasks) == 0

        async with lifespan(app):
            assert len(store.flow_steps) == 6
            assert len(store.tasks) == 8

    @pytest.mark.anyio
    async def test_lifespan_populates_steps_sorted(self):
        """Steps loaded by lifespan are sorted by order."""
        async with lifespan(app):
            orders = [step.order for step in store.flow_steps]
            assert orders == sorted(orders)
