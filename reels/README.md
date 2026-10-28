# Reels animados — Con Alma del Creador

Fábrica de reels verticales (1080×1920, 30 fps) para Instagram.

## Cómo funciona

1. **Guion** (`guiones/*.json`): textos de cada escena, tiempos, estilo de cada línea y el texto de la publicación.
2. **Plantilla** (`plantillas/*.html`): el diseño animado de cada formato. Las piezas de marca comunes (tipografías, logo cruz-wifi, textos, cierre) están en `plantillas/comun.js` y `plantillas/comun.css`, así todos los reels mantienen la misma identidad.
3. **Render** (`render.mjs`): abre la plantilla en un navegador, la graba fotograma a fotograma y crea el vídeo.
4. **Música** (`musica/generar.py`): compone una banda sonora original (pad, piano, bajo y campanas) con los acordes y momentos que indica el guion en su apartado `musica`. Es música propia, sin derechos de autor.

```bash
npm install
pip install numpy scipy
node render.mjs guiones/01-desierto.json
node render.mjs guiones/01-desierto.json --solo-musica   # rehace solo el audio (segundos)
```

Resultado en `salida/<guion>/`:
- `reel.mp4` — el vídeo listo para subir, con su música.
- `portada.png` — la portada del reel.
- `publicacion.txt` — texto de la publicación, sugerencia de música y comentario para fijar.

## Plantillas

| Plantilla | Reel de ejemplo | Idea |
|---|---|---|
| `desierto` | `guiones/01-desierto.json` | Noche en el desierto con un amanecer que sube durante el reel. |
| `bateria` | `guiones/02-bateria.json` | Batería espiritual al 3 % que se conecta al logo y se carga al 100 %. Los tiempos van en el apartado `bateria` del guion. |
| `amanecer` | `guiones/04-amanecer.json` | Cielo que pasa de la noche a un amanecer cálido; se abre una puerta de luz y sale el sol. Para mensajes de esperanza. Tiempos en el apartado `amanecer` (puerta, sol e invitación a compartir a mitad del reel). |
| `carrusel` | `guiones/03-ansiedad.json` | Carrusel de imágenes 1080×1350 (`"formato": "carrusel"`): portada, versículos con reflexión, oración y cierre. Genera `01.jpg`, `02.jpg`… |
| `producto` | `guiones/06-caprichosa.json` | Para la parte de impresión 3D y producto para empresas: enseña una pieza con el material del cliente (fotogramas de vídeo y renders). Escenas a sangre o en tarjeta, chapas numeradas para los detalles, visor 3D, pasos de trabajo y cierre con botón. Estilo crema y granate, tipografías Bebas Neue, Cormorant y Montserrat. Ver «Reels de producto» más abajo. |

## Reels de producto (plantilla `producto`)

El material de cada pieza va en `material/<pieza>/` (vídeo, renders y su script de preparación). En el guion, `"material": "../material/<pieza>/"`.

**Preparar la grabación.** El vídeo de La Caprichosa es una grabación de pantalla del visor 3D, con el cursor del ratón encima. Antes de renderizar hay que quitarlo (tarda unos 5 minutos y deja `material/caprichosa/fotogramas/`, que no se sube al repositorio):

```bash
python3 material/caprichosa/limpiar.py
node render.mjs guiones/06-caprichosa.json
```

**Cada escena** indica:
- `fondo`: `crema`, `oscuro`, `acento` o `desenfocado`.
- `medio`: `{"video": [primerFotograma, últimoFotograma]}` (se reparte a lo largo de la escena: más fotogramas = más rápido) o `{"imagen": "archivo.webp"}`.
- `disposicion`: `completo` (a sangre), `tarjeta` o `visor` (tarjeta con interfaz de vista previa 3D).
- `encuadre`: `centro` (punto que se mantiene centrado, de 0 a 1), `zoom` inicial y final; en tarjeta también `ancho` e `y` (centro vertical).
- `oscurecer`: degradado para leer el texto sobre el vídeo, `[arriba, abajo]` o `[arriba, centro, abajo]`.
- `transicion`: `corte` (por defecto: golpe de zoom y destello) o `cortina` (panel granate).
- `textos`: estilos `etiqueta`, `titulo`, `acento`, `chapa` (caja con número, `"num": "01"`) y `servicios`; cada uno con `x`, `y`, `en`, `alinear`, `color`, `tam` y, si se quiere, `subrayar`.
- Piezas opcionales: `pasos` (lista numerada), `boton` (llamada a la acción) y `escaneo` (línea que recorre un QR).

La portada se diseña aparte en `portadaDiseno` (misma forma que una escena) y se activa con `"portada": -1`.

**Música con ritmo.** Con `"estilo": "ritmo"` en el apartado `musica`, `musica/ritmo.py` compone una base de 120 BPM (bombo, palmas, charles, bajo, piano eléctrico y arpegio) con subidas, golpes y barridos en los segundos que se indiquen, para que los cortes caigan a ritmo. También es música propia, sin derechos.

## Estilos de línea disponibles

`grande`, `oroGrande`, `normal`, `oro`, `cita`, `referencia`.
Cada línea puede llevar `"en": segundos` para aparecer en un momento concreto de su escena, y cada escena `"y"` para colocar su bloque de texto en vertical (por defecto, 840).

## Al subirlo a Instagram

- El vídeo ya lleva música original. Si se prefiere una canción de la biblioteca de Instagram, bajar a 0 el volumen del audio original al subirlo.
- Elegir `portada.png` como portada.
- Pegar el texto de `publicacion.txt` y fijar el comentario sugerido.

## Vista previa en el navegador

Servir esta carpeta (por ejemplo `npx http-server .`) y abrir
`plantillas/desierto.html?guion=../guiones/01-desierto.json`
(o `plantillas/bateria.html?guion=../guiones/02-bateria.json`).
