"""Convierte el arte en QPixmap escalados (enteros, sin suavizado) y los cachea.

Si existe sprites/<nombre>@N.png o sprites/<nombre>.png se usa en lugar del
arte generado: N fotogramas en horizontal, 1 píxel del PNG = 1 píxel de arte.
Así se pueden reutilizar los PNG del firmware (cobaya_idle@2.png, ...).
"""

import glob
import os
import re
from collections import OrderedDict

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from . import arte, config

MAX_CACHE = 48


def _imagen(filas, pal=None):
    w, h, datos = arte.a_rgba(filas, 1, pal)
    img = QImage(datos, w, h, w * 4, QImage.Format_RGBA8888)
    return img.copy()   # copia para que no dependa del buffer de Python


class Sprites:
    def __init__(self, estilo="tricolor", accesorios=None):
        self._base = {}      # nombre -> [QImage]
        self._cache = OrderedDict()   # pocos sprites escalados a la vez (ahorra RAM)
        self.dpr = 1.0       # relación píxel físico/lógico de la pantalla
        self.configurar(estilo, accesorios)

    def configurar(self, estilo, accesorios):
        """Vuelve a generar el arte con otro estilo o accesorios."""
        pal = arte.paleta(estilo)
        self._base = {nombre: [_imagen(f, pal) for f in fotogramas]
                      for nombre, fotogramas in arte.catalogo(estilo, accesorios).items()}
        self._cache.clear()
        # los PNG de sprites/ sustituyen al arte de la cobaya tricolor sin accesorios
        if estilo == "tricolor" and not any((accesorios or {}).values()):
            self._cargar_png()

    def _cargar_png(self):
        carpeta = config.carpeta_sprites()
        for ruta in glob.glob(os.path.join(carpeta, "*.png")):
            m = re.match(r"^(.+?)(?:@(\d+))?\.png$", os.path.basename(ruta))
            if not m:
                continue
            nombre, n = m.group(1), int(m.group(2) or 1)
            img = QImage(ruta)
            if img.isNull():
                continue
            img = img.convertToFormat(QImage.Format_RGBA8888)
            ancho = img.width() // n
            self._base[nombre] = [img.copy(i * ancho, 0, ancho, img.height()) for i in range(n)]

    def n(self, nombre):
        return len(self._base[nombre])

    def tam(self, nombre, i=0):
        img = self._base[nombre][i % len(self._base[nombre])]
        return img.width(), img.height()

    def get(self, nombre, i=0, escala=4, espejo=False):
        fotos = self._base[nombre]
        i %= len(fotos)
        # escala entera en píxeles físicos para que el pixel art siga nítido
        # también con el escalado de Windows al 125 % o 150 %
        fisica = max(1, int(round(escala * self.dpr)))
        clave = (nombre, i, fisica, espejo)
        pm = self._cache.get(clave)
        if pm is not None:
            self._cache.move_to_end(clave)
        else:
            img = fotos[i]
            if espejo:
                img = img.mirrored(True, False)
            img = img.scaled(img.width() * fisica, img.height() * fisica,
                             Qt.IgnoreAspectRatio, Qt.FastTransformation)
            pm = QPixmap.fromImage(img)
            pm.setDevicePixelRatio(fisica / escala)
            self._cache[clave] = pm
            while len(self._cache) > MAX_CACHE:
                self._cache.popitem(last=False)
        return pm

    def vaciar_cache(self):
        self._cache.clear()

    def icono(self, escala=2):
        """Cara de la cobaya para la bandeja del sistema."""
        img = self._base["cobaya_idle"][0]
        return QPixmap.fromImage(img.scaled(img.width() * escala, img.height() * escala,
                                            Qt.IgnoreAspectRatio, Qt.FastTransformation))


def tam(pm):
    """Tamaño lógico de un QPixmap (ancho, alto)."""
    s = pm.deviceIndependentSize()
    return int(round(s.width())), int(round(s.height()))
