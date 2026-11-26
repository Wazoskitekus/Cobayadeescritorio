# Tamacuychi para PC

La cobaya del Tamacuychi, ahora viviendo en el escritorio del ordenador. Anda por
encima de la barra de tareas, hace "cui", se come los archivos que le das (los
manda a la papelera), hace *popcorning* por la pantalla cuando la tocas y deja
cacas que hay que recoger.

Funciona en **Windows** (el objetivo principal), macOS y Linux (X11).

![Estados](art/estados.png)

## Instalar en Windows

1. Ve a **[Releases](https://github.com/Wazoskitekus/Cobayadeescritorio/releases/latest)**.
2. Descarga **`Tamacuychi-instalador-X.Y.Z.exe`** y ábrelo.
3. Si aparece "Windows protegió su PC", pulsa **Más información → Ejecutar de todas formas**
   (sale porque el programa no está firmado digitalmente).
4. Elige si quieres acceso directo en el escritorio.

La cobaya **arranca sola al encender el ordenador** (se puede quitar en su menú:
*Iniciar con Windows*). La primera vez pregunta cómo se llama. Si abres el
programa cuando ya está en marcha, no sale otra: la que hay viene a la pantalla
principal.

No pide permisos de administrador: se instala en `%LOCALAPPDATA%\Programs\Tamacuychi`
y se desinstala desde *Configuración → Aplicaciones*. Si no quieres instalar nada,
descarga **`Tamacuychi-portable.exe`**, que funciona con doble clic.

Los .exe los compila GitHub Actions (`.github/workflows/windows.yml`) en cada
cambio de `main` y los publica en Releases con la versión de
`tamacuychi/__init__.py`. Para sacar una versión nueva, sube ese número
(por ejemplo a `1.0.1`); si no cambia, se actualizan los archivos de la misma Release.

## Arrancar desde el código

Doble clic en `iniciar.bat` (Windows), o:

```bash
pip install -r requirements.txt
```

```bash
python tamacuychi.pyw
```

Para crear el instalador en tu PC: `construir_exe.bat` y después
`iscc instalador.iss` ([Inno Setup 6](https://jrsoftware.org/isinfo.php)).

Para probar con el tiempo acelerado (1 minuto por segundo):

```bash
python tamacuychi.pyw --rapido
```

## Qué se puede hacer con ella

| Acción | Qué pasa |
|---|---|
| **Clic** sobre ella | *Popcorning*: de 4 a 8 saltos de distinta altura por la pantalla, girándose en el aire (+15 felicidad, −6 energía, −3 saciedad). Si está muy cansada, no juega. |
| **Arrastrar** un archivo y soltarlo encima | Abre la boca al olerlo y **se lo come**: mordiscos al icono del archivo, migas y "ñam". El archivo va a la **papelera** (se puede recuperar). Llena más cuanto más grande es (de +8 a +30 de saciedad). |
| **Pasar el ratón** por encima de un lado a otro | Caricia: corazones (+8 felicidad). |
| **Cogerla** (pulsar y mover) | La levantas; al soltarla cae con gravedad y rebota. Se puede lanzar. |
| Clic en una **caca** | La recoge con destellos (+2 felicidad). |
| Clic en el **bocadillo de lechuga** | Le das lechuga (+25 saciedad). |
| Clic mientras **duerme** | Se despierta: sale del heno, se estira y bosteza. |
| **Clic derecho** (o el icono de la bandeja) | Menú: lechuga, dormir/despertar, jugar, cui, recoger cacas, "ven aquí", nombre, tamaño (por defecto *Pequeña*), sonido, iniciar con Windows y salir. |

Al pasar el ratón por encima aparecen su nombre y tres barras: saciedad (naranja),
felicidad (rosa) y energía (amarilla). Parpadean en rojo por debajo del 30 %.

### Qué no se come (por seguridad)

Nunca borra nada para siempre. Si no puede mandarlo a la papelera, no se lo come
y pone cara triste:

- **Carpetas**: "¡Carpetas no!"
- Archivos de más de **2 GB** (pueden no caber en la papelera): "¡Es enorme!"
- En Windows, archivos de **memorias USB o unidades de red**, que no tienen papelera: "De ahí no como".
- Si Windows no deja moverlo (archivo abierto, permisos...): "No puedo morderlo".

Al soltar, el programa siempre le dice al Explorador "copiar", nunca "mover",
para que el Explorador no borre el original por su cuenta.

## Varias cobayas

Clic derecho → **Añadir otra cobaya** (hasta 4). Cada una tiene su nombre, su
estilo, sus accesorios y sus estadísticas, y llega cayendo desde arriba. Juntas:

- **Se buscan** y se quedan cerca unas de otras.
- **Se saludan** nariz con nariz, con corazones (+5 de felicidad).
- **Juegan al pillapilla**: una persigue a otra hasta pillarla (+10 de felicidad).
- **Popcorning contagioso**: si una salta, las demás se animan.
- **Cui en coro**: cuando una hace cui, las otras contestan.
- **Comen juntas**: al darle lechuga a una, las que tienen hambre se acercan y comen a su lado.
- **Sueño contagioso**: si una se va a dormir, las que tienen sueño también.

El clic derecho sobre una cobaya muestra su menú (con *Despedirse de…* para
quitarla) y debajo lo común: *Lechuga para todas*, *Llamarlas a todas*, tamaño,
sonido... En el icono de la bandeja hay un submenú por cobaya.

![Varias cobayas](art/manada.png)

## Estilos y accesorios

En el menú (clic derecho): **Estilo** (tricolor, negra, marrón o espacial, con
antenas) y **Accesorios**: en la cabeza sombrero, gorro de fiesta, corona o lazo;
en la cara gafas de sol; y en el cuerpo mochila o bufanda. Se pueden combinar uno
de cada sitio, y se ven de frente, de perfil y de espaldas.

![Estilos y accesorios](art/estilos_y_accesorios.png)

## Actualizaciones

La cobaya mira en GitHub si hay una versión nueva al minuto de arrancar y cada
6 horas (se puede desactivar: *Buscar actualizaciones sola*). Si la hay, lo dice
con un bocadillo y aparece **Actualizar a la versión X** en el menú. Al pulsarlo:

- **Instalada**: descarga el instalador, comprueba su huella SHA-256, lo ejecuta
  en silencio y la cobaya vuelve a abrirse ya actualizada.
- **Portable**: descarga el .exe nuevo y lo pone en lugar del viejo.

Si falla, el bocadillo dice por qué ("sin conexión", "certificado", "GitHub
ocupado") y el menú ofrece **Abrir la página de descargas**. El detalle queda en
`registro.txt`, en la carpeta de datos (`%APPDATA%\Tamacuychi` en Windows).

Para que funcione en cualquier PC, **el repositorio tiene que ser público**: si es
privado, GitHub no deja ver las Releases sin iniciar sesión.

## Comportamiento propio

Igual que en el firmware:

- **Desgaste**: la saciedad se vacía en 10 h, la felicidad en 8 h (el doble de rápido con hambre y un 50 % más por cada caca) y la energía en 16 h despierta. **Durmiendo recarga en 20 minutos** y se despierta sola.
- El tiempo con el programa cerrado también cuenta (hasta 12 h).
- **Cacas**: una cada 30–60 min y otra 10–20 min después de comer, como mucho 4, en el suelo a su lado, con líneas de olor.
- **Descuidada** (saciedad < 25, felicidad < 30 o 3 cacas o más): cara triste y anda más despacio. Con hambre pide lechuga con un bocadillo.
- **Cui**: de 1 a 3 silbidos que suben de tono, con bocadillo "cui!". Cada 1–3 min, o cada 15–35 s si tiene hambre.
- **Anda** sola de un lado a otro por encima de la barra de tareas, mira a los lados y parpadea.
- Muy contenta, a veces hace *popcorning* sola.
- **Siestas**: con la energía por debajo de 20 se va a dormir sola, y por debajo de 50 echa alguna siesta (nunca en los 45 minutos siguientes a despertarse). Por debajo de 10 no quiere jugar.
- **Dormir**: aparece el heno, se da la vuelta (frente, perfil, espaldas), camina hacia él haciéndose pequeña y se mete dentro; el heno respira, asoman las orejas y salen zetas.

Se guarda todo en `%APPDATA%\Tamacuychi\estado.json` (Windows),
`~/Library/Application Support/Tamacuychi` (macOS) o `~/.config/Tamacuychi` (Linux).

## Estructura

```
tamacuychi.pyw          arranque (doble clic en Windows, sin consola)
tamacuychi/
  app.py                aplicación, bandeja del sistema, menús, iniciar con Windows
  ventana.py            la cobaya: estados, animaciones, ratón, arrastrar y soltar
  mascota.py            estadísticas, desgaste, cacas y guardado (sin Qt)
  papelera.py           comprobaciones y envío seguro a la papelera
  cacas.py              ventanitas de las cacas
  manada.py             varias cobayas y lo que hacen juntas
  sonido.py             cui, bostezo, ñam... sintetizados a WAV
  actualizar.py         busca, descarga e instala versiones nuevas desde GitHub
  arte.py               pixel art generado por código, estilos y accesorios (sin Qt)
  sprites.py            escalado entero y nítido, PNG opcionales de sprites/
  config.py             rutas y velocidad del tiempo
herramientas/
  exportar_sprites.py   arte -> sprites_generados/*.png e icono.ico
sprites/                PNG que sustituyen al arte generado (opcional)
construir_exe.bat       crea dist\Tamacuychi\Tamacuychi.exe con PyInstaller
instalador.iss          instalador de Windows (Inno Setup)
iniciar.bat             arranca desde el código en Windows
.github/workflows/      compila el instalador y el portable en GitHub
```

## Retocar el arte

El dibujo está hecho por código en `tamacuychi/arte.py` (elipses sin suavizado
con contorno automático, ojos y boca como sellos de píxeles). Para retocarlo a mano:

```bash
python herramientas/exportar_sprites.py
```

Abre el PNG que quieras de `sprites_generados/` en Aseprite, edítalo y cópialo a
`sprites/` con el mismo nombre. El programa usa el de `sprites/` en lugar del
generado. Sirven también los PNG del firmware (`cobaya_idle@2.png`,
`cobaya_feliz@2.png`...): la cobaya se apoya por el centro de la fila de abajo,
así que no importa que midan distinto.

![Sprites](art/sprites.png)

## Memoria y CPU (pensado para equipos con poca RAM)

- No carga QtMultimedia (unos 25 MB con FFmpeg): los sonidos van con `winsound`
  en Windows y con `afplay`/`paplay` en el resto.
- Dibuja a 60 fotogramas por segundo solo al saltar o caer; quieta, a 12, y
  dormida, a 8. Las cacas se redibujan a 8 por segundo.
- Los sprites escalados se guardan en una caché pequeña (48 como máximo).
- En Windows, al terminar de arrancar y cada 30 minutos, devuelve al sistema la
  memoria que ya no usa.
- Medido en Linux: unos 56 MB con una cobaya y unos 61 MB con cuatro, de los que unos 50 MB son Qt (una
  ventana de Qt vacía ya ocupa eso). La versión 1.0 ocupaba unos 80 MB.

## Notas técnicas

- **Qt (PySide6)**: ventana sin marco, siempre encima, transparente píxel a píxel y
  fuera de la barra de tareas. En Windows y macOS los píxeles transparentes dejan
  pasar el ratón; en Linux X11 se usa una máscara con las zonas visibles.
- **Pixel art nítido**: escalado entero en píxeles físicos, también con Windows al 125 % o 150 %.
- **Sonido**: los WAV se generan la primera vez; en Windows se reproducen con `winsound`.
- **Una sola instancia** (Windows): un mutex con nombre; la segunda copia avisa a
  la primera con un evento para que venga y se cierra.
- **Papelera**: `Send2Trash` (en Windows con `pywin32`, que además se niega a
  borrar si el archivo no cabe en la papelera).
- **Wayland**: las ventanas no pueden moverse solas, así que en Linux se fuerza XWayland.
