"""Sonidos sintetizados (equivale a src/sonido.cpp del firmware).

Se generan como WAV la primera vez. En Windows se reproducen con winsound y en
el resto con QSoundEffect. Si
QtMultimedia no está disponible, la cobaya simplemente no suena.
"""

import math
import os
import random
import struct
import sys
import wave

from . import config

FS = 48000


def _escribir(ruta, muestras):
    # 48 kHz estéreo de 16 bits: el formato que acepta cualquier tarjeta de sonido
    datos = bytearray()
    for s in muestras:
        v = struct.pack("<h", int(max(-1.0, min(1.0, s)) * 20000))
        datos += v + v
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(bytes(datos))


def _barrido(f0, f1, dur, vol=0.6, armonico=0.25, vibrato=0.0, curva=1.0):
    """Seno con un armónico, frecuencia de f0 a f1, subida y bajada suaves."""
    n = int(dur * FS)
    out = []
    fase = 0.0
    for i in range(n):
        s = i / max(1, n - 1)
        f = f0 + (f1 - f0) * (s ** curva)
        if vibrato:
            f *= 1 + vibrato * math.sin(2 * math.pi * 6 * i / FS)
        fase += 2 * math.pi * f / FS
        env = min(1.0, s / 0.12) * min(1.0, (1 - s) / 0.25)
        out.append(vol * env * (math.sin(fase) + armonico * math.sin(2 * fase)) / (1 + armonico))
    return out


def _silencio(dur):
    return [0.0] * int(dur * FS)


def cui(silbidos):
    """El 'cui' de las cobayas: silbidos que suben de tono."""
    out = []
    base = random.uniform(1250, 1450)
    for k in range(silbidos):
        f0 = base + 160 * k
        out += _barrido(f0, f0 * 1.55, random.uniform(0.17, 0.23), vol=0.55, curva=0.7)
        out += _silencio(0.07)
    return out


def bostezo():
    return _barrido(720, 330, 0.95, vol=0.5, armonico=0.6, vibrato=0.03, curva=1.4)


def ñam():
    """Crujido: ráfagas de ruido cortas."""
    out = []
    rnd = random.Random(3)
    for _ in range(3):
        n = int(0.035 * FS)
        prev = 0.0
        for i in range(n):
            env = (1 - i / n) ** 2
            prev = 0.6 * prev + 0.4 * rnd.uniform(-1, 1)
            out.append(0.7 * env * prev)
        out += _silencio(0.04)
    return out


def pop():
    return _barrido(1100, 2300, 0.08, vol=0.35, armonico=0.1)


def salto():
    return _barrido(380, 820, 0.11, vol=0.25, armonico=0.3)


def puaj():
    return _barrido(420, 260, 0.25, vol=0.4, armonico=0.5, vibrato=0.08)


class Sonidos:
    def __init__(self):
        self._efectos = {}
        self.silencio = False
        self._rutas = {}
        carpeta = os.path.join(config.carpeta_datos(), "sonidos48")
        os.makedirs(carpeta, exist_ok=True)
        generar = {
            "cui1": lambda: cui(1), "cui2": lambda: cui(2), "cui3": lambda: cui(3),
            "bostezo": bostezo, "nam": ñam, "pop": pop, "salto": salto, "puaj": puaj,
        }
        for nombre, fn in generar.items():
            ruta = os.path.join(carpeta, nombre + ".wav")
            if not os.path.exists(ruta):
                try:
                    _escribir(ruta, fn())
                except OSError:
                    continue
            self._rutas[nombre] = ruta
        if sys.platform == "win32":
            return          # en Windows se usa winsound, que no falla nunca
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect
        except Exception:
            return
        for nombre, ruta in self._rutas.items():
            ef = QSoundEffect()
            ef.setSource(QUrl.fromLocalFile(ruta))
            ef.setVolume(0.6)
            self._efectos[nombre] = ef

    def tocar(self, nombre):
        if self.silencio:
            return
        if sys.platform == "win32":
            ruta = self._rutas.get(nombre)
            if ruta:
                import winsound
                try:
                    winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC
                                       | winsound.SND_NODEFAULT)
                except RuntimeError:
                    pass
            return
        ef = self._efectos.get(nombre)
        if ef is not None:
            ef.play()
