"""Pruebas del archivo de cadenas y de su emparejamiento con las expresiones."""

from __future__ import annotations

from pathlib import Path

import pytest

from regex_automata.cli import (
    DEFAULT_EXPRESSIONS_FILE,
    DEFAULT_WORDS_FILE,
    build_parser,
    resolve_default,
)
from regex_automata.errors import RegexAutomataError
from regex_automata.services.file_processor import (
    ExpressionLine,
    WordLine,
    pair_expressions_and_words,
    read_expressions,
    read_words,
)


def test_lectura_de_cadenas(tmp_path: Path) -> None:
    archivo = tmp_path / "cadenas.txt"
    archivo.write_text("# comentario\n\nabb\n\n  baa  \n", encoding="utf-8")
    cadenas = read_words(archivo)
    assert [linea.word for linea in cadenas] == ["abb", "baa"]
    assert [linea.line_number for linea in cadenas] == [3, 5]


def test_la_virgulilla_es_la_cadena_vacia(tmp_path: Path) -> None:
    archivo = tmp_path / "cadenas.txt"
    archivo.write_text("~\nab\n", encoding="utf-8")
    assert [linea.word for linea in read_words(archivo)] == ["", "ab"]


def test_archivo_de_cadenas_inexistente_falla() -> None:
    with pytest.raises(RegexAutomataError) as error:
        read_words(Path("no_existe_cadenas.txt"))
    assert "cadenas" in str(error.value)


def test_archivo_de_cadenas_vacio_falla(tmp_path: Path) -> None:
    archivo = tmp_path / "cadenas.txt"
    archivo.write_text("# solo comentarios\n\n", encoding="utf-8")
    with pytest.raises(RegexAutomataError):
        read_words(archivo)


def test_emparejamiento_correcto() -> None:
    expresiones = [ExpressionLine(1, "a"), ExpressionLine(2, "b")]
    cadenas = [WordLine(1, "a"), WordLine(2, "")]
    pares = pair_expressions_and_words(
        expresiones,
        cadenas,
        expressions_path=Path("e.txt"),
        words_path=Path("c.txt"),
    )
    assert [(e.expression, c.word) for e, c in pares] == [("a", "a"), ("b", "")]


@pytest.mark.parametrize(
    ("n_expresiones", "n_cadenas"), [(3, 2), (2, 3), (10, 0), (0, 5)]
)
def test_cantidades_distintas_fallan(n_expresiones: int, n_cadenas: int) -> None:
    expresiones = [ExpressionLine(i + 1, "a") for i in range(n_expresiones)]
    cadenas = [WordLine(i + 1, "a") for i in range(n_cadenas)]
    with pytest.raises(RegexAutomataError) as error:
        pair_expressions_and_words(
            expresiones,
            cadenas,
            expressions_path=Path("e.txt"),
            words_path=Path("c.txt"),
        )
    mensaje = str(error.value)
    assert f"{n_expresiones} expresiones" in mensaje
    assert f"{n_cadenas} cadenas" in mensaje


def test_los_archivos_por_omision_existen_y_coinciden() -> None:
    expresiones = read_expressions(resolve_default(DEFAULT_EXPRESSIONS_FILE))
    cadenas = read_words(resolve_default(DEFAULT_WORDS_FILE))
    assert len(expresiones) == len(cadenas)
    assert len(expresiones) > 0


def test_sin_argumentos_no_falla_el_parser() -> None:
    args = build_parser().parse_args([])
    assert args.regex is None
    assert args.file is None
    assert args.word is None
    assert args.words_file is None


def test_keep_dot_esta_disponible() -> None:
    assert build_parser().parse_args(["--keep-dot"]).keep_dot is True
    assert build_parser().parse_args([]).keep_dot is False


def test_regex_y_file_son_excluyentes() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--regex", "a", "--file", "x.txt"])


def test_word_y_words_file_son_excluyentes() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--word", "a", "--words-file", "x.txt"])
