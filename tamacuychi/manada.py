"""Varias cobayas a la vez (hasta 4) y lo que hacen juntas.

Cada cobaya es su propia ventana (ventana.Cobaya) con su propio estado
(mascota.Mascota). La manada las crea, las guarda y decide cuándo se juntan:

- Se buscan: una cobaya aburrida va a ver a otra.
- Se saludan: dos cobayas cerca se huelen y salen corazones.
- Juegan al pillapilla: una persigue a la otra hasta pillarla.
- Popcorning contagioso: si una salta, las demás se animan.
- Cui en coro: cuando una hace cui, otras contestan.
- Comen juntas: al dar lechuga a una, las que tienen hambre se acercan a comer.
- Sueño contagioso: si una se va a dormir, las que tienen sueño también.
"""

import random

from PySide6.QtCore import QTimer

from .arte import ESTILOS
from .mascota import MAX_COBAYAS, Mascota
from .sprites import Sprites
from .ventana import Cobaya


class Manada:
    def __init__(self, ajustes, sonidos, dpr):
        self.ajustes, self.snd, self.dpr = ajustes, sonidos, dpr
        self.cobayas = []
        self.menu_fn = None            # lo pone app.py: fn(cobaya) -> QMenu
        for ident in list(ajustes.cobayas):
            self._crear(Mascota(ident))
        self._reloj = QTimer()
        self._reloj.timeout.connect(self._social)
        self._reloj.start(1000)

    # -- altas y bajas ---------------------------------------------------------
    def _crear(self, m):
        spr = Sprites(m.estilo, m.accesorios)
        spr.dpr = self.dpr
        c = Cobaya(m, spr, self.snd, self.ajustes.escala, self)
        c.menu_fn = lambda c=c: self.menu_fn(c) if self.menu_fn else None
        c.setWindowTitle(m.nombre or "Tamacuychi")
        self.cobayas.append(c)
        return c

    @property
    def llena(self):
        return len(self.cobayas) >= MAX_COBAYAS

    def anadir(self, nombre=""):
        """Una cobaya nueva que cae desde arriba. Devuelve la cobaya o None."""
        if self.llena:
            return None
        ident = self.ajustes.nuevo_id()
        m = Mascota(ident)
        m.reset()
        m.nombre = nombre[:24]
        m.nombre_preguntado = True
        # un estilo que no tenga ninguna otra, si queda alguno
        usados = {c.m.estilo for c in self.cobayas}
        libres = [k for k in ESTILOS if k not in usados] or list(ESTILOS)
        m.estilo = random.choice(libres)
        m.guardar()
        self.ajustes.cobayas.append(ident)
        self.ajustes.guardar()
        c = self._crear(m)
        c.show()
        g = c._pantalla()
        c.llamar(random.uniform(g.left() + g.width() * 0.2, g.right() - g.width() * 0.2))
        c.decir("¡Hola!" if not nombre else "¡%s!" % nombre, dur=3)
        return c

    def quitar(self, c):
        """Se despide una cobaya (siempre queda al menos una)."""
        if len(self.cobayas) <= 1 or c not in self.cobayas:
            return
        for o in self.cobayas:
            if o._pareja is c:
                o._fin_juego(False)
        self.cobayas.remove(c)
        c.cerrar()
        c.m.borrar()
        self.ajustes.cobayas = [o.m.ident for o in self.cobayas]
        self.ajustes.guardar()

    def mostrar(self):
        for c in self.cobayas:
            c.show()

    def cerrar(self):
        self._reloj.stop()
        for c in self.cobayas:
            c.cerrar()

    # -- todas a la vez ------------------------------------------------------------
    def cambiar_escala(self, e):
        self.ajustes.escala = e
        self.ajustes.guardar()
        for c in self.cobayas:
            c.cambiar_escala(e)

    def llamar_todas(self):
        g = self.cobayas[0]._pantalla() if self.cobayas else None
        for i, c in enumerate(self.cobayas):
            x = None
            if g is not None:
                x = g.center().x() + (i - (len(self.cobayas) - 1) / 2) * 50 * c.e
            c.llamar(x)

    def lechuga_para_todas(self):
        for c in self.cobayas:
            c.dar_lechuga(compartir=False)

    def recoger_cacas(self):
        for c in self.cobayas:
            c.recoger_cacas()

    def guardar(self):
        for c in self.cobayas:
            c.m.posicion = [c.px, c.py]
            c.m.guardar()

    # -- lo que pasa entre ellas ------------------------------------------------------
    def _otras(self, c, libres=True):
        return [o for o in self.cobayas if o is not c and (o.libre or not libres)]

    def _misma_pantalla(self, a, b):
        return a._pantalla() == b._pantalla()

    def aviso(self, evento, c):
        """Una cobaya cuenta lo que hace; las demás reaccionan."""
        otras = [o for o in self._otras(c) if self._misma_pantalla(o, c)]
        if evento == "cui":
            for o in otras:
                if random.random() < 0.55:
                    QTimer.singleShot(random.randint(500, 1400),
                                      lambda o=o: o.cui(avisar=False) if o.libre else None)
        elif evento == "popcorn":
            for o in otras:
                if not o.m.muy_cansada and random.random() < 0.7:
                    QTimer.singleShot(random.randint(200, 900),
                                      lambda o=o: o.popcorn(contagio=True) if o.libre else None)
        elif evento == "lechuga":
            for o in otras:
                if o.m.saciedad < 90:
                    lado = random.choice((-1, 1)) * random.uniform(22, 34) * o.e
                    o.ir_a(c.px + lado, al_llegar=lambda o=o: o.dar_lechuga(compartir=False))
                    o.decir("¡ñam!", dur=1.5)
        elif evento == "dormir":
            for o in otras:
                if o.m.energia < 60 and random.random() < 0.5:
                    QTimer.singleShot(random.randint(1500, 4000),
                                      lambda o=o: o.dormir(contagio=True) if o.libre else None)

    def _social(self):
        """Cada segundo: a ver si a alguna le apetece hacer algo con otra."""
        if len(self.cobayas) < 2:
            return
        for c in self.cobayas:
            if not c.libre or c.estado != "reposo":
                continue
            otras = [o for o in self._otras(c) if self._misma_pantalla(o, c)]
            if not otras:
                continue
            o = min(otras, key=lambda o: abs(o.px - c.px))
            dist = abs(o.px - c.px)
            cerca = dist < 60 * c.e
            nariz = 34 * c.e          # distancia entre centros con las narices juntas
            animadas = (c.m.felicidad > 45 and o.m.felicidad > 45
                        and not c.m.muy_cansada and not o.m.muy_cansada)
            r = random.random()
            if cerca and o.estado == "reposo" and r < 0.05:
                # se acerca hasta tocar narices y entonces se saludan las dos
                lado = -1 if c.px < o.px else 1
                o._mirando = 0
                c.ir_a(o.px + lado * nariz,
                       al_llegar=lambda c=c, o=o: self._saludo(c, o))
            elif animadas and o.estado in ("reposo", "andar") and r < 0.03:
                persigue = random.random() < 0.5
                c.pillapilla(o, persigue)
                o.pillapilla(c, not persigue)
                return
            elif not cerca and r < 0.04:
                # va a ver a la otra (se queda a su lado)
                lado = -1 if c.px < o.px else 1
                c.ir_a(o.px + lado * random.uniform(40, 52) * c.e)

    def _saludo(self, c, o):
        if o.estado in ("reposo", "andar", "cui") and c.estado == "reposo" \
                and abs(o.px - c.px) < 60 * c.e:
            c.saludar(o)
            o.saludar(c)
