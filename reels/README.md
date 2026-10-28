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
| `escucha` | `guiones/06-salmo81.json` | Móvil lleno de notificaciones que entierran un mensaje de Dios; al silenciarlo se escucha. Después, ilustraciones de línea dorada que se dibujan solas (cruce de caminos, muro que cae, trigo y miel de la peña). |
| `carrusel` | `guiones/03-ansiedad.json` | Carrusel de imágenes 1080×1350 (`"formato": "carrusel"`): portada, versículos con reflexión, oración y cierre. Genera `01.jpg`, `02.jpg`… |

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
