import re
from pathlib import Path

from core.config import load_settings
from financial_risk_manager.cli import main

_SECRET = re.compile(
    r"sk-ant-[A-Za-z0-9_\-]{8,}|AIza[0-9A-Za-z_\-]{10,}|ghp_[A-Za-z0-9]{10,}|gho_[A-Za-z0-9]{10,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"
)


def test_env_override_replaces_the_yaml_rate(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "risk_free_rate: 0.01\ntrading_days: 252\nvar_confidence: 0.95\n",
        encoding="utf-8",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("FRM_RISK_FREE_RATE=0.08\n", encoding="utf-8")
    monkeypatch.delenv("FRM_RISK_FREE_RATE", raising=False)
    monkeypatch.delenv("FRM_CONFIG", raising=False)
    settings = load_settings(config, env_file=env_file)
    assert settings.risk_free_rate == 0.08
    assert settings.trading_days == 252


def test_cli_prints_a_summary_for_the_examples(capsys) -> None:
    code = main(
        [
            "--holdings",
            "examples/holdings.csv",
            "--prices",
            "examples/prices.csv",
            "--config",
            "config.yaml",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "Sharpe (mean excess)" in captured.out
    assert "AAPL" in captured.out


def test_cli_rejects_a_missing_file(capsys) -> None:
    code = main(
        [
            "--holdings",
            "examples/holdings.csv",
            "--prices",
            "examples/does-not-exist.csv",
            "--config",
            "config.yaml",
        ]
    )
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_repo_has_no_secret_material() -> None:
    root = Path(__file__).resolve().parents[1]
    banned_names = {
        ".env",
        "secrets.toml",
        "credentials.toml",
        "portfolios.json",
        "config_agents.json",
    }
    banned_snippets = _SECRET
    skip = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}

    def files(directory: Path):
        for path in directory.iterdir():
            if path.name in skip:
                continue
            if path.is_dir():
                yield from files(path)
            elif path.is_file():
                yield path

    for path in files(root):
        assert path.name not in banned_names
        if path.suffix.lower() in {".py", ".md", ".yml", ".yaml", ".csv", ".toml", ".txt", ".example"}:
            text = path.read_text(encoding="utf-8")
            assert banned_snippets.search(text) is None
