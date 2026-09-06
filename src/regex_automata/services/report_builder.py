"""Construccion del texto de ``resumen.txt``."""

from __future__ import annotations

from ..constants import EPSILON_LABEL
from .expression_processor import ExpressionAnalysis, SimulationBundle

_SEPARADOR = "=" * 78
_SUBSEPARADOR = "-" * 78


def build_summary(
    analysis: ExpressionAnalysis, simulations: list[SimulationBundle]
) -> str:
    """Genera el resumen completo de una expresion.

    Args:
        analysis: Analisis con los cuatro automatas construidos.
        simulations: Simulaciones realizadas sobre esos automatas.

    Returns:
        El contenido de ``resumen.txt`` como texto.
    """
    lineas: list[str] = []
    agregar = lineas.append

    agregar(_SEPARADOR)
    agregar(f"EXPRESION REGULAR: {analysis.expression}")
    agregar(_SEPARADOR)
    agregar("")

    agregar("1. ANALISIS DE LA EXPRESION")
    agregar(_SUBSEPARADOR)
    agregar(f"  Expresion original    : {analysis.expression}")
    agregar(f"  Concatenacion explicita: {analysis.normalized_expression}")
    agregar(f"  Notacion postfix       : {analysis.postfix_expression}")
    alfabeto = analysis.alphabet
    agregar(
        "  Alfabeto               : "
        + ("{" + ", ".join(alfabeto) + "}" if alfabeto else "vacio")
    )
    agregar(f"  (epsilon se escribe '~' y se muestra como '{EPSILON_LABEL}')")
    agregar("")

    agregar("2. AUTOMATAS CONSTRUIDOS")
    agregar(_SUBSEPARADOR)
    agregar(f"  AFN (Thompson)                : {analysis.nfa.state_count} estados")
    agregar(
        f"  AFD (subconjuntos)            : {analysis.subset.dfa.state_count} estados"
    )
    agregar(
        f"  AFD preparado para minimizar  : {analysis.prepared.dfa.state_count} estados"
    )
    agregar(
        f"  AFD minimo (particiones)      : {analysis.partition.dfa.state_count} estados"
    )
    agregar(
        f"  AFD minimo (tabla de pares)   : {analysis.table_filling.dfa.state_count} estados"
    )
    if analysis.prepared.removed:
        agregar(
            "  Estados inaccesibles eliminados: "
            + ", ".join(analysis.prepared.removed)
        )
    if analysis.prepared.trap_added:
        agregar("  Se agrego un estado pozo para completar la funcion de transicion.")
    agregar("")

    agregar("3. CONSTRUCCION DE SUBCONJUNTOS")
    agregar(_SUBSEPARADOR)
    for estado in analysis.subset.dfa.sorted_states:
        marca = []
        if estado == analysis.subset.dfa.start:
            marca.append("inicial")
        if analysis.subset.dfa.is_accepting(estado):
            marca.append("aceptacion")
        sufijo = f"  <- {', '.join(marca)}" if marca else ""
        agregar(f"  {estado.label} = {analysis.subset.describe_subset(estado)}{sufijo}")
    agregar("")
    agregar("  Tabla de transiciones del AFD:")
    agregar(_transition_table(analysis))
    agregar("")

    agregar("4. MINIMIZACION POR REFINAMIENTO DE PARTICIONES")
    agregar(_SUBSEPARADOR)
    for indice, particion in enumerate(analysis.partition.history):
        bloques = "  ".join("{" + ",".join(bloque) + "}" for bloque in particion)
        agregar(f"  P{indice} = {bloques}")
    agregar(f"  Refinamientos aplicados: {analysis.partition.iterations}")
    agregar("")

    agregar("5. MINIMIZACION POR TABLA DE PARES DISTINGUIBLES")
    agregar(_SUBSEPARADOR)
    iniciales = analysis.table_filling.initial_marks
    agregar(f"  Pares marcados inicialmente ({len(iniciales)}):")
    if iniciales:
        for marca in iniciales:
            agregar(f"    ({marca.first},{marca.second})  {marca.reason}")
    else:
        agregar("    ninguno")
    propagadas = [
        marca for marca in analysis.table_filling.marks if marca.iteration > 0
    ]
    agregar(f"  Pares marcados por propagacion ({len(propagadas)}):")
    if propagadas:
        for marca in propagadas:
            agregar(
                f"    ({marca.first},{marca.second})  iteracion {marca.iteration}, "
                f"simbolo '{marca.symbol}': {marca.reason}"
            )
    else:
        agregar("    ninguno")
    agregar(f"  Iteraciones con marcas nuevas: {analysis.table_filling.iterations}")
    equivalentes = analysis.table_filling.equivalent_pairs
    agregar(f"  Pares equivalentes finales ({len(equivalentes)}):")
    if equivalentes:
        for primero, segundo in equivalentes:
            agregar(f"    ({primero},{segundo})")
    else:
        agregar("    ninguno: el AFD ya era minimo")
    agregar("")

    agregar("6. EQUIVALENCIA DE LOS DOS AFD MINIMOS")
    agregar(_SUBSEPARADOR)
    agregar(
        "  Comprobacion formal por recorrido del producto de estados: "
        + ("EQUIVALENTES" if analysis.equivalence.equivalent else "DIFERENTES")
    )
    agregar(f"  Pares de estados explorados: {analysis.equivalence.pairs_explored}")
    agregar(
        "  Cantidad de estados: "
        f"{analysis.partition.dfa.state_count} (particiones) y "
        f"{analysis.table_filling.dfa.state_count} (tabla de pares)"
    )
    agregar("")

    agregar("7. SIMULACION")
    agregar(_SUBSEPARADOR)
    if not simulations:
        agregar("  No se evaluo ninguna cadena.")
    for paquete in simulations:
        mostrada = paquete.word if paquete.word else f"{EPSILON_LABEL} (cadena vacia)"
        agregar(f"  Cadena w = {mostrada}")
        for resultado in paquete.results:
            agregar(f"    {resultado.automaton:<30} {resultado.answer}")
            agregar(f"      traza: {resultado.format_trace()}")
        agregar(
            "    Los cuatro automatas coinciden: "
            + ("si" if paquete.consistent else "NO (error interno)")
        )
        agregar(f"    w pertenece a L(r): {paquete.answer}")
        agregar("")

    return "\n".join(lineas).rstrip() + "\n"


def _transition_table(analysis: ExpressionAnalysis) -> str:
    """Tabla de transiciones del AFD por subconjuntos, en formato de texto."""
    dfa = analysis.subset.dfa
    alfabeto = dfa.sorted_alphabet
    ancho = max([len(estado.label) for estado in dfa.sorted_states] + [6]) + 2

    lineas = ["     " + "estado".ljust(ancho) + "".join(s.ljust(ancho) for s in alfabeto)]
    for estado in dfa.sorted_states:
        prefijo = "->" if estado == dfa.start else "  "
        prefijo += "*" if dfa.is_accepting(estado) else " "
        celdas = []
        for simbolo in alfabeto:
            destino = dfa.transition(estado, simbolo)
            celdas.append((destino.label if destino else "-").ljust(ancho))
        lineas.append("  " + prefijo + estado.label.ljust(ancho) + "".join(celdas))
    return "\n".join(lineas)
