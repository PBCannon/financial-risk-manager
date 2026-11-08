"""Load config.yaml and optional environment overrides. No secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(ValueError):
    """config.yaml or an environment override cannot be read."""


@dataclass(frozen=True)
class Settings:
    risk_free_rate: float
    trading_days: int
    var_confidence: float


def load_settings(path: Path | None = None, *, env_file: Path | None = None) -> Settings:
    """Read settings. Existing environment variables win over the env file."""
    _load_env_file(env_file or Path(".env"))
    if path is not None:
        config_path = path
    else:
        config_path = Path(os.environ.get("FRM_CONFIG") or "config.yaml")
    if not config_path.is_file():
        raise ConfigError(f"Missing config file: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path} must be a mapping.")
    risk_free = _as_float(raw.get("risk_free_rate", 0.0), "risk_free_rate")
    trading_days = _as_int(raw.get("trading_days", 252), "trading_days")
    confidence = _as_float(raw.get("var_confidence", 0.95), "var_confidence")
    override = os.environ.get("FRM_RISK_FREE_RATE", "").strip()
    if override:
        risk_free = _as_float(override, "FRM_RISK_FREE_RATE")
    if trading_days <= 0:
        raise ConfigError("trading_days must be positive.")
    if not 0.0 < confidence < 1.0:
        raise ConfigError("var_confidence must be between 0 and 1.")
    return Settings(risk_free, trading_days, confidence)


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _as_float(value: object, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be a number.") from exc


def _as_int(value: object, name: str) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be an integer.") from exc
    if not number.is_integer():
        raise ConfigError(f"{name} must be an integer.")
    return int(number)
