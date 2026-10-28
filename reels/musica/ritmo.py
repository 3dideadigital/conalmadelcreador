"""Base rítmica original para reels de producto ("estilo": "ritmo" en el guion).

La llama musica/generar.py. Todo se sintetiza aquí (bombo, palmas, charles,
bajo, acordes eléctricos, arpegio, subidas y golpes), así que no hay
problemas de derechos. El guion indica:

    "musica": {
      "estilo": "ritmo",
      "bpm": 120,
      "primerCompas": -1.0,          # segundo en el que cae un primer tiempo
      "acordes": [["F2", "A3", ...], ...],   # uno por compás, en bucle
      "partes": {"bombo": [[3, 15], [17, 24]], "hats": [[0, 24]], ...},
      "subidas": [[1.0, 3.0]],       # redoble y ruido que suben hasta el golpe
      "golpes": [3.0, 21.0],         # impacto grave + platillo
      "barridos": [7.0, 9.0],        # "whoosh" corto en los cortes de escena
      "final": 24.0,                 # último golpe: se corta el ritmo y queda el acorde
      "acordeFinal": ["C2", ...]     # opcional: acorde que suena en el final
    }

Partes disponibles: bombo, palmas, hats, bajo, acordes, arpegio. Las que no
aparecen no suenan.
"""

import numpy as np
from scipy.signal import butter, sosfilt

from generar import SR, colocar, envolvente, frecuencia, pasa_altos, pasa_bajos, reverberacion


def paso_banda(x, bajo, alto):
    return sosfilt(butter(2, [bajo, alto], btype="band", fs=SR, output="sos"), x)


def ruido(dur):
    return np.random.randn(int(round(dur * SR)))


def bombo(dur=0.45):
    t = np.arange(int(dur * SR)) / SR
    fase = 2 * np.pi * np.cumsum(46 + 110 * np.exp(-t * 32)) / SR
    cuerpo = np.sin(fase) * np.exp(-t * 7.5)
    clic = pasa_bajos(ruido(0.012), 4000) * np.exp(-np.arange(int(0.012 * SR)) / SR * 300)
    cuerpo[: len(clic)] += 0.6 * clic
    cuerpo += 0.25 * paso_banda(np.sin(fase * 2), 900, 3000) * np.exp(-t * 30)
    return np.tanh(1.6 * cuerpo)


def palmas():
    señal = np.zeros(int(0.32 * SR))
    for k, retraso in enumerate((0.0, 0.011, 0.023)):
        n = int((0.32 - retraso) * SR)
        caida = 70 if k < 2 else 16
        golpe = np.random.randn(n) * np.exp(-np.arange(n) / SR * caida)
        i = int(retraso * SR)
        señal[i:i + n] += golpe
    return paso_banda(señal, 900, 3800) * 0.9


def hat(abierto=False):
    dur = 0.22 if abierto else 0.05
    n = int(dur * SR)
    return pasa_altos(np.random.randn(n), 7500) * np.exp(-np.arange(n) / SR * (14 if abierto else 85))


def bajo(f, dur):
    """Bajo redondo: armónicos de diente de sierra filtrados, ataque corto."""
    t = np.arange(int(dur * SR)) / SR
    señal = sum((1 / h) * np.sin(2 * np.pi * f * h * t) for h in range(1, 8))
    return pasa_bajos(señal, 700) * envolvente(len(t), 0.004, 0.06) * np.exp(-t * 2.2)


def tecla(f, dur):
    """Piano eléctrico: tono con campana suave y trémolo ligero."""
    t = np.arange(int(dur * SR)) / SR
    señal = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
    señal += 0.22 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 5)
    señal += 0.12 * np.sin(2 * np.pi * 7.02 * f * t) * np.exp(-t * 14)  # "tine"
    señal *= 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    return señal * np.exp(-t * 1.6) * envolvente(len(t), 0.006, 0.12)


def pulsacion(f, dur=0.35):
    """Nota de arpegio corta y brillante."""
    t = np.arange(int(dur * SR)) / SR
    señal = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 12)
    return señal * np.exp(-t * 11) * envolvente(len(t), 0.003, 0.05)


def subida(dur):
    """Ruido que se abre y crece hasta el golpe."""
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    trozos = np.array_split(np.random.randn(n), 24)
    señal = np.concatenate([pasa_altos(tr, 300 + 6000 * (k / 24) ** 2) for k, tr in enumerate(trozos)])
    return señal * x ** 2.2


def redoble(dur, bpm):
    """Golpes de caja que se aceleran (corcheas, semicorcheas, fusas)."""
    señal = np.zeros(int(dur * SR))
    negra = 60 / bpm
    t = 0.0
    while t < dur - 0.01:
        progreso = t / dur
        paso = negra / (2 if progreso < 0.4 else 4 if progreso < 0.75 else 8)
        golpe = paso_banda(ruido(0.09), 180, 5000) * np.exp(-np.arange(int(0.09 * SR)) / SR * 40)
        i = int(t * SR)
        trozo = golpe[: len(señal) - i] * (0.25 + 0.75 * progreso)
        señal[i:i + len(trozo)] += trozo
        t += paso
    return señal


def golpe():
    """Impacto: bombo grave largo + platillo."""
    t = np.arange(int(1.8 * SR)) / SR
    grave = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 18)) / SR) * np.exp(-t * 2.4)
    platillo = pasa_altos(np.random.randn(len(t)), 4500) * np.exp(-t * 2.8) * 0.5
    return np.tanh(1.4 * grave) + platillo


def barrido(dur=0.4):
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    return paso_banda(np.random.randn(n), 500, 6000) * np.sin(np.pi * x) ** 2


def dentro(t, tramos):
    return any(a <= t < b for a, b in tramos)


def componer_ritmo(guion):
    conf = guion["musica"]
    dur = guion["duracion"]
    np.random.seed(conf.get("semilla", 11))
    bpm = conf.get("bpm", 120)
    negra = 60 / bpm
    compas = 4 * negra
    origen = conf.get("primerCompas", 0.0)
    partes = conf.get("partes", {})
    final = conf.get("final", dur)
    total = int((dur + 2) * SR)
    ritmo = np.zeros((total, 2))      # bombo, palmas, charles
    armonia = np.zeros((total, 2))    # bajo, acordes, arpegio (con bombeo)
    efectos = np.zeros((total, 2))
    acordes = conf["acordes"]

    def toca(parte, t):
        return t < final and dentro(t, partes.get(parte, []))

    # Rejilla de semicorcheas desde el primer compás anterior al inicio.
    k0 = int(np.floor((0 - origen) / (negra / 4)))
    golpes_bombo = []
    k = k0
    while True:
        t = origen + k * negra / 4
        if t > dur:
            break
        semi = k % 16                        # posición dentro del compás
        n_compas = int(np.floor((t - origen) / compas + 1e-9))
        acorde = acordes[n_compas % len(acordes)]
        if t >= 0:
            if semi % 4 == 0 and toca("bombo", t):
                colocar(ritmo, bombo(), t, 0, 0.5)
                golpes_bombo.append(t)
            if semi in (4, 12) and toca("palmas", t):
                colocar(ritmo, palmas(), t, 0.05, 0.5)
            if toca("hats", t):
                if semi % 4 == 2:
                    colocar(ritmo, hat(abierto=True), t, 0.25, 0.16)
                elif semi % 2 == 1:
                    colocar(ritmo, hat(), t, -0.2, 0.09 + 0.03 * np.random.rand())
            if semi % 4 == 2 and toca("bajo", t):
                colocar(armonia, bajo(frecuencia(acorde[0]), negra * 0.9), t, 0, 0.36)
            # Acordes a contratiempo (estilo "house" elegante).
            if semi in (2, 6, 10, 15) and toca("acordes", t):
                largo = negra * (1.6 if semi == 15 else 0.9)
                for j, nota in enumerate(acorde[1:]):
                    pan = -0.5 + j / max(1, len(acorde) - 2)
                    env = envolvente(int((largo + 0.5) * SR), 0.004, 0.4)
                    colocar(armonia, tecla(frecuencia(nota), largo + 0.5) * env, t, pan, 0.15)
                    # Doblado una octava arriba: brillo en el altavoz del móvil.
                    colocar(armonia, tecla(2 * frecuencia(nota), largo + 0.5) * env, t, -pan, 0.08)
            if toca("arpegio", t):
                agudas = [n[:-1] + str(int(n[-1]) + 2) for n in acorde[1:]]
                nota = agudas[(semi * 3) % len(agudas)]
                colocar(armonia, pulsacion(frecuencia(nota)), t, 0.4 * np.sin(semi), 0.15)
                # Eco a corchea con puntillo, al otro lado.
                colocar(armonia, pulsacion(frecuencia(nota)), t + negra * 0.75, -0.4 * np.sin(semi), 0.06)
        k += 1

    # Bombeo: la armonía se aparta cada vez que suena el bombo.
    curva = np.ones(total)
    caida = np.exp(-np.arange(int(0.3 * SR)) / SR * 9)
    for t in golpes_bombo:
        i = int(t * SR)
        trozo = 1 - 0.55 * caida[: total - i]
        curva[i:i + len(trozo)] = np.minimum(curva[i:i + len(trozo)], trozo)
    armonia *= curva[:, None]

    for a, b in conf.get("subidas", []):
        colocar(efectos, subida(b - a), a, 0, 0.16)
        colocar(efectos, redoble(min(b - a, compas / 2), bpm), b - min(b - a, compas / 2), 0, 0.28)
    for t in conf.get("golpes", []):
        colocar(efectos, golpe(), t, 0, 0.55)
    for t in conf.get("barridos", []):
        colocar(efectos, barrido(), t - 0.3, 0.3 * np.sin(t), 0.12)

    # Final: golpe y acorde abierto que se apaga.
    if final < dur:
        colocar(efectos, golpe(), final, 0, 0.6)
        acorde = conf.get("acordeFinal") or acordes[int(np.floor((final - origen) / compas)) % len(acordes)]
        for j, nota in enumerate(acorde):
            colocar(armonia, tecla(frecuencia(nota), dur - final + 1.5), final, -0.4 + 0.8 * j / len(acorde), 0.12)

    mezcla = 0.85 * ritmo + reverberacion(armonia, 1.6, 0.25) + reverberacion(efectos, 2.2, 0.3)
    mezcla = pasa_altos(mezcla, 40)
    mezcla += 1.0 * paso_banda(mezcla, 1800, 6500)  # presencia
    mezcla = mezcla[: int(dur * SR)]
    mezcla *= envolvente(len(mezcla), 0.005, conf.get("finalSuave", 0.6))[:, None]
    mezcla = np.tanh(1.3 * mezcla / np.max(np.abs(mezcla)))  # algo de cuerpo sin recortar
    return mezcla * 0.86 / np.max(np.abs(mezcla))
