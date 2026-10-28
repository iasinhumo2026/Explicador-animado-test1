#!/usr/bin/env python3
"""Control de ritmo: comprueba que el vídeo nunca se quede quieto demasiado tiempo.

Uso:  python3 ritmo.py P/salida/video.mp4 [--max 0.6]

Mide qué fotogramas cambian respecto al anterior, en total y por zonas (tarjeta, subtítulos, zona de abajo).
Avisa de cada tramo de más de --max segundos sin ningún cambio en pantalla.
"""
import argparse, os, subprocess, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import FFMPEG  # noqa: E402

ZONAS = {  # (y0, y1, x0, x1) en fracción de la pantalla
    "vertical": {"tarjeta": (0.10, 0.48, 0, 1), "subtitulos": (0.48, 0.56, 0, 1), "abajo": (0.56, 0.95, 0, 1)},
    "horizontal": {"tarjeta": (0.03, 0.80, 0.12, 0.76), "subtitulos": (0.82, 0.96, 0, 1), "derecha": (0.1, 0.8, 0.76, 1.0)},
}


def huecos(cambia, fps):
    idx = np.where(cambia)[0]
    bordes = np.concatenate([[-1], idx, [len(cambia)]])
    salida = []
    for a, b in zip(bordes[:-1], bordes[1:]):
        if b - a - 1 > 0:
            salida.append(((a + 1) / fps, (b - a) / fps))
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--max", type=float, default=0.6)
    a = ap.parse_args()
    fps = 30
    pr = subprocess.run([FFMPEG, "-hide_banner", "-i", a.video], capture_output=True, text=True).stderr
    vertical = True
    import re
    m = re.search(r", (\d{3,4})x(\d{3,4})", pr)
    if m:
        vertical = int(m.group(2)) > int(m.group(1))
    w, h = (180, 320) if vertical else (320, 180)
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", a.video, "-vf", f"fps={fps},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    if len(f) < 2:
        sys.exit("No he podido leer el vídeo.")
    d = np.abs(np.diff(f, axis=0)) > 10
    total = d.mean(axis=(1, 2)) > 0.0006
    print(f"Duración: {len(f) / fps:.1f} s · fotogramas con cambio: {total.mean() * 100:.0f} %")
    for nombre, (y0, y1, x0, x1) in ZONAS["vertical" if vertical else "horizontal"].items():
        z = d[:, int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].mean(axis=(1, 2)) > 0.002
        largo = max((g for _, g in huecos(z, fps)), default=0)
        print(f"  {nombre:11s} activa {z.mean() * 100:3.0f} % · quieta como mucho {largo:.2f} s")
    print("  (Las zonas son orientativas: es normal que los subtítulos estén quietos en el final sin subtítulos.\n"
          "   Lo que cuenta es la línea de abajo: ningún momento con toda la pantalla quieta.)")
    malos = [(t, g) for t, g in huecos(total, fps) if g > a.max]
    if malos:
        print(f"AVISO: {len(malos)} tramo(s) de más de {a.max} s sin nada que se mueva:")
        for t, g in malos:
            print(f"  en el segundo {t:.1f}: {g:.2f} s quieto → añade algo con \"en\" en ese momento (píldora, pegatina, mundo, nota)")
    else:
        largo = max((g for _, g in huecos(total, fps)), default=0)
        print(f"OK: ningún tramo quieto de más de {a.max} s (el más largo: {largo:.2f} s).")


if __name__ == "__main__":
    main()
