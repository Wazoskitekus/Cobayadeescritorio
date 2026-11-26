# Tamacuychi PC: contexto del proyecto

Continuación de `CONTEXTO_TAMAGOYCUI.md` (el firmware para ESP32-S3). Esto es la
versión de escritorio: la misma cobaya viviendo en el escritorio del PC. Si
empiezas una conversación nueva, adjunta este archivo y di en qué quieres seguir.

- **Repositorio:** https://github.com/Wazoskitekus/Cobayadeescritorio (rama `main`).
  El firmware sigue en https://github.com/Wazoskitekus/Tamacuychi.
- **Instalador de Windows:** lo compila GitHub Actions (`.github/workflows/windows.yml`):
  PyInstaller (carpeta) + Inno Setup (`instalador.iss`) y además un .exe portable.
  Cada push a `main` lo publica en Releases con la versión de `tamacuychi/__init__.py`.
- **Estado:** probado en Linux sin pantalla (Qt *offscreen*): todos los estados,
  clic, arrastrar, caricias, soltar archivos (van de verdad a la papelera), cacas,
  dormir y despertar, y un ejecutable de PyInstaller que arranca. **Falta probarlo
  en un Windows real** (transparencia, sonido con winsound, iconos de archivo,
  arrastrar desde el Explorador).

## Decisiones

- **Python 3 + PySide6 (Qt 6)**: ventanas transparentes y sin marco en Windows,
  macOS y Linux, arrastrar y soltar archivos, bandeja del sistema. Se empaqueta en
  un .exe con PyInstaller y se instala con Inno Setup, sin permisos de
  administrador, en `%LOCALAPPDATA%\Programs\Tamacuychi`.
- **Arte**: no había acceso al repositorio (es privado), así que la cobaya
  tricolor se redibujó por código en `tamacuychi/arte.py`: elipses sin suavizado,
  contorno automático, y ojos y boca como sellos. Vista de frente (33×30), de
  perfil para andar (38×26) y de espaldas. Los PNG de `sprites/` sustituyen al
  arte generado, así que valen los del firmware.
- **Escala**: entera (2 a 6, por defecto 2) y en píxeles físicos.
- **Papelera**: `Send2Trash`, solo archivos sueltos, como mucho 2 GB y, en
  Windows, solo de discos fijos. Al soltar se responde siempre "copiar".
- **Sonido**: la partitura del firmware (barridos con armónico) sintetizada a WAV
  de 48 kHz; `winsound` en Windows y `afplay`/`paplay` en el resto.
- **Mismas cifras que el firmware** en desgaste, cacas, cui y descuido.

## Versión 1.1

- Tamaño por defecto *Pequeña* (escala 2). Se guarda como `tamano` en
  `estado.json` (la 1.0 guardaba `escala` siempre, así que se ignora).
- Nombre: se pregunta la primera vez y se cambia en el menú; sale encima de las
  barras, en el menú y en el icono de la bandeja.
- Arranca con Windows: el instalador lo activa siempre y el programa lo activa la
  primera vez que se abre (`inicio_configurado`); se quita en el menú.
- Una sola instancia (mutex `Local\TamacuychiMutex`); abrirlo otra vez trae la cobaya.
- Poca RAM: sin QtMultimedia, menos fotogramas en reposo, caché de sprites
  limitada y recorte de memoria en Windows. Unos 59 MB (Qt solo ya son unos 50).
- El instalador cierra la cobaya abierta antes de actualizar.

## Versión 1.2

- **Actualizaciones** (`actualizar.py`): consulta la API de Releases de GitHub al
  minuto y cada 6 h; descarga el instalador por la API (enlace del asset con
  `Accept: application/octet-stream`), comprueba tamaño y SHA-256, lo ejecuta con
  `/VERYSILENT` y el instalador vuelve a abrir la cobaya. La portable cambia su
  propio .exe (renombra el que está en marcha a `.viejo`). **El repositorio es
  privado: así no funciona en otros PC; hay que hacerlo público** (o publicar las
  Releases en otro repositorio público).
- **Estilos** (`arte.ESTILOS`): tricolor, negra, marrón y espacial (verde con
  antenas, basada en una foto del usuario). Solo cambian las letras de la paleta;
  las patas (`F`) y la nariz (`N`) tienen letra propia.
- **Accesorios** (`arte.ACCESORIOS`): cabeza (sombrero, gorro, corona, lazo),
  cara (gafas) y cuerpo (mochila, bufanda). Se dibujan con `arte.vestir()` en cada
  vista (frente, perfil, espalda) buscando dónde está la cabeza.
- **Sueño**: recarga en 45 min, se cansa en 8 h, se duerme sola por debajo de 30
  y echa siestas por debajo de 75.
- Windows bloqueaba el instalador en otro PC por no estar firmado; la solución
  definitiva es firmarlo (SignPath Foundation es gratis si el repositorio es público).

## Comportamiento

Clic → popcorning por la pantalla (4–8 saltos de 40–280 px girándose en el
aire); archivo soltado encima → se lo come mordiendo el icono y va a la papelera;
ratón de lado a lado → caricia; pulsar y mover → la coges y al soltar cae y
rebota; anda sola por encima de la barra de tareas; cui; cacas en ventanitas;
duerme en el heno; barras de estado al pasar el ratón; menú con clic derecho y en
la bandeja.

Estados (`ventana.py`): reposo, andar, comiendo, feliz, cui, popcorn, cogida,
cayendo, aterriza, negar, yendo_a_dormir, durmiendo, despertando.

## Ideas pendientes

- Subirse y andar por encima de las ventanas abiertas (como los *shimeji*).
- Que persiga el cursor o huya de él.
- Sincronizar el estado con la placa ESP32 o con el servidor del usuario (MQTT).
- Grabación real de un "cui".
- Comer otras cosas: texto o imágenes arrastradas desde el navegador.
- Firmar el .exe para que Windows no avise al instalar.
