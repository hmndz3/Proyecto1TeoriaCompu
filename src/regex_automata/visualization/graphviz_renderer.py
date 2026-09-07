"""Invocacion del ejecutable ``dot`` de Graphviz.

El proyecto no depende de ningun paquete de Python para dibujar: construye el
codigo DOT y llama al binario.

El codigo DOT se le pasa a ``dot`` por la entrada estandar, de modo que cuando
Graphviz esta disponible la carpeta de salida queda solo con las imagenes y no
con archivos intermedios. Si Graphviz no esta instalado, el ``.dot`` se escribe
en disco para no perder el automata.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_TIMEOUT_SECONDS = 30

#: Variable de entorno con la ruta al ejecutable, si se quiere forzar.
_ENV_VAR = "GRAPHVIZ_DOT"

#: Ruta indicada a mano desde la linea de comandos.
_override: str | None = None


def set_dot_executable(path: str | None) -> None:
    """Fija la ruta del ejecutable ``dot`` y descarta la deteccion en cache."""
    global _override
    _override = path
    find_dot.cache_clear()
    is_graphviz_available.cache_clear()
    graphviz_version.cache_clear()


def _windows_candidates() -> list[Path]:
    """Carpetas donde Graphviz suele quedar instalado en Windows."""
    raices = [
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("PROGRAMW6432"),
    ]
    encontrados: list[Path] = []
    for raiz in raices:
        if not raiz:
            continue
        base = Path(raiz) / "Graphviz"
        if not base.is_dir():
            continue
        directo = base / "bin" / "dot.exe"
        if directo.is_file():
            encontrados.append(directo)
        # La version portable se extrae en Graphviz/Graphviz-X.Y.Z-win64/bin.
        for hijo in sorted(base.glob("*/bin/dot.exe")):
            if hijo.is_file():
                encontrados.append(hijo)
    return encontrados


def _unix_candidates() -> list[Path]:
    """Rutas habituales en macOS y Linux."""
    rutas = [
        Path("/usr/bin/dot"),
        Path("/usr/local/bin/dot"),
        Path("/opt/homebrew/bin/dot"),
        Path("/opt/local/bin/dot"),
    ]
    return [ruta for ruta in rutas if ruta.is_file()]


@lru_cache(maxsize=1)
def find_dot() -> str | None:
    """Localiza el ejecutable ``dot``.

    Se busca en este orden:

    1. La ruta indicada con ``--dot``.
    2. La variable de entorno ``GRAPHVIZ_DOT``.
    3. El PATH del proceso.
    4. Las carpetas de instalacion habituales de cada sistema.

    El cuarto paso existe porque en Windows es comun que Graphviz este
    instalado pero el PATH del proceso sea antiguo: los programas que se abren
    desde el explorador heredan el entorno que este tenia al arrancar, asi que
    el PATH nuevo no llega hasta cerrar la sesion.

    Returns:
        La ruta del ejecutable, o ``None`` si no aparece por ningun lado.
    """
    if _override:
        return _override if Path(_override).is_file() else None

    del_entorno = os.environ.get(_ENV_VAR)
    if del_entorno and Path(del_entorno).is_file():
        return del_entorno

    en_path = shutil.which("dot")
    if en_path:
        return en_path

    for candidato in (*_windows_candidates(), *_unix_candidates()):
        return str(candidato)
    return None


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
    """Indica si se pudo localizar el ejecutable ``dot``."""
    return find_dot() is not None


@lru_cache(maxsize=1)
def graphviz_version() -> str | None:
    """Devuelve la version reportada por ``dot -V``, o ``None`` si no responde."""
    ejecutable = find_dot()
    if ejecutable is None:
        return None
    try:
        proceso = subprocess.run(
            [ejecutable, "-V"], capture_output=True, timeout=_TIMEOUT_SECONDS
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    salida = (proceso.stderr or proceso.stdout).decode("utf-8", "replace").strip()
    return salida or None


def installation_hint() -> str:
    """Instrucciones de instalacion de Graphviz para mostrar al usuario."""
    return (
        "No se encontro Graphviz ('dot') ni en el PATH ni en las carpetas\n"
        "habituales de instalacion.\n"
        "  Windows : winget install graphviz\n"
        "            (o el instalador de https://graphviz.org/download/ marcando\n"
        "            'Add Graphviz to the system PATH'). Despues hay que CERRAR y\n"
        "            volver a abrir la terminal para que tome el PATH nuevo.\n"
        "  macOS   : brew install graphviz\n"
        "  Debian  : sudo apt install graphviz\n"
        "Compruebe la instalacion con:  dot -V\n"
        "Si ya esta instalado, indique la ruta con --dot o con la variable de\n"
        "entorno GRAPHVIZ_DOT, por ejemplo:\n"
        "  python main.py --dot \"C:\\ruta\\a\\Graphviz\\bin\\dot.exe\"\n"
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
    ejecutable = find_dot()
    if ejecutable is None:
        return RenderResult(
            False, "no se encontro el ejecutable 'dot' de Graphviz en el sistema"
        )

    image_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [ejecutable, f"-T{image_format}", "-o", str(image_path)],
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
