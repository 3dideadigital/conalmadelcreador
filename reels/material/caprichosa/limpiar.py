"""Quita el cursor del visor 3D de la grabación de pantalla del cartel.

    python3 material/caprichosa/limpiar.py

La grabación (visor.mp4) se hizo girando el modelo con el ratón, así que en
casi todos los fotogramas aparece algún cursor: el de órbita (con una cruz
azul en el centro), la flecha, el de mover (cuatro flechas) o el de girar,
además del punto del pivote de órbita. Este script los localiza en cada
fotograma, los borra rellenando con los píxeles de alrededor y guarda los
fotogramas limpios en fotogramas/0001.jpg, 0002.jpg… (los usa la plantilla
«producto»).

Las formas de los cursores se recortan de fotogramas concretos de la propia
grabación, donde aparecen sobre fondo liso.
"""

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

AQUI = Path(__file__).resolve().parent
VIDEO = AQUI / "visor.mp4"
SALIDA = AQUI / "fotogramas"
W, H = 942, 654

# nombre: (fotograma, x0, y0, x1, y1, umbral de detección)
CURSORES = {
    "orbita": (16, 465, 343, 500, 376, 12),
    "flecha": (1, 480, 359, 497, 382, 15),
    "mover": (781, 605, 260, 639, 287, 60),
    # Es el trozo del cursor de órbita que queda a la vista cuando el resto
    # cae sobre el granate.
    "girar": (631, 589, 373, 600, 390, 40),
}
# Desplazamiento de la cruz azul respecto a la esquina del cursor de órbita.
CRUZ = (18, 16)
# Punto verde del pivote de órbita: fijo en pantalla mientras no se cambia el
# pivote. (centro, primer fotograma, último fotograma)
PUNTOS = [((484, 360), 1, 545), ((463, 409), 560, 665)]
RADIO_PUNTO = 7


def fotogramas():
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(VIDEO), "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        datos = proc.stdout.read(W * H * 3)
        if len(datos) < W * H * 3:
            break
        yield np.frombuffer(datos, np.uint8).reshape(H, W, 3)
    proc.wait()


def gris(a):
    return a[..., :3].astype(np.float64) @ np.array([0.299, 0.587, 0.114])


def preparar_cursores(todos):
    """Máscaras de cada cursor: trazo oscuro, anillo claro alrededor y zona a borrar."""
    plantillas = {}
    for nombre, (n, x0, y0, x1, y1, umbral) in CURSORES.items():
        a = todos[n - 1][y0:y1, x0:x1].astype(np.float64)
        g = gris(a)
        fondo = np.median(g)
        trazo = g < fondo - 55
        azul = (a[..., 2] - a[..., 0]) > 40
        anillo = ndi.binary_dilation(trazo, iterations=2) & ~ndi.binary_dilation(trazo, iterations=1)
        if nombre == "orbita":
            silueta = trazo | azul | (np.abs(g - fondo) > 18)
        else:
            silueta = ndi.binary_fill_holes(ndi.binary_dilation(trazo, iterations=1))
        # Margen generoso: la compresión del vídeo emborrona el cursor.
        plantillas[nombre] = dict(trazo=trazo, anillo=anillo, umbral=umbral,
                                  borrar=ndi.binary_dilation(silueta, iterations=3))
    return plantillas


def correlar(img, mascara):
    return fftconvolve(img, mascara[::-1, ::-1].astype(np.float64), mode="valid")


def puntuacion(g, p):
    """Contraste entre el anillo claro y el trazo oscuro, penalizando zonas con textura."""
    g2 = g * g
    nT, nA = p["trazo"].sum(), p["anillo"].sum()
    mT, mA = correlar(g, p["trazo"]) / nT, correlar(g, p["anillo"]) / nA
    vT = np.maximum(correlar(g2, p["trazo"]) / nT - mT * mT, 0)
    vA = np.maximum(correlar(g2, p["anillo"]) / nA - mA * mA, 0)
    return mA - mT - 0.7 * np.sqrt(vT) - 0.7 * np.sqrt(vA)


def cruz_azul(a):
    """Centro de la cruz azul del cursor de órbita (nada más en la escena es azul)."""
    a = a.astype(np.int16)
    azul = ((a[..., 2] - a[..., 0]) > 40) & (a[..., 2] > 150)
    etiquetas, n = ndi.label(azul)
    mejor = None
    for i in range(1, n + 1):
        ys, xs = np.nonzero(etiquetas == i)
        # La selección azul del QR es enorme; la cruz ocupa unos pocos píxeles.
        if 3 <= len(ys) <= 40 and (mejor is None or len(ys) > mejor[0]):
            mejor = (len(ys), int(round(xs.mean())), int(round(ys.mean())))
    return None if mejor is None else (mejor[1] - CRUZ[0], mejor[2] - CRUZ[1])


def buscar_cerca(g, p, cx, cy, radio):
    """Mejor posición del cursor en una ventana alrededor de (cx, cy)."""
    ph, pw = p["trazo"].shape
    x0, y0 = int(max(cx - radio, 0)), int(max(cy - radio, 0))
    s = puntuacion(g[y0:int(cy) + radio + ph, x0:int(cx) + radio + pw], p)
    y, x = np.unravel_index(np.argmax(s), s.shape)
    return x0 + int(x), y0 + int(y)


def detectar(todos, plantillas):
    """Posición (esquina superior izquierda) de cada cursor en cada fotograma, o None."""
    pos = {n: [None] * len(todos) for n in plantillas}
    for i, a in enumerate(todos):
        g = gris(a)
        for nombre, p in plantillas.items():
            if nombre == "orbita" and (c := cruz_azul(a)):
                # El halo azul desplaza un poco el centro: se afina con la forma.
                pos[nombre][i] = buscar_cerca(g, p, c[0], c[1], 6)
                continue
            s = puntuacion(g, p)
            y, x = np.unravel_index(np.argmax(s), s.shape)
            if s[y, x] > p["umbral"]:
                pos[nombre][i] = (int(x), int(y))
        if (i + 1) % 100 == 0:
            print(f"  detectados {i + 1}/{len(todos)}", flush=True)
    return pos


def rellenar_huecos(todos, plantillas, pos, hueco_max=45, radio=30):
    """Entre dos detecciones cercanas, busca el cursor en los fotogramas donde se
    pierde (p. ej. al pasar por encima del granate o del QR) alrededor de la
    trayectoria interpolada."""
    for nombre, p in plantillas.items():
        lista = pos[nombre]
        conocidos = [i for i, v in enumerate(lista) if v is not None]
        for a, b in zip(conocidos, conocidos[1:]):
            if b - a <= 1 or b - a > hueco_max:
                continue
            (xa, ya), (xb, yb) = lista[a], lista[b]
            if abs(xa - xb) + abs(ya - yb) > 220:
                continue
            for i in range(a + 1, b):
                f = (i - a) / (b - a)
                lista[i] = buscar_cerca(gris(todos[i]), p, xa + (xb - xa) * f, ya + (yb - ya) * f, radio)


def suavizar(pos, ventana=3, tolerancia=12):
    """Corrige saltos sueltos: el cursor se mueve de forma continua, así que una
    posición que se aparta de la mediana de sus vecinas es una detección falsa."""
    for lista in pos.values():
        originales = list(lista)
        for i, v in enumerate(originales):
            if v is None:
                continue
            vecinas = [p for p in originales[max(0, i - ventana): i + ventana + 1] if p is not None]
            if len(vecinas) < 3:
                continue
            mx, my = np.median([p[0] for p in vecinas]), np.median([p[1] for p in vecinas])
            if abs(v[0] - mx) + abs(v[1] - my) > tolerancia:
                lista[i] = (int(mx), int(my))


def inpaint(img, mascara, iteraciones=250):
    """Rellena la máscara difundiendo los colores del borde (relleno armónico)."""
    ys, xs = np.nonzero(mascara)
    if not len(ys):
        return
    y0, y1 = max(ys.min() - 2, 0), min(ys.max() + 3, H)
    x0, x1 = max(xs.min() - 2, 0), min(xs.max() + 3, W)
    sub = img[y0:y1, x0:x1]
    m = mascara[y0:y1, x0:x1]
    borde = ndi.binary_dilation(m) & ~m
    sub[m] = sub[borde].mean(0)
    for _ in range(iteraciones):
        media = (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1)) / 4
        sub[m] = media[m]


def main():
    print("Leyendo la grabación…")
    todos = list(fotogramas())
    plantillas = preparar_cursores(todos)
    print("Buscando cursores…")
    pos = detectar(todos, plantillas)
    rellenar_huecos(todos, plantillas, pos)
    suavizar(pos)

    yy, xx = np.mgrid[0:H, 0:W]
    SALIDA.mkdir(exist_ok=True)
    registro = []
    for i, a in enumerate(todos):
        mascara = np.zeros((H, W), bool)
        for (px, py), desde, hasta in PUNTOS:
            if desde <= i + 1 <= hasta:
                mascara |= (xx - px) ** 2 + (yy - py) ** 2 <= RADIO_PUNTO ** 2
        for nombre, p in plantillas.items():
            if pos[nombre][i] is None:
                continue
            x, y = pos[nombre][i]
            h, w = p["borrar"].shape
            mascara[y:y + h, x:x + w] |= p["borrar"][: H - y, : W - x]
            registro.append(f"{i + 1}\t{nombre}\t{x}\t{y}")
        img = a.astype(np.float64)
        inpaint(img, mascara)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(SALIDA / f"{i + 1:04d}.jpg", quality=94)
    (SALIDA / "cursores.tsv").write_text("fotograma\tcursor\tx\ty\n" + "\n".join(registro) + "\n")
    print(f"Listo: {len(todos)} fotogramas limpios en {SALIDA.relative_to(Path.cwd()) if SALIDA.is_relative_to(Path.cwd()) else SALIDA}")


if __name__ == "__main__":
    main()
