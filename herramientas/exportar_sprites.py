"""Exporta el arte generado a PNG para retocarlo (por ejemplo en Aseprite).

    python herramientas/exportar_sprites.py

Crea sprites_generados/<nombre>@N.png (N fotogramas en horizontal, 1 píxel = 1
píxel de arte). Para usar uno retocado, cópialo a sprites/ con el mismo nombre:
el programa lo carga en lugar del generado. También crea icono.ico.
"""
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from tamacuychi import arte  # noqa: E402


def _png(w, h, rgba):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, "x.png")
        arte.guardar_png(ruta, w, h, rgba)
        with open(ruta, "rb") as f:
            return f.read()


def _reducir(rgba, lado, nuevo):
    """Remuestreo al vecino más cercano de una imagen cuadrada RGBA."""
    out = bytearray()
    for y in range(nuevo):
        sy = y * lado // nuevo
        for x in range(nuevo):
            sx = x * lado // nuevo
            i = (sy * lado + sx) * 4
            out += rgba[i:i + 4]
    return bytes(out)


def _dib(lado, rgba):
    """Entrada de icono clásica (BMP de 32 bits), la que entiende cualquier herramienta."""
    cab = struct.pack("<IiiHHIIiiII", 40, lado, lado * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    filas = b""
    for y in range(lado - 1, -1, -1):          # de abajo arriba
        for x in range(lado):
            r, g, b, a = rgba[(y * lado + x) * 4:(y * lado + x) * 4 + 4]
            filas += bytes((b, g, r, a))
    mascara = b"\x00" * (((lado + 31) // 32) * 4 * lado)
    return cab + filas + mascara


def icono(ruta):
    cara = arte.frente()
    lado = 34
    filas = ["." * lado] * (lado - len(cara))
    filas += [("." * ((lado - len(f)) // 2) + f).ljust(lado, ".") for f in cara]
    # 256x256: la cobaya a 7x (238 px) centrada
    _, _, grande = arte.a_rgba(filas, 7)
    m = (256 - 238) // 2
    lienzo = bytearray(256 * 256 * 4)
    for y in range(238):
        lienzo[((y + m) * 256 + m) * 4:((y + m) * 256 + m + 238) * 4] = grande[y * 238 * 4:(y + 1) * 238 * 4]
    lienzo = bytes(lienzo)
    entradas = [(_dib(t, _reducir(lienzo, 256, t)), t) for t in (16, 24, 32, 48, 64, 128)]
    entradas.append((_png(256, 256, lienzo), 256))
    cab = struct.pack("<HHH", 0, 1, len(entradas))
    desp = 6 + 16 * len(entradas)
    dir_, datos = b"", b""
    for blob, tam in entradas:
        t = 0 if tam >= 256 else tam
        dir_ += struct.pack("<BBBBHHII", t, t, 0, 0, 1, 32, len(blob), desp + len(datos))
        datos += blob
    with open(ruta, "wb") as f:
        f.write(cab + dir_ + datos)


def main():
    salida = os.path.join(RAIZ, "sprites_generados")
    os.makedirs(salida, exist_ok=True)
    for nombre, fotogramas in arte.catalogo().items():
        sufijo = "@%d" % len(fotogramas) if len(fotogramas) > 1 else ""
        w, h, datos = arte.a_rgba(arte.hoja(fotogramas))
        arte.guardar_png(os.path.join(salida, nombre + sufijo + ".png"), w, h, datos)
    icono(os.path.join(RAIZ, "icono.ico"))
    print("Sprites en", salida, "e icono.ico creado")


if __name__ == "__main__":
    main()
