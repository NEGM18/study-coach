import logging

import pytest

from ml_core import registry
from ml_core.knowledge.predict import predict_mastery
from ml_core.topics.predict import classify_chunks


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test gets its own copy of the version table and empty env vars."""
    targets = {model: dict(versions) for model, versions in registry._TARGETS.items()}
    monkeypatch.setattr(registry, "_TARGETS", targets)
    for env_var in registry.MODEL_ENV_VARS.values():
        monkeypatch.delenv(env_var, raising=False)


def test_unset_env_var_means_stub() -> None:
    assert registry.resolve_version("knowledge") == "stub"
    assert registry.get_predictor("knowledge") is predict_mastery


def test_empty_env_var_means_stub() -> None:
    assert registry.resolve_version("topics", env={"TOPICS_MODEL_VERSION": "  "}) == "stub"


def test_env_var_is_read_and_normalized() -> None:
    assert registry.resolve_version("topics", env={"TOPICS_MODEL_VERSION": " V1 "}) == "v1"


def test_explicit_stub_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOPICS_MODEL_VERSION", "stub")
    assert registry.get_predictor("topics") is classify_chunks


def test_unknown_version_falls_back_to_stub(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR, logger="ml_core.registry"):
        predictor = registry.get_predictor("knowledge", env={"KNOWLEDGE_MODEL_VERSION": "v9"})
    assert predictor is predict_mastery
    assert "unknown version 'v9'" in caplog.text


def test_registered_version_is_used() -> None:
    registry.register("knowledge", "v1", "ml_core.knowledge.features:build_features")
    predictor = registry.get_predictor("knowledge", env={"KNOWLEDGE_MODEL_VERSION": "v1"})
    assert predictor.__name__ == "build_features"
    assert registry.available_versions("knowledge") == ["stub", "v1"]


def test_explicit_version_argument_beats_env() -> None:
    registry.register("knowledge", "v1", "ml_core.knowledge.features:build_features")
    predictor = registry.get_predictor("knowledge", version="stub", env={"KNOWLEDGE_MODEL_VERSION": "v1"})
    assert predictor is predict_mastery


def test_broken_version_falls_back_to_stub(caplog: pytest.LogCaptureFixture) -> None:
    registry.register("topics", "v1", "ml_core.topics.does_not_exist:classify_chunks")
    with caplog.at_level(logging.ERROR, logger="ml_core.registry"):
        predictor = registry.get_predictor("topics", version="v1")
    assert predictor is classify_chunks
    assert "failed to load" in caplog.text


def test_unknown_model_raises() -> None:
    with pytest.raises(ValueError, match="Unknown model"):
        registry.get_predictor("vision")


@pytest.mark.parametrize(
    ("version", "target"),
    [("stub", "ml_core.knowledge.predict:predict_mastery"), ("v1", "no_colon_here")],
)
def test_register_rejects_bad_input(version: str, target: str) -> None:
    with pytest.raises(ValueError):
        registry.register("knowledge", version, target)


def test_speech_stub_resolves() -> None:
    pytest.importorskip("soundfile")
    from ml_core.speech.predict import transcribe

    assert registry.get_predictor("speech") is transcribe


def test_every_model_has_an_env_var_and_a_stub() -> None:
    for model in registry.MODEL_ENV_VARS:
        assert registry.available_versions(model)[0] == "stub"
