"""La cobaya en el escritorio: una ventana transparente sin marco que se mueve.

Interacciones:
- Clic sobre ella: popcorning (saltos por la pantalla girándose en el aire).
- Pasar el ratón por encima de un lado a otro: caricia (corazones).
- Arrastrar con el botón pulsado: la coges; al soltar cae (y se puede lanzar).
- Soltar archivos encima: se los come (van a la papelera).
- Clic derecho: menú.
"""

import math
import os
import random
import sys
import time

from PySide6.QtCore import QFileInfo, QPoint, QRect, Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QImage,
                           QPainter, QPixmap, QRegion)
from PySide6.QtWidgets import QFileIconProvider, QWidget

from . import papelera
from .cacas import Caca
from .mascota import MAX_CACAS
from .sprites import tam

# Tamaño de la ventana en píxeles de arte
WA, HA = 64, 62
FONDO = 5           # cuánto más arriba está el heno ("al fondo"), en píxeles de arte

REPOSO, ANDAR, COMIENDO, FELIZ, CUI, POPCORN = "reposo", "andar", "comiendo", "feliz", "cui", "popcorn"
COGIDA, CAYENDO, ATERRIZA, NEGAR = "cogida", "cayendo", "aterriza", "negar"
YENDO_A_DORMIR, DURMIENDO, DESPERTANDO = "yendo_a_dormir", "durmiendo", "despertando"

OCUPADA = (COMIENDO, POPCORN, COGIDA, CAYENDO, YENDO_A_DORMIR, DURMIENDO, DESPERTANDO, NEGAR)

COL_SACIEDAD = QColor(240, 140, 50)
COL_FELICIDAD = QColor(250, 120, 170)
COL_ENERGIA = QColor(250, 215, 70)
COL_ALERTA = QColor(230, 40, 40)
COL_CONTORNO = QColor(59, 36, 24)

MENSAJES_RECHAZO = {
    "carpeta": "¡Carpetas no!",
    "grande": "¡Es enorme!",
    "sin_papelera": "De ahí no como",
    "no_existe": "¿Dónde está?",
    "falta_send2trash": "Falta Send2Trash",
}


class Cobaya(QWidget):
    def __init__(self, mascota, sprites, sonidos):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                         | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setWindowTitle("Tamacuychi")

        self.m, self.spr, self.snd = mascota, sprites, sonidos
        self.snd.silencio = self.m.silencio
        self.e = self.m.escala
        self.setFixedSize(WA * self.e, HA * self.e)
        self.menu_fn = None            # lo pone app.py
        self._mascara_x11 = QGuiApplication.platformName() == "xcb"
        self._ultima_mascara = None

        # posición del centro de los pies, en coordenadas de pantalla
        self.px, self.py = self._posicion_inicial()
        self.vx = self.vy = 0.0
        self.dir = 1

        self.estado = REPOSO
        self.t_estado = 0.0
        self._dur = 3.0
        self._objetivo = self.px
        self._parpadeo = 0.0
        self._prox_parpadeo = time.monotonic() + 2
        self._mirando = 0.0

        self._particulas = []
        self._bocadillo = None
        self._barras_hasta = 0.0
        self._hover = False
        self._oliendo = False

        self._cola = []                # archivos pendientes de comer
        self._comida = None
        self._saltos = []
        self._salto = None
        self._cogida = None
        self._raton = None             # pulsación en curso
        self._caricia = []             # cambios de dirección del ratón
        self._ultimo_x_raton = None
        self._dir_raton = 0
        self._heno_alpha = 0.0
        self._prox_cui = time.monotonic() + random.uniform(20, 60)
        self._prox_pedir = time.monotonic() + 5
        self._prox_zeta = 0.0
        self._hoja = None

        self.cacas = []
        for x, y in list(self.m.cacas):
            self._crear_caca_ventana(x, y)

        if self.m.durmiendo:
            self.estado = DURMIENDO
            self._heno_alpha = 1.0

        self._t_ant = time.monotonic()
        self._t_stats = 0.0
        self._t_guardar = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        self._colocar()

    # ------------------------------------------------------------------
    # Pantalla y posición
    # ------------------------------------------------------------------
    def _pantalla(self, x=None, y=None):
        x = self.px if x is None else x
        y = self.py - 10 if y is None else y
        s = QGuiApplication.screenAt(QPoint(int(x), int(y)))
        if s is None:
            # la más cercana
            mejor, dmin = None, None
            for sc in QGuiApplication.screens():
                g = sc.availableGeometry()
                cx = min(max(x, g.left()), g.right())
                cy = min(max(y, g.top()), g.bottom())
                d = (cx - x) ** 2 + (cy - y) ** 2
                if dmin is None or d < dmin:
                    mejor, dmin = sc, d
            s = mejor or QGuiApplication.primaryScreen()
        return s.availableGeometry()

    def _suelo(self, x=None):
        return self._pantalla(x).bottom() + 1

    def _limites_x(self, x=None):
        g = self._pantalla(x)
        margen = 20 * self.e
        return g.left() + margen, g.right() - margen

    def _posicion_inicial(self):
        if self.m.posicion:
            x, y = self.m.posicion
            s = QGuiApplication.screenAt(QPoint(int(x), int(y) - 10))
            if s is not None:
                g = s.availableGeometry()
                return float(x), float(g.bottom() + 1)
        g = QGuiApplication.primaryScreen().availableGeometry()
        return float(g.left() + g.width() * 0.75), float(g.bottom() + 1)

    def _colocar(self):
        self.move(int(round(self.px - self.width() / 2)), int(round(self.py - self.height())))

    def cambiar_escala(self, e):
        self.e = self.m.escala = e
        self.setFixedSize(WA * e, HA * e)
        self.px = min(max(self.px, self._limites_x()[0]), self._limites_x()[1])
        self._colocar()
        for c in list(self.cacas):
            x, y = c.pos_suelo
            c.close()
            self.cacas.remove(c)
            self._crear_caca_ventana(x, y)
        self.m.guardar()

    def llamar(self):
        """Aparece cayendo desde arriba en la pantalla principal."""
        if self.estado in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO):
            return
        g = QGuiApplication.primaryScreen().availableGeometry()
        self.px = g.center().x()
        self.py = g.top() + self.height()
        self.vx, self.vy = random.uniform(-150, 150), 0.0
        self._cambiar(CAYENDO)
        self.show()
        self.raise_()

    # ------------------------------------------------------------------
    # Bucle
    # ------------------------------------------------------------------
    def _cambiar(self, estado, dur=None):
        self.estado = estado
        self.t_estado = 0.0
        if dur is not None:
            self._dur = dur

    def decir(self, texto=None, icono=None, dur=2.0):
        self._bocadillo = {"texto": texto, "icono": icono, "hasta": time.monotonic() + dur}

    def _tick(self):
        ahora = time.monotonic()
        dt = min(0.05, ahora - self._t_ant)
        self._t_ant = ahora
        self.t_estado += dt

        # estadísticas (cada segundo)
        self._t_stats += dt
        if self._t_stats >= 1.0:
            self._t_stats = 0.0
            for ev in self.m.avanzar():
                if ev == "caca":
                    self.hacer_caca()
                elif ev == "despierta" and self.estado == DURMIENDO:
                    self.despertar()
        if ahora - self._t_guardar > 60:
            self._t_guardar = ahora
            self.m.posicion = [self.px, self.py]
            self.m.guardar()

        self._comportamiento(ahora)
        actualizar = getattr(self, "_act_" + self.estado)
        actualizar(dt, ahora)
        self._particulas_avanzar(dt)
        if self._bocadillo and ahora > self._bocadillo["hasta"]:
            self._bocadillo = None
        for c in list(self.cacas):
            c.avanzar()

        rapido = self.estado in (POPCORN, CAYENDO, COGIDA, ANDAR) or bool(self._particulas)
        self.timer.setInterval(16 if rapido else 33)
        self._colocar()
        self.update()

    def _comportamiento(self, ahora):
        """Cosas que pasan solas: cui, pedir comida, cola de archivos."""
        libre = self.estado in (REPOSO, ANDAR, FELIZ)
        if self._cola and libre:
            self._siguiente_archivo()
            return
        if ahora >= self._prox_cui:
            hambre = self.m.hambrienta
            self._prox_cui = ahora + (random.uniform(15, 35) if hambre else random.uniform(60, 180))
            if self.estado in (REPOSO, ANDAR):
                self.cui()
            elif self.estado == POPCORN:
                self.cui(solo_sonido=True)
        if self.m.hambrienta and self.estado == REPOSO and ahora >= self._prox_pedir and not self._bocadillo:
            self._prox_pedir = ahora + 9
            self.decir(icono="lechuga", dur=3.5)

    # --- estados -------------------------------------------------------
    def _act_reposo(self, dt, ahora):
        if self._oliendo:
            return
        if ahora >= self._prox_parpadeo:
            self._parpadeo = ahora + 0.15
            self._prox_parpadeo = ahora + random.uniform(2.0, 5.0)
        if self.t_estado < self._dur:
            return
        # decidir qué hacer
        if self.m.cansada and not self.m.durmiendo:
            self.decir("zzz...", dur=1.5)
            self.dormir()
            return
        r = random.random()
        feliz = self.m.felicidad > 85 and self.m.energia > 50
        if feliz and r < 0.05:
            self.popcorn()
        elif r < (0.35 if self.m.descuidada else 0.65):
            self.andar()
        elif r < 0.8:
            self._mirando = ahora + random.uniform(0.8, 2.0)
            self._cambiar(REPOSO, random.uniform(2, 4))
        else:
            self._cambiar(REPOSO, random.uniform(3, 8))

    def andar(self, destino=None):
        lo, hi = self._limites_x()
        if destino is None:
            dist = random.uniform(60, 400) * self.e / 4
            destino = self.px + random.choice((-1, 1)) * dist
        destino = min(max(destino, lo), hi)
        if abs(destino - self.px) < 8:
            self._cambiar(REPOSO, 2)
            return
        self._objetivo = destino
        self.dir = 1 if destino > self.px else -1
        self._cambiar(ANDAR)

    def _act_andar(self, dt, ahora):
        vel = 16 * self.e * (0.6 if self.m.descuidada else 1.0)
        self.px += self.dir * vel * dt
        if (self.px - self._objetivo) * self.dir >= 0:
            self.px = self._objetivo
            self._cambiar(REPOSO, random.uniform(2, 7))
        self.py = self._suelo()

    def _act_feliz(self, dt, ahora):
        if self.t_estado < 1.0 and int(self.t_estado / 0.25) != int((self.t_estado - dt) / 0.25):
            self._corazon()
        if self.t_estado >= self._dur:
            self._cambiar(REPOSO, random.uniform(2, 5))

    def _act_cui(self, dt, ahora):
        if self.t_estado >= self._dur:
            self._cambiar(REPOSO, random.uniform(1.5, 4))

    def _act_negar(self, dt, ahora):
        if self.t_estado >= 0.9:
            self._cambiar(REPOSO, 2)

    def _act_aterriza(self, dt, ahora):
        if self.t_estado >= 0.3:
            self._cambiar(REPOSO, random.uniform(1, 3))
            if random.random() < 0.4:
                self.cui()

    # --- cui -------------------------------------------------------------
    def cui(self, solo_sonido=False):
        n = random.choice((1, 2, 2, 3))
        self.snd.tocar("cui%d" % n)
        self.decir("cui!" if n == 1 else "cui " * (n - 1) + "cui!", dur=2.0)
        if not solo_sonido and self.estado in (REPOSO, ANDAR):
            self._cambiar(CUI, 0.27 * n + 0.15)

    # --- caricias ----------------------------------------------------------
    def caricia(self):
        if self.estado in OCUPADA:
            return
        self.m.caricia()
        self._barras_hasta = time.monotonic() + 3
        self._cambiar(FELIZ, 1.8)

    def _corazon(self):
        self._particulas.append({
            "tipo": "corazon", "x": self.width() / 2 + random.uniform(-14, 14) * self.e,
            "y": self.height() - 26 * self.e, "vx": random.uniform(-6, 6) * self.e,
            "vy": -14 * self.e, "vida": 0.0, "dur": 1.2})

    # --- comer -------------------------------------------------------------
    def dar_lechuga(self):
        if self.estado in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO, COMIENDO):
            return
        self._comida = {"tipo": "lechuga"}
        self._bocadillo = None
        self._cambiar(COMIENDO)

    def _siguiente_archivo(self):
        ruta = self._cola.pop(0)
        ok, motivo, tam_bytes = papelera.revisar(ruta)
        icono = self._icono_pixel(ruta) if ok else None
        if ok:
            ok, motivo = papelera.a_la_papelera(ruta)
        if not ok:
            if motivo.startswith("error") or motivo == "sigue_ahi":
                print("Tamacuychi: no se pudo mandar a la papelera %s: %s" % (ruta, motivo),
                      file=sys.stderr)
            self.snd.tocar("puaj")
            self.decir(MENSAJES_RECHAZO.get(motivo, "No puedo morderlo"), dur=2.5)
            self._cambiar(NEGAR)
            return
        nombre = os.path.basename(ruta)
        if len(nombre) > 16:
            raiz, ext = os.path.splitext(nombre)
            nombre = raiz[:14 - len(ext[:5])] + "…" + ext[:5]
        self._comida = {"tipo": "archivo", "icono": icono, "tam": tam_bytes}
        self.decir("ñam: " + nombre, dur=3.0)
        self._cambiar(COMIENDO)

    def _icono_pixel(self, ruta):
        """Icono del archivo a 16x16 (luego se escala como pixel art)."""
        icono = QFileIconProvider().icon(QFileInfo(ruta))
        pm = icono.pixmap(32, 32)
        img = pm.toImage().convertToFormat(QImage.Format_ARGB32)
        if img.isNull() or img.width() == 0:
            img = QImage(16, 16, QImage.Format_ARGB32)
            img.fill(QColor(230, 230, 240))
        img = img.scaled(16, 16, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        # alfa binaria y contorno para que parezca pixel art
        for y in range(16):
            for x in range(16):
                c = img.pixelColor(x, y)
                c.setAlpha(255 if c.alpha() > 100 else 0)
                img.setPixelColor(x, y, c)
        return img

    def _act_comiendo(self, dt, ahora):
        t = self.t_estado
        bocado = 0.7
        n_bocados = 4
        k = int((t - 0.3) / bocado) + 1 if t >= 0.3 else 0
        prev = int((t - dt - 0.3) / bocado) + 1 if t - dt >= 0.3 else 0
        if k != prev and 1 <= k <= n_bocados:
            self.snd.tocar("nam")
            self._migas()
        if t >= 0.3 + bocado * n_bocados + 0.2:
            comida = self._comida
            self._comida = None
            if comida and comida["tipo"] == "lechuga":
                self.m.comer_lechuga()
            elif comida:
                self.m.comer_archivo(comida["tam"])
            self._barras_hasta = ahora + 3
            self._cambiar(FELIZ, 1.6)

    def _migas(self):
        com = self._comida or {}
        for _ in range(5):
            if com.get("tipo") == "archivo" and com.get("icono") is not None:
                img = com["icono"]
                c = img.pixelColor(random.randrange(16), random.randrange(16))
                if c.alpha() == 0:
                    c = QColor(220, 220, 230)
            else:
                c = QColor(*random.choice(((126, 204, 92), (70, 146, 58), (196, 238, 152))))
            self._particulas.append({
                "tipo": "miga", "color": c,
                "x": self.width() / 2 + random.uniform(-6, 6) * self.e,
                "y": self.height() - 12 * self.e,
                "vx": random.uniform(-30, 30) * self.e, "vy": random.uniform(-40, -15) * self.e,
                "vida": 0.0, "dur": 0.7})

    # --- popcorning ---------------------------------------------------------
    def popcorn(self):
        if self.estado in OCUPADA:
            return
        if self.m.cansada:
            self.decir("uff...", dur=1.5)
            self._cambiar(REPOSO, 2)
            return
        self.m.jugar()
        self._barras_hasta = time.monotonic() + 2
        self._saltos = list(range(random.randint(4, 8)))
        self._salto = None
        self._cambiar(POPCORN)
        self.cui(solo_sonido=True)
        self._nuevo_salto()

    def _nuevo_salto(self):
        g = self._pantalla()
        lo, hi = self._limites_x()
        e4 = self.e / 4
        dx = random.uniform(70, 340) * e4 * random.choice((-1, 1))
        if not lo <= self.px + dx <= hi:
            dx = -dx
        x1 = min(max(self.px + dx, lo), hi)
        alto_max = max(30.0, (self.py - g.top()) - self.height())
        h = min(random.uniform(40, 280) * e4, alto_max)
        dur = 0.22 + 0.034 * math.sqrt(h)
        self._salto = {"x0": self.px, "x1": x1, "h": h, "dur": dur, "t": 0.0, "pausa": 0.0,
                       "gira": random.random() < 0.7, "dir": 1 if x1 >= self.px else -1,
                       "suelo": self._suelo(x1), "y0": self.py}
        self.snd.tocar("salto")

    def _act_popcorn(self, dt, ahora):
        s = self._salto
        if s is None:
            self._cambiar(REPOSO, 2)
            return
        if s["t"] < s["dur"]:
            s["t"] = min(s["dur"], s["t"] + dt)
            u = s["t"] / s["dur"]
            self.px = s["x0"] + (s["x1"] - s["x0"]) * u
            base = s["y0"] + (s["suelo"] - s["y0"]) * u
            self.py = base - 4 * s["h"] * u * (1 - u)
            if s["t"] >= s["dur"]:
                self.py = s["suelo"]
                s["aterrizo"] = ahora
                s["pausa"] = random.uniform(0.12, 0.35)
                if random.random() < 0.5:
                    self._corazon()
            return
        s["pausa"] -= dt
        if s["pausa"] <= 0:
            if self._saltos:
                self._saltos.pop()
            if self._saltos:
                self._nuevo_salto()
            else:
                self._salto = None
                self._cambiar(FELIZ, 1.2)

    # --- coger y caer -------------------------------------------------------
    def _act_cogida(self, dt, ahora):
        pos = QCursor.pos()
        nx = pos.x() - self._cogida["dx"]
        ny = pos.y() - self._cogida["dy"]
        if dt > 0:
            self.vx = 0.7 * self.vx + 0.3 * (nx - self.px) / dt
            self.vy = 0.7 * self.vy + 0.3 * (ny - self.py) / dt
        self.px, self.py = float(nx), float(ny)

    def _act_cayendo(self, dt, ahora):
        g = self._pantalla()
        self.vy += 2600 * dt
        self.vx *= (1 - 0.8 * dt)
        self.px += self.vx * dt
        self.py += self.vy * dt
        lo, hi = g.left() + 20 * self.e, g.right() - 20 * self.e
        if self.px < lo or self.px > hi:
            self.px = min(max(self.px, lo), hi)
            self.vx = -self.vx * 0.5
        tope = g.top() + 34 * self.e
        if self.py < tope and self.vy < 0:
            self.py = tope
            self.vy = -self.vy * 0.4
        suelo = g.bottom() + 1
        if self.py >= suelo:
            self.py = suelo
            if self.vy > 700:
                self.vy = -self.vy * 0.33
                self.vx *= 0.6
                self.snd.tocar("salto")
            else:
                self.vx = self.vy = 0.0
                self._cambiar(ATERRIZA)

    # --- dormir ---------------------------------------------------------------
    def dormir(self):
        if self.estado in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO, COGIDA, CAYENDO):
            return
        self._comida = None
        self._salto = None
        self._bocadillo = None
        self.py = self._suelo()
        self._cambiar(YENDO_A_DORMIR)

    def despertar(self):
        if self.estado == DURMIENDO:
            self.m.despertar()
            self._cambiar(DESPERTANDO)

    def _act_yendo_a_dormir(self, dt, ahora):
        self._heno_alpha = min(1.0, self.t_estado / 0.5)
        if self.t_estado >= 3.6:
            self.m.dormir()
            self._cambiar(DURMIENDO)

    def _act_durmiendo(self, dt, ahora):
        self._heno_alpha = 1.0
        if ahora >= self._prox_zeta:
            self._prox_zeta = ahora + 1.4
            self._particulas.append({
                "tipo": "zeta", "x": self.width() / 2 + 8 * self.e,
                "y": self.height() - (FONDO + 27) * self.e, "vx": 5 * self.e, "vy": -7 * self.e,
                "vida": 0.0, "dur": 2.4})

    def _act_despertando(self, dt, ahora):
        t = self.t_estado
        if 3.2 <= t - dt < 3.25 or (t - dt < 3.2 <= t):
            self.snd.tocar("bostezo")
            self.decir("uaaah", dur=1.4)
        if t > 3.2:
            self._heno_alpha = max(0.0, 1.0 - (t - 3.2) / 1.0)
        if t >= 4.5:
            self._heno_alpha = 0.0
            self._cambiar(REPOSO, 3)

    # --- cacas ------------------------------------------------------------------
    def hacer_caca(self):
        if len(self.m.cacas) >= MAX_CACAS:
            return
        lo, hi = self._limites_x()
        suelo = self._suelo()
        for _ in range(20):
            x = self.px + random.choice((-1, 1)) * random.uniform(22, 40) * self.e
            x = min(max(x, lo - 10 * self.e), hi + 10 * self.e)
            if all(abs(x - cx) > 16 * self.e for cx, _ in self.m.cacas):
                break
        self.m.cacas.append([x, suelo])
        self._crear_caca_ventana(x, suelo)
        self.m.guardar()
        self.raise_()

    def _crear_caca_ventana(self, x, y):
        c = Caca(self.spr, self.e, x, y, self._caca_recogida, self.snd)
        self.cacas.append(c)
        c.show()

    def _caca_recogida(self, caca):
        try:
            i = self.cacas.index(caca)
        except ValueError:
            return
        self.cacas.pop(i)
        self.m.recoger_caca(i)
        self._barras_hasta = time.monotonic() + 2

    def recoger_cacas(self):
        for c in list(self.cacas):
            c.mousePressEvent(_ClicFalso())

    # ------------------------------------------------------------------
    # Partículas y bocadillo
    # ------------------------------------------------------------------
    def _particulas_avanzar(self, dt):
        vivas = []
        for p in self._particulas:
            p["vida"] += dt
            if p["vida"] >= p["dur"]:
                continue
            if p["tipo"] == "miga":
                p["vy"] += 160 * self.e * dt
            if p["tipo"] in ("corazon", "zeta"):
                p["x"] += math.sin(p["vida"] * 6) * 0.4 * self.e
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            vivas.append(p)
        self._particulas = vivas

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def _pose(self):
        """Devuelve (sprite, fotograma, espejo, escala, dx, dy) o None si no se ve."""
        e, t, ahora = self.e, self.t_estado, time.monotonic()
        est = self.estado
        if est == REPOSO:
            if self._oliendo:
                return ("cobaya_comer", 0, False, e, 0, 0)
            if self.m.descuidada:
                return ("cobaya_triste", int(ahora * 1.5) % 2, False, e, 0, 0)
            if ahora < self._mirando:
                return ("cobaya_mira", 0, False, e, 0, 0)
            return ("cobaya_idle", 1 if ahora < self._parpadeo else 0, False, e, 0, 0)
        if est == ANDAR:
            return ("cobaya_andar", int(t / 0.13), self.dir < 0, e, 0, 0)
        if est == FELIZ:
            salto = -abs(math.sin(t * 9)) * 3 * e if t < 1.0 else 0
            return ("cobaya_feliz", int(t * 4) % 2, False, e, 0, salto)
        if est == CUI:
            return ("cobaya_cui", int(t * 7) % 2, False, e, 0, 0)
        if est == COMIENDO:
            fase = ((self.t_estado - 0.3) % 0.7) if self.t_estado >= 0.3 else 0
            return ("cobaya_comer", 0 if fase < 0.35 else 1, False, e, 0, 0)
        if est == NEGAR:
            dx = (e if int(t * 10) % 2 else -e) if t < 0.6 else 0
            return ("cobaya_triste", 0, False, e, dx, 0)
        if est == ATERRIZA:
            return ("cobaya_aterriza", 0, False, e, 0, 0)
        if est in (COGIDA, CAYENDO):
            return ("cobaya_colgando", int(t * 3) % 2, self.vx < -50, e, 0, 0)
        if est == POPCORN:
            s = self._salto
            if s is None:
                return ("cobaya_feliz", 0, False, e, 0, 0)
            if s["t"] >= s["dur"]:
                aplasta = ahora - s.get("aterrizo", 0) < 0.1
                return ("cobaya_aterriza" if aplasta else "cobaya_feliz", 0, False, e, 0, 0)
            u = s["t"] / s["dur"]
            if s["gira"]:
                if u < 0.18 or u > 0.84:
                    return ("cobaya_feliz", 1, False, e, 0, 0)
                if u < 0.40:
                    return ("cobaya_perfil_feliz", 0, s["dir"] < 0, e, 0, 0)
                if u < 0.62:
                    return ("cobaya_espalda", 0, False, e, 0, 0)
                return ("cobaya_perfil_feliz", 0, s["dir"] > 0, e, 0, 0)
            # salto con patada: se gira a mitad del salto
            return ("cobaya_perfil_feliz", 0, (s["dir"] < 0) != (u > 0.5), e, 0, 0)
        if est == YENDO_A_DORMIR:
            if t < 0.5:
                return ("cobaya_idle", 0, False, e, 0, 0)
            if t < 0.8:
                return ("cobaya_perfil", 0, False, e, 0, 0)
            if t < 1.1:
                return ("cobaya_espalda", 0, False, e, 0, 0)
            u = min(1.0, (t - 1.1) / 2.2)
            if u >= 1.0:
                return None
            emin = max(1, e - 2)
            esc = e - int(round(u * (e - emin)))
            return ("cobaya_espalda", int(t / 0.2), False, esc, 0, -u * FONDO * e)
        if est == DURMIENDO:
            return None
        if est == DESPERTANDO:
            emin = max(1, e - 2)
            if t < 0.3:
                return None
            if t < 1.6:
                u = (t - 0.3) / 1.3
                esc = emin + int(round(u * (e - emin)))
                return ("cobaya_idle", 0, False, esc, 0, -(1 - u) * FONDO * e)
            if t < 2.3:
                return ("cobaya_estirar", 0, False, e, 0, 0)
            if t < 3.2:
                return ("cobaya_estirar", 1, False, e, 0, 0)
            return ("cobaya_bostezo", int(t * 3) % 2, False, e, 0, 0)
        return ("cobaya_idle", 0, False, e, 0, 0)

    def _heno_fase(self):
        if self.estado == DURMIENDO:
            return 1 + int(self.t_estado / 1.2) % 2
        if self.estado == YENDO_A_DORMIR and self.t_estado >= 3.2:
            return 1
        return 0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform, False)
        e = self.e
        W, H = self.width(), self.height()
        zonas = []

        pose = self._pose()
        heno_delante = (self.estado == YENDO_A_DORMIR and self.t_estado > 2.6) or \
                       (self.estado == DESPERTANDO and self.t_estado < 0.9)

        def pintar_heno():
            if self._heno_alpha <= 0:
                return
            pm = self.spr.get("heno", self._heno_fase(), e)
            w, h = tam(pm)
            r = QRect(int(W / 2 - w / 2), int(H - h - FONDO * e), w, h)
            p.setOpacity(self._heno_alpha)
            p.drawPixmap(r.topLeft(), pm)
            p.setOpacity(1.0)
            zonas.append(r)

        if not heno_delante:
            pintar_heno()
        if pose is not None:
            nombre, fot, espejo, esc, dx, dy = pose
            pm = self.spr.get(nombre, fot, esc, espejo)
            w, h = tam(pm)
            r = QRect(int(W / 2 - w / 2 + dx), int(H - h + dy), w, h)
            p.drawPixmap(r.topLeft(), pm)
            zonas.append(r)
        if heno_delante:
            pintar_heno()

        # comida delante de la boca
        if self.estado == COMIENDO and self._comida:
            self._pintar_comida(p, W, H, zonas)

        # partículas
        for q in self._particulas:
            a = 1.0 - max(0.0, (q["vida"] - q["dur"] * 0.6) / (q["dur"] * 0.4))
            p.setOpacity(max(0.0, a))
            if q["tipo"] == "miga":
                r = QRect(int(q["x"]), int(q["y"]), e, e)
                p.fillRect(r, q["color"])
            else:
                nombre = {"corazon": "corazon", "zeta": "zeta"}[q["tipo"]]
                esc = e if q["tipo"] == "corazon" else max(1, e - 1)
                pm = self.spr.get(nombre, 0, esc)
                w, h = tam(pm)
                r = QRect(int(q["x"] - w / 2), int(q["y"] - h / 2), w, h)
                p.drawPixmap(r.topLeft(), pm)
            zonas.append(r)
        p.setOpacity(1.0)

        # bocadillo
        if self._bocadillo:
            zonas.append(self._pintar_bocadillo(p, W, H, pose))

        # barras de estado al pasar el ratón
        if self._hover or time.monotonic() < self._barras_hasta:
            zonas.append(self._pintar_barras(p, W))
        p.end()

        if self._mascara_x11:
            reg = QRegion()
            for r in zonas:
                reg = reg.united(QRegion(r.adjusted(-e, -e, e, e)))
            if reg != self._ultima_mascara:
                self._ultima_mascara = reg
                self.setMask(reg)

    def _pintar_comida(self, p, W, H, zonas):
        e = self.e
        t = self.t_estado
        mordiscos = min(4, int((t - 0.3) / 0.7) + 1) if t >= 0.3 else 0
        if mordiscos >= 4:
            return
        cx, cy = W / 2, H - 9 * e
        if self._comida["tipo"] == "lechuga":
            pm = self.spr.get("lechuga", mordiscos, max(1, e - 1))
            w, h = tam(pm)
            r = QRect(int(cx - w / 2), int(cy - h / 2), w, h)
            p.drawPixmap(r.topLeft(), pm)
        else:
            img = QImage(self._comida["icono"])
            # mordiscos: círculos borrados desde arriba a la derecha
            centros = ((14, 2), (15, 9), (9, 1))
            for i in range(min(mordiscos, 3)):
                bx, by = centros[i]
                for y in range(16):
                    for x in range(16):
                        if (x - bx) ** 2 + (y - by) ** 2 <= 16:
                            img.setPixelColor(x, y, QColor(0, 0, 0, 0))
            esc = max(1, e - 1)
            fis = max(1, int(round(esc * self.spr.dpr)))
            img = img.scaled(16 * fis, 16 * fis, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            pm = QPixmap.fromImage(img)
            pm.setDevicePixelRatio(fis / esc)
            w = h = 16 * esc
            r = QRect(int(cx - w / 2), int(cy - h / 2), w, h)
            p.drawPixmap(r.topLeft(), pm)
        zonas.append(r)

    def _fuente(self):
        f = QFont()
        f.setPixelSize(max(11, int(3.6 * self.e)))
        f.setBold(True)
        f.setStyleStrategy(QFont.NoAntialias)
        return f

    def _pintar_bocadillo(self, p, W, H, pose):
        e = self.e
        b = self._bocadillo
        texto, icono = b.get("texto"), b.get("icono")
        if icono:
            pm = self.spr.get(icono, 0, max(1, e // 2))
            cw, ch = tam(pm)
        else:
            f = self._fuente()
            p.setFont(f)
            fm = QFontMetrics(f)
            cw, ch = fm.horizontalAdvance(texto), fm.height()
        pad = 2 * e
        bw = min(W - 2 * e, cw + 2 * pad)
        bh = ch + 2 * pad - e
        # encima de la cabeza
        alto_cobaya = 31 * e
        if pose is not None:
            alto_cobaya = tam(self.spr.get(pose[0], pose[1], pose[3]))[1] - int(pose[5])
        if self.estado == DURMIENDO:
            alto_cobaya = (FONDO + 30) * e
        bx = int(W / 2 - bw / 2)
        by = int(max(10 * e, H - alto_cobaya - bh - 4 * e))
        blanco = QColor(255, 255, 255)
        # cuerpo con esquinas recortadas (estilo pixel)
        p.fillRect(QRect(bx + e, by, bw - 2 * e, bh), COL_CONTORNO)
        p.fillRect(QRect(bx, by + e, bw, bh - 2 * e), COL_CONTORNO)
        p.fillRect(QRect(bx + e, by + e, bw - 2 * e, bh - 2 * e), blanco)
        # pico
        px0 = int(W / 2 - e)
        p.fillRect(QRect(px0 - e, by + bh - e, 3 * e, e), blanco)
        p.fillRect(QRect(px0 - 2 * e, by + bh - e, e, e), COL_CONTORNO)
        p.fillRect(QRect(px0 + 2 * e, by + bh - e, e, e), COL_CONTORNO)
        p.fillRect(QRect(px0, by + bh, e, e), blanco)
        p.fillRect(QRect(px0 - e, by + bh, e, e), COL_CONTORNO)
        p.fillRect(QRect(px0 + e, by + bh, e, e), COL_CONTORNO)
        p.fillRect(QRect(px0, by + bh + e, e, e), COL_CONTORNO)
        if icono:
            p.drawPixmap(int(bx + bw / 2 - cw / 2), int(by + bh / 2 - ch / 2), pm)
        else:
            p.setPen(COL_CONTORNO)
            p.drawText(QRect(bx, by, bw, bh), Qt.AlignCenter, texto)
        self._rect_bocadillo = QRect(bx, by, bw, bh)
        return QRect(bx, by, bw, bh + 2 * e)

    def _pintar_barras(self, p, W):
        e = self.e
        parpadeo = int(time.monotonic() * 4) % 2 == 0
        ancho = 24 * e
        x0 = int(W / 2 - ancho / 2)
        y = e
        for valor, col in ((self.m.saciedad, COL_SACIEDAD), (self.m.felicidad, COL_FELICIDAD),
                           (self.m.energia, COL_ENERGIA)):
            if valor < 30 and parpadeo:
                col = COL_ALERTA
            p.fillRect(QRect(x0, y, ancho, 3 * e), COL_CONTORNO)
            p.fillRect(QRect(x0 + e, y + e, ancho - 2 * e, e), QColor(255, 255, 255, 200))
            lleno = int((ancho - 2 * e) * valor / 100.0)
            p.fillRect(QRect(x0 + e, y + e, lleno, e), col)
            y += 3 * e
        return QRect(x0, e, ancho, 9 * e)

    # ------------------------------------------------------------------
    # Ratón
    # ------------------------------------------------------------------
    def enterEvent(self, ev):
        self._hover = True

    def leaveEvent(self, ev):
        self._hover = False
        self._barras_hasta = time.monotonic() + 1.5
        self._caricia.clear()

    def mousePressEvent(self, ev):
        if ev.button() != Qt.LeftButton:
            return
        g = ev.globalPosition()
        self._raton = {"x": g.x(), "y": g.y(), "t": time.monotonic(), "local": ev.position()}

    def mouseMoveEvent(self, ev):
        g = ev.globalPosition()
        if self._raton and ev.buttons() & Qt.LeftButton:
            d = abs(g.x() - self._raton["x"]) + abs(g.y() - self._raton["y"])
            if d > 6 and self.estado not in (COGIDA, DURMIENDO, YENDO_A_DORMIR, DESPERTANDO, COMIENDO):
                self._cogida = {"dx": g.x() - self.px, "dy": g.y() - self.py}
                self._salto = None
                self._bocadillo = None
                self.vx = self.vy = 0.0
                self._cambiar(COGIDA)
                self.snd.tocar("cui1")
            return
        # caricia: mover el ratón de un lado a otro por encima
        x = g.x()
        if self._ultimo_x_raton is not None:
            d = x - self._ultimo_x_raton
            if abs(d) >= 2:
                nueva = 1 if d > 0 else -1
                if self._dir_raton and nueva != self._dir_raton:
                    ahora = time.monotonic()
                    self._caricia = [t for t in self._caricia if ahora - t < 1.5] + [ahora]
                    if len(self._caricia) >= 4:
                        self._caricia.clear()
                        self.caricia()
                self._dir_raton = nueva
        self._ultimo_x_raton = x

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.LeftButton or not self._raton:
            return
        r, self._raton = self._raton, None
        if self.estado == COGIDA:
            self.vx = max(-2500, min(2500, self.vx))
            self.vy = max(-2500, min(1000, self.vy))
            self._cambiar(CAYENDO)
            return
        if time.monotonic() - r["t"] > 0.6:
            return
        pos = ev.position().toPoint()
        rb = getattr(self, "_rect_bocadillo", None)
        if self._bocadillo and self._bocadillo.get("icono") == "lechuga" and rb and rb.contains(pos):
            self.dar_lechuga()
            return
        if self.estado == DURMIENDO:
            self.despertar()
        elif self.estado not in OCUPADA:
            self.popcorn()

    def contextMenuEvent(self, ev):
        if self.menu_fn:
            self.menu_fn().exec(ev.globalPos())

    # ------------------------------------------------------------------
    # Arrastrar y soltar archivos
    # ------------------------------------------------------------------
    def _rutas(self, mime):
        if not mime.hasUrls():
            return []
        return [u.toLocalFile() for u in mime.urls() if u.isLocalFile() and u.toLocalFile()]

    def dragEnterEvent(self, ev):
        if self._rutas(ev.mimeData()) and self.estado not in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO):
            ev.setDropAction(Qt.CopyAction)
            ev.accept()
            if self.estado in (REPOSO, ANDAR, FELIZ, CUI):
                self._cambiar(REPOSO, 1.5)
                self._oliendo = True
                self.decir("¿ñam?", dur=30)
        else:
            ev.ignore()

    def dragMoveEvent(self, ev):
        # siempre "copiar": con "mover" el Explorador borraría el original por su cuenta
        ev.setDropAction(Qt.CopyAction)
        ev.accept()

    def dragLeaveEvent(self, ev):
        self._oliendo = False
        self._bocadillo = None

    def dropEvent(self, ev):
        self._oliendo = False
        self._bocadillo = None
        rutas = self._rutas(ev.mimeData())
        if not rutas:
            return
        ev.setDropAction(Qt.CopyAction)
        ev.accept()
        self._cola.extend(rutas)

    # ------------------------------------------------------------------
    def cerrar(self):
        self.m.posicion = [self.px, self.py]
        self.m.guardar()
        for c in list(self.cacas):
            c.close()
        self.close()


class _ClicFalso:
    def button(self):
        return Qt.LeftButton
