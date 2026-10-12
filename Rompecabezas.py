#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juego del 8 (rompecabezas deslizante 3x3) con interfaz gráfica.
================================================================

Programa de un solo archivo que utiliza únicamente la librería estándar de
Python (``tkinter``, ``random``). Para jugar basta con ejecutar::

    python juego.py

Reglas del juego
----------------
* El tablero es una cuadrícula de 3x3 con las fichas numeradas del 1 al 8 y
  un espacio en blanco (hueco).
* Solo se puede mover una ficha si está pegada (arriba, abajo, izquierda o
  derecha) al hueco; la ficha se desliza ocupando el hueco.
* El objetivo es ordenar las fichas de izquierda a derecha y de arriba a
  abajo, dejando el hueco en la esquina inferior derecha::

        1 2 3
        4 5 6
        7 8 _

Controles
---------
* Clic del ratón sobre una ficha adyacente al hueco: la desliza.
* Teclas de flecha: desplazan la ficha contigua al hueco en esa dirección
  (por ejemplo, "Izquierda" mueve hacia la izquierda la ficha que está a la
  derecha del hueco).
* Botón "Reiniciar / Mezclar": genera una nueva partida en cualquier momento.

Estructura del código
---------------------
1. Configuración: constantes de tamaño, animación, colores y fuentes.
2. Lógica pura: funciones sin dependencia de la interfaz (inversiones,
   resolubilidad, mezcla y comprobación de victoria).
3. Interfaz: la clase ``PuzzleApp``, que dibuja el tablero, gestiona los
   eventos y conecta con la lógica.
"""

import random
import tkinter as tk
from tkinter import messagebox

# =============================================================================
# 1. CONFIGURACIÓN
# =============================================================================

# --- Geometría del tablero ---------------------------------------------------
N = 3                  # Lado del tablero (3 -> 3x3 = 9 celdas)
TILE = 110             # Lado de cada ficha, en píxeles
GAP = 8                # Separación entre fichas contiguas, en píxeles
PAD = 14               # Margen entre el borde del lienzo y las fichas
# Tamaño total del lienzo: márgenes + fichas + separaciones intermedias.
BOARD_PX = PAD * 2 + N * TILE + (N - 1) * GAP

# --- Animación del deslizamiento --------------------------------------------
ANIM_STEPS = 8         # Número de fotogramas que dura el deslizamiento
ANIM_DELAY = 12        # Milisegundos entre fotogramas (~100 ms en total)

# --- Paleta de colores (formato hexadecimal #RRGGBB) -------------------------
COL_BG = "#1b1f33"            # Fondo de la ventana
COL_BOARD = "#2a3050"         # Fondo del lienzo del tablero
COL_SLOT = "#232843"          # Huecos (celdas) visibles detrás de las fichas
COL_TILE = "#4f8cff"          # Relleno de una ficha normal
COL_TILE_BORDER = "#7aa8ff"   # Borde de las fichas
COL_TILE_OK = "#2fbf8f"       # Relleno de las fichas al resolver el puzzle
COL_TEXT = "#ffffff"          # Texto principal
COL_MUTED = "#9aa3c7"         # Texto secundario (marcador y ayuda)
COL_BTN = "#ff7a59"           # Botón en reposo
COL_BTN_HOVER = "#ff9275"     # Botón con el ratón encima

# --- Fuentes (familia, tamaño, estilo) --------------------------------------
FONT_TILE = ("Helvetica", 38, "bold")    # Números de las fichas
FONT_TITLE = ("Helvetica", 26, "bold")   # Título de la ventana
FONT_SCORE = ("Helvetica", 16)           # Contador de movimientos
FONT_BTN = ("Helvetica", 14, "bold")     # Texto del botón
FONT_HINT = ("Helvetica", 10)            # Texto de ayuda inferior

# --- Estado objetivo ---------------------------------------------------------
# El tablero se representa como una lista plana de N*N enteros, recorrida por
# filas (de izquierda a derecha y de arriba a abajo). El valor 0 representa el
# hueco. El estado resuelto es [1, 2, 3, 4, 5, 6, 7, 8, 0].
GOAL = list(range(1, N * N)) + [0]


# =============================================================================
# 2. LÓGICA PURA (independiente de la interfaz gráfica)
# =============================================================================

def count_inversions(tiles):
    """Cuenta las inversiones de una disposición del tablero.

    Una inversión es una pareja de fichas (a, b) tal que ``a`` aparece antes
    que ``b`` en la lectura por filas, pero ``a > b``. El hueco (0) no se
    tiene en cuenta.

    Args:
        tiles (list[int]): Disposición del tablero (lista plana con el 0 como
            hueco).

    Returns:
        int: Número total de inversiones.

    Ejemplo:
        >>> count_inversions([1, 2, 3, 4, 5, 6, 8, 7, 0])
        1
    """
    # Se elimina el hueco, ya que no cuenta como ficha.
    seq = [t for t in tiles if t != 0]
    inversions = 0
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if seq[i] > seq[j]:
                inversions += 1
    return inversions


def is_solvable(tiles):
    """Indica si una disposición del tablero puede resolverse.

    Fundamento matemático: en un tablero de ancho impar (como el 3x3), mover
    una ficha horizontalmente no altera el orden de lectura, y moverla
    verticalmente la desplaza sobre otras N-1 = 2 fichas, cambiando el número
    de inversiones en -2, 0 o +2. Por tanto, la *paridad* de las inversiones
    es invariante con cualquier movimiento legal. Como el estado resuelto
    tiene 0 inversiones (par), una disposición es resoluble si y solo si su
    número de inversiones es par.

    Args:
        tiles (list[int]): Disposición del tablero.

    Returns:
        bool: ``True`` si existe una secuencia de movimientos que la resuelve.
    """
    return count_inversions(tiles) % 2 == 0


def generate_shuffled():
    """Genera una disposición aleatoria que siempre es resoluble.

    Se baraja la lista completa al azar y se descartan las disposiciones que
    no cumplen la condición de paridad (aproximadamente la mitad). También se
    descarta la disposición ya resuelta para que la partida no empiece
    ganada.

    Returns:
        list[int]: Nueva disposición del tablero, resoluble y distinta de
        ``GOAL``.
    """
    while True:
        tiles = GOAL[:]            # Copia, para no modificar la constante
        random.shuffle(tiles)
        if is_solvable(tiles) and tiles != GOAL:
            return tiles


def is_solved(tiles):
    """Comprueba si el tablero está en el estado de victoria.

    Args:
        tiles (list[int]): Disposición actual del tablero.

    Returns:
        bool: ``True`` si las fichas van del 1 al 8 en orden y el hueco
        ocupa la última posición.
    """
    return tiles == GOAL


# =============================================================================
# 3. INTERFAZ GRÁFICA
# =============================================================================

class PuzzleApp:
    """Ventana principal del juego: dibuja el tablero y gestiona las partidas.

    Atributos de estado:
        root (tk.Tk): Ventana raíz de la aplicación.
        tiles (list[int]): Disposición actual (lista plana, 0 = hueco).
        moves (int): Movimientos realizados en la partida en curso.
        animating (bool): ``True`` mientras se reproduce la animación de una
            ficha; durante ese tiempo se ignoran nuevas entradas del jugador.
        locked (bool): ``True`` cuando el puzzle está resuelto; impide seguir
            moviendo fichas hasta que se inicie una nueva partida.
        _after_id (str | None): Identificador de la siguiente llamada
            programada con ``root.after`` (permite cancelarla al reiniciar).
    """

    def __init__(self, root):
        """Inicializa la ventana, construye los widgets y empieza una partida.

        Args:
            root (tk.Tk): Ventana raíz sobre la que se construye la interfaz.
        """
        self.root = root
        root.title("Juego del 8")
        root.configure(bg=COL_BG)
        root.resizable(False, False)       # Tamaño fijo para mantener el diseño

        # Estado inicial (se sobrescribe en new_game).
        self.tiles = GOAL[:]
        self.moves = 0
        self.animating = False
        self.locked = False
        self._after_id = None

        self._build_ui()
        self.new_game()

        # Soporte de teclado: cada flecha dispara on_key.
        for key in ("<Up>", "<Down>", "<Left>", "<Right>"):
            root.bind(key, self.on_key)

    # -------------------------------------------------------------------------
    # Construcción de la interfaz
    # -------------------------------------------------------------------------
    def _build_ui(self):
        """Crea y coloca todos los widgets: título, marcador, tablero, botón
        y texto de ayuda."""
        # Título.
        tk.Label(self.root, text="Juego del 8", font=FONT_TITLE,
                 bg=COL_BG, fg=COL_TEXT).pack(pady=(18, 4))

        # Marcador de movimientos. Se enlaza a una StringVar para actualizar
        # el texto sin tener que reconfigurar el Label.
        self.score_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.score_var, font=FONT_SCORE,
                 bg=COL_BG, fg=COL_MUTED).pack(pady=(0, 10))

        # Lienzo donde se dibuja el tablero. El clic del ratón se captura aquí.
        self.canvas = tk.Canvas(self.root, width=BOARD_PX, height=BOARD_PX,
                                bg=COL_BOARD, highlightthickness=0)
        self.canvas.pack(padx=24)
        self.canvas.bind("<Button-1>", self.on_click)

        # Botón de reinicio. Se usa relief="flat" para un aspecto moderno.
        self.btn = tk.Button(
            self.root, text="Reiniciar / Mezclar", font=FONT_BTN,
            bg=COL_BTN, fg=COL_TEXT, activebackground=COL_BTN_HOVER,
            activeforeground=COL_TEXT, relief="flat", bd=0,
            padx=24, pady=10, cursor="hand2", command=self.new_game)
        self.btn.pack(pady=(16, 6))
        # Efecto "hover": cambia de color al pasar el ratón por encima.
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=COL_BTN_HOVER))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=COL_BTN))

        # Texto de ayuda con los controles.
        tk.Label(self.root,
                 text="Haz clic en una ficha junto al hueco, "
                      "o usa las flechas del teclado",
                 font=FONT_HINT, bg=COL_BG, fg=COL_MUTED).pack(pady=(0, 16))

    # -------------------------------------------------------------------------
    # Utilidades
    # -------------------------------------------------------------------------
    @staticmethod
    def cell_xy(index):
        """Convierte un índice de celda en coordenadas de píxeles.

        Args:
            index (int): Posición en la lista plana (0 a N*N-1).

        Returns:
            tuple[int, int]: Coordenadas (x, y) de la esquina superior
            izquierda de esa celda dentro del lienzo.
        """
        row, col = divmod(index, N)   # fila y columna a partir del índice
        return PAD + col * (TILE + GAP), PAD + row * (TILE + GAP)

    def update_score(self):
        """Refresca en pantalla el texto del contador de movimientos."""
        self.score_var.set(f"Movimientos: {self.moves}")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        """Dibuja un rectángulo con esquinas redondeadas en el lienzo.

        tkinter no incluye esta figura, así que se emula con un polígono
        suavizado (``smooth=True``) cuyos puntos de control repetidos en las
        esquinas producen el redondeo.

        Args:
            x1, y1 (int | float): Esquina superior izquierda.
            x2, y2 (int | float): Esquina inferior derecha.
            r (int): Radio del redondeo, en píxeles.
            **kw: Opciones de ``create_polygon`` (fill, outline, width...).

        Returns:
            int: Identificador del elemento creado en el lienzo.
        """
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
                  x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                  x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.canvas.create_polygon(points, smooth=True, **kw)

    # -------------------------------------------------------------------------
    # Dibujo
    # -------------------------------------------------------------------------
    def draw(self, moving=None):
        """Redibuja por completo el tablero.

        Orden de dibujo (de atrás hacia delante): huecos de fondo, fichas
        estáticas y, por último, la ficha en movimiento (si la hay) para que
        quede por encima de las demás durante la animación.

        Args:
            moving (tuple[int, float, float] | None): Si se indica, es
                ``(valor, x, y)`` de una ficha que se está animando; se
                dibuja en esa posición en píxeles en lugar de en su celda.
        """
        cv = self.canvas
        cv.delete("all")   # Se borra todo y se vuelve a pintar (es muy ligero)

        # 1) Huecos de fondo: marcan visualmente las 9 celdas.
        for i in range(N * N):
            x, y = self.cell_xy(i)
            self._rounded_rect(x, y, x + TILE, y + TILE, 16,
                               fill=COL_SLOT, outline="")

        # 2) Fichas estáticas.
        for i, value in enumerate(self.tiles):
            if value == 0:
                continue                     # El hueco no se dibuja
            if moving and value == moving[0]:
                continue                     # Esta se pinta aparte (animada)
            x, y = self.cell_xy(i)
            self._draw_tile(value, x, y, correct=(value == GOAL[i]))

        # 3) Ficha en movimiento, encima del resto.
        if moving:
            self._draw_tile(moving[0], moving[1], moving[2], correct=False)

    def _draw_tile(self, value, x, y, correct):
        """Dibuja una ficha individual (sombra, cuerpo y número).

        Args:
            value (int): Número que se muestra en la ficha (1-8).
            x, y (int | float): Esquina superior izquierda de la ficha.
            correct (bool): ``True`` si la ficha está en su posición final.
                Solo se colorea de verde cuando además la partida está
                resuelta (``self.locked``), como efecto de victoria.
        """
        fill = COL_TILE_OK if (correct and self.locked) else COL_TILE
        # Sombra: mismo rectángulo desplazado 3 px hacia abajo.
        self._rounded_rect(x, y + 3, x + TILE, y + TILE + 3, 16,
                           fill="#12162a", outline="")
        # Cuerpo de la ficha.
        self._rounded_rect(x, y, x + TILE, y + TILE, 16,
                           fill=fill, outline=COL_TILE_BORDER, width=2)
        # Número centrado.
        self.canvas.create_text(x + TILE / 2, y + TILE / 2, text=str(value),
                                font=FONT_TILE, fill=COL_TEXT)

    # -------------------------------------------------------------------------
    # Lógica de la partida
    # -------------------------------------------------------------------------
    def new_game(self):
        """Inicia una partida nueva con una mezcla resoluble.

        Puede llamarse en cualquier momento (también a mitad de una
        animación): se cancela la animación pendiente, se reinician los
        indicadores de estado y el contador, y se redibuja el tablero.
        """
        # Si hay un fotograma de animación programado, se cancela.
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.animating = False
        self.locked = False
        self.tiles = generate_shuffled()
        self.moves = 0
        self.update_score()
        self.draw()

    def try_move(self, index):
        """Intenta mover la ficha situada en ``index`` hacia el hueco.

        El movimiento solo se realiza si no hay una animación en curso, la
        partida no está terminada y la ficha es adyacente al hueco (misma
        fila y columnas contiguas, o misma columna y filas contiguas).
        Si no se cumple alguna condición, no ocurre nada.

        Args:
            index (int): Índice (en la lista plana) de la ficha pulsada.
        """
        if self.animating or self.locked:
            return

        blank = self.tiles.index(0)           # Posición actual del hueco
        r1, c1 = divmod(index, N)
        r2, c2 = divmod(blank, N)
        # Adyacencia: distancia de Manhattan igual a 1. Esto excluye a la
        # propia celda del hueco (distancia 0) y a las diagonales (distancia 2).
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return

        self.animate_slide(index, blank)

    def animate_slide(self, src, dst):
        """Anima el deslizamiento de una ficha desde ``src`` hasta ``dst``.

        La posición intermedia se calcula por interpolación lineal con una
        función de suavizado, y los fotogramas se encadenan con
        ``root.after`` para no bloquear la interfaz. Al terminar se llama a
        ``finish_move`` para actualizar el estado real del tablero.

        Args:
            src (int): Celda de origen (donde está la ficha).
            dst (int): Celda de destino (donde está el hueco).
        """
        self.animating = True                 # Bloquea nuevas entradas
        value = self.tiles[src]
        x0, y0 = self.cell_xy(src)
        x1, y1 = self.cell_xy(dst)

        def step(k):
            """Dibuja el fotograma ``k`` y programa el siguiente."""
            t = k / ANIM_STEPS                # Progreso lineal: 0.0 -> 1.0
            t = t * t * (3 - 2 * t)           # "Smoothstep": arranca y frena suave
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            self.draw(moving=(value, x, y))
            if k < ANIM_STEPS:
                self._after_id = self.root.after(ANIM_DELAY, step, k + 1)
            else:
                self._after_id = None
                self.finish_move(src, dst)

        step(0)

    def finish_move(self, src, dst):
        """Consolida un movimiento una vez terminada su animación.

        Intercambia la ficha y el hueco en la lista de estado, incrementa el
        contador y comprueba si se ha ganado.

        Args:
            src (int): Celda de origen de la ficha.
            dst (int): Celda de destino (antiguo hueco).
        """
        # La ficha pasa al destino y el origen se convierte en el hueco.
        self.tiles[dst], self.tiles[src] = self.tiles[src], 0
        self.moves += 1
        self.animating = False
        self.update_score()

        if is_solved(self.tiles):
            self.locked = True                # Impide más movimientos
            self.draw()                       # Repinta con fichas en verde
            # Pequeña espera para que se vea el tablero resuelto antes de
            # que aparezca el cuadro de diálogo (que es bloqueante).
            self.root.after(150, self.show_victory)
        else:
            self.draw()

    def show_victory(self):
        """Muestra el mensaje de felicitación con el total de movimientos."""
        messagebox.showinfo(
            "¡Felicidades!",
            f"¡Has resuelto el rompecabezas!\n\n"
            f"Total de movimientos: {self.moves}")

    # -------------------------------------------------------------------------
    # Manejadores de eventos
    # -------------------------------------------------------------------------
    def on_click(self, event):
        """Gestiona un clic del ratón sobre el lienzo.

        Traduce las coordenadas del clic a una celda del tablero y delega en
        ``try_move``. Los clics en los márgenes o en las separaciones entre
        fichas se ignoran.

        Args:
            event (tk.Event): Evento de ratón con las coordenadas ``x`` e ``y``
                relativas al lienzo.
        """
        # Cada celda ocupa (TILE + GAP) píxeles contando su separación.
        col = (event.x - PAD) // (TILE + GAP)
        row = (event.y - PAD) // (TILE + GAP)
        if not (0 <= col < N and 0 <= row < N):
            return                            # Clic fuera del tablero

        # Si el resto de la división es >= TILE, el clic cayó en la
        # separación entre dos fichas y no sobre una ficha.
        if ((event.x - PAD) % (TILE + GAP) >= TILE or
                (event.y - PAD) % (TILE + GAP) >= TILE):
            return

        self.try_move(row * N + col)

    def on_key(self, event):
        """Gestiona las teclas de flecha.

        La flecha indica la dirección en la que se desliza una ficha, de modo
        que la ficha afectada es la situada en el lado *opuesto* del hueco.
        Por ejemplo, "Arriba" mueve hacia arriba la ficha que está justo
        debajo del hueco. Si no hay ficha en ese lado (el hueco está en el
        borde), la tecla no hace nada.

        Args:
            event (tk.Event): Evento de teclado; ``event.keysym`` contiene
                el nombre de la tecla ("Up", "Down", "Left" o "Right").
        """
        blank = self.tiles.index(0)
        row, col = divmod(blank, N)

        if event.keysym == "Up" and row < N - 1:
            self.try_move(blank + N)          # Ficha de debajo del hueco
        elif event.keysym == "Down" and row > 0:
            self.try_move(blank - N)          # Ficha de encima del hueco
        elif event.keysym == "Left" and col < N - 1:
            self.try_move(blank + 1)          # Ficha a la derecha del hueco
        elif event.keysym == "Right" and col > 0:
            self.try_move(blank - 1)          # Ficha a la izquierda del hueco


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def main():
    """Crea la ventana principal, instancia el juego y arranca el bucle de
    eventos de tkinter."""
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()