"""Тесты консольного интерфейса (main.py)."""
import pytest

from main import ConsoleApp
from particles import ResultRepository
from particles.models import SPEED_OF_LIGHT


@pytest.mark.parametrize("text, expected", [
    ("", 0.0), ("1e6", 1e6), ("0,5c", 0.5 * SPEED_OF_LIGHT), ("c", SPEED_OF_LIGHT),
])
def test_parse_velocity(text, expected):
    assert ConsoleApp.parse_velocity(text) == pytest.approx(expected)


def test_full_session(monkeypatch, tmp_path, capsys):
    # 1 → протон → 0.1c; 2 → все частицы при v=0; 5 → xlsx; 0 → выход
    answers = iter(["1", "2", "0.1c", "2", "", "5", "0"])
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))
    with ResultRepository(":memory:") as repo:
        ConsoleApp(repo, str(tmp_path))()
        assert len(repo) == 4
    out = capsys.readouterr().out
    assert "Протон" in out and "сохранён" in out
    assert list(tmp_path.glob("*.xlsx"))
