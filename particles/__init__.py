"""Пакет particles — расчёт удельного заряда и комптоновской длины волны
элементарных частиц (электрон, протон, нейтрон).

Модули пакета:
    models   — классы частиц (ABC + наследование) и расчёты;
    database — сохранение результатов в SQLite;
    reports  — выгрузка отчётов в .docx и .xlsx.
"""

from .database import ResultRepository
from .models import (
    CalculationResult,
    Electron,
    Hadron,
    Lepton,
    Neutron,
    Particle,
    Proton,
)
from .reports import DocxReportWriter, ReportWriter, XlsxReportWriter

__all__ = [
    "Particle", "Lepton", "Hadron", "Electron", "Proton", "Neutron",
    "CalculationResult", "ResultRepository",
    "ReportWriter", "DocxReportWriter", "XlsxReportWriter",
]
