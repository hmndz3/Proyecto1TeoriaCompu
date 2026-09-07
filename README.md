# Proyecto 1 — Teoría de la Computación

Construcción, minimización, visualización y simulación de **autómatas finitos** a
partir de **expresiones regulares**. Es la parte inicial de un analizador léxico:
dada una expresión regular `r` y una cadena `w`, el programa responde si
`w ∈ L(r)`.

Universidad del Valle de Guatemala · Teoría de la Computación

## Tabla de contenido

1. [Objetivo](#1-objetivo)
2. [Requisitos e instalación](#2-requisitos-e-instalación)
3. [Instalación de Graphviz](#3-instalación-de-graphviz)
4. [Operadores y precedencia](#4-operadores-y-precedencia)
5. [Epsilon, escapes y cadena vacía](#5-epsilon-escapes-y-cadena-vacía)
6. [Ejecución](#6-ejecución)
7. [Arquitectura](#7-arquitectura)
8. [Shunting Yard, Thompson y subconjuntos](#8-shunting-yard-thompson-y-subconjuntos)
9. [Los dos métodos de minimización](#9-los-dos-métodos-de-minimización)
10. [Salidas y visualizaciones](#10-salidas-y-visualizaciones)
11. [Pruebas](#11-pruebas)
12. [Ejemplos completos](#12-ejemplos-completos)
13. [Limitaciones](#13-limitaciones)
14. [Integrantes](#14-integrantes)

---

## 1. Objetivo

Por cada expresión regular `r` el programa ejecuta el siguiente flujo:

```text
infix
  → tokenización y validación
  → inserción de concatenación explícita
  → postfix (Shunting Yard)
  → AFN (Thompson)
  → AFD (construcción de subconjuntos)
  → preparación del AFD (accesibles + estado pozo)
  → AFD mínimo por refinamiento de particiones
  → AFD mínimo por tabla de pares distinguibles
```

Una cadena `w` se simula en **los cuatro autómatas**: el AFN, el AFD por
subconjuntos y los dos AFD mínimos. Los cuatro resultados deben coincidir; si no
lo hacen, el programa lo reporta como un defecto interno. Además, la equivalencia
de los dos AFD mínimos se comprueba **formalmente**, recorriendo el producto de
estados, no con unas cuantas cadenas de muestra.

## 2. Requisitos e instalación

- **Python 3.10 o superior**
- **Graphviz** — opcional. Si está, las imágenes salen en `.png` con su trazado;
  si no, el programa las dibuja él mismo en `.svg`. **Siempre hay imagen.**

El programa **no necesita dependencias de terceros para ejecutarse**: todos los
algoritmos son propios y los archivos DOT se escriben directamente. La librería
`re` de Python no se utiliza en ninguna parte del reconocimiento.

```bash
git clone https://github.com/hmndz3/Proyecto1TeoriaCompu.git
cd Proyecto1TeoriaCompu

# Opcional pero recomendado
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Solo hace falta para correr las pruebas
pip install -r requirements.txt
```

## 3. Instalación de Graphviz

Se usa el ejecutable `dot`, no un paquete de Python.

| Sistema | Comando |
|---|---|
| Windows | `winget install graphviz` o el instalador oficial marcando **"Add Graphviz to the system PATH"** |
| macOS | `brew install graphviz` |
| Debian / Ubuntu | `sudo apt install graphviz` |

Para verificar la instalación:

```bash
dot -V
```

Si `dot -V` no responde, Graphviz no está instalado o no quedó en el PATH; en
Windows hay que **cerrar y volver a abrir la terminal** después de instalarlo.

Al arrancar, el programa imprime la versión detectada (`Graphviz detectado: dot
- graphviz version ...`).

**No hace falta que `dot` esté en el PATH.** El programa lo busca en este orden:

1. La ruta que se le pase con `--dot`.
2. La variable de entorno `GRAPHVIZ_DOT`.
3. El PATH del proceso.
4. Las carpetas de instalación habituales: `%LOCALAPPDATA%\Graphviz\...\bin`,
   `%ProgramFiles%\Graphviz\bin`, `/usr/bin`, `/usr/local/bin`,
   `/opt/homebrew/bin`.

El cuarto paso resuelve un caso muy común en Windows: Graphviz está instalado y
`dot -V` funciona en una terminal nueva, pero los programas abiertos desde el
explorador (VS Code incluido) heredan el PATH que tenía el explorador al
arrancar, así que no lo ven hasta cerrar sesión. Si aun así no aparece:

```bash
python main.py --dot "C:\Users\tu_usuario\AppData\Local\Graphviz\Graphviz-16.0.0-win64\bin\dot.exe"
```

**Graphviz no es obligatorio.** Si no está, el proyecto dibuja los autómatas con
un generador de SVG propio, escrito en Python puro y sin dependencias: los `.svg`
se abren en cualquier navegador y muestran lo mismo (estado inicial, doble
círculo en los de aceptación, transiciones con sus símbolos). El trazado de
Graphviz es más pulido, por eso se prefiere cuando está disponible.

## 4. Operadores y precedencia

| Operador | Significado | Aridad | Precedencia |
|---|---|---|---|
| `*` | Cero o más repeticiones | Unario postfix | 3 |
| `+` | Una o más repeticiones | Unario postfix | 3 |
| `?` | Cero o una aparición | Unario postfix | 3 |
| `.` | Concatenación | Binario, asociativo por la izquierda | 2 |
| `\|` | Unión | Binario, asociativo por la izquierda | 1 |
| `( )` | Agrupación | — | — |

Los operadores postfix se aplican al átomo o subexpresión inmediatamente anterior.

### Concatenación explícita e implícita

Se aceptan las dos formas. Antes de aplicar Shunting Yard, un paso de
normalización inserta el operador `.` donde corresponde, sin duplicar el que el
usuario ya escribió:

| Escrito | Normalizado |
|---|---|
| `ab` | `a.b` |
| `a(b)` | `a.(b)` |
| `(a)b` | `(a).b` |
| `a*b` | `a*.b` |
| `a+b` | `a+.b` |
| `a?b` | `a?.b` |
| `(a)(b)` | `(a).(b)` |
| `a.b` | `a.b` (sin cambios) |

Por eso la expresión del enunciado `(b|b)*abb(a|b)*` funciona tal cual.

### Gramática aceptada

```text
expresión      → unión
unión          → concatenación ("|" concatenación)*
concatenación  → repetición ("." repetición)*
repetición     → átomo ("*" | "+" | "?")*
átomo          → símbolo | epsilon | "(" expresión ")"
```

## 5. Epsilon, escapes y cadena vacía

- **Epsilon se escribe `~`.** Es un carácter que difícilmente aparece como
  símbolo del alfabeto, tal como pide el enunciado. Se muestra como `ε` en
  trazas, resúmenes e imágenes.
- Epsilon **no pertenece al alfabeto**, no consume caracteres y participa en la
  cerradura-ε. Internamente se representa con una constante propia, nunca con el
  string de un símbolo ordinario.
- Los **caracteres reservados** son `* + ? . | ( ) ~ \`. Para usar uno como
  símbolo literal se escapa con `\`:

  | Escrito | Significa |
  |---|---|
  | `\+` | el símbolo `+` |
  | `\.` | el símbolo `.` |
  | `\~` | el símbolo `~` |
  | `\\` | el símbolo `\` |
  | `\ ` | un espacio literal |

- Los espacios exteriores se ignoran.
- La **cadena vacía** se evalúa dejando `--word` vacío (`--word ""`) o pulsando
  Enter sin escribir nada en el modo interactivo.

### Validación

Se detectan, con número de línea, posición y fragmento relevante:

expresión vacía · paréntesis desbalanceados · paréntesis vacíos `()` ·
unión sin operando izquierdo o derecho · concatenación explícita sin alguno de
sus operandos · expresión que empieza con `* + ? | .` · operador postfix sin
operando · escape incompleto · secuencias de operadores inválidas.

Una expresión inválida dentro de un archivo **no detiene** el procesamiento de
las demás líneas.

## 6. Ejecución

### Forma principal: los dos archivos

```bash
python main.py
```

Sin argumentos, el programa lee **dos archivos**:

- `data/expresiones.txt` — una expresión regular por línea.
- `data/cadenas.txt` — una cadena `w` por línea.

y las **empareja por posición**: la expresión de la línea 1 se evalúa con la
cadena de la línea 1, la de la línea 2 con la cadena 2, y así. Si hay 10
expresiones tiene que haber 10 cadenas; si no coinciden, el programa lo dice y
se detiene.

Para cada par construye los cuatro autómatas, genera sus imágenes y responde
`sí` o `no`.

`main.py` agrega `src/` al path, así que no hace falta instalar nada ni
configurar `PYTHONPATH`, y los archivos por omisión se encuentran aunque
ejecutes el programa desde otra carpeta.

### Otros archivos

```bash
python main.py --file mis_expresiones.txt --words-file mis_cadenas.txt
```

### Una sola cadena para todas las expresiones

```bash
python main.py --file data/expresiones.txt --word babbaaaa
```

### Una expresión suelta

```bash
python main.py --regex "(b|b)*abb(a|b)*" --word babbaaaa
```

Con `--regex` y `--words-file`, esa única expresión se evalúa con **todas** las
cadenas del archivo.

### Modo interactivo (pide las cadenas por teclado)

```bash
python main.py --interactive
```

Enter sin texto evalúa la cadena vacía y `:fin` pasa a la siguiente expresión.

### Instalando el paquete

```bash
pip install -e .
python -m regex_automata --regex "(b|b)*abb(a|b)*" --word babbaaaa
regex-automata
```

### Opciones

| Opción | Descripción |
|---|---|
| `--regex`, `-r` | Expresión regular suelta |
| `--file`, `-f` | Archivo de expresiones (por defecto `data/expresiones.txt`) |
| `--word`, `-w` | Una sola cadena, aplicada a todas las expresiones |
| `--words-file`, `-W` | Archivo de cadenas (por defecto `data/cadenas.txt`) |
| `--interactive`, `-i` | Pide las cadenas por teclado |
| `--output`, `-o` | Carpeta raíz de las salidas (por defecto `output`) |
| `--no-images` | No dibuja nada; deja solo los `.dot` |
| `--dot` | Ruta al ejecutable `dot`, si no se encuentra solo |
| `--svg` | Genera también el `.svg` propio aunque Graphviz funcione |
| `--keep-dot` | Conserva los `.dot` además de las imágenes |
| `--quiet`, `-q` | Imprime únicamente `si` o `no` |

`--regex` y `--file` son mutuamente excluyentes, igual que `--word` y
`--words-file`.

### Formato de los archivos

En ambos se ignoran las líneas vacías y las que empiezan con `#`.

`data/expresiones.txt`:

```text
# una expresión regular por línea
(a|b)*abb(a|b)*
a+.b?
(a|~).b*
```

`data/cadenas.txt`:

```text
# una cadena por línea, emparejada con la expresión de la misma posición
# '~' es la cadena vacía
babbaaaa
ab
~
```

## 7. Arquitectura

```text
Proyecto1TeoriaCompu/
├── README.md
├── main.py                          lanzador: python main.py --regex ...
├── pyproject.toml
├── requirements.txt
├── data/
│   ├── expresiones.txt              una expresión regular por línea
│   └── cadenas.txt                  una cadena por línea, emparejada 1 a 1
├── output/                          salidas generadas, una carpeta por expresión
├── src/regex_automata/
│   ├── cli.py                       interfaz de consola
│   ├── constants.py                 operadores, precedencias, epsilon
│   ├── errors.py                    jerarquía de errores con posición
│   ├── models/                      token, state, nfa, dfa
│   ├── regex/                       tokenizer, validator, concatenation, shunting_yard
│   ├── algorithms/                  thompson, subset_construction, dfa_preparation,
│   │                                partition_minimizer, table_filling_minimizer,
│   │                                quotient, equivalence, labels
│   ├── simulation/                  nfa_simulator, dfa_simulator, result
│   ├── visualization/               graph_model, dot_builder, svg_renderer,
│   │                                graphviz_renderer
│   └── services/                    expression_processor, file_processor,
│                                    report_builder, output_writer
└── tests/                           pruebas unitarias y de integración
```

Principios aplicados: los algoritmos y simuladores **no imprimen**, devuelven
datos; la presentación vive en la CLI y en `report_builder`. Los modelos son
inmutables y no hay estado global mutable. El código y los nombres internos están
en inglés; la CLI, los errores y la documentación en español.

## 8. Shunting Yard, Thompson y subconjuntos

### Shunting Yard

Opera sobre tokens tipados, no sobre strings. Respeta precedencia y asociatividad
por la izquierda de `|` y `.`, maneja las agrupaciones y trata `*`, `+` y `?`
como operadores postfix, que se emiten directamente a la salida porque su
operando ya fue emitido.

```text
Infix normalizada: (a|b)*.a.b
Postfix:           a b | * a . b .
```

### Thompson

Usa una pila de fragmentos; cada fragmento tiene **un** estado inicial y **un**
estado final, lo que permite componerlos sin ambigüedad. Se implementan
directamente símbolo, epsilon, unión, concatenación, cerradura de Kleene,
cerradura positiva y opcional:

```text
r*  cero o más ocurrencias     (con atajo inicio → fin y ciclo fin → inicio)
r+  una o más ocurrencias      (con ciclo, sin atajo)
r?  epsilon o una ocurrencia   (con atajo, sin ciclo)
```

### Construcción de subconjuntos

Implementa explícitamente `epsilon_closure(states)` y `move(states, symbol)`. El
estado inicial del AFD es la cerradura-ε del inicial del AFN, y un estado
compuesto es de aceptación si contiene al menos un estado final del AFN. El AFD
resultante puede quedar parcial: los subconjuntos vacíos no se crean como estado.

### Preparación previa a la minimización

Antes de minimizar, y para **ambos** métodos por igual:

1. Se eliminan los estados inaccesibles.
2. Se completa la función de transición.
3. Se crea un estado pozo (`TRAMPA`) cuando hace falta.
4. El AFD original **no se muta**: se construye uno nuevo.

## 9. Los dos métodos de minimización

Son dos implementaciones **independientes**: ninguna invoca a la otra. Solo
comparten el paso final de armar el autómata cociente a partir de las clases de
equivalencia, que es construcción y no decisión.

### 9.1 Refinamiento sucesivo de particiones

1. `P0 = {estados de aceptación, estados de no aceptación}` (sin bloques vacíos).
2. Para cada símbolo se calcula a qué bloque llega cada estado.
3. Los estados con firmas de destino distintas se separan.
4. Se repite hasta alcanzar un punto fijo.
5. Se crea un estado por bloque final.

El historial `P0, P1, ..., Pn` se conserva y aparece completo en `resumen.txt`.

### 9.2 Tabla de pares distinguibles (Myhill-Nerode)

1. Se forman todos los pares no ordenados de estados distintos.
2. Se marcan los pares donde **exactamente uno** es de aceptación.
3. Para cada par no marcado y cada símbolo se calcula el par de destinos.
4. Si el par destino ya está marcado, se marca el par original.
5. Se repite hasta que no aparezcan marcas nuevas.
6. Los pares que quedan sin marcar son equivalentes.
7. Las clases de equivalencia se cierran transitivamente con union-find.

Se conserva y se reporta: los pares marcados inicialmente, la iteración en que se
marcó cada par, el símbolo que demostró la distinción y los pares equivalentes
finales.

### Verificación de que ambos coinciden

Por cada expresión se exige que los dos AFD mínimos tengan **la misma cantidad de
estados** y que sean **formalmente equivalentes**, comprobado con un recorrido
del producto de estados que considera la unión de alfabetos y los estados pozo
implícitos. Si fallan, se lanza un error interno explícito.

## 10. Salidas y visualizaciones

Por cada expresión se crea una carpeta:

```text
output/expresion_001/
├── resumen.txt
├── afn.png
├── afd.png
├── afd_min_particiones.png
└── afd_min_pares.png
```

Si Graphviz no está instalado, los cuatro archivos salen como `.svg` en lugar de
`.png`, dibujados por el propio programa. En cualquier caso **siempre hay cuatro
imágenes**.

El código DOT es un paso intermedio: se le pasa a Graphviz por la entrada
estándar, así que la carpeta queda solo con las imágenes y el resumen. Los `.dot`
aparecen únicamente si se piden con `--keep-dot` o `--no-images`.

Antes de escribir, el programa **borra sus propias salidas de la corrida
anterior** en esa carpeta, así que nunca queda un `.dot` o un `.svg` suelto de
una ejecución previa. Los archivos que no genera el programa no se tocan.

Los archivos de texto se escriben siempre con saltos de línea `\n`, de modo que
salen idénticos en Windows, macOS y Linux.

`resumen.txt` incluye: expresión original, expresión normalizada, postfix,
alfabeto, cantidad de estados de cada autómata, correspondencia de subconjuntos,
tabla de transiciones del AFD, historial completo de particiones, información del
marcado de pares, confirmación de equivalencia de los dos mínimos y el resultado
de las cuatro simulaciones con su traza.

Ambos formatos comparten el mismo modelo de grafo intermedio, así que dibujan
exactamente lo mismo. Convenciones:

- Flecha externa hacia el estado inicial, que además se resalta en azul.
- **Doble círculo** para los estados de aceptación, círculo simple para el resto.
- Glifo `ε` en las transiciones vacías.
- Estados del AFN etiquetados `q0`, `q1`, ...; los del AFD `A`, `B`, `C`, ...;
  los minimizados con sus miembros, por ejemplo `{A,C}`.
- Los símbolos que comparten origen y destino se agrupan como `a,b`.
- Estados y símbolos se recorren ordenados, así que dos ejecuciones producen
  exactamente el mismo archivo.

## 11. Pruebas

```bash
pip install -r requirements.txt
python -m pytest          # suite completa
python -m ruff check .    # análisis estático y formato
```

La suite cubre tokenización, escapes, validación, concatenación implícita y
explícita, Shunting Yard, Thompson, subconjuntos, preparación del AFD, ambos
minimizadores, equivalencia formal, simulación, generación de DOT, lectura de
archivos y continuación tras una línea inválida. Las pruebas de integración
comparan **siempre** la aceptación del AFN, el AFD y los dos AFD mínimos.

## 12. Ejemplos completos

### Ejemplo del enunciado

```bash
python main.py --regex "(b|b)*abb(a|b)*" --word babbaaaa
```

```text
==============================================================================
EXPRESION 1: (b|b)*abb(a|b)*
==============================================================================
  Concatenacion explicita : (b|b)*.a.b.b.(a|b)*
  Postfix (shunting yard) : b b | * a . b . b . a b | * .
  Alfabeto                : {a, b}
  AFN (Thompson)          : 22 estados
  AFD (subconjuntos)      : 7 estados
  AFD min. particiones    : 5 estados
  AFD min. tabla de pares : 5 estados
  Los dos AFD minimos son equivalentes: si

  Simulacion con w = babbaaaa
    AFN                            si
    AFD (subconjuntos)             si
    AFD minimo (particiones)       si
    AFD minimo (tabla de pares)    si
    >>> w pertenece a L(r): SI
```

El historial de particiones de este caso, tal como aparece en `resumen.txt`:

```text
  P0 = {A,B,C,D,TRAMPA}  {E,F,G}
  P1 = {A,B,C,TRAMPA}  {D}  {E,F,G}
  P2 = {A,C,TRAMPA}  {B}  {D}  {E,F,G}
  P3 = {A,C}  {B}  {D}  {E,F,G}  {TRAMPA}
```

### Otros casos

| Expresión | Cadena | Resultado |
|---|---|---|
| `a` | `a` | sí |
| `a` | (vacía) | no |
| `~` | (vacía) | sí |
| `a*` | (vacía) | sí |
| `a+` | (vacía) | no |
| `a+` | `aaa` | sí |
| `a?` | `aa` | no |
| `a\|b` | `b` | sí |
| `ab` | `ab` | sí |
| `(a\|b)*` | `abba` | sí |
| `(a\|b)*abb(a\|b)*` | `babbaaaa` | sí |
| `\+*` | `+++` | sí |

### Cadena vacía y errores

```bash
python main.py --regex "a*" --word ""      # si
python main.py --regex "a+" --word ""      # no
python main.py --regex "(a|b" --word "ab"
```

```text
Error de sintaxis (posicion 1): parentesis de apertura sin cerrar
  (a|b
  ^
```

## 13. Limitaciones

- Cada símbolo del alfabeto es **un solo carácter**. No hay clases de caracteres
  (`[a-z]`), comodines (`.` es concatenación, no "cualquier carácter"),
  contadores (`{n,m}`), anclas ni grupos con nombre. No se agregaron porque el
  enunciado no los pide.
- El AFN de Thompson no se optimiza: conserva todas las transiciones ε que genera
  el algoritmo, que es lo que se quiere mostrar. Por eso tiene bastantes más
  estados que el AFD.
- La construcción de subconjuntos es exponencial en el peor caso; con expresiones
  muy grandes el AFD puede crecer mucho antes de minimizarse.
- El dibujante de SVG propio coloca los estados por capas según su distancia al
  inicial. Es legible y suficiente, pero con autómatas grandes cruza más aristas
  que Graphviz, que hace un ruteo mucho más elaborado. Por eso se prefiere
  Graphviz cuando está disponible.
- El estado pozo aparece en los AFD mínimos porque la minimización trabaja sobre
  el AFD completo. Es lo correcto formalmente, aunque haga los dibujos un poco
  más grandes.

## 14. Integrantes

| Integrante | Usuario de GitHub |
|---|---|
| Harry Méndez | [@hmndz3](https://github.com/hmndz3) |
| Denil Parada | [@dparada2020225](https://github.com/dparada2020225) |
| Juan Gualim | [@JuanGualim](https://github.com/JuanGualim) |
