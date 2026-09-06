"""Invocacion del ejecutable ``dot`` de Graphviz.

El proyecto no depende de ningun paquete de Python para dibujar: construye el
codigo DOT y llama al binario.

El codigo DOT se le pasa a ``dot`` por la entrada estandar, de modo que cuando
Graphviz esta disponible la carpeta de salida queda solo con las imagenes y no
con archivos intermedios. Si Graphviz no esta instalado, el ``.dot`` se escribe
en disco para no perder el automata.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class RenderResult:
    """Resultado de intentar generar una imagen.

    Attributes:
        ok: ``True`` si la imagen quedo escrita en disco.
        error: Motivo del fallo, en espanol, cuando ``ok`` es ``False``.
    """

    ok: bool
    error: str | None = None


@lru_cache(maxsize=1)
def is_graphviz_available() -> bool:
    """Indica si el comando ``dot`` esta disponible en el PATH."""
    return shutil.which("dot") is not None


@lru_cache(maxsize=1)
def graphviz_version() -> str | None:
    """Devuelve la version reportada por ``dot -V``, o ``None`` si no responde."""
    if not is_graphviz_available():
        return None
    try:
        proceso = subprocess.run(
            ["dot", "-V"], capture_output=True, timeout=_TIMEOUT_SECONDS
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    salida = (proceso.stderr or proceso.stdout).decode("utf-8", "replace").strip()
    return salida or None


def installation_hint() -> str:
    """Instrucciones de instalacion de Graphviz para mostrar al usuario."""
    return (
        "Graphviz no esta instalado, o el comando 'dot' no esta en el PATH.\n"
        "  Windows : winget install graphviz\n"
        "            (o el instalador de https://graphviz.org/download/ marcando\n"
        "            'Add Graphviz to the system PATH'). Despues hay que CERRAR y\n"
        "            volver a abrir la terminal para que tome el PATH nuevo.\n"
        "  macOS   : brew install graphviz\n"
        "  Debian  : sudo apt install graphviz\n"
        "Compruebe la instalacion con:  dot -V\n"
        "Mientras tanto se generan archivos .dot, que pueden verse en\n"
        "https://dreampuf.github.io/GraphvizOnline/"
    )


def write_dot(dot_source: str, path: Path) -> Path:
    """Escribe el codigo DOT en ``path`` con saltos de linea ``\\n``.

    El salto de linea se fija de forma explicita para que el archivo sea
    identico en Windows, macOS y Linux.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dot_source, encoding="utf-8", newline="\n")
    return path


def render_image(
    dot_source: str, image_path: Path, *, image_format: str = "png"
) -> RenderResult:
    """Genera la imagen de ``dot_source`` en ``image_path``.

    El codigo DOT viaja por la entrada estandar de ``dot``, asi que no se crea
    ningun archivo intermedio.

    Args:
        dot_source: Codigo DOT completo.
        image_path: Ruta de la imagen a generar.
        image_format: Formato de salida aceptado por Graphviz.

    Returns:
        Un :class:`RenderResult` con el exito y, si fallo, el motivo concreto.
    """
    if not is_graphviz_available():
        return RenderResult(False, "el comando 'dot' de Graphviz no esta en el PATH")

    image_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["dot", f"-T{image_format}", "-o", str(image_path)],
            input=dot_source.encode("utf-8"),
            check=True,
            capture_output=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except subprocess.CalledProcessError as error:
        detalle = error.stderr.decode("utf-8", "replace").strip()
        return RenderResult(
            False, f"'dot' devolvio el codigo {error.returncode}: {detalle or 'sin detalle'}"
        )
    except subprocess.TimeoutExpired:
        return RenderResult(
            False, f"'dot' tardo mas de {_TIMEOUT_SECONDS} segundos y se interrumpio"
        )
    except OSError as error:
        return RenderResult(False, f"no se pudo ejecutar 'dot': {error}")

    if not image_path.exists():
        return RenderResult(False, "'dot' termino bien pero no dejo la imagen en disco")
    return RenderResult(True)
