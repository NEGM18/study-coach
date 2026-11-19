"""Picks which version of each model's predict() the worker calls (issue #38, W2-04).

The version comes from an env var (`KNOWLEDGE_MODEL_VERSION`, `SPEECH_MODEL_VERSION`,
`TOPICS_MODEL_VERSION`), never from code. Values are `stub`, `v1`, `v2`, ...; unset means `stub`.
An unknown version, or one whose code fails to import, logs an error and falls back to the stub,
so a bad env var or a broken model never stops the worker.

A trained model adds itself with `register()`: its version maps to an import target
("package.module:function") that keeps the same signature as the stub. Its weights path is read
from that model's YAML config, not from here. Targets are imported only when first requested,
so the worker does not load speech libraries just to compute mastery.
"""

import importlib
import logging
import os
from collections.abc import Callable, Mapping
from functools import cache
from typing import Any

LOGGER = logging.getLogger(__name__)

STUB_VERSION = "stub"

MODEL_ENV_VARS: dict[str, str] = {
    "knowledge": "KNOWLEDGE_MODEL_VERSION",
    "speech": "SPEECH_MODEL_VERSION",
    "topics": "TOPICS_MODEL_VERSION",
}

_TARGETS: dict[str, dict[str, str]] = {
    "knowledge": {STUB_VERSION: "ml_core.knowledge.predict:predict_mastery"},
    "speech": {STUB_VERSION: "ml_core.speech.predict:transcribe"},
    "topics": {STUB_VERSION: "ml_core.topics.predict:classify_chunks"},
}


def _check_model(model: str) -> None:
    if model not in MODEL_ENV_VARS:
        raise ValueError(f"Unknown model {model!r}; expected one of {sorted(MODEL_ENV_VARS)}")


def register(model: str, version: str, target: str) -> None:
    """Make `version` of `model` available, e.g. register("knowledge", "v1", "pkg.mod:fn")."""
    _check_model(model)
    if version == STUB_VERSION:
        raise ValueError("The stub version cannot be replaced")
    if ":" not in target:
        raise ValueError(f"Target {target!r} must look like 'package.module:function'")
    _TARGETS[model][version] = target


def available_versions(model: str) -> list[str]:
    """Versions that can be selected for `model`, stub first."""
    _check_model(model)
    return sorted(_TARGETS[model], key=lambda v: (v != STUB_VERSION, v))


def resolve_version(model: str, env: Mapping[str, str] | None = None) -> str:
    """The version named by the model's env var, or `stub` when it is unset or empty."""
    _check_model(model)
    source = os.environ if env is None else env
    value = source.get(MODEL_ENV_VARS[model], "").strip().lower()
    return value or STUB_VERSION


@cache
def _load(target: str) -> Callable[..., Any]:
    module_name, function_name = target.split(":", 1)
    function = getattr(importlib.import_module(module_name), function_name)
    if not callable(function):
        raise TypeError(f"{target} is not callable")
    return function


def get_predictor(
    model: str, version: str | None = None, env: Mapping[str, str] | None = None
) -> Callable[..., Any]:
    """The predict() function for `model` at `version` (default: from the env var)."""
    _check_model(model)
    wanted = version or resolve_version(model, env)
    target = _TARGETS[model].get(wanted)
    if target is None:
        LOGGER.error(
            "%s: unknown version %r (available: %s); using %s",
            model,
            wanted,
            available_versions(model),
            STUB_VERSION,
        )
        return _load(_TARGETS[model][STUB_VERSION])
    try:
        predictor = _load(target)
    except (ImportError, AttributeError, TypeError):
        if wanted == STUB_VERSION:
            raise
        LOGGER.exception("%s: version %r failed to load; using %s", model, wanted, STUB_VERSION)
        return _load(_TARGETS[model][STUB_VERSION])
    LOGGER.info("%s: using version %r", model, wanted)
    return predictor
