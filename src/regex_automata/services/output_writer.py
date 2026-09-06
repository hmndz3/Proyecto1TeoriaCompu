"""Escritura de los archivos de salida de cada expresion.

Estructura generada, una carpeta por expresion:

    output/expresion_001/
    |-- resumen.txt
    |-- afn.png                 (o afn.svg si no hay Graphviz)
    |-- afd.png
    |-- afd_min_particiones.png
    `-- afd_min_pares.png

Siempre hay imagen. Si Graphviz esta disponible se usa ``dot``, que produce el
mejor dibujo; si no, se cae al generador de SVG propio, que no depende de nada
externo y se abre en cualquier navegador.

Los archivos ``.dot`` son un paso intermedio y no se dejan en disco salvo que se
pidan con ``keep_dot``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..visualization.dot_builder import dfa_to_dot, nfa_to_dot
from ..visualization.graphviz_renderer import RenderResult, render_image, write_dot
from ..visualization.svg_renderer import dfa_to_svg, nfa_to_svg
from .expression_processor import ExpressionAnalysis, SimulationBundle
from .report_builder import build_summary

#: Nombres base de los archivos que genera cada expresion.
_BASE_NAMES = ("afn", "afd", "afd_min_particiones", "afd_min_pares")

#: Extensiones que puede tener cada uno.
_EXTENSIONS = (".png", ".svg", ".dot")


@dataclass(frozen=True)
class OutputReport:
    """Archivos generados para una expresion.

    Attributes:
        directory: Carpeta creada para la expresion.
        image_files: Imagenes ``.png`` generadas con Graphviz.
        svg_files: Imagenes ``.svg`` generadas por el dibujante propio.
        dot_files: Archivos ``.dot``, solo si se pidieron.
        summary_file: Ruta de ``resumen.txt``.
        render_errors: Motivos por los que Graphviz no pudo generar la imagen.
    """

    directory: Path
    image_files: tuple[Path, ...]
    svg_files: tuple[Path, ...]
    dot_files: tuple[Path, ...]
    summary_file: Path
    render_errors: tuple[str, ...] = ()

    @property
    def images_generated(self) -> bool:
        """``True`` si hay alguna imagen, sea PNG o SVG."""
        return bool(self.image_files or self.svg_files)

    @property
    def all_images(self) -> tuple[Path, ...]:
        return self.image_files + self.svg_files


def write_expression_outputs(
    analysis: ExpressionAnalysis,
    simulations: list[SimulationBundle],
    output_root: Path,
    index: int,
    *,
    generate_images: bool = True,
    keep_dot: bool = False,
    always_svg: bool = False,
) -> OutputReport:
    """Escribe el resumen y las imagenes de una expresion.

    Args:
        analysis: Analisis de la expresion.
        simulations: Simulaciones ya realizadas.
        output_root: Carpeta raiz de salidas.
        index: Numero de expresion, base uno. Da nombre a la subcarpeta.
        generate_images: Si es ``False`` no se dibuja nada y solo quedan los
            ``.dot`` junto al resumen.
        keep_dot: Conserva el ``.dot`` aunque se haya generado la imagen.
        always_svg: Genera tambien el SVG propio aunque Graphviz funcione.

    Returns:
        Un :class:`OutputReport` con las rutas escritas.
    """
    carpeta = output_root / f"expresion_{index:03d}"
    carpeta.mkdir(parents=True, exist_ok=True)
    _clean_previous(carpeta)

    resumen = carpeta / "resumen.txt"
    resumen.write_text(
        build_summary(analysis, simulations), encoding="utf-8", newline="\n"
    )

    trabajos = [
        ("afn", nfa_to_dot(analysis.nfa, name="AFN"), nfa_to_svg(analysis.nfa, title="AFN")),
        (
            "afd",
            dfa_to_dot(analysis.subset.dfa, name="AFD"),
            dfa_to_svg(analysis.subset.dfa, title="AFD"),
        ),
        (
            "afd_min_particiones",
            dfa_to_dot(analysis.partition.dfa, name="AFD_min_particiones"),
            dfa_to_svg(analysis.partition.dfa, title="AFD minimo por particiones"),
        ),
        (
            "afd_min_pares",
            dfa_to_dot(analysis.table_filling.dfa, name="AFD_min_pares"),
            dfa_to_svg(analysis.table_filling.dfa, title="AFD minimo por tabla de pares"),
        ),
    ]

    pngs: list[Path] = []
    svgs: list[Path] = []
    dots: list[Path] = []
    errores: list[str] = []

    for nombre, fuente_dot, fuente_svg in trabajos:
        png = carpeta / f"{nombre}.png"
        resultado = (
            render_image(fuente_dot, png)
            if generate_images
            else RenderResult(False, "no se pidieron imagenes")
        )
        if resultado.ok:
            pngs.append(png)
        elif generate_images:
            # Sin Graphviz se dibuja igual, con el generador propio.
            svgs.append(_write_svg(fuente_svg, carpeta / f"{nombre}.svg"))
            if resultado.error and resultado.error not in errores:
                errores.append(resultado.error)

        if resultado.ok and always_svg:
            svgs.append(_write_svg(fuente_svg, carpeta / f"{nombre}.svg"))

        if keep_dot or not generate_images:
            dots.append(write_dot(fuente_dot, carpeta / f"{nombre}.dot"))

    return OutputReport(
        directory=carpeta,
        image_files=tuple(pngs),
        svg_files=tuple(svgs),
        dot_files=tuple(dots),
        summary_file=resumen,
        render_errors=tuple(errores),
    )


def _clean_previous(directory: Path) -> None:
    """Borra las salidas de una corrida anterior en esa carpeta.

    Sin esto, un ``.dot`` o un ``.svg`` que quedo de una ejecucion previa
    seguiria ahi aunque esta vez si se hayan generado los ``.png``, y daria la
    impresion de que el programa lo dejo suelto. Solo se tocan los nombres que
    genera el propio programa.
    """
    for nombre in _BASE_NAMES:
        for extension in _EXTENSIONS:
            ruta = directory / f"{nombre}{extension}"
            try:
                ruta.unlink()
            except FileNotFoundError:
                continue
            except OSError:
                # Si el sistema no permite borrar, se sobrescribe y ya.
                continue


def _write_svg(source: str, path: Path) -> Path:
    """Escribe un SVG con saltos de linea ``\\n``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")
    return path
