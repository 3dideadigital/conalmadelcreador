# Reels animados — Con Alma del Creador

Fábrica de reels verticales (1080×1920, 30 fps) para Instagram.

## Cómo funciona

1. **Guion** (`guiones/*.json`): textos de cada escena, tiempos, estilo de cada línea y el texto de la publicación.
2. **Plantilla** (`plantillas/*.html`): el diseño animado (fondo, tipografías, logo cruz-wifi).
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

## Estilos de línea disponibles (plantilla "desierto")

`grande`, `oroGrande`, `normal`, `oro`, `cita`, `referencia`.
Cada línea puede llevar `"en": segundos` para aparecer en un momento concreto de su escena.

## Al subirlo a Instagram

- El vídeo ya lleva música original. Si se prefiere una canción de la biblioteca de Instagram, bajar a 0 el volumen del audio original al subirlo.
- Elegir `portada.png` como portada.
- Pegar el texto de `publicacion.txt` y fijar el comentario sugerido.

## Vista previa en el navegador

Servir esta carpeta (por ejemplo `npx http-server .`) y abrir
`plantillas/desierto.html?guion=../guiones/01-desierto.json`.
