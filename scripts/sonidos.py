"""Efectos de sonido sintetizados (sin archivos ni licencias de terceros)."""
import numpy as np

SR = 48000


def _env(n, ataque=0.003, caida=8.0):
    t = np.arange(n) / SR
    a = np.minimum(1, t / max(1e-4, ataque))
    return a * np.exp(-t * caida)


def _tono(f0, f1, dur, caida=10.0, forma="seno", ataque=0.003):
    n = int(SR * dur)
    f = np.geomspace(max(1, f0), max(1, f1), n)
    fase = 2 * np.pi * np.cumsum(f) / SR
    w = np.sin(fase) if forma == "seno" else (np.sign(np.sin(fase)) * 0.5 if forma == "cuadrada" else 2 * np.abs(2 * ((fase / (2 * np.pi)) % 1) - 1) - 1)
    return w * _env(n, ataque=ataque, caida=caida)


def _ruido(dur, caida=30.0, color="blanco", rng=None, ataque=0.001):
    rng = rng or np.random.default_rng(1)
    n = int(SR * dur)
    r = rng.standard_normal(n)
    if color == "agudo":
        r = np.diff(np.concatenate([[0], r]))
    elif color == "grave":
        r = np.convolve(r, np.ones(40) / 40, mode="same") * 4
    elif color == "medio":
        r = np.convolve(r, np.ones(8) / 8, mode="same") * 2
    return r * _env(n, ataque=ataque, caida=caida)


def _suma(*partes):
    n = max(len(p) for p in partes)
    out = np.zeros(n)
    for p in partes:
        out[:len(p)] += p
    return out


def _retraso(s, seg):
    return np.concatenate([np.zeros(int(SR * seg)), s])


def efecto(nombre, rng):
    if nombre == "pop":  # burbuja suave
        f = rng.uniform(520, 680)
        return 0.22 * _tono(f, f * 2.3, 0.09, caida=38, ataque=0.002)
    if nombre == "pasa":  # whoosh
        n = int(SR * 0.32)
        r = rng.standard_normal(n)
        k = np.linspace(4, 40, n).astype(int)
        acc = np.cumsum(r)
        out = (acc[np.minimum(n - 1, np.arange(n) + 6)] - acc) / 6
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        return 0.16 * out * env
    if nombre == "tecla":
        return _suma(0.08 * _ruido(0.016, caida=240, color="agudo", rng=rng), 0.035 * _tono(rng.uniform(1900, 2600), 1500, 0.014, caida=280))
    if nombre == "tic":
        return 0.12 * _tono(1700, 1500, 0.03, caida=140)
    if nombre == "check":
        return 0.15 * _suma(_tono(880, 880, 0.2, caida=16), 0.7 * _retraso(_tono(1320, 1320, 0.22, caida=14), 0.06))
    if nombre == "tachar":
        n = int(SR * 0.22)
        r = _ruido(0.22, caida=6, color="medio", rng=rng)
        return 0.12 * r * np.linspace(1, 0.2, n)
    if nombre == "boli":
        n = int(SR * 0.5)
        r = _ruido(0.5, caida=2.5, color="agudo", rng=rng)
        mod = 0.5 + 0.5 * np.abs(np.sin(np.linspace(0, 14 * np.pi, n)))
        return 0.05 * r * mod
    if nombre == "ding":
        return 0.13 * _suma(_tono(1568, 1568, 0.6, caida=6), 0.4 * _tono(3136, 3136, 0.4, caida=9))
    if nombre == "exito":
        out = np.zeros(int(SR * 0.8))
        for i, f in enumerate([659, 784, 988, 1319]):
            s = _tono(f, f, 0.4, caida=7) * 0.13
            k = int(SR * 0.075 * i)
            out[k:k + len(s)] += s[:len(out) - k]
        return out
    if nombre == "sello":
        return _suma(0.3 * _tono(180, 70, 0.18, caida=18), 0.1 * _ruido(0.06, caida=60, color="medio", rng=rng))
    if nombre == "nam":  # bocado
        return _suma(0.22 * _tono(220, 90, 0.12, caida=26), 0.08 * _ruido(0.05, caida=80, color="medio", rng=rng))
    if nombre == "boing":
        n = int(SR * 0.28)
        t = np.arange(n) / SR
        f = 260 + 140 * np.sin(2 * np.pi * 18 * t) * np.exp(-t * 9)
        return 0.13 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, caida=11)
    if nombre == "piu":
        return 0.07 * _tono(1500, 500, 0.12, caida=22, forma="triangulo")
    if nombre == "voltea":
        return _suma(0.12 * _tono(300, 900, 0.18, caida=14), efecto("pasa", rng) * 0.6)
    if nombre == "brillo":
        out = np.zeros(int(SR * 0.5))
        for i in range(5):
            f = rng.uniform(2200, 3800)
            s = 0.05 * _tono(f, f, 0.12, caida=30)
            k = int(SR * 0.05 * i)
            out[k:k + len(s)] += s[:len(out) - k]
        return out
    return np.zeros(10)


GANANCIA = {"tecla": 0.8, "tic": 0.7, "piu": 0.5, "nam": 0.7, "boing": 0.6}


def pista(eventos, duracion, ganancia=1.0, semilla=7):
    """eventos: lista de (segundo, nombre). Devuelve la pista mono float32 a 48 kHz."""
    rng = np.random.default_rng(semilla)
    out = np.zeros(int(SR * (duracion + 1.0)), np.float32)
    ultimos = {}
    for t, nombre in sorted(eventos):
        minimo = 0.05 if nombre in ("tecla", "tic") else (0.3 if nombre in ("nam", "boing", "piu") else 0.06)
        if t - ultimos.get(nombre, -9) < minimo:
            continue
        ultimos[nombre] = t
        s = efecto(nombre, rng).astype(np.float32) * ganancia * GANANCIA.get(nombre, 1.0)
        k = int(t * SR)
        if k < 0 or k >= len(out):
            continue
        fin = min(len(out), k + len(s))
        out[k:fin] += s[:fin - k]
    return out[:int(SR * duracion)]
