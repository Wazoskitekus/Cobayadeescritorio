"""Mandar a la papelera lo que se come la cobaya, sin borrar nunca nada para siempre.

Reglas:
- Solo archivos sueltos (las carpetas no se las come).
- Como mucho TAM_MAXIMO (los archivos enormes pueden no caber en la papelera
  y Windows los borraría del todo).
- En Windows, solo de discos locales fijos: las memorias USB y las unidades de
  red no tienen papelera.
- Si la papelera falla por lo que sea, el archivo se queda donde estaba.
"""

import os
import sys

TAM_MAXIMO = 2 * 1024 ** 3   # 2 GB


def _unidad_sin_papelera(ruta):
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        raiz = os.path.splitdrive(ruta)[0]
        if not raiz or raiz.startswith("\\\\"):
            return True            # ruta de red (\\servidor\...)
        tipo = ctypes.windll.kernel32.GetDriveTypeW(raiz + "\\")
        return tipo != 3           # DRIVE_FIXED
    except Exception:
        return True


def revisar(ruta):
    """Devuelve (se_puede, motivo, tamaño)."""
    ruta = os.path.abspath(ruta)
    if not os.path.lexists(ruta):
        return False, "no_existe", 0
    if os.path.isdir(ruta) and not os.path.islink(ruta):
        return False, "carpeta", 0
    try:
        tam = os.path.getsize(ruta)
    except OSError:
        tam = 0
    if tam > TAM_MAXIMO:
        return False, "grande", tam
    if _unidad_sin_papelera(ruta):
        return False, "sin_papelera", tam
    return True, "", tam


def a_la_papelera(ruta):
    """Devuelve (ok, motivo)."""
    ok, motivo, _ = revisar(ruta)
    if not ok:
        return False, motivo
    try:
        from send2trash import send2trash
    except ImportError:
        return False, "falta_send2trash"
    ruta = os.path.abspath(ruta)
    try:
        send2trash(ruta)
    except Exception as e:  # permisos, archivo abierto, etc.
        return False, "error: %s" % e
    if os.path.lexists(ruta):
        return False, "sigue_ahi"
    return True, ""
