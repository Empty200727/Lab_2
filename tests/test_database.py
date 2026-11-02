"""Тесты хранения результатов в SQLite (модуль particles.database)."""
from particles import Electron, Neutron, ResultRepository


def test_add_and_read(tmp_path):
    db = tmp_path / "test.db"
    with ResultRepository(db) as repo:
        assert len(repo) == 0
        first = Electron(1e6).calculate()
        repo.add(first)
        repo.add(Neutron().calculate())
        assert len(repo) == 2
        assert repo.all()[0] == first
    # данные сохраняются между подключениями
    with ResultRepository(db) as repo:
        assert [r.particle for r in repo] == ["Электрон", "Нейтрон"]


def test_clear():
    with ResultRepository(":memory:") as repo:
        repo.add(Electron().calculate())
        repo.clear()
        assert len(repo) == 0 and repo.all() == []


def test_repr():
    with ResultRepository(":memory:") as repo:
        assert repr(repo) == "ResultRepository(path=':memory:')"
