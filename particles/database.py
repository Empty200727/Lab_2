"""Модуль database — хранение результатов расчётов в SQLite (sqlite3)."""

from __future__ import annotations

import sqlite3
from dataclasses import fields
from pathlib import Path

from .models import CalculationResult

#: имена колонок таблицы совпадают с полями CalculationResult
_COLUMNS = [f.name for f in fields(CalculationResult)]


class ResultRepository:
    """Репозиторий результатов расчётов поверх sqlite3.

    Использование как контекстный менеджер:
        with ResultRepository("data/results.db") as repo:
            repo.add(result)
            print(len(repo))
    """

    TABLE = "results"

    def __init__(self, path: str | Path = "data/results.db") -> None:
        self._path = str(path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._path)
        self._create_table()

    @property
    def path(self) -> str:
        """Путь к файлу БД (только чтение)."""
        return self._path

    def _create_table(self) -> None:
        self._connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE} (
                id                           INTEGER PRIMARY KEY AUTOINCREMENT,
                particle                     TEXT NOT NULL,
                symbol                       TEXT NOT NULL,
                family                       TEXT NOT NULL,
                velocity                     REAL NOT NULL,
                beta                         REAL NOT NULL,
                lorentz_factor               REAL NOT NULL,
                rest_mass                    REAL NOT NULL,
                relativistic_mass            REAL NOT NULL,
                charge                       REAL NOT NULL,
                specific_charge              REAL NOT NULL,
                relativistic_specific_charge REAL NOT NULL,
                compton_wavelength           REAL NOT NULL,
                reduced_compton_wavelength   REAL NOT NULL,
                created_at                   TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def add(self, result: CalculationResult) -> int:
        """Сохранить результат, вернуть его id в БД."""
        placeholders = ", ".join("?" for _ in _COLUMNS)
        cursor = self._connection.execute(
            f"INSERT INTO {self.TABLE} ({', '.join(_COLUMNS)}) VALUES ({placeholders})",
            tuple(result),
        )
        self._connection.commit()
        return cursor.lastrowid

    def all(self) -> list[CalculationResult]:
        """Все сохранённые результаты в порядке добавления."""
        rows = self._connection.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM {self.TABLE} ORDER BY id"
        ).fetchall()
        return [CalculationResult(*row) for row in rows]

    def clear(self) -> None:
        """Удалить всю историю расчётов."""
        self._connection.execute(f"DELETE FROM {self.TABLE}")
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    # ---- dunder-методы ----
    def __len__(self) -> int:
        return self._connection.execute(f"SELECT COUNT(*) FROM {self.TABLE}").fetchone()[0]

    def __iter__(self):
        return iter(self.all())

    def __enter__(self) -> "ResultRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"ResultRepository(path={self._path!r})"
