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
    from PySide6.QtWidgets import (QApplication, QInputDialog, QMenu, QMessageBox,
                                   QSystemTrayIcon)

    from . import __version__
    from .actualizar import Actualizador, limpiar_restos
    from .arte import ACCESORIOS, ESTILOS
    from .manada import Manada
    from .mascota import MAX_COBAYAS, Ajustes
    from .sonido import Sonidos
    from .ventana import DESPERTANDO, DURMIENDO, YENDO_A_DORMIR

    app = QApplication(sys.argv)
    app.setApplicationName(config.NOMBRE)
    app.setQuitOnLastWindowClosed(False)

    ajustes = Ajustes()
    sonidos = Sonidos()
    sonidos.silencio = ajustes.silencio
    manada = Manada(ajustes, sonidos, QGuiApplication.primaryScreen().devicePixelRatio())
    primera = manada.cobayas[0]
    icono = QIcon(primera.spr.icono(2))
    app.setWindowIcon(icono)
    bandeja = None
    limpiar_restos()
    act = Actualizador()
    aviso = {"estado": None, "manual": False}

    def portavoz():
        """La cobaya que da los avisos (la primera que esté despierta)."""
        for c in manada.cobayas:
            if c.estado not in (DURMIENDO, YENDO_A_DORMIR):
                return c
        return manada.cobayas[0]

    def actualizar_icono():
        nuevo = QIcon(manada.cobayas[0].spr.icono(2))
        app.setWindowIcon(nuevo)
        if bandeja is not None:
            bandeja.setIcon(nuevo)
            nombres = [c.m.nombre for c in manada.cobayas if c.m.nombre]
            bandeja.setToolTip(", ".join(nombres) or "Tamacuychi")

    def poner_aspecto(c, estilo=None, hueco=None, valor=None):
        """Cambia el estilo o un accesorio de una cobaya y la vuelve a dibujar."""
        if estilo is not None:
            c.m.estilo = estilo
        if hueco is not None:
            if valor:
                c.m.accesorios[hueco] = valor
            else:
                c.m.accesorios.pop(hueco, None)
        c.spr.configurar(c.m.estilo, c.m.accesorios)
        c.m.guardar()
        actualizar_icono()
        if valor or estilo:
            c.caricia_gratis()

    def buscar_actualizacion(manual=False):
        if act.ocupado:
            return
        aviso["manual"] = manual
        if manual:
            portavoz().decir("Mirando...", dur=10)
        act.buscar()

    def revisar_actualizacion():
        """Lo que pasa con la actualización, visto desde el hilo de Qt (cada segundo)."""
        est = act.estado
        if est == "descargando":
            portavoz().decir("Descargando %d%%" % int(act.progreso * 100), dur=2)
            return
        if est == aviso["estado"]:
            return
        aviso["estado"] = est
        if est == "nueva":
            v = act.nueva["version"]
            portavoz().decir("¡Versión %s!" % v, dur=5)
            if bandeja is not None:
                bandeja.showMessage("Tamacuychi", "Hay una versión nueva (%s). Clic derecho en "
                                    "una cobaya → Actualizar." % v, icono)
        elif est == "al_dia" and aviso["manual"]:
            portavoz().decir("¡Estoy al día!", dur=3)
        elif est == "error" and (aviso["manual"] or act.nueva):
            portavoz().decir("No se pudo :(", dur=3)
            print("Tamacuychi: actualización:", act.error, file=sys.stderr)
        elif est == "lista":
            portavoz().decir("¡Hasta ahora!", dur=3)
            manada.guardar()
            if act.instalar():
                QTimer.singleShot(400, salir)

    def poner_nombre(c, pregunta="¿Cómo se llama tu cobaya?"):
        nombre, ok = QInputDialog.getText(None, "Tamacuychi", pregunta, text=c.m.nombre)
        c.m.nombre_preguntado = True
        if ok:
            c.m.nombre = nombre.strip()[:24]
            c.decir((c.m.nombre + "!") if c.m.nombre else "cui!", dur=2.5)
            c.mostrar_barras(3)
        c.m.guardar()
        c.setWindowTitle(c.m.nombre or "Tamacuychi")
        actualizar_icono()

    def anadir_cobaya():
        if manada.llena:
            return
        nombre, ok = QInputDialog.getText(None, "Tamacuychi", "¿Cómo se llama la cobaya nueva?")
        if not ok:
            return
        manada.anadir(nombre.strip())
        actualizar_icono()

    def despedir(c):
        nombre = c.m.nombre or "esta cobaya"
        r = QMessageBox.question(None, "Tamacuychi", "¿Seguro que quieres despedirte de %s?\n"
                                 "Se borrarán su nombre, su aspecto y sus estadísticas." % nombre)
        if r == QMessageBox.Yes:
            manada.quitar(c)
            actualizar_icono()

    # La primera vez, la cobaya se apunta sola al inicio de Windows
    if sys.platform == "win32" and not ajustes.inicio_configurado:
        try:
            inicio_windows(True)
        except OSError as e:
            print("No se pudo activar el inicio con Windows:", e, file=sys.stderr)
        ajustes.inicio_configurado = True
        ajustes.guardar()

    def salir():
        manada.cerrar()
        app.quit()

    # --- menús -------------------------------------------------------------
    def menu_cobaya(menu, c):
        """Lo que se puede hacer con una cobaya concreta."""
        m = c.m

        def accion(texto, fn, activa=True):
            a = menu.addAction(texto)
            a.triggered.connect(fn)
            a.setEnabled(activa)
            return a

        durmiendo = c.estado in (DURMIENDO, YENDO_A_DORMIR, DESPERTANDO)
        titulo = menu.addAction("🐹  " + (m.nombre or "Sin nombre"))
        titulo.setEnabled(False)
        info = menu.addAction("Saciedad %d%%  ·  Felicidad %d%%  ·  Energía %d%%"
                              % (m.saciedad, m.felicidad, m.energia))
        info.setEnabled(False)
        if m.archivos_comidos:
            a = menu.addAction("Archivos comidos: %d" % m.archivos_comidos)
            a.setEnabled(False)
        menu.addSeparator()
        accion("🥬  Darle lechuga", c.dar_lechuga, not durmiendo)
        if c.estado == DURMIENDO:
            accion("☀  Despertar", c.despertar)
        else:
            accion("🌙  A dormir", c.dormir, not durmiendo)
        accion("🍿  ¡A jugar! (popcorning)", c.popcorn, not durmiendo)
        accion("🎵  Cui", lambda: c.cui(), not durmiendo)
        accion("📍  Ven aquí", c.llamar, not durmiendo)
        menu.addSeparator()
        accion("✏  Ponerle nombre…" if not m.nombre else "✏  Cambiar el nombre…",
               lambda: poner_nombre(c))

        est = menu.addMenu("🎨  Estilo")
        grupo_est = QActionGroup(est)
        for clave, (nombre, _) in ESTILOS.items():
            a = est.addAction(nombre)
            a.setCheckable(True)
            a.setChecked(m.estilo == clave)
            a.setActionGroup(grupo_est)
            a.triggered.connect(lambda _=False, k=clave: poner_aspecto(c, estilo=k))

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
                a.triggered.connect(
                    lambda _=False, h=hueco, k=clave: poner_aspecto(c, hueco=h, valor=k))
        if any(m.accesorios.values()):
            accs.addSeparator()
            quitar = accs.addAction("Quitárselo todo")
            quitar.triggered.connect(lambda: [poner_aspecto(c, hueco=h) for h in ACCESORIOS])
        if len(manada.cobayas) > 1:
            accion("👋  Despedirse de %s…" % (m.nombre or "esta cobaya"), lambda: despedir(c))

    def menu_comun(menu):
        """Lo que afecta a todas las cobayas y al programa."""
        def accion(texto, fn, activa=True):
            a = menu.addAction(texto)
            a.triggered.connect(fn)
            a.setEnabled(activa)
            return a

        n = len(manada.cobayas)
        if n > 1:
            accion("🥬  Lechuga para todas", manada.lechuga_para_todas)
            accion("📍  Llamarlas a todas", manada.llamar_todas)
        total_cacas = sum(len(c.cacas) for c in manada.cobayas)
        accion("🧹  Recoger cacas (%d)" % total_cacas, manada.recoger_cacas, bool(total_cacas))
        accion("➕  Añadir otra cobaya (%d/%d)" % (n, MAX_COBAYAS), anadir_cobaya,
               not manada.llena)
        menu.addSeparator()

        tam = menu.addMenu("Tamaño")
        grupo = QActionGroup(tam)
        for nombre, e in (("Pequeña", 2), ("Mediana", 3), ("Normal", 4), ("Grande", 5), ("Enorme", 6)):
            a = tam.addAction(nombre)
            a.setCheckable(True)
            a.setChecked(ajustes.escala == e)
            a.setActionGroup(grupo)
            a.triggered.connect(lambda _=False, e=e: manada.cambiar_escala(e))

        son = menu.addAction("Sonido")
        son.setCheckable(True)
        son.setChecked(not ajustes.silencio)

        def cambiar_sonido(activo):
            ajustes.silencio = not activo
            sonidos.silencio = ajustes.silencio
            ajustes.guardar()
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
        auto.setChecked(bool(ajustes.buscar_actualizaciones))

        def cambiar_auto(activo):
            ajustes.buscar_actualizaciones = activo
            ajustes.guardar()
        auto.toggled.connect(cambiar_auto)
        ver = menu.addAction("Versión " + __version__)
        ver.setEnabled(False)
        menu.addSeparator()
        accion("Salir", salir)

    menu_contextual = QMenu()

    def menu_de(c):
        """Clic derecho sobre una cobaya: sus cosas y después las comunes."""
        menu_contextual.clear()
        menu_cobaya(menu_contextual, c)
        menu_contextual.addSeparator()
        menu_comun(menu_contextual)
        return menu_contextual

    manada.menu_fn = menu_de

    def menu_de_bandeja(menu):
        menu.clear()
        if len(manada.cobayas) == 1:
            menu_cobaya(menu, manada.cobayas[0])
        else:
            for c in manada.cobayas:
                sub = menu.addMenu("🐹  " + (c.m.nombre or "Sin nombre"))
                menu_cobaya(sub, c)
        menu.addSeparator()
        menu_comun(menu)

    if QSystemTrayIcon.isSystemTrayAvailable():
        bandeja = QSystemTrayIcon(icono)
        menu_bandeja = QMenu()
        menu_bandeja.aboutToShow.connect(lambda: menu_de_bandeja(menu_bandeja))
        menu_de_bandeja(menu_bandeja)
        bandeja.setContextMenu(menu_bandeja)
        bandeja.activated.connect(
            lambda motivo: manada.llamar_todas() if motivo == QSystemTrayIcon.Trigger else None)
        bandeja.show()

    actualizar_icono()
    manada.mostrar()
    app.aboutToQuit.connect(manada.guardar)

    # Si se vuelve a abrir el programa, las cobayas que ya están vienen
    llamada = QTimer()
    llamada.timeout.connect(lambda: manada.llamar_todas() if instancia.la_llaman() else None)
    if instancia.evento:
        llamada.start(1000)

    if not primera.m.nombre_preguntado:
        QTimer.singleShot(1500, lambda: poner_nombre(primera))

    # Actualizaciones: al minuto de arrancar y cada 6 horas
    vigila_act = QTimer()
    vigila_act.timeout.connect(revisar_actualizacion)
    vigila_act.start(1000)

    def busqueda_automatica():
        if ajustes.buscar_actualizaciones and act.estado not in ("nueva", "descargando", "lista"):
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
