from core.planner_htn import PlannerHTN, Task
from core.memory_vector import MemoryVectorStore
from core.world_model import WorldModel


def test_htn_basic_planning():
    planner = PlannerHTN()
    plan = planner.plan("abrir youtube")
    assert plan.name == "goal_abrir youtube"
    assert len(plan.children) > 0


def test_htn_task_hierarchy():
    root = Task(name="main", description="Main task")
    sub1 = Task(name="sub1", description="Subtask 1")
    sub2 = Task(name="sub2", description="Subtask 2")
    root.add_subtask(sub1)
    root.add_subtask(sub2)

    assert len(root.children) == 2
    assert root.children[0].parent == root


def test_htn_flatten_plan():
    planner = PlannerHTN()
    plan = planner.plan("salvar arquivo")
    actions = planner.flatten_plan(plan)
    assert isinstance(actions, list)
    assert len(actions) > 0


def test_htn_memory_integration():
    memory = MemoryVectorStore()
    planner = PlannerHTN(memory_store=memory)

    # Adiciona histórico
    memory.add_text("abrir youtube navegador")
    memory.add_text("salvar arquivo ctrl+s")

    # Planeja e recupera contexto via RAG
    plan = planner.plan("abrir youtube")
    assert plan.confidence >= 0.0  # confidence definida pelo RAG match
