from core.world_model import Belief, Goal, Fact, Context, ConfidenceLevel, WorldModel


def test_world_model_beliefs():
    wm = WorldModel()
    belief = Belief(fact="screen shows youtube", confidence=0.9, source="perception")
    wm.add_belief("youtube_visible", belief)

    retrieved = wm.get_belief("youtube_visible")
    assert retrieved is not None
    assert retrieved.fact == "screen shows youtube"
    assert retrieved.confidence == 0.9


def test_world_model_goals():
    wm = WorldModel()
    goal = Goal(description="Open YouTube", priority=1)
    wm.add_goal("goal_open_yt", goal)

    retrieved = wm.get_goal("goal_open_yt")
    assert retrieved is not None
    assert retrieved.status == "pending"

    wm.mark_goal_complete("goal_open_yt")
    assert wm.get_goal("goal_open_yt").status == "completed"


def test_world_model_facts():
    wm = WorldModel()
    fact = Fact(subject="user", predicate="wants", obj="open_youtube")
    wm.add_fact(fact)

    facts = wm.query_facts(subject="user")
    assert len(facts) == 1
    assert facts[0].obj == "open_youtube"
