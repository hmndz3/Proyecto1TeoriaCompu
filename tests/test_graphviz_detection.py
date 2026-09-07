"""Pruebas de la localizacion del ejecutable de Graphviz.

En Windows es comun que Graphviz este instalado y aun asi no aparezca en el
PATH del proceso, porque los programas abiertos desde el explorador heredan el
entorno que este tenia al arrancar. Por eso la busqueda no se queda en el PATH.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from regex_automata.cli import build_parser
from regex_automata.visualization import graphviz_renderer as gr


@pytest.fixture(autouse=True)
def _limpiar_cache():
    """Cada prueba parte de una deteccion limpia y no ensucia a las demas."""
    gr.set_dot_executable(None)
    yield
    gr.set_dot_executable(None)


def _falso_dot(tmp_path: Path) -> Path:
    ruta = tmp_path / "dot"
    ruta.write_text("#!/bin/sh\n", encoding="utf-8")
    return ruta


def test_la_ruta_indicada_a_mano_tiene_prioridad(tmp_path: Path, monkeypatch) -> None:
    falso = _falso_dot(tmp_path)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: "/otro/dot")
    gr.set_dot_executable(str(falso))
    assert gr.find_dot() == str(falso)


def test_una_ruta_indicada_que_no_existe_no_se_usa(tmp_path: Path) -> None:
    gr.set_dot_executable(str(tmp_path / "no_existe"))
    assert gr.find_dot() is None
    assert gr.is_graphviz_available() is False


def test_la_variable_de_entorno_se_respeta(tmp_path: Path, monkeypatch) -> None:
    falso = _falso_dot(tmp_path)
    monkeypatch.setenv("GRAPHVIZ_DOT", str(falso))
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: None)
    gr.set_dot_executable(None)
    assert gr.find_dot() == str(falso)


def test_una_variable_de_entorno_invalida_se_ignora(monkeypatch) -> None:
    monkeypatch.setenv("GRAPHVIZ_DOT", "/ruta/que/no/existe/dot")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: "/usr/bin/dot")
    gr.set_dot_executable(None)
    assert gr.find_dot() == "/usr/bin/dot"


def test_se_usa_el_path_cuando_no_hay_nada_mas(monkeypatch) -> None:
    monkeypatch.delenv("GRAPHVIZ_DOT", raising=False)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: "/usr/bin/dot")
    gr.set_dot_executable(None)
    assert gr.find_dot() == "/usr/bin/dot"


def test_se_busca_en_las_carpetas_habituales_si_falta_del_path(
    tmp_path: Path, monkeypatch
) -> None:
    """El caso de Windows: instalado, pero fuera del PATH del proceso."""
    instalado = tmp_path / "Graphviz" / "Graphviz-16.0.0-win64" / "bin"
    instalado.mkdir(parents=True)
    (instalado / "dot.exe").write_text("", encoding="utf-8")

    monkeypatch.delenv("GRAPHVIZ_DOT", raising=False)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(gr, "_unix_candidates", list)
    gr.set_dot_executable(None)

    assert gr.find_dot() == str(instalado / "dot.exe")
    assert gr.is_graphviz_available() is True


def test_tambien_encuentra_la_instalacion_clasica(tmp_path: Path, monkeypatch) -> None:
    """El instalador deja Graphviz/bin/dot.exe, sin subcarpeta de version."""
    instalado = tmp_path / "Graphviz" / "bin"
    instalado.mkdir(parents=True)
    (instalado / "dot.exe").write_text("", encoding="utf-8")

    monkeypatch.delenv("GRAPHVIZ_DOT", raising=False)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: None)
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "vacio"))
    monkeypatch.setattr(gr, "_unix_candidates", list)
    gr.set_dot_executable(None)

    assert gr.find_dot() == str(instalado / "dot.exe")


def test_sin_graphviz_no_se_inventa_nada(monkeypatch) -> None:
    monkeypatch.delenv("GRAPHVIZ_DOT", raising=False)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: None)
    monkeypatch.setattr(gr, "_windows_candidates", list)
    monkeypatch.setattr(gr, "_unix_candidates", list)
    gr.set_dot_executable(None)

    assert gr.find_dot() is None
    assert gr.is_graphviz_available() is False
    assert gr.graphviz_version() is None
    resultado = gr.render_image("digraph g {a}", Path("/tmp/no_se_usa.png"))
    assert resultado.ok is False
    assert "no se encontro" in resultado.error.lower()


def test_el_aviso_explica_como_indicar_la_ruta() -> None:
    texto = gr.installation_hint()
    assert "--dot" in texto
    assert "GRAPHVIZ_DOT" in texto


def test_la_cli_acepta_la_opcion_dot() -> None:
    args = build_parser().parse_args(["--dot", "C:/g/bin/dot.exe"])
    assert args.dot == "C:/g/bin/dot.exe"
    assert build_parser().parse_args([]).dot is None
