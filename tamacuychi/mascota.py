"""Estadísticas, desgaste, cacas y guardado. Sin Qt (equivale a src/mascota.* del firmware)."""

import json
import math
import os
import random
import time

from . import config

HORA = 3600.0
MAX_CACAS = 4
ESCALA_DEFECTO = 2         # "Pequeña"
MAX_AUSENCIA = 12 * HORA   # lo que se tiene en cuenta del tiempo con el programa cerrado


def ahora():
    """Reloj del juego (acelerado con VELOCIDAD_TIEMPO)."""
    return time.time() * config.VELOCIDAD_TIEMPO


class Mascota:
    def __init__(self):
        self.saciedad = 80.0
        self.felicidad = 80.0
        self.energia = 90.0
        self.durmiendo = False
        self.cacas = []            # [[x, y], ...] en coordenadas de pantalla
        self.prox_caca = ahora() + random.uniform(30, 60) * 60
        self.caca_tras_comer = None
        self.archivos_comidos = 0
        self.silencio = False
        self.escala = ESCALA_DEFECTO
        self.nombre = ""
        self.nombre_preguntado = False
        self.posicion = None       # [x, y] del centro de los pies
        self.inicio_configurado = False   # la primera vez se activa el inicio con Windows
        self._ultimo = ahora()
        self._ruta = os.path.join(config.carpeta_datos(), "estado.json")
        self.cargar()

    # -- estado derivado --------------------------------------------------
    @property
    def hambrienta(self):
        return self.saciedad < 25

    @property
    def descuidada(self):
        return self.saciedad < 25 or self.felicidad < 30 or len(self.cacas) >= 3

    @property
    def cansada(self):
        return self.energia < 15

    # -- paso del tiempo --------------------------------------------------
    def avanzar(self):
        """Aplica el desgaste desde la última llamada. Devuelve eventos ('caca', 'despierta')."""
        t = ahora()
        dt = min(max(0.0, t - self._ultimo), MAX_AUSENCIA)
        self._ultimo = t
        eventos = []
        h = dt / HORA
        self.saciedad -= 100.0 / 10.0 * h
        ritmo_fel = 100.0 / 8.0 * (2.0 if self.hambrienta else 1.0) * (1.0 + 0.5 * len(self.cacas))
        self.felicidad -= ritmo_fel * h
        if self.durmiendo:
            self.energia += 100.0 / 3.0 * h
            if self.energia >= 100:
                eventos.append("despierta")
        else:
            self.energia -= 100.0 / 14.0 * h
        self._limitar()

        if t >= self.prox_caca:
            eventos.append("caca")
            self.prox_caca = t + random.uniform(30, 60) * 60
        if self.caca_tras_comer is not None and t >= self.caca_tras_comer:
            eventos.append("caca")
            self.caca_tras_comer = None
        return eventos

    def _limitar(self):
        self.saciedad = min(100.0, max(0.0, self.saciedad))
        self.felicidad = min(100.0, max(0.0, self.felicidad))
        self.energia = min(100.0, max(0.0, self.energia))

    # -- acciones ---------------------------------------------------------
    def comer_lechuga(self):
        self.saciedad += 25
        self.felicidad += 3
        self._tras_comer()

    def comer_archivo(self, tam_bytes):
        """Cuanto más grande el archivo, más llena (entre 8 y 30)."""
        kb = max(1.0, tam_bytes / 1024.0)
        self.saciedad += min(30.0, 8.0 + 2.0 * math.log2(kb))
        self.felicidad += 4
        self.archivos_comidos += 1
        self._tras_comer()

    def _tras_comer(self):
        if self.caca_tras_comer is None:
            self.caca_tras_comer = ahora() + random.uniform(10, 20) * 60
        self._limitar()
        self.guardar()

    def caricia(self):
        self.felicidad += 8
        self._limitar()
        self.guardar()

    def jugar(self):
        self.felicidad += 15
        self.energia -= 6
        self.saciedad -= 3
        self._limitar()
        self.guardar()

    def recoger_caca(self, indice):
        if 0 <= indice < len(self.cacas):
            self.cacas.pop(indice)
        self.felicidad += 2
        self._limitar()
        self.guardar()

    def dormir(self):
        self.durmiendo = True
        self.guardar()

    def despertar(self):
        self.durmiendo = False
        self.guardar()

    def reset(self):
        self.saciedad, self.felicidad, self.energia = 80.0, 80.0, 90.0
        self.durmiendo = False
        self.cacas = []
        self.guardar()

    # -- guardado ---------------------------------------------------------
    _CAMPOS = ("saciedad", "felicidad", "energia", "durmiendo", "cacas", "prox_caca",
               "caca_tras_comer", "archivos_comidos", "silencio", "posicion",
               "nombre", "nombre_preguntado", "inicio_configurado")

    def guardar(self):
        datos = {k: getattr(self, k) for k in self._CAMPOS}
        datos["tamano"] = self.escala    # "escala" era el tamaño de la 1.0 (ya no se lee)
        datos["ultimo_real"] = time.time()
        tmp = self._ruta + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=1)
            os.replace(tmp, self._ruta)
        except OSError:
            pass

    def cargar(self):
        try:
            with open(self._ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except (OSError, ValueError):
            return
        for k in self._CAMPOS:
            if k in datos:
                setattr(self, k, datos[k])
        self.escala = datos.get("tamano", ESCALA_DEFECTO)
        self.nombre = str(self.nombre or "")[:24]
        # el tiempo con el programa cerrado también cuenta (con tope)
        if "ultimo_real" in datos:
            fuera = max(0.0, time.time() - float(datos["ultimo_real"])) * config.VELOCIDAD_TIEMPO
            self._ultimo = ahora() - min(fuera, MAX_AUSENCIA)
        # los temporizadores guardados con otra VELOCIDAD_TIEMPO no tienen sentido
        t = ahora()
        if not isinstance(self.prox_caca, (int, float)) or abs(self.prox_caca - t) > 2 * HORA:
            self.prox_caca = t + random.uniform(30, 60) * 60
        if self.caca_tras_comer is not None and abs(self.caca_tras_comer - t) > 2 * HORA:
            self.caca_tras_comer = None
        self.cacas = [list(c) for c in self.cacas][:MAX_CACAS]
        try:
            self.escala = int(self.escala) if int(self.escala) in (2, 3, 4, 5, 6) else ESCALA_DEFECTO
        except (TypeError, ValueError):
            self.escala = ESCALA_DEFECTO
        self._limitar()
