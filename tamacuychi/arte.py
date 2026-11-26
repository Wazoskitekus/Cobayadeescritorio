"""Pixel art de la cobaya, generado por código.

No depende de Qt: cada sprite es una lista de fotogramas y cada fotograma una
lista de filas de caracteres (una letra por color, como en cobaya_mapa.py del
firmware). Las figuras se rellenan con elipses sin suavizado y luego se les pone
contorno, así salen nítidas a cualquier escala entera.

Si en la carpeta sprites/ hay un PNG con el mismo nombre (por ejemplo
cobaya_idle@2.png), se usa ese en lugar del generado (ver sprites.py).
"""


PALETA = {
    "K": (59, 36, 24),      # contorno
    "O": (234, 146, 64),    # naranja
    "o": (198, 108, 44),    # naranja sombra
    "C": (252, 240, 214),   # crema
    "c": (228, 204, 166),   # crema sombra
    "B": (88, 54, 36),      # marrón oscuro
    "b": (62, 38, 26),      # marrón sombra
    "P": (246, 168, 170),   # rosa
    "p": (214, 118, 124),   # rosa oscuro
    "E": (24, 16, 12),      # ojo
    "W": (255, 255, 255),   # brillo
    "R": (250, 132, 146),   # rubor
    "T": (118, 196, 244),   # lágrima
    "H": (238, 200, 96),    # heno
    "h": (204, 156, 62),    # heno sombra
    "j": (150, 106, 40),    # heno contorno
    "G": (126, 204, 92),    # lechuga
    "g": (70, 146, 58),     # lechuga sombra / nervio
    "l": (196, 238, 152),   # lechuga clara
    "d": (40, 74, 34),      # contorno lechuga
    "Y": (255, 232, 110),   # destello
    "y": (255, 255, 220),   # destello centro
    "M": (70, 42, 28),      # caca
    "m": (112, 74, 50),     # caca brillo
    "Z": (240, 244, 255),   # zetas
    "z": (120, 130, 170),   # contorno zetas
    "r": (232, 64, 96),     # corazón
    "q": (255, 150, 170),   # corazón brillo
    "Q": (120, 24, 48),     # corazón contorno
}

SOMBRA = {"O": "o", "C": "c", "B": "b", "P": "p", "H": "h", "G": "g"}


class Lienzo:
    def __init__(self, ancho, alto):
        self.w, self.h = ancho, alto
        self.px = [["."] * ancho for _ in range(alto)]

    def copia(self):
        n = Lienzo(self.w, self.h)
        n.px = [fila[:] for fila in self.px]
        return n

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return "."

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def elipse(self, cx, cy, rx, ry, c, si=None):
        for y in range(self.h):
            for x in range(self.w):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0 and (si is None or si(x, y, self.px[y][x])):
                    self.px[y][x] = c

    def rect(self, x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.set(x, y, c)

    def recolorear(self, fn):
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c != ".":
                    n = fn(x, y, c)
                    if n:
                        self.px[y][x] = n

    def sombra_inferior(self, filas=2):
        """Oscurece los píxeles que están a 'filas' o menos del borde inferior."""
        orig = [f[:] for f in self.px]
        for y in range(self.h):
            for x in range(self.w):
                c = orig[y][x]
                if c in SOMBRA:
                    for k in range(1, filas + 1):
                        if y + k >= self.h or orig[y + k][x] == ".":
                            self.px[y][x] = SOMBRA[c]
                            break

    def contorno(self, color="K", diagonales=False):
        orig = [f[:] for f in self.px]
        vec = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonales:
            vec += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for y in range(self.h):
            for x in range(self.w):
                if orig[y][x] != ".":
                    continue
                for dx, dy in vec:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h and orig[yy][xx] not in ".":
                        self.px[y][x] = color
                        break

    def sello(self, x0, y0, filas, transparente="."):
        for dy, fila in enumerate(filas):
            for dx, c in enumerate(fila):
                if c != transparente:
                    self.set(x0 + dx, y0 + dy, c)

    def espejo(self):
        n = Lienzo(self.w, self.h)
        n.px = [list(reversed(f)) for f in self.px]
        return n

    def filas(self):
        return ["".join(f) for f in self.px]


def espejo_filas(filas):
    return [f[::-1] for f in filas]


# ---------------------------------------------------------------------------
# Cobaya de frente (33 x 30)
# ---------------------------------------------------------------------------
FW, FH = 33, 30
CX = 16.5

OJO = [".EE.", "EWEE", "EEEE", ".EE."]
OJO_MIRA = [".EE.", "EEWE", "EEEE", ".EE."]
OJO_CERRADO = ["....", "....", "EEEE", "...."]
OJO_FELIZ = ["....", ".EE.", "E..E", "...."]
OJO_TRISTE = ["....", ".EE.", "EWEE", ".EE."]
OJO_APRETADO_I = ["E...", ".EE.", "...E", "...."]   # >
OJO_APRETADO_D = ["...E", ".EE.", "E...", "...."]   # <
OJO_I = (7, 9)    # esquina superior izquierda del ojo izquierdo
OJO_D = (22, 9)


def _cuerpo_frente(orejas_arriba=False, aplastar=0):
    c = Lienzo(FW, FH)
    # orejas (detrás de la cabeza)
    ey = 4.2 if not orejas_arriba else 2.8
    for ox, col in ((6.2, "O"), (26.8, "B")):
        c.elipse(ox, ey, 3.6, 2.7 if not orejas_arriba else 3.2, col)
        c.elipse(ox + (-0.6 if ox < CX else 0.6), ey + 0.6, 2.2, 1.5, "P")
    # cabeza y cuerpo
    c.elipse(CX, 11.5 + aplastar * 0.5, 11.5, 8.6, "O")
    c.elipse(CX, 18.8 + aplastar * 0.3, 15.2 + aplastar * 0.6, 9.4 - aplastar * 0.4, "O")

    def color(x, y, col):
        if col != "O":
            return None
        px, py = x + 0.5, y + 0.5
        # morro y pecho crema
        if ((px - CX) / 5.4) ** 2 + ((py - 15.4) / 3.6) ** 2 <= 1:
            return "C"
        if ((px - CX) / 8.5) ** 2 + ((py - 24.0) / 6.0) ** 2 <= 1:
            return "C"
        # lista crema entre los ojos
        if py < 14 and abs(px - CX) <= 1.6 + max(0.0, py - 4) * 0.12:
            return "C"
        # mancha marrón: lado derecho de la cara y flanco derecho
        if px > 18.5 and py < 16.5 and py > 2:
            return "B"
        if px > 23.5 and py >= 16.5:
            return "B"
        return None

    c.recolorear(color)
    c.sombra_inferior(2)
    # patitas
    for px in (10.5, 22.5):
        c.elipse(px, 27.6 + aplastar * 0.3, 2.3, 1.3, "P")
    c.contorno("K")
    return c


def _cara(c, ojos="normal", boca="w", rubor=False, lagrimas=0, cejas=False):
    ojo_i = ojo_d = OJO
    if ojos == "cerrado":
        ojo_i = ojo_d = OJO_CERRADO
    elif ojos == "feliz":
        ojo_i = ojo_d = OJO_FELIZ
    elif ojos == "triste":
        ojo_i = ojo_d = OJO_TRISTE
    elif ojos == "apretado":
        ojo_i, ojo_d = OJO_APRETADO_I, OJO_APRETADO_D
    elif ojos == "mira":
        ojo_i = ojo_d = OJO_MIRA
    c.sello(*OJO_I, ojo_i)
    c.sello(*OJO_D, ojo_d)
    if cejas:
        c.sello(OJO_I[0], OJO_I[1] - 2, ["..EE", "EE.."])
        c.sello(OJO_D[0], OJO_D[1] - 2, ["EE..", "..EE"])
    if rubor:
        c.sello(OJO_I[0] - 1, OJO_I[1] + 5, ["RRR"])
        c.sello(OJO_D[0] + 2, OJO_D[1] + 5, ["RRR"])
    if lagrimas:
        y = OJO_I[1] + 3 + lagrimas
        c.sello(OJO_I[0] + 1, y, ["T", "T"])
        c.sello(OJO_D[0] + 2, y, ["T", "T"])
    # nariz
    c.sello(15, 13, ["pPp", ".p."])
    if boca == "w":
        c.sello(14, 15, ["K.K.K", ".K.K."])
    elif boca == "abierta":
        c.sello(15, 15, ["KKK", "KpK", ".K."])
    elif boca == "muy_abierta":
        c.sello(14, 15, [".KKK.", "KbbbK", "KpppK", ".KKK."])
    elif boca == "masticar":
        c.sello(14, 15, ["KK.KK", ".KKK."])
    elif boca == "triste":
        c.sello(14, 16, [".KKK.", "K...K"])
    elif boca == "bostezo":
        c.sello(14, 14, [".KKK.", "KbbbK", "KbbbK", "KpppK", ".KKK."])
    return c


def frente(ojos="normal", boca="w", rubor=False, lagrimas=0, cejas=False,
           orejas_arriba=False, aplastar=0):
    c = _cuerpo_frente(orejas_arriba, aplastar)
    _cara(c, ojos, boca, rubor, lagrimas, cejas)
    return c.filas()


# ---------------------------------------------------------------------------
# Cobaya de espaldas
# ---------------------------------------------------------------------------
def espalda(paso=0):
    c = Lienzo(FW, FH)
    for ox, col in ((6.2, "B"), (26.8, "O")):
        c.elipse(ox, 4.2, 3.6, 2.7, col)
    c.elipse(CX, 11.5, 11.5, 8.6, "O")
    c.elipse(CX, 18.8, 15.2, 9.4, "O")

    def color(x, y, col):
        px, py = x + 0.5, y + 0.5
        if col != "O":
            return None
        if ((px - CX) / 9.5) ** 2 + ((py - 24.5) / 6.0) ** 2 <= 1:
            return "C"
        if px < 14.5 and py < 16:
            return "B"
        if px < 9 and py >= 16:
            return "B"
        return None

    c.recolorear(color)
    c.sombra_inferior(2)
    # patitas traseras alternas
    dy = (0, -1) if paso == 0 else (-1, 0)
    c.elipse(10.5, 27.6 + dy[0], 2.4, 1.3, "P")
    c.elipse(22.5, 27.6 + dy[1], 2.4, 1.3, "P")
    c.contorno("K")
    # rayita del culete
    c.sello(16, 23, ["c", "c", "c"])
    return c.filas()


# ---------------------------------------------------------------------------
# Cobaya de perfil, mirando a la derecha (38 x 26)
# ---------------------------------------------------------------------------
PW, PH = 38, 26


def perfil(paso=0, ojos="normal", boca="cerrada", orejas_arriba=False, estirar=0):
    c = Lienzo(PW, PH)
    # patas (detrás del cuerpo): paso 0 quieta, 1 y 2 alternas
    pies = {0: (0, 0, 0, 0), 1: (-1, 1, 1, -1), 2: (1, -1, -1, 1)}[paso]
    for (x, d) in zip((8.5, 13.0, 25.0, 29.0), pies):
        c.elipse(x + d * 0.8, 23.4 - (abs(d) * 0.4 if d < 0 else 0), 2.2, 1.4, "P")
    # oreja
    oy = 6.0 if not orejas_arriba else 4.6
    c.elipse(24.0, oy, 3.4, 2.4, "B")
    c.elipse(23.4, oy + 0.4, 2.0, 1.4, "P")
    # cuerpo, cabeza y morro
    bob = -0.5 if paso else 0
    c.elipse(16.0 - estirar * 0.5, 15.2 + bob, 14.0 + estirar, 8.2 - estirar * 0.3, "O")
    c.elipse(27.0 + estirar, 13.2 + bob, 7.6, 7.0, "O")
    c.elipse(32.4 + estirar, 15.0 + bob, 3.4, 3.4, "O")

    def color(x, y, col):
        if col != "O":
            return None
        px, py = x + 0.5, y + 0.5
        hx = 27.0 + estirar
        # morro crema
        if ((px - (32.6 + estirar)) / 3.6) ** 2 + ((py - 15.8) / 3.0) ** 2 <= 1:
            return "C"
        # lista crema en la frente
        if py < 10.5 and px > hx + 2.0 and px < hx + 4.4:
            return "C"
        # cabeza marrón
        if px > hx - 6.0 and py < 18:
            return "B"
        # banda crema en el lomo y pecho
        if px > 15.5 - estirar * 0.5 and px < 21.5:
            return "C"
        if px >= 21.5 and py > 17:
            return "C"
        return None

    c.recolorear(color)
    c.sombra_inferior(2)
    c.contorno("K")
    ex, ey = int(28 + estirar), 10 + (0 if not paso else 0)
    if ojos == "normal":
        c.sello(ex, ey, ["EE", "WE", "EE"])
    elif ojos == "cerrado":
        c.sello(ex, ey, ["..", "..", "EE"])
    elif ojos == "feliz":
        c.sello(ex, ey, ["..", "EE", "E."])
    nx = int(35 + estirar)
    c.sello(nx, 14, ["p"])
    if boca == "abierta":
        c.sello(nx - 2, 17, ["KK", "pK"])
    elif boca == "masticar":
        c.sello(nx - 2, 17, ["KK"])
    else:
        c.sello(nx - 1, 16, ["K"])
    return c.filas()


# ---------------------------------------------------------------------------
# Objetos
# ---------------------------------------------------------------------------
def heno(fase=0):
    """fase 0: vacío; 1: con orejas asomando; 2: orejas y respirando."""
    w, h = 50, 30
    sube = 1 if fase == 2 else 0
    orejas = Lienzo(w, h)
    if fase:
        oy = 5.0 - sube
        orejas.elipse(19.0, oy, 3.2, 3.0, "O")
        orejas.elipse(31.0, oy, 3.2, 3.0, "B")
        orejas.elipse(19.0, oy + 0.5, 1.8, 1.6, "P")
        orejas.elipse(31.0, oy + 0.5, 1.8, 1.6, "P")
        orejas.contorno("K")
    c = Lienzo(w, h)
    c.elipse(25, 29.5, 23.5, 22.0 + sube, "H")
    for x in range(w):            # cortar por debajo del suelo
        c.set(x, 29, ".")
    c.sombra_inferior(2)
    c.contorno("j")
    # briznas
    rnd = _rng(7)
    for _ in range(80):
        x = rnd(2, w - 3)
        y = rnd(9, h - 3)
        if c.get(x, y) in "Hh" and c.get(x + 1, y + 1) in "Hh":
            c.set(x, y, "h")
            c.set(x + (1 if rnd(0, 1) else -1), y + 1, "h")
    for _ in range(16):
        x = rnd(4, w - 5)
        y = rnd(9, h - 4)
        if c.get(x, y) == "H":
            c.set(x, y, "j")
    # briznas sueltas arriba
    top = 8 - sube
    for x, dy in ((13, 2), (24, 0), (37, 2)):
        c.set(x, top + dy, "j")
        c.set(x + 1, top + dy - 1, "j")
    # componer: el heno tapa la parte de abajo de las orejas
    for y in range(h):
        for x in range(w):
            if c.px[y][x] == "." and orejas.px[y][x] != ".":
                c.px[y][x] = orejas.px[y][x]
    return c.filas()


def lechuga(mordiscos=0):
    w, h = 18, 18
    c = Lienzo(w, h)
    c.elipse(9, 8.5, 8.2, 7.8, "G")
    c.elipse(9, 9.5, 5.5, 5.5, "l", si=lambda x, y, k: k == "G")
    c.elipse(9, 9.5, 3.5, 3.5, "G", si=lambda x, y, k: k == "l")
    # bordes ondulados
    for x, y in ((1, 5), (2, 2), (5, 1), (13, 1), (16, 3), (16, 11), (14, 15), (3, 14)):
        c.set(x, y, ".")
    # tallo
    c.rect(8, 15, 2, 3, "l")
    # mordiscos desde la derecha
    for i in range(mordiscos):
        cx, cy = ((15.5, 6.0), (14.0, 11.5), (11.0, 3.0))[i]
        c.elipse(cx, cy, 3.6, 3.4, ".")
    c.sombra_inferior(1)
    c.contorno("d")
    # nervios
    for y in range(4, 15):
        if c.get(9, y) in "Gl":
            c.set(9, y, "g")
    for (x, y) in ((7, 7), (6, 6), (11, 8), (12, 7), (7, 11), (6, 10), (11, 11), (12, 10)):
        if c.get(x, y) in "Gl":
            c.set(x, y, "g")
    return c.filas()


CACA = [
    "..KKKK...KKKK..",
    ".KMMMMK.KmMMMK.",
    "KmMMMMMKMMMMMMK",
    "KMMMMMMKMMMMMMK",
    ".KMMMMK.KMMMMK.",
    "..KKKK...KKKK..",
]

CORAZON = [
    ".QQ.QQ.",
    "QqrQrrQ",
    "QrrrrrQ",
    ".QrrrQ.",
    "..QrQ..",
    "...Q...",
]

DESTELLO = [
    [
        ".....",
        "..Y..",
        ".YyY.",
        "..Y..",
        ".....",
    ],
    [
        "..Y..",
        "..Y..",
        "YYyYY",
        "..Y..",
        "..Y..",
    ],
    [
        "Y...Y",
        ".Y.Y.",
        "..y..",
        ".Y.Y.",
        "Y...Y",
    ],
]

ZETA = [
    "zzzzzz",
    "zZZZZz",
    "zzzZzz",
    ".zZzz.",
    "zZzzzz",
    "zZZZZz",
    "zzzzzz",
]

MIGA = ["Gg", "gG"]


def _rng(semilla):
    estado = [semilla]

    def r(a, b):
        estado[0] = (estado[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return a + estado[0] % (b - a + 1)
    return r


# ---------------------------------------------------------------------------
# Catálogo: nombre -> lista de fotogramas
# ---------------------------------------------------------------------------
def catalogo():
    s = {}
    s["cobaya_idle"] = [frente(), frente(ojos="cerrado")]
    s["cobaya_mira"] = [frente(ojos="mira")]
    s["cobaya_feliz"] = [frente(ojos="feliz", rubor=True), frente(ojos="feliz", boca="abierta", rubor=True)]
    s["cobaya_triste"] = [frente(ojos="triste", boca="triste", cejas=True, lagrimas=1),
                          frente(ojos="triste", boca="triste", cejas=True, lagrimas=3)]
    s["cobaya_comer"] = [frente(boca="abierta"), frente(ojos="feliz", boca="masticar")]
    s["cobaya_cui"] = [frente(boca="muy_abierta"), frente(boca="muy_abierta", orejas_arriba=True)]
    s["cobaya_espalda"] = [espalda(0), espalda(1)]
    s["cobaya_estirar"] = [perfil(estirar=2, ojos="cerrado"), perfil(estirar=3, ojos="cerrado", boca="abierta")]
    s["cobaya_bostezo"] = [frente(ojos="apretado", boca="bostezo"), frente(ojos="apretado", boca="bostezo", orejas_arriba=True)]
    s["cobaya_colgando"] = [frente(ojos="normal", boca="abierta", orejas_arriba=True),
                            frente(ojos="mira", boca="abierta", orejas_arriba=True)]
    s["cobaya_aterriza"] = [frente(ojos="feliz", aplastar=2)]
    s["cobaya_perfil"] = [perfil(0), perfil(0, ojos="cerrado")]
    s["cobaya_andar"] = [perfil(1), perfil(0), perfil(2), perfil(0)]
    s["cobaya_perfil_feliz"] = [perfil(0, ojos="feliz", boca="abierta")]
    s["cobaya_perfil_comer"] = [perfil(0, boca="abierta"), perfil(0, ojos="feliz", boca="masticar")]
    s["heno"] = [heno(0), heno(1), heno(2)]
    s["lechuga"] = [lechuga(i) for i in range(4)]
    s["caca"] = [CACA]
    s["corazon"] = [CORAZON]
    s["destello"] = DESTELLO
    s["zeta"] = [ZETA]
    s["miga"] = [MIGA]
    return s


# ---------------------------------------------------------------------------
# Utilidades para exportar (sin dependencias)
# ---------------------------------------------------------------------------
def a_rgba(filas, escala=1):
    """Devuelve (ancho, alto, bytes RGBA)."""
    h = len(filas)
    w = max(len(f) for f in filas)
    out = bytearray()
    for f in filas:
        linea = bytearray()
        for x in range(w):
            ch = f[x] if x < len(f) else "."
            if ch == "." or ch not in PALETA:
                px = b"\x00\x00\x00\x00"
            else:
                r, g, b = PALETA[ch]
                px = bytes((r, g, b, 255))
            linea += px * escala
        out += bytes(linea) * escala
    return w * escala, h * escala, bytes(out)


def guardar_png(ruta, ancho, alto, rgba):
    import struct
    import zlib

    def trozo(tipo, datos):
        c = struct.pack(">I", len(datos)) + tipo + datos
        return c + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)

    filas = b"".join(b"\x00" + rgba[y * ancho * 4:(y + 1) * ancho * 4] for y in range(alto))
    png = b"\x89PNG\r\n\x1a\n"
    png += trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
    png += trozo(b"IDAT", zlib.compress(filas, 9))
    png += trozo(b"IEND", b"")
    with open(ruta, "wb") as f:
        f.write(png)


def hoja(fotogramas, separacion=0):
    """Une fotogramas en horizontal (formato nombre@N.png del firmware)."""
    h = max(len(f) for f in fotogramas)
    w = max(len(r) for f in fotogramas for r in f)
    filas = []
    for y in range(h):
        linea = ""
        for f in fotogramas:
            r = f[y] if y < len(f) else ""
            linea += r.ljust(w, ".") + "." * separacion
        filas.append(linea)
    return filas
