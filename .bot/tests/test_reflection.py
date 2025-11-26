from core.reflection import Reflector, ReflectionType
from core.world_model import WorldModel
from core.memory_vector import MemoryVectorStore


def test_reflector_success():
    reflector = Reflector()
    record = reflector.reflect_on_execution(
        plan_name="open_youtube",
        execution_trace="Successfully navigated to YouTube",
        success=True,
    )
    assert record.reflection_type == ReflectionType.SUCCESS
    assert record.confidence_update == 0.1


def test_reflector_failure():
    reflector = Reflector()
    record = reflector.reflect_on_execution(
        plan_name="open_zoom",
        execution_trace="Application failed to launch",
        success=False,
    )
    assert record.reflection_type == ReflectionType.FAILURE
    assert record.confidence_update == -0.2


def test_reflector_lessons():
    reflector = Reflector()
    record = reflector.reflect_on_execution(
        plan_name="save_file",
        execution_trace="File saved successfully",
        success=True,
    )
    assert len(record.lessons_learned) > 0
    assert any("succeeded" in lesson for lesson in record.lessons_learned)


def test_reflector_history():
    reflector = Reflector()
    reflector.reflect_on_execution("task1", "trace1", success=True)
    reflector.reflect_on_execution("task2", "trace2", success=False)
    history = reflector.get_reflection_history()
    assert len(history) == 2
    assert history[0].plan_name == "task1"
    assert history[1].plan_name == "task2"
