"""Cacas: ventanitas sueltas en el escritorio que se recogen haciendo clic."""

import math
import time

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from .sprites import tam

ANCHO, ALTO = 17, 17     # en píxeles de arte


class Caca(QWidget):
    def __init__(self, sprites, escala, x, y, al_recoger, sonidos):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                         | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.sprites, self.e, self.sonidos = sprites, escala, sonidos
        self.al_recoger = al_recoger
        self.pos_suelo = [x, y]
        self.recogida = None
        self.t0 = time.monotonic() + (x % 7) * 0.3
        self.setFixedSize(ANCHO * escala, ALTO * escala)
        self.move(int(x - self.width() / 2), int(y - self.height()))
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Clic para recoger")

    def avanzar(self):
        if self.recogida is not None and time.monotonic() - self.recogida > 0.45:
            self.close()
            return
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.recogida is None:
            self.recogida = time.monotonic()
            self.sonidos.tocar("pop")
            self.al_recoger(self)

    def paintEvent(self, _):
        p = QPainter(self)
        e = self.e
        t = time.monotonic()
        if self.recogida is not None:
            k = int((t - self.recogida) / 0.15)
            pm = self.sprites.get("destello", min(k, 2), e)
            p.drawPixmap(int(self.width() / 2 - tam(pm)[0] / 2), self.height() - 9 * e, pm)
            for dx, dy in ((-5, -3), (5, -6)):
                pm2 = self.sprites.get("destello", min(k + 1, 2), max(1, e // 2))
                p.drawPixmap(int(self.width() / 2 + dx * e), self.height() + dy * e - 6 * e, pm2)
            return
        pm = self.sprites.get("caca", 0, e)
        w, h = tam(pm)
        p.drawPixmap(int(self.width() / 2 - w / 2), self.height() - h, pm)
        # líneas de olor
        col = QColor(150, 170, 110, 170)
        for i, x0 in enumerate((5, 8, 11)):
            fase = (t - self.t0) * 1.4 + i * 0.9
            sube = (fase % 2.0) / 2.0
            for k in range(4):
                yy = 9 - k - int(sube * 3)
                xx = x0 + int(round(math.sin(fase * 2 + k * 1.3)))
                if yy >= 0:
                    p.fillRect(QRect(xx * e, yy * e, e, e), col)
