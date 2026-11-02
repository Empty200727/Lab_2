"""Тесты генерации отчётов (модуль particles.reports)."""
import pytest
from docx import Document
from openpyxl import load_workbook

from particles import DocxReportWriter, Electron, Proton, ReportWriter, XlsxReportWriter


@pytest.fixture
def results():
    return [Electron().calculate(), Proton(1e7).calculate()]


def test_docx_report(tmp_path, results):
    path = DocxReportWriter().save(results, tmp_path / "r.docx")
    table = Document(path).tables[0]
    assert len(table.rows) == 3                  # заголовок + 2 строки
    assert table.cell(1, 0).text == "Электрон"


def test_xlsx_report(tmp_path, results):
    path = XlsxReportWriter()(results, tmp_path)  # __call__, имя файла генерируется
    assert path.suffix == ".xlsx" and path.exists()
    ws = load_workbook(path).active
    assert ws["A4"].value == "Электрон" and ws["A5"].value == "Протон"
    assert ws["G4"].value == pytest.approx(results[0].specific_charge)


def test_empty_results_and_title_validation(tmp_path):
    with pytest.raises(ValueError):
        DocxReportWriter().save([], tmp_path)
    with pytest.raises(ValueError):
        XlsxReportWriter(title="  ")


def test_abstract_writer_and_dunders():
    with pytest.raises(TypeError):
        ReportWriter()
    assert repr(DocxReportWriter("T")) == "DocxReportWriter(title='T')"
    assert "Excel" in str(XlsxReportWriter())
