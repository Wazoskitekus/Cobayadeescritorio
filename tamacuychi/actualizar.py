"""Actualizaciones desde las Releases de GitHub.

- Instalada (con el instalador): descarga el instalador nuevo y lo ejecuta en
  silencio; el instalador cierra esta cobaya y abre la nueva.
- Portable (Tamacuychi-portable.exe): descarga el .exe nuevo, renombra el que
  está en marcha (Windows lo permite) y pone el nuevo en su sitio.
- Desde el código: abre la página de la Release.

Todo lo de red va en un hilo aparte para no congelar la cobaya, y se importa
solo al buscar (urllib y ssl ocupan unos MB).
"""

import os
import re
import sys
import threading

from . import __version__, config

REPO = "Wazoskitekus/Cobayadeescritorio"
API = "https://api.github.com/repos/%s/releases/latest" % REPO
PAGINA = "https://github.com/%s/releases/latest" % REPO


def _version(texto):
    nums = re.findall(r"\d+", texto or "")
    return tuple(int(n) for n in nums[:3]) if nums else (0,)


def modo():
    """'instalada', 'portable' o 'codigo'."""
    if not getattr(sys, "frozen", False):
        return "codigo"
    carpeta = os.path.dirname(sys.executable)
    if os.path.exists(os.path.join(carpeta, "unins000.exe")):
        return "instalada"
    return "portable"


def _contexto_ssl():
    """Certificados para hablar con GitHub.

    1. truststore: usa el verificador del propio Windows, que descarga solo los
       certificados raíz que le falten (el Python empaquetado no lo hace).
    2. certifi: lista de certificados que va dentro del programa.
    3. Lo que traiga Python.
    """
    import ssl
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_ABRIDOR = None


def _abrir(url, timeout=20, binario=False):
    global _ABRIDOR
    import urllib.request
    if _ABRIDOR is None:
        _ABRIDOR = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_contexto_ssl()))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Tamacuychi/" + __version__,
        "Accept": "application/octet-stream" if binario else "application/vnd.github+json",
    })
    return _ABRIDOR.open(req, timeout=timeout)


def _motivo(e):
    """Explicación corta del error para el bocadillo."""
    import ssl
    import urllib.error
    if isinstance(e, ssl.SSLError) or "CERTIFICATE" in str(e).upper():
        return "certificado"
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (403, 429):
            return "GitHub ocupado"
        return "GitHub %d" % e.code
    if isinstance(e, urllib.error.URLError):
        if isinstance(e.reason, ssl.SSLError) or "CERTIFICATE" in str(e.reason).upper():
            return "certificado"
        return "sin conexión"
    if isinstance(e, (TimeoutError, OSError)):
        return "sin conexión"
    return "error"


def registrar(texto):
    """Apunta en registro.txt (en la carpeta de datos) lo que ha pasado."""
    import time
    ruta = os.path.join(config.carpeta_datos(), "registro.txt")
    try:
        lineas = []
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8", errors="replace") as f:
                lineas = f.read().splitlines()[-300:]
        lineas.append(time.strftime("%Y-%m-%d %H:%M:%S ") + texto)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
    except OSError:
        pass


def _fallo(act, e):
    import traceback
    act.error = str(e)
    act.motivo = _motivo(e)
    registrar("Tamacuychi %s: actualización (%s): %s\n%s" % (
        __version__, act.motivo, e, traceback.format_exc()))
    act.estado = "error"


class Actualizador:
    """Se usa desde el hilo de Qt; el trabajo de red va en otro hilo.

    El hilo deja el resultado en self.estado y la interfaz lo consulta.
    estado: None | "buscando" | "al_dia" | "nueva" | "descargando" | "lista" | "error"
    """

    def __init__(self):
        self.estado = None
        self.nueva = None          # {"version", "url", "tam", "sha256", "pagina"}
        self.progreso = 0.0
        self.error = ""
        self.motivo = ""
        self.intento = 0           # cambia en cada búsqueda o descarga (para la interfaz)
        self.ruta_descarga = None
        self._hilo = None

    @property
    def ocupado(self):
        return self._hilo is not None and self._hilo.is_alive()

    # -- buscar -------------------------------------------------------------
    def buscar(self):
        if self.ocupado:
            return
        self.estado = "buscando"
        self.intento += 1
        self._hilo = threading.Thread(target=self._buscar, daemon=True)
        self._hilo.start()

    def _buscar(self):
        import json
        try:
            with _abrir(API) as r:
                datos = json.load(r)
            version = (datos.get("tag_name") or "").lstrip("v")
            if _version(version) <= _version(__version__):
                self.estado = "al_dia"
                return
            patron = "Tamacuychi-portable" if modo() == "portable" else "Tamacuychi-instalador"
            activo = next((a for a in datos.get("assets", [])
                           if a.get("name", "").startswith(patron)
                           and a.get("name", "").endswith(".exe")), None)
            digest = (activo or {}).get("digest") or ""
            self.nueva = {
                "version": version,
                # enlace de la API: sirve igual en repositorios públicos y privados
                "url": activo and (activo.get("url") or activo.get("browser_download_url")),
                "nombre": activo and activo.get("name"),
                "tam": (activo or {}).get("size", 0),
                "sha256": digest[7:] if digest.startswith("sha256:") else None,
                "pagina": datos.get("html_url") or PAGINA,
            }
            self.estado = "nueva"
        except Exception as e:      # sin internet, GitHub caído, etc.
            _fallo(self, e)

    # -- descargar ------------------------------------------------------------
    def descargar(self):
        if self.ocupado or not self.nueva:
            return
        if modo() == "codigo" or not self.nueva.get("url"):
            import webbrowser
            webbrowser.open(self.nueva.get("pagina") or PAGINA)
            return
        self.estado = "descargando"
        self.intento += 1
        self.progreso = 0.0
        self._hilo = threading.Thread(target=self._descargar, daemon=True)
        self._hilo.start()

    def _descargar(self):
        import hashlib
        n = self.nueva
        carpeta = os.path.join(config.carpeta_datos(), "actualizacion")
        try:
            os.makedirs(carpeta, exist_ok=True)
            destino = os.path.join(carpeta, n["nombre"])
            h = hashlib.sha256()
            recibido = 0
            with _abrir(n["url"], timeout=60, binario=True) as r, open(destino + ".part", "wb") as f:
                while True:
                    trozo = r.read(256 * 1024)
                    if not trozo:
                        break
                    f.write(trozo)
                    h.update(trozo)
                    recibido += len(trozo)
                    if n["tam"]:
                        self.progreso = recibido / n["tam"]
            if n["tam"] and recibido != n["tam"]:
                raise IOError("descarga incompleta")
            if n["sha256"] and h.hexdigest().lower() != n["sha256"].lower():
                raise IOError("el archivo descargado no coincide")
            os.replace(destino + ".part", destino)
            self.ruta_descarga = destino
            self.estado = "lista"
        except Exception as e:
            _fallo(self, e)

    # -- instalar (hilo de Qt; después hay que cerrar la aplicación) ------------
    def instalar(self):
        """Lanza la versión nueva. Devuelve True si hay que salir ya."""
        ruta = self.ruta_descarga
        if not ruta or not os.path.exists(ruta):
            return False
        import subprocess
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        if modo() == "instalada":
            subprocess.Popen([ruta, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                             creationflags=flags, close_fds=True)
            return True
        # portable: cambiar el .exe en marcha por el nuevo
        actual = sys.executable
        viejo = actual + ".viejo"
        try:
            if os.path.exists(viejo):
                os.remove(viejo)
            os.replace(actual, viejo)
            os.replace(ruta, actual)
        except OSError as e:
            self.intento += 1
            _fallo(self, e)
            return False
        subprocess.Popen([actual], creationflags=flags, close_fds=True)
        return True


def limpiar_restos():
    """Borra el .exe viejo de la versión portable y descargas ya usadas."""
    if getattr(sys, "frozen", False):
        viejo = sys.executable + ".viejo"
        if os.path.exists(viejo):
            try:
                os.remove(viejo)
            except OSError:
                pass
    carpeta = os.path.join(config.carpeta_datos(), "actualizacion")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            try:
                os.remove(os.path.join(carpeta, nombre))
            except OSError:
                pass
