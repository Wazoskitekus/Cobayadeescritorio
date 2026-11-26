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


# ---------------------------------------------------------------------------
# Una sola cobaya a la vez (Windows): si ya hay una, se la avisa para que venga
# ---------------------------------------------------------------------------
_MUTEX = "Local\\TamacuychiMutex"       # también lo usa instalador.iss (AppMutex)
_EVENTO = "Local\\TamacuychiVenAqui"


class _Instancia:
    def __init__(self):
        self.evento = None
        if sys.platform != "win32":
            self.primera = True
            return
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW.restype = ctypes.c_void_p
        k32.CreateEventW.restype = ctypes.c_void_p
        self._k32 = k32
        self._mutex = k32.CreateMutexW(None, False, _MUTEX)
        self.primera = k32.GetLastError() != 183          # ERROR_ALREADY_EXISTS
        self.evento = k32.CreateEventW(None, False, False, _EVENTO)
        if not self.primera and self.evento:
            k32.SetEvent(ctypes.c_void_p(self.evento))

    def la_llaman(self):
        if not self.evento:
            return False
        import ctypes
        return self._k32.WaitForSingleObject(ctypes.c_void_p(self.evento), 0) == 0


def liberar_memoria():
    """Devuelve a Windows la memoria que ya no se está usando."""
    import gc
    gc.collect()
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = ctypes.c_void_p
            k32.K32EmptyWorkingSet(ctypes.c_void_p(k32.GetCurrentProcess()))
        except (AttributeError, OSError):
            pass


def main():
    _preparar_entorno()
    instancia = _Instancia()
    if not instancia.primera:
        return 0           # ya hay una cobaya: le hemos pedido que venga y salimos
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QActionGroup, QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QSystemTrayIcon

    from . import __version__
    from .actualizar import Actualizador, limpiar_restos
    from .arte import ACCESORIOS, ESTILOS
    from .mascota import Mascota
    from .sonido import Sonidos
    from .sprites import Sprites
    from .ventana import DESPERTANDO, DURMIENDO, YENDO_A_DORMIR, Cobaya

    app = QApplication(sys.argv)
    app.setApplicationName(config.NOMBRE)
    app.setQuitOnLastWindowClosed(False)

    mascota = Mascota()
    sprites = Sprites(mascota.estilo, mascota.accesorios)
    sprites.dpr = QGuiApplication.primaryScreen().devicePixelRatio()
    sonidos = Sonidos()
    cobaya = Cobaya(mascota, sprites, sonidos)
    icono = QIcon(sprites.icono(2))
    app.setWindowIcon(icono)
    bandeja = None
    limpiar_restos()
    act = Actualizador()
    aviso = {"estado": None, "manual": False}

    def poner_aspecto(estilo=None, hueco=None, valor=None):
        """Cambia el estilo o un accesorio y vuelve a dibujar la cobaya."""
        if estilo is not None:
            mascota.estilo = estilo
        if hueco is not None:
            if valor:
                mascota.accesorios[hueco] = valor
            else:
                mascota.accesorios.pop(hueco, None)
        sprites.configurar(mascota.estilo, mascota.accesorios)
        nuevo = QIcon(sprites.icono(2))
        app.setWindowIcon(nuevo)
        if bandeja is not None:
            bandeja.setIcon(nuevo)
        mascota.guardar()
        if valor or estilo:
            cobaya.caricia_gratis()

    def buscar_actualizacion(manual=False):
        if act.ocupado:
            return
        aviso["manual"] = manual
        if manual:
            cobaya.decir("Mirando...", dur=10)
        act.buscar()

    def revisar_actualizacion():
        """Lo que pasa con la actualización, visto desde el hilo de Qt (cada segundo)."""
        est = act.estado
        if est == "descargando":
            cobaya.decir("Descargando %d%%" % int(act.progreso * 100), dur=2)
            return
        if est == aviso["estado"]:
            return
        aviso["estado"] = est
        if est == "nueva":
            v = act.nueva["version"]
            cobaya.decir("¡Versión %s!" % v, dur=5)
            if bandeja is not None:
                bandeja.showMessage("Tamacuychi", "Hay una versión nueva (%s). Clic derecho en "
                                    "la cobaya → Actualizar." % v, icono)
        elif est == "al_dia" and aviso["manual"]:
            cobaya.decir("¡Estoy al día!", dur=3)
        elif est == "error" and (aviso["manual"] or act.nueva):
            cobaya.decir("No se pudo :(", dur=3)
            print("Tamacuychi: actualización:", act.error, file=sys.stderr)
        elif est == "lista":
            cobaya.decir("¡Hasta ahora!", dur=3)
            mascota.guardar()
            if act.instalar():
                QTimer.singleShot(400, salir)

    def actualizar_nombre():
        nombre = mascota.nombre or "Tamacuychi"
        cobaya.setWindowTitle(nombre)
        if bandeja is not None:
            bandeja.setToolTip(nombre)

    def poner_nombre():
        nombre, ok = QInputDialog.getText(None, "Tamacuychi", "¿Cómo se llama tu cobaya?",
                                          text=mascota.nombre)
        mascota.nombre_preguntado = True
        if ok:
            mascota.nombre = nombre.strip()[:24]
            cobaya.decir((mascota.nombre + "!") if mascota.nombre else "cui!", dur=2.5)
            cobaya.mostrar_barras(3)
        mascota.guardar()
        actualizar_nombre()

    # La primera vez, la cobaya se apunta sola al inicio de Windows
    if sys.platform == "win32" and not mascota.inicio_configurado:
        try:
            inicio_windows(True)
        except OSError as e:
            print("No se pudo activar el inicio con Windows:", e, file=sys.stderr)
        mascota.inicio_configurado = True
        mascota.guardar()

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
        if m.nombre:
            titulo = menu.addAction("🐹  " + m.nombre)
            titulo.setEnabled(False)
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
        accion("✏  Ponerle nombre…" if not m.nombre else "✏  Cambiar el nombre…", poner_nombre)

        est = menu.addMenu("🎨  Estilo")
        grupo_est = QActionGroup(est)
        for clave, (nombre, _) in ESTILOS.items():
            a = est.addAction(nombre)
            a.setCheckable(True)
            a.setChecked(m.estilo == clave)
            a.setActionGroup(grupo_est)
            a.triggered.connect(lambda _=False, k=clave: poner_aspecto(estilo=k))

        accs = menu.addMenu("🎩  Accesorios")
        titulos = {"cabeza": "Cabeza", "cara": "Cara", "cuerpo": "Cuerpo"}
        for hueco, opciones in ACCESORIOS.items():
            sub = accs.addMenu(titulos[hueco])
            grupo_acc = QActionGroup(sub)
            for clave, nombre in [(None, "Nada")] + opciones:
                a = sub.addAction(nombre)
                a.setCheckable(True)
                a.setChecked(m.accesorios.get(hueco) == clave)
                a.setActionGroup(grupo_acc)
                a.triggered.connect(lambda _=False, h=hueco, k=clave: poner_aspecto(hueco=h, valor=k))
        if any(m.accesorios.values()):
            accs.addSeparator()
            quitar = accs.addAction("Quitárselo todo")
            quitar.triggered.connect(lambda: [poner_aspecto(hueco=h) for h in ACCESORIOS])

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
                except OSError as e:
                    print("No se pudo cambiar el inicio con Windows:", e, file=sys.stderr)
            ini.toggled.connect(cambiar_inicio)

        menu.addSeparator()
        if act.estado == "nueva":
            accion("⬆  Actualizar a la versión %s" % act.nueva["version"], act.descargar)
        elif act.estado == "descargando":
            accion("⬇  Descargando… %d%%" % int(act.progreso * 100), lambda: None, False)
        else:
            accion("🔄  Buscar actualizaciones", lambda: buscar_actualizacion(True), not act.ocupado)
        auto = menu.addAction("Buscar actualizaciones sola")
        auto.setCheckable(True)
        auto.setChecked(bool(m.buscar_actualizaciones))

        def cambiar_auto(activo):
            m.buscar_actualizaciones = activo
            m.guardar()
        auto.toggled.connect(cambiar_auto)
        ver = menu.addAction("Versión " + __version__)
        ver.setEnabled(False)
        menu.addSeparator()
        accion("Salir", salir)
        return menu

    menu_contextual = QMenu()
    cobaya.menu_fn = lambda: construir_menu(menu_contextual)

    if QSystemTrayIcon.isSystemTrayAvailable():
        bandeja = QSystemTrayIcon(icono)
        menu_bandeja = QMenu()
        menu_bandeja.aboutToShow.connect(lambda: construir_menu(menu_bandeja))
        construir_menu(menu_bandeja)
        bandeja.setContextMenu(menu_bandeja)
        bandeja.activated.connect(
            lambda motivo: cobaya.llamar() if motivo == QSystemTrayIcon.Trigger else None)
        bandeja.show()

    actualizar_nombre()
    cobaya.show()
    app.aboutToQuit.connect(lambda: mascota.guardar())

    # Si se vuelve a abrir el programa, la cobaya que ya está viene
    llamada = QTimer()
    llamada.timeout.connect(lambda: cobaya.llamar() if instancia.la_llaman() else None)
    if instancia.evento:
        llamada.start(1000)

    if not mascota.nombre_preguntado:
        QTimer.singleShot(1500, poner_nombre)

    # Actualizaciones: al minuto de arrancar y cada 6 horas
    vigila_act = QTimer()
    vigila_act.timeout.connect(revisar_actualizacion)
    vigila_act.start(1000)

    def busqueda_automatica():
        if mascota.buscar_actualizaciones and act.estado not in ("nueva", "descargando", "lista"):
            buscar_actualizacion(False)
    QTimer.singleShot(60 * 1000, busqueda_automatica)
    cada_6h = QTimer()
    cada_6h.timeout.connect(busqueda_automatica)
    cada_6h.start(6 * 3600 * 1000)

    # Memoria: al terminar de arrancar y cada 30 minutos
    QTimer.singleShot(8000, liberar_memoria)
    limpieza = QTimer()
    limpieza.timeout.connect(liberar_memoria)
    limpieza.start(30 * 60 * 1000)

    latido = QTimer()
    if sys.platform != "win32":
        # Ctrl+C en la consola cierra guardando
        signal.signal(signal.SIGINT, lambda *_: salir())
        latido.timeout.connect(lambda: None)   # deja que Python atienda las señales
        latido.start(500)
    return app.exec()
