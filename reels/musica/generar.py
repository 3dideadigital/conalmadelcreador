"""Compone la música de fondo de un reel a partir de su guion.

    python3 musica/generar.py guiones/01-desierto.json salida.wav

Toda la música se sintetiza aquí (pad cálido, piano suave, bajo y campanas),
así que es original y no tiene problemas de derechos. El guion indica los
acordes y en qué segundo entra cada uno, para que la armonía acompañe a las
escenas, y los momentos en los que suena una campana (p. ej. al encenderse
cada onda del logo).
"""

import json
import sys
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
NOTAS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
         "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def frecuencia(nota):
    nombre, octava = nota[:-1], int(nota[-1])
    midi = 12 * (octava + 1) + NOTAS[nombre]
    return 440.0 * 2 ** ((midi - 69) / 12)


def envolvente(n, ataque, salida):
    env = np.ones(n)
    a, s = int(ataque * SR), int(salida * SR)
    if a:
        env[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if s:
        env[-s:] *= np.cos(np.linspace(0, np.pi / 2, s)) ** 2
    return env


def pad(f, dur):
    """Pad cálido: armónicos suaves con un ligero desafinado (efecto coro)."""
    t = np.arange(int(dur * SR)) / SR
    señal = np.zeros_like(t)
    for desafinado in (-0.004, 0.0, 0.0035):
        for h, amp in ((1, 1.0), (2, 0.35), (3, 0.12), (4, 0.05)):
            fase = np.random.uniform(0, 2 * np.pi)
            vibrato = 1 + 0.0015 * np.sin(2 * np.pi * 0.2 * t + fase)
            señal += amp * np.sin(2 * np.pi * f * h * (1 + desafinado) * vibrato * t + fase)
    return señal / 4


def piano(f, dur=3.5):
    """Nota de piano sencilla: armónicos con caída exponencial."""
    t = np.arange(int(dur * SR)) / SR
    señal = np.zeros_like(t)
    for h in range(1, 7):
        inarmonia = h * (1 + 0.0004 * h * h)
        señal += (1 / h ** 1.6) * np.exp(-t * (1.2 + 0.9 * h)) * np.sin(2 * np.pi * f * inarmonia * t)
    return pasa_bajos(señal * envolvente(len(t), 0.008, 0.3), 6000)


def campana(f, dur=4.0):
    """Campana suave (parciales inarmónicos)."""
    t = np.arange(int(dur * SR)) / SR
    señal = np.zeros_like(t)
    for parcial, amp, caida in ((1, 1.0, 1.1), (2.76, 0.45, 2.0), (5.4, 0.22, 3.2), (8.93, 0.1, 4.5)):
        señal += amp * np.exp(-t * caida) * np.sin(2 * np.pi * f * parcial * t)
    return señal * envolvente(len(t), 0.003, 0.5)


def pasa_bajos(x, corte):
    return sosfilt(butter(2, corte, btype="low", fs=SR, output="sos"), x)


def pasa_altos(x, corte):
    return sosfilt(butter(2, corte, btype="high", fs=SR, output="sos"), x, axis=0)


def reverberacion(estereo, segundos=3.2, mezcla=0.38):
    n = int(segundos * SR)
    cola = np.exp(-np.linspace(0, 7, n))
    salida = np.zeros_like(estereo)
    for canal in range(2):
        ir = pasa_bajos(np.random.randn(n), 5000) * cola
        ir /= np.sqrt(np.sum(ir ** 2))
        salida[:, canal] = fftconvolve(estereo[:, canal], ir)[: len(estereo)]
    return (1 - mezcla) * estereo + mezcla * salida


def colocar(pista, señal, inicio, pan=0.0, ganancia=1.0):
    i = int(inicio * SR)
    if i >= len(pista):
        return
    señal = señal[: len(pista) - i] * ganancia
    pista[i:i + len(señal), 0] += señal * np.sqrt(0.5 * (1 - pan))
    pista[i:i + len(señal), 1] += señal * np.sqrt(0.5 * (1 + pan))


def componer(guion):
    conf = guion["musica"]
    if conf.get("estilo") == "ritmo":
        from ritmo import componer_ritmo  # base rítmica para reels de producto
        return componer_ritmo(guion)
    dur = guion["duracion"]
    np.random.seed(conf.get("semilla", 7))
    total = int((dur + 0.5) * SR)
    pista = np.zeros((total, 2))
    acordes = conf["acordes"]

    for i, acorde in enumerate(acordes):
        inicio = acorde["en"]
        fin = acordes[i + 1]["en"] if i + 1 < len(acordes) else dur + 0.5
        solape = 0.9  # los acordes se funden entre sí
        largo = fin - inicio + solape
        notas = acorde["notas"]
        # Pad: todas las notas del acorde, abiertas en el estéreo.
        for j, nota in enumerate(notas[1:]):
            env = envolvente(int(largo * SR), 0.25 if i == 0 else 0.8, solape)
            pan = -0.6 + 1.2 * j / max(1, len(notas) - 2)
            colocar(pista, pasa_bajos(pad(frecuencia(nota), largo), 1800) * env, inicio, pan, 0.11)
        # Bajo: la primera nota del acorde.
        env = envolvente(int(largo * SR), 0.2 if i == 0 else 0.6, solape)
        colocar(pista, pasa_bajos(pad(frecuencia(notas[0]), largo), 400) * env, inicio, 0, 0.22)
        # Piano: arpegio con las notas del acorde una octava arriba. Por defecto
        # lento y espaciado; con "patron": "ascendente" sube nota a nota a ritmo
        # constante (sensación de algo que crece, p. ej. una carga).
        paso = acorde.get("paso", conf.get("pasoPiano", 0.85))
        ascendente = acorde.get("patron") == "ascendente"
        t = inicio + (0.0 if i == 0 else 0.15)
        agudas = [n[:-1] + str(int(n[-1]) + 1) for n in notas[1:]]
        k = 0
        while t < fin - 0.3:
            if ascendente:
                nota = agudas[k % len(agudas)]
            else:
                nota = agudas[(k * 2 + np.random.randint(0, 2)) % len(agudas)]
            colocar(pista, piano(frecuencia(nota)), t, np.random.uniform(-0.35, 0.35), 0.16 + 0.04 * np.random.rand())
            t += paso * (1 if ascendente or k % 4 != 3 else 1.5)
            k += 1

    for c in conf.get("campanas", []):
        colocar(pista, pasa_bajos(campana(frecuencia(c["nota"])), 5000), c["en"], c.get("pan", 0.0), c.get("ganancia", 0.12))

    pista = reverberacion(pista)
    pista = pasa_altos(pista, 45)  # los altavoces del móvil no reproducen graves profundos
    pista = pista[: int(dur * SR)]
    pista *= envolvente(len(pista), 0.02, conf.get("finalSuave", 1.2))[:, None]
    pista *= 0.78 / np.max(np.abs(pista))  # ≈ -14 LUFS, el nivel habitual en Instagram
    return pista


def guardar(pista, ruta):
    datos = (np.clip(pista, -1, 1) * 32767).astype("<i2")
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Uso: python3 musica/generar.py guiones/<guion>.json salida.wav")
    with open(sys.argv[1], encoding="utf-8") as f:
        guion = json.load(f)
    guardar(componer(guion), sys.argv[2])
