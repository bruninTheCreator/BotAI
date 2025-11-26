import pytest
from core.executor_v2 import ExecutorV2, ExecutionStatus


@pytest.mark.asyncio
async def test_executor_dry_run():
    exe = ExecutorV2()
    record = await exe.execute("click", {"x": 100, "y": 200}, dry_run=True)
    assert record.status == ExecutionStatus.SIMULATED
    assert record.dry_run is True
    assert record.result["simulated"] is True


@pytest.mark.asyncio
async def test_executor_execution_record():
    exe = ExecutorV2()
    record = await exe.execute("type", {"text": "hello"})
    assert record.action == "type"
    assert record.args["text"] == "hello"
    assert record in exe.get_history()


@pytest.mark.asyncio
async def test_executor_history():
    exe = ExecutorV2()
    await exe.execute("open_app", {"app": "chrome"})
    await exe.execute("click", {"x": 10, "y": 20})
    history = exe.get_history()
    assert len(history) == 2
    assert history[0].action == "open_app"
    assert history[1].action == "click"


@pytest.mark.asyncio
async def test_executor_history_limit():
    exe = ExecutorV2()
    for i in range(5):
        await exe.execute("type", {"text": f"text_{i}"})
    history_limited = exe.get_history(limit=2)
    assert len(history_limited) == 2
    assert history_limited[-1].args["text"] == "text_4"
