"""Rutas y ajustes globales."""

import os
import sys

NOMBRE = "Tamacuychi"


def _velocidad():
    if "--rapido" in sys.argv:
        return 60.0
    try:
        return float(os.environ.get("TAMACUYCHI_VELOCIDAD", "1"))
    except ValueError:
        return 1.0


# Multiplicador del paso del tiempo (60 = 1 minuto por segundo, para pruebas).
VELOCIDAD_TIEMPO = _velocidad()


def carpeta_datos():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    ruta = os.path.join(base, NOMBRE)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def carpeta_programa():
    """Carpeta donde están tamacuychi.pyw y sprites/ (o el .exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carpeta_sprites():
    """sprites/ junto al programa; dentro del .exe, la copia empaquetada."""
    junto = os.path.join(carpeta_programa(), "sprites")
    if os.path.isdir(junto):
        return junto
    empaquetada = os.path.join(getattr(sys, "_MEIPASS", ""), "sprites")
    return empaquetada if os.path.isdir(empaquetada) else junto
