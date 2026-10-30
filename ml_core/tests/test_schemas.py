from ml_core.schemas import Attempt


def test_attempt_defaults():
    a = Attempt(user_id="h1", topic_id=1, question_id=2, attempt_order=1, is_correct=True)
    assert a.attempt_count == 1 and a.hint_count == 0
