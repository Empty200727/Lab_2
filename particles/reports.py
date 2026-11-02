"""Модуль reports — сохранение результатов в отчёты .docx (python-docx) и .xlsx (openpyxl)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from .models import CalculationResult

#: (поле CalculationResult, заголовок колонки, формат числа)
REPORT_COLUMNS: list[tuple[str, str, str]] = [
    ("particle", "Частица", "{}"),
    ("symbol", "Символ", "{}"),
    ("velocity", "v, м/с", "{:.4e}"),
    ("lorentz_factor", "γ", "{:.6f}"),
    ("rest_mass", "m₀, кг", "{:.6e}"),
    ("charge", "q, Кл", "{:.6e}"),
    ("specific_charge", "q/m₀, Кл/кг", "{:.6e}"),
    ("relativistic_specific_charge", "q/(γm₀), Кл/кг", "{:.6e}"),
    ("compton_wavelength", "λc, м", "{:.6e}"),
    ("reduced_compton_wavelength", "ƛc, м", "{:.6e}"),
    ("created_at", "Дата расчёта", "{}"),
]


class ReportWriter(ABC):
    """Абстрактный генератор отчёта (шаблонный метод save → _write)."""

    def __init__(self, title: str = "Расчёт характеристик элементарных частиц") -> None:
        self.title = title

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Managed-атрибут: заголовок не может быть пустым."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Заголовок отчёта не может быть пустым")
        self._title = value.strip()

    @property
    @abstractmethod
    def extension(self) -> str:
        """Расширение файла, например '.docx'."""

    @abstractmethod
    def _write(self, results: list[CalculationResult], path: Path) -> None:
        """Записать отчёт в файл (реализуется в наследниках)."""

    def default_filename(self) -> str:
        return f"report_{datetime.now():%Y%m%d_%H%M%S}{self.extension}"

    def save(self, results: Iterable[CalculationResult], path: str | Path) -> Path:
        """Сохранить отчёт. Если path — папка, имя файла генерируется автоматически."""
        results = list(results)
        if not results:
            raise ValueError("Нет результатов для отчёта")
        path = Path(path)
        if path.suffix.lower() != self.extension:
            path = path / self.default_filename()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(results, path)
        return path

    @staticmethod
    def cell_values(result: CalculationResult) -> list[str]:
        data = result.as_dict()
        return [fmt.format(data[name]) for name, _, fmt in REPORT_COLUMNS]

    # ---- dunder-методы ----
    def __call__(self, results: Iterable[CalculationResult], path: str | Path) -> Path:
        """writer(results, path) — то же, что writer.save(results, path)."""
        return self.save(results, path)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(title={self.title!r})"


class DocxReportWriter(ReportWriter):
    """Отчёт в формате Word (.docx)."""

    def __init__(self, title: str = "Расчёт характеристик элементарных частиц") -> None:
        super().__init__(title)

    @property
    def extension(self) -> str:
        return ".docx"

    def _write(self, results: list[CalculationResult], path: Path) -> None:
        doc = Document()
        doc.add_heading(self.title, level=1)
        doc.add_paragraph(f"Дата формирования: {datetime.now():%d.%m.%Y %H:%M}")
        doc.add_paragraph(
            "Формулы: удельный заряд q/m; комптоновская длина волны λc = h/(m·c); "
            "приведённая ƛc = ħ/(m·c); γ = 1/√(1 − v²/c²)."
        )

        table = doc.add_table(rows=1, cols=len(REPORT_COLUMNS))
        table.style = "Table Grid"
        for cell, (_, header, _) in zip(table.rows[0].cells, REPORT_COLUMNS):
            cell.text = header
            cell.paragraphs[0].runs[0].bold = True
        for result in results:
            row = table.add_row().cells
            for cell, value in zip(row, self.cell_values(result)):
                cell.text = value
        for row in table.rows:
            for cell in row.cells:
                for run in cell.paragraphs[0].runs:
                    run.font.size = Pt(7)

        doc.add_heading("Подробно", level=2)
        for i, result in enumerate(results, start=1):
            doc.add_paragraph(f"{i}. {result}")
        doc.save(path)

    def __str__(self) -> str:
        return f"Word-отчёт «{self.title}»"


class XlsxReportWriter(ReportWriter):
    """Отчёт в формате Excel (.xlsx)."""

    def __init__(self, title: str = "Расчёт характеристик элементарных частиц") -> None:
        super().__init__(title)

    @property
    def extension(self) -> str:
        return ".xlsx"

    def _write(self, results: list[CalculationResult], path: Path) -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = "Результаты"
        ws.append([self.title])
        ws["A1"].font = Font(bold=True, size=14)
        ws.append([])
        ws.append([header for _, header, _ in REPORT_COLUMNS])
        for cell in ws[3]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        for result in results:
            data = result.as_dict()
            # в Excel пишем «сырые» числа, чтобы с ними можно было считать
            ws.append([data[name] for name, _, _ in REPORT_COLUMNS])
            for cell, (_, _, fmt) in zip(ws[ws.max_row], REPORT_COLUMNS):
                if "e}" in fmt:
                    cell.number_format = "0.000000E+00"
        for i, _ in enumerate(REPORT_COLUMNS, start=1):
            ws.column_dimensions[ws.cell(row=3, column=i).column_letter].width = 20
        wb.save(path)

    def __str__(self) -> str:
        return f"Excel-отчёт «{self.title}»"
