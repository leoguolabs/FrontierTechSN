"""Release-clock regressions use an isolated database and mocked publishers."""

import asyncio
import sqlite3
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend import config, database, publishing, worker
from backend.daily_news import scheduler
from backend.daily_news.publication_schedule import daily_release_at
from backend.models import DailyAutomationSettings, TaskConfig, TaskStatus


BEFORE = datetime(2026, 10, 19, 11, 0, tzinfo=timezone.utc)
DUE = datetime(2026, 10, 19, 12, 0, 20, tzinfo=timezone.utc)
LATE = datetime(2026, 10, 19, 12, 1, tzinfo=timezone.utc)


@pytest.fixture
def release_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "release.db")
    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(scheduler, "_state_path", lambda: tmp_path / "state.json")
    monkeypatch.setattr(config, "AI_ENDPOINT", "")
    monkeypatch.setattr(config, "VIDEO_AUTO_PUBLISH_ENABLED", True)
    monkeypatch.setattr(publishing, "automatic_publication_configuration_errors", lambda targets: [])
    publisher = AsyncMock(return_value={"platforms": {"youtube": {"url": "https://example.com/video"}}})
    monkeypatch.setattr(publishing, "publish_task", publisher)
    asyncio.run(database.init_db())
    return publisher


async def ready_task(*, publish_time="20:00", planned="2026-10-19T12:00:00+00:00", **settings):
    task = await database.create_task(
        "news_daily", "{}",
        TaskConfig(auto_publish=True, publish_time=publish_time, **settings),
        origin_type="daily_news", origin_id="2026-10-19", planned_publish_at=planned,
    )
    await database.update_task(task.id, status=TaskStatus.COMPLETE.value, auto_publish_pending=True)
    return await database.get_task(task.id)


@pytest.mark.parametrize("value", ["", "24:00", "20:60", "8:30", "20:00:00"])
def test_publish_time_requires_24_hour_hours_and_minutes(value):
    with pytest.raises(ValueError, match="HH:MM"):
        DailyAutomationSettings(publish_time=value)
    with pytest.raises(ValueError, match="HH:MM"):
        TaskConfig(publish_time=value)


def test_release_time_uses_recipe_timezone_and_dst():
    assert daily_release_at(date(2026, 10, 19), "20:00", "Asia/Singapore").isoformat() == "2026-10-19T12:00:00+00:00"
    assert daily_release_at(date(2026, 7, 1), "20:00", "America/New_York").isoformat() == "2026-07-02T00:00:00+00:00"
    assert daily_release_at(date(2026, 12, 1), "20:00", "America/New_York").isoformat() == "2026-12-02T01:00:00+00:00"
    assert TaskConfig().publish_time is None
    assert DailyAutomationSettings().publish_time == "20:00"


@pytest.mark.parametrize("auto_publish,test_mode", [(True, False), (False, False), (True, True)])
def test_new_editions_snapshot_release_time_without_affecting_test_runs(release_runtime, auto_publish, test_mode):
    async def scenario():
        task = await scheduler.create_daily_task(
            DailyAutomationSettings(
                auto_publish=auto_publish, publish_time="19:45", timezone="Asia/Tokyo",
            ),
            edition_date=date(2026, 10, 19), trigger="manual", test_mode=test_mode,
        )
        assert task.config.publish_time == "19:45"
        assert task.config.news_timezone == "Asia/Tokyo"
        assert task.config.auto_publish is (auto_publish and not test_mode)
        assert task.planned_publish_at == (
            "2026-10-19T10:45:00+00:00" if auto_publish and not test_mode else None
        )
        assert task.auto_publish_pending is False
    asyncio.run(scenario())


@pytest.mark.parametrize("action,reason,pending", [
    ("scheduled", "Waiting for release", True),
    ("awaiting_review", "Publication time was missed; manual publication required", False),
])
def test_worker_finalizes_cut_and_persists_release_intent(release_runtime, monkeypatch, action, reason, pending):
    async def scenario():
        task = await ready_task()
        await database.update_task(task.id, status=TaskStatus.QUEUED.value, auto_publish_pending=False)
        task = await database.get_task(task.id)

        async def produce(*args, **kwargs):
            await database.update_task(task.id, status=TaskStatus.PUBLISHING.value)

        monkeypatch.setattr(worker, "get_next_priority_morning_task", AsyncMock(return_value=None))
        monkeypatch.setattr(worker, "get_next_queued_task", AsyncMock(side_effect=[task, asyncio.CancelledError()]))
        monkeypatch.setattr(worker, "run_pipeline", produce)
        monkeypatch.setattr(worker, "run_auto_publish_pipeline", AsyncMock(
            return_value=publishing.PublicationResult(action, reason),
        ))
        with patch("backend.social_copy.start_generation"):
            with pytest.raises(asyncio.CancelledError):
                await worker._worker_loop()
        current = await database.get_task(task.id)
        assert current.status == TaskStatus.COMPLETE
        assert current.auto_publish_pending is pending
        assert current.error_message == (reason if not pending else None)
        assert current.publication_safety_hold is False
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_early_completion_only_queues_a_release(release_runtime):
    async def scenario():
        task = await ready_task()
        result = await publishing.run_auto_publish_pipeline(task, now=BEFORE)
        assert result.action == "scheduled"
        assert task.planned_publish_at in result.reason
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_completion_after_release_time_requires_manual_publication(release_runtime):
    async def scenario():
        task = await ready_task()
        result = await publishing.run_auto_publish_pipeline(task, now=DUE)
        assert result.action == "awaiting_review"
        assert "manual publication required" in result.reason
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


@pytest.mark.parametrize("planned,publish_time", [(None, None), (None, "20:00"), ("2026-10-19T20:00:00", "20:00")])
def test_legacy_or_unzoned_release_never_publishes(release_runtime, planned, publish_time):
    async def scenario():
        task = await ready_task(planned=planned, publish_time=publish_time)
        result = await publishing.run_auto_publish_pipeline(task, now=BEFORE)
        assert result.action == "awaiting_review"
        await publishing.dispatch_due_daily_publications(now=DUE)
        assert (await database.get_task(task.id)).auto_publish_pending is False
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_release_survives_database_reopen_and_dispatches_once(release_runtime):
    async def scenario():
        task = await ready_task()
        await database.init_db()
        await publishing.dispatch_due_daily_publications(now=BEFORE)
        release_runtime.assert_not_awaited()
        await asyncio.gather(
            publishing.dispatch_due_daily_publications(now=DUE),
            publishing.dispatch_due_daily_publications(now=DUE),
        )
        await publishing.dispatch_due_daily_publications(now=DUE)
        release_runtime.assert_awaited_once()
        current = await database.get_task(task.id)
        assert current.status == TaskStatus.COMPLETE
        assert current.auto_publish_pending is False
        assert current.publication_safety_hold is False
        assert current.error_message is None
    asyncio.run(scenario())


def test_restart_after_missed_slot_keeps_cut_for_manual_publication(release_runtime):
    async def scenario():
        task = await ready_task()
        await publishing.dispatch_due_daily_publications(now=LATE)
        await publishing.dispatch_due_daily_publications(now=DUE.replace(day=20))
        current = await database.get_task(task.id)
        assert current.status == TaskStatus.COMPLETE
        assert current.auto_publish_pending is False
        assert "manual publication required" in current.error_message
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_global_switch_does_not_trigger_late_catch_up(release_runtime, monkeypatch):
    async def scenario():
        task = await ready_task()
        monkeypatch.setattr(config, "VIDEO_AUTO_PUBLISH_ENABLED", False)
        await publishing.dispatch_due_daily_publications(now=DUE)
        assert (await database.get_task(task.id)).auto_publish_pending is True
        monkeypatch.setattr(config, "VIDEO_AUTO_PUBLISH_ENABLED", True)
        await publishing.dispatch_due_daily_publications(now=LATE)
        assert (await database.get_task(task.id)).auto_publish_pending is False
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


@pytest.mark.parametrize("guard", ["suppress_next_auto_publish", "publication_safety_hold"])
def test_rework_and_publication_holds_prevent_release(release_runtime, guard):
    async def scenario():
        task = await ready_task()
        await database.update_task(task.id, **{guard: True})
        await publishing.dispatch_due_daily_publications(now=DUE)
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_test_editions_never_dispatch_even_if_pending(release_runtime):
    async def scenario():
        task = await ready_task(publish_test_mode=True)
        await publishing.dispatch_due_daily_publications(now=DUE)
        assert (await database.get_task(task.id)).auto_publish_pending is False
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_automatic_failure_retains_safety_hold_without_retry(release_runtime):
    release_runtime.side_effect = RuntimeError("Receipt missing after upload")

    async def scenario():
        task = await ready_task()
        await publishing.dispatch_due_daily_publications(now=DUE)
        await publishing.dispatch_due_daily_publications(now=DUE)
        current = await database.get_task(task.id)
        assert current.status == TaskStatus.FAILED
        assert current.publication_safety_hold is True
        assert current.auto_publish_pending is False
        release_runtime.assert_awaited_once()
    asyncio.run(scenario())


def test_manual_publication_consumes_pending_release(release_runtime):
    from backend.models import TaskPublicationRequest
    from backend.routers import tasks

    async def scenario():
        task = await ready_task()
        plan = publishing.PublicationPlan(("youtube",), ("youtube",), "public", {})
        with (
            patch.object(tasks, "plan_publication", return_value=plan),
            patch.object(tasks, "execute_publication_plan", AsyncMock(return_value={})),
            patch.object(tasks, "publication_manifest_view", return_value={}),
        ):
            await tasks.publish_task_now(task.id, TaskPublicationRequest(targets=["youtube"]))
        await publishing.dispatch_due_daily_publications(now=DUE)
        assert (await database.get_task(task.id)).auto_publish_pending is False
        release_runtime.assert_not_awaited()
    asyncio.run(scenario())


def test_existing_task_migration_does_not_enroll_completed_editions(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(config, "AI_ENDPOINT", "")
    old_schema = database.SCHEMA.replace(
        "planned_publish_at TEXT,\n    auto_publish_pending INTEGER NOT NULL DEFAULT 0", "planned_publish_at TEXT"
    )
    with sqlite3.connect(db_path) as connection:
        connection.executescript(old_schema)
        connection.execute(
            """INSERT INTO tasks (id, created_at, updated_at, source_type, status, config_json, origin_type)
               VALUES ('legacy', ?, ?, 'news_daily', 'complete', ?, 'daily_news')""",
            (BEFORE.isoformat(), BEFORE.isoformat(), TaskConfig(auto_publish=True).model_dump_json()),
        )

    async def scenario():
        await database.init_db()
        task = await database.get_task("legacy")
        assert task.status == TaskStatus.COMPLETE
        assert task.config.auto_publish is True
        assert task.auto_publish_pending is False
        assert await database.list_pending_daily_publications() == []
    asyncio.run(scenario())
