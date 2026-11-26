"""Arranque: aplicación Qt, icono en la bandeja y menús."""

import os
import signal
import sys

from . import config


def _preparar_entorno():
    # En Wayland una ventana no puede moverse sola: se usa XWayland.
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY") \
            and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"


# ---------------------------------------------------------------------------
# Iniciar con Windows (clave Run del registro del usuario)
# ---------------------------------------------------------------------------
_CLAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _orden_arranque():
    if getattr(sys, "frozen", False):
        return '"%s"' % sys.executable
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    script = os.path.join(config.carpeta_programa(), "tamacuychi.pyw")
    return '"%s" "%s"' % (pyw, script)


def inicio_windows_activo():
    """Mira el registro (lo puede haber activado el instalador)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _CLAVE_RUN) as k:
            winreg.QueryValueEx(k, config.NOMBRE)
        return True
    except OSError:
        return False


def inicio_windows(activar):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _CLAVE_RUN, 0, winreg.KEY_SET_VALUE) as k:
        if activar:
            winreg.SetValueEx(k, config.NOMBRE, 0, winreg.REG_SZ, _orden_arranque())
        else:
            try:
                winreg.DeleteValue(k, config.NOMBRE)
            except FileNotFoundError:
                pass


def main():
    _preparar_entorno()
    from PySide6.QtGui import QActionGroup, QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

    from .mascota import Mascota
    from .sonido import Sonidos
    from .sprites import Sprites
    from .ventana import DESPERTANDO, DURMIENDO, YENDO_A_DORMIR, Cobaya

    app = QApplication(sys.argv)
    app.setApplicationName(config.NOMBRE)
    app.setQuitOnLastWindowClosed(False)

    mascota = Mascota()
    sprites = Sprites()
    sprites.dpr = QGuiApplication.primaryScreen().devicePixelRatio()
    sonidos = Sonidos()
    cobaya = Cobaya(mascota, sprites, sonidos)
    icono = QIcon(sprites.icono(2))
    app.setWindowIcon(icono)

    def salir():
        cobaya.cerrar()
        app.quit()

    def construir_menu(menu=None):
        menu = menu or QMenu()
        menu.clear()
        m = mascota

        def accion(texto, fn, activa=True):
            a = menu.addAction(texto)
            a.triggered.connect(fn)
            a.setEnabled(activa)
            return a

        durmiendo = cobaya.estado in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO)
        info = menu.addAction("Saciedad %d%%  ·  Felicidad %d%%  ·  Energía %d%%"
                              % (m.saciedad, m.felicidad, m.energia))
        info.setEnabled(False)
        if m.archivos_comidos:
            a = menu.addAction("Archivos comidos: %d" % m.archivos_comidos)
            a.setEnabled(False)
        menu.addSeparator()
        accion("🥬  Darle lechuga", cobaya.dar_lechuga, not durmiendo)
        if cobaya.estado == DURMIENDO:
            accion("☀  Despertar", cobaya.despertar)
        else:
            accion("🌙  A dormir", cobaya.dormir, not durmiendo)
        accion("🍿  ¡A jugar! (popcorning)", cobaya.popcorn, not durmiendo)
        accion("🎵  Cui", lambda: cobaya.cui(), not durmiendo)
        accion("🧹  Recoger cacas (%d)" % len(cobaya.cacas), cobaya.recoger_cacas, bool(cobaya.cacas))
        accion("📍  Ven aquí", cobaya.llamar, not durmiendo)
        menu.addSeparator()

        tam = menu.addMenu("Tamaño")
        grupo = QActionGroup(tam)
        for nombre, e in (("Pequeña", 2), ("Mediana", 3), ("Normal", 4), ("Grande", 5), ("Enorme", 6)):
            a = tam.addAction(nombre)
            a.setCheckable(True)
            a.setChecked(cobaya.e == e)
            a.setActionGroup(grupo)
            a.triggered.connect(lambda _=False, e=e: cobaya.cambiar_escala(e))

        son = menu.addAction("Sonido")
        son.setCheckable(True)
        son.setChecked(not m.silencio)

        def cambiar_sonido(activo):
            m.silencio = not activo
            sonidos.silencio = m.silencio
            m.guardar()
        son.toggled.connect(cambiar_sonido)

        if sys.platform == "win32":
            ini = menu.addAction("Iniciar con Windows")
            ini.setCheckable(True)
            ini.setChecked(inicio_windows_activo())

            def cambiar_inicio(activo):
                try:
                    inicio_windows(activo)
                    m.inicio_windows = activo
                    m.guardar()
                except OSError as e:
                    print("No se pudo cambiar el inicio con Windows:", e, file=sys.stderr)
            ini.toggled.connect(cambiar_inicio)

        menu.addSeparator()
        accion("Salir", salir)
        return menu

    menu_contextual = QMenu()
    cobaya.menu_fn = lambda: construir_menu(menu_contextual)

    bandeja = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        bandeja = QSystemTrayIcon(icono)
        bandeja.setToolTip("Tamacuychi")
        menu_bandeja = QMenu()
        menu_bandeja.aboutToShow.connect(lambda: construir_menu(menu_bandeja))
        construir_menu(menu_bandeja)
        bandeja.setContextMenu(menu_bandeja)
        bandeja.activated.connect(
            lambda motivo: cobaya.llamar() if motivo == QSystemTrayIcon.Trigger else None)
        bandeja.show()

    cobaya.show()
    app.aboutToQuit.connect(lambda: mascota.guardar())
    # Ctrl+C en la consola cierra guardando
    signal.signal(signal.SIGINT, lambda *_: salir())
    from PySide6.QtCore import QTimer
    latido = QTimer()
    latido.timeout.connect(lambda: None)   # deja que Python atienda las señales
    latido.start(300)
    return app.exec()
