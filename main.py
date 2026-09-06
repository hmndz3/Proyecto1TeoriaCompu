"""Punto de entrada directo del proyecto.

Permite ejecutar el programa sin instalar el paquete ni configurar PYTHONPATH:

    python main.py --regex "(b|b)*abb(a|b)*" --word babbaaaa
    python main.py --file data/expresiones.txt --word babbaaaa

Es equivalente a `python -m regex_automata`, que funciona una vez que el
paquete se instala con `pip install -e .`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from regex_automata.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
