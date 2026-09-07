"""Interfaz de linea de comandos.

Sin argumentos, el programa procesa los dos archivos por omision y empareja
cada expresion con la cadena de la misma posicion:

    python main.py

Tambien admite una expresion suelta o archivos distintos:

    python main.py --regex "(b|b)*abb(a|b)*" --word babbaaaa
    python main.py --file data/expresiones.txt --words-file data/cadenas.txt
    python main.py --file data/expresiones.txt --word babbaaaa
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .constants import EPSILON_INPUT, EPSILON_LABEL
from .errors import RegexAutomataError, RegexSyntaxError
from .services.expression_processor import (
    ExpressionAnalysis,
    SimulationBundle,
    analyze_expression,
    simulate_all,
)
from .services.file_processor import (
    ExpressionLine,
    pair_expressions_and_words,
    read_expressions,
    read_words,
)
from .services.output_writer import OutputReport, write_expression_outputs
from .visualization.graphviz_renderer import (
    graphviz_version,
    installation_hint,
    set_dot_executable,
)

_ANCHO = 78

#: Archivos usados cuando no se indica ninguno.
DEFAULT_EXPRESSIONS_FILE = Path("data/expresiones.txt")
DEFAULT_WORDS_FILE = Path("data/cadenas.txt")

#: Raiz del proyecto, para encontrar los archivos por omision aunque el
#: programa se ejecute desde otra carpeta.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_default(relative: Path) -> Path:
    """Busca un archivo por omision primero en la carpeta actual y luego en el proyecto."""
    if relative.exists():
        return relative
    desde_raiz = _PROJECT_ROOT / relative
    return desde_raiz if desde_raiz.exists() else relative


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="regex-automata",
        description=(
            "Convierte expresiones regulares en AFN (Thompson), AFD "
            "(subconjuntos) y AFD minimos (particiones y tabla de pares), y "
            "simula cadenas sobre los cuatro automatas."
        ),
        epilog=(
            "Sin argumentos procesa data/expresiones.txt junto con data/cadenas.txt,\n"
            "emparejando la expresion de la linea N con la cadena de la linea N.\n"
            f"Epsilon se escribe '{EPSILON_INPUT}' y se muestra como '{EPSILON_LABEL}'; "
            f"en el archivo de cadenas '{EPSILON_INPUT}' es la cadena vacia.\n"
            "Use '\\' para escapar un caracter reservado."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument(
        "--regex", "-r", metavar="EXPR", help="expresion regular a procesar"
    )
    entrada.add_argument(
        "--file",
        "-f",
        metavar="RUTA",
        type=Path,
        help=(
            "archivo con una expresion regular por linea "
            f"(por defecto: {DEFAULT_EXPRESSIONS_FILE})"
        ),
    )

    cadenas = parser.add_mutually_exclusive_group()
    cadenas.add_argument(
        "--word",
        "-w",
        metavar="CADENA",
        help="una sola cadena, aplicada a todas las expresiones",
    )
    cadenas.add_argument(
        "--words-file",
        "-W",
        metavar="RUTA",
        type=Path,
        help=(
            "archivo con una cadena por linea, emparejada por posicion con cada "
            f"expresion (por defecto: {DEFAULT_WORDS_FILE})"
        ),
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="pide las cadenas por teclado en lugar de leerlas de un archivo",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="CARPETA",
        type=Path,
        default=Path("output"),
        help="carpeta raiz de las salidas (por defecto: output)",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="genera solo los archivos .dot, sin invocar a Graphviz",
    )
    parser.add_argument(
        "--dot",
        metavar="RUTA",
        help=(
            "ruta al ejecutable 'dot' de Graphviz, si no se encuentra solo "
            "(tambien sirve la variable de entorno GRAPHVIZ_DOT)"
        ),
    )
    parser.add_argument(
        "--svg",
        action="store_true",
        help=(
            "genera tambien el .svg dibujado por el propio programa, aunque "
            "Graphviz este disponible"
        ),
    )
    parser.add_argument(
        "--keep-dot",
        action="store_true",
        help=(
            "conserva los archivos .dot ademas de las imagenes "
            "(por omision se descartan y solo quedan los .png)"
        ),
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="muestra unicamente la respuesta 'si' o 'no' de cada cadena",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la aplicacion.

    Returns:
        ``0`` si todas las expresiones se procesaron sin errores, ``1`` en caso
        contrario.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dot:
        set_dot_executable(args.dot)

    try:
        trabajos = _build_jobs(args)
    except RegexAutomataError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    graficar = not args.no_images
    if graficar and not args.quiet:
        version = graphviz_version()
        if version:
            print(f"Graphviz detectado: {version}")
        else:
            _print_graphviz_warning()

    fallidas = 0
    pngs = 0
    svgs = 0
    for indice, (entrada, palabras) in enumerate(trabajos, start=1):
        reporte = _process_one(entrada, palabras, indice, args)
        if reporte is None:
            fallidas += 1
            continue
        pngs += len(reporte.image_files)
        svgs += len(reporte.svg_files)

    if len(trabajos) > 1 and not args.quiet:
        print(_titulo("RESUMEN GENERAL"))
        print(f"  Expresiones procesadas: {len(trabajos) - fallidas}/{len(trabajos)}")
        if fallidas:
            print(f"  Expresiones con error : {fallidas}")
        if pngs:
            print(f"  Imagenes .png (Graphviz): {pngs}")
        if svgs:
            print(f"  Imagenes .svg (dibujante propio): {svgs}")

    return 1 if fallidas else 0


def _print_graphviz_warning() -> None:
    """Avisa que se dibujara en SVG por no haber Graphviz."""
    print("=" * _ANCHO, file=sys.stderr)
    print("AVISO: se dibujaran archivos .svg en lugar de .png", file=sys.stderr)
    print("=" * _ANCHO, file=sys.stderr)
    print(
        "Los .svg los dibuja el propio programa y se abren en cualquier navegador,\n"
        "asi que no se pierde ninguna salida. Para obtener .png con el mejor\n"
        "trazado, instale Graphviz:",
        file=sys.stderr,
    )
    print(installation_hint(), file=sys.stderr)
    print("=" * _ANCHO, file=sys.stderr)
    print("", file=sys.stderr)


def _build_jobs(args: argparse.Namespace) -> list[tuple[ExpressionLine, list[str]]]:
    """Arma la lista de ``(expresion, cadenas a evaluar)`` segun los argumentos.

    Raises:
        RegexAutomataError: Si falta un archivo o si la cantidad de expresiones
            y de cadenas no coincide.
    """
    # --- una sola expresion ------------------------------------------------ #
    if args.regex is not None:
        entrada = ExpressionLine(line_number=1, expression=args.regex)
        if args.word is not None:
            return [(entrada, [args.word])]
        if args.words_file is not None:
            palabras = [linea.word for linea in read_words(args.words_file)]
            return [(entrada, palabras)]
        return [(entrada, _ask_words(entrada.expression))]

    # --- archivo de expresiones -------------------------------------------- #
    ruta_expresiones = (
        args.file if args.file is not None else resolve_default(DEFAULT_EXPRESSIONS_FILE)
    )
    expresiones = read_expressions(ruta_expresiones)

    if args.word is not None:
        return [(entrada, [args.word]) for entrada in expresiones]

    if args.interactive:
        return [(entrada, _ask_words(entrada.expression)) for entrada in expresiones]

    ruta_cadenas = (
        args.words_file
        if args.words_file is not None
        else resolve_default(DEFAULT_WORDS_FILE)
    )
    if args.words_file is None and not ruta_cadenas.exists():
        # Sin archivo de cadenas se pregunta por teclado.
        return [(entrada, _ask_words(entrada.expression)) for entrada in expresiones]

    cadenas = read_words(ruta_cadenas)
    pares = pair_expressions_and_words(
        expresiones,
        cadenas,
        expressions_path=ruta_expresiones,
        words_path=ruta_cadenas,
    )
    return [(expresion, [cadena.word]) for expresion, cadena in pares]


def _process_one(
    entrada: ExpressionLine,
    palabras: list[str],
    indice: int,
    args: argparse.Namespace,
) -> OutputReport | None:
    """Procesa una expresion con sus cadenas.

    Returns:
        El reporte de archivos escritos, o ``None`` si la expresion era invalida.
    """
    if not args.quiet:
        print(_titulo(f"EXPRESION {indice}: {entrada.expression}"))

    try:
        analisis = analyze_expression(
            entrada.expression, line_number=entrada.line_number
        )
    except RegexSyntaxError as error:
        print(error.describe(), file=sys.stderr)
        print("", file=sys.stderr)
        return None
    except RegexAutomataError as error:
        print(f"Error en '{entrada.expression}': {error}", file=sys.stderr)
        print("", file=sys.stderr)
        return None

    if not args.quiet:
        _print_analysis(analisis)

    simulaciones = [simulate_all(analisis, palabra) for palabra in palabras]
    for paquete in simulaciones:
        _print_simulation(paquete, quiet=args.quiet)

    reporte = write_expression_outputs(
        analisis,
        simulaciones,
        args.output,
        indice,
        generate_images=not args.no_images,
        keep_dot=args.keep_dot,
        always_svg=args.svg,
    )
    if not args.quiet:
        print(f"  Salidas en: {reporte.directory}")
        partes = ["resumen.txt"]
        if reporte.image_files:
            partes.append(f"{len(reporte.image_files)} imagenes .png")
        if reporte.svg_files:
            partes.append(f"{len(reporte.svg_files)} imagenes .svg")
        if reporte.dot_files:
            partes.append(f"{len(reporte.dot_files)} archivos .dot")
        print("    " + ", ".join(partes))
        if reporte.svg_files and reporte.render_errors:
            print(f"    (.svg del dibujante propio: {reporte.render_errors[0]})")
        print("")
    return reporte


def _ask_words(expression: str) -> list[str]:
    """Pide cadenas de forma interactiva hasta que el usuario termine."""
    print(f"  Cadenas para r = {expression}")
    print("    Enter sin texto evalua la cadena vacia; escriba ':fin' para continuar.")
    palabras: list[str] = []
    while True:
        try:
            entrada = input("    w = ")
        except EOFError:
            print("")
            break
        if entrada.strip() == ":fin":
            break
        palabras.append(entrada)
    return palabras


def _print_analysis(analysis: ExpressionAnalysis) -> None:
    """Muestra el analisis de la expresion en consola."""
    print(f"  Concatenacion explicita : {analysis.normalized_expression}")
    print(f"  Postfix (shunting yard) : {analysis.postfix_expression}")
    alfabeto = analysis.alphabet
    print(
        "  Alfabeto                : "
        + ("{" + ", ".join(alfabeto) + "}" if alfabeto else "vacio")
    )
    print(f"  AFN (Thompson)          : {analysis.nfa.state_count} estados")
    print(f"  AFD (subconjuntos)      : {analysis.subset.dfa.state_count} estados")
    print(f"  AFD min. particiones    : {analysis.partition.dfa.state_count} estados")
    print(
        f"  AFD min. tabla de pares : {analysis.table_filling.dfa.state_count} estados"
    )
    print("  Los dos AFD minimos son equivalentes: si")
    print("")


def _print_simulation(bundle: SimulationBundle, *, quiet: bool) -> None:
    """Muestra el resultado de simular una cadena."""
    if quiet:
        print(bundle.answer)
        return

    mostrada = bundle.word if bundle.word else f"{EPSILON_LABEL} (cadena vacia)"
    print(f"  Simulacion con w = {mostrada}")
    for resultado in bundle.results:
        print(f"    {resultado.automaton:<30} {resultado.answer}")
        print(f"      {resultado.format_trace()}")
    if not bundle.consistent:
        print("    ATENCION: los automatas no coinciden, hay un defecto interno.")
    print(f"    >>> w pertenece a L(r): {bundle.answer.upper()}")
    print("")


def _titulo(texto: str) -> str:
    """Encabezado de seccion para la consola."""
    return f"\n{'=' * _ANCHO}\n{texto}\n{'=' * _ANCHO}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
