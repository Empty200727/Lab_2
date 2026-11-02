"""Основная программа — консольный интерфейс к пакету particles.

Запуск:  python main.py  [--db data/results.db] [--reports reports]
"""

from __future__ import annotations

import argparse

from particles import (
    DocxReportWriter,
    Particle,
    ResultRepository,
    XlsxReportWriter,
)
from particles.models import SPEED_OF_LIGHT

MENU = """
========== Элементарные частицы (вариант 13) ==========
 1. Рассчитать характеристики частицы
 2. Рассчитать для всех частиц (сравнение)
 3. Показать историю расчётов (БД)
 4. Сохранить отчёт в Word (.docx)
 5. Сохранить отчёт в Excel (.xlsx)
 6. Очистить историю
 0. Выход
========================================================"""

PARTICLE_MENU = {"1": "electron", "2": "proton", "3": "neutron"}


class ConsoleApp:
    """Консольное приложение: ввод параметров, вывод результатов, отчёты."""

    def __init__(self, repository: ResultRepository, reports_dir: str = "reports") -> None:
        self.repository = repository
        self.reports_dir = reports_dir
        self._actions = {
            "1": self.calculate_one,
            "2": self.calculate_all,
            "3": self.show_history,
            "4": lambda: self.save_report(DocxReportWriter()),
            "5": lambda: self.save_report(XlsxReportWriter()),
            "6": self.clear_history,
        }

    @staticmethod
    def parse_velocity(text: str) -> float:
        """Разобрать скорость: '1e6' (м/с), '0.5c' (доля скорости света), '' → 0."""
        text = text.strip().lower().replace(",", ".")
        if not text:
            return 0.0
        if text.endswith("c"):
            return float(text[:-1] or 1) * SPEED_OF_LIGHT
        return float(text)

    def ask_velocity(self) -> float:
        raw = input("Скорость частицы (м/с, или доля c, например 0.5c; Enter = 0): ")
        return self.parse_velocity(raw)

    def calculate_one(self) -> None:
        print("Выберите частицу: 1 — электрон, 2 — протон, 3 — нейтрон")
        key = PARTICLE_MENU.get(input("> ").strip())
        if key is None:
            print("Нет такой частицы.")
            return
        particle = Particle.create(key, self.ask_velocity())
        result = particle.calculate()
        self.repository.add(result)
        print("\n" + str(result))
        print("Результат сохранён в БД.")

    def calculate_all(self) -> None:
        velocity = self.ask_velocity()
        particles = sorted(Particle.create(key, velocity) for key in Particle.registry)
        print(f"\n{'Частица':<10}{'q/m₀, Кл/кг':>16}{'q/(γm₀), Кл/кг':>18}{'λc, м':>16}")
        for particle in particles:
            r = particle.calculate()
            self.repository.add(r)
            print(f"{r.particle:<10}{r.specific_charge:>16.6e}"
                  f"{r.relativistic_specific_charge:>18.6e}{r.compton_wavelength:>16.6e}")
        print("Результаты сохранены в БД.")

    def show_history(self) -> None:
        results = self.repository.all()
        if not results:
            print("История пуста.")
            return
        for i, r in enumerate(results, start=1):
            print(f"{i:>3}. [{r.created_at}] {r.particle:<9} v={r.velocity:.3e} м/с  "
                  f"q/m={r.specific_charge:.4e} Кл/кг  λc={r.compton_wavelength:.4e} м")

    def save_report(self, writer) -> None:
        path = writer.save(self.repository.all(), self.reports_dir)
        print(f"{writer} сохранён: {path}")

    def clear_history(self) -> None:
        self.repository.clear()
        print("История очищена.")

    def run(self) -> None:
        while True:
            print(MENU)
            choice = input("Пункт меню: ").strip()
            if choice == "0":
                print("До свидания!")
                return
            action = self._actions.get(choice)
            if action is None:
                print("Неизвестный пункт меню.")
                continue
            try:
                action()
            except (ValueError, TypeError) as error:
                print(f"Ошибка: {error}")

    def __repr__(self) -> str:
        return f"ConsoleApp(repository={self.repository!r}, reports_dir={self.reports_dir!r})"

    def __call__(self) -> None:
        self.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Расчёт удельного заряда и комптоновской длины волны")
    parser.add_argument("--db", default="data/results.db", help="путь к файлу SQLite")
    parser.add_argument("--reports", default="reports", help="папка для отчётов")
    args = parser.parse_args()
    with ResultRepository(args.db) as repository:
        try:
            ConsoleApp(repository, args.reports)()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")


if __name__ == "__main__":
    main()
