#!/usr/bin/env python3
"""Portada del vídeo (la misma para Instagram y TikTok) a partir de video.json → "portada".

Uso:  python3 portada.py P/video.json   → P/salida/portada.png y P/salida/portada_recorte.png (cómo se ve en la cuadrícula 3:4)

"portada": {
  "etiqueta": "SKILL DE CLAUDE",                 píldora pequeña de arriba
  "lineas": ["ANIMA", "CUALQUIER TEMA"],         título en 2–3 líneas cortas
  "clave": 1,                                    índice de la línea que va dentro de la caja de color
  "remate": "con 1 sola frase",                  línea en cursiva debajo (opcional)
  "mundo": "batalla", "segundo": 3.0,            el mundo que sale en la tarjeta y en qué segundo de su animación
  "personaje": "becario", "pose": "celebra", "cara": "sorpresa",
  "pegatina": "0 dibujos a mano"                 (opcional)
  "personaje_pos": [x, y, tamaño]                (opcional: dónde va el personaje; y = pies en los humanos)
}
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia  # noqa: E402

import kit as K  # noqa: E402
import personajes as P  # noqa: E402
from comun import ancho, caja, col, nuevo_lienzo, pildora, rrect, texto, texto_sobre, relleno  # noqa: E402
from render import Escena, cargar  # noqa: E402
from mundo import W as MW, H as MH  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    a = ap.parse_args()
    V = cargar(os.path.abspath(a.video))
    E = Escena(V)
    cfg = V.get("portada", {})
    W, H = E.W, E.H
    est = E.est
    s, _ = nuevo_lienzo(W, H)
    c = s.getCanvas()
    K.fondo_pagina(c, est, W, H, variante=1)
    vertical = E.formato == "9:16"
    # zona útil: el recorte 3:4 del centro (y 240–1680 en vertical)
    y0 = 235 if vertical else 60
    # etiqueta
    xc = W / 2 if vertical else W * 0.27
    if cfg.get("etiqueta"):
        pildora(c, cfg["etiqueta"], xc, y0 + 40, "extrabold", 40 if vertical else 36, est["etiqueta"], texto_sobre(est["etiqueta"]), ancla="centro", sombra=0.25)
    lineas = cfg.get("lineas", ["MI VÍDEO", "ANIMADO"])
    clave = cfg.get("clave", len(lineas) - 1)
    tam = 128 if vertical else 110
    y = y0 + 175
    ancho_max = W * (0.88 if vertical else 0.46)
    for i, ln in enumerate(lineas):
        t_ = tam
        while ancho(ln, "black", t_) > ancho_max - (60 if i == clave else 0):
            t_ -= 2
        if i == clave:
            w = ancho(ln, "black", t_) + 70
            c.save(); c.translate(xc, y); c.rotate(-2.5)
            caja(c, -w / 2, -t_ * 0.68, w, t_ * 1.36, 26, est["acento"], sombra=0.3, sombra_y=10, difuso=14)
            texto(c, ln, 0, 0, "black", t_, texto_sobre(est["acento"]), ancla="centro")
            c.restore()
        else:
            texto(c, ln, xc, y, "black", t_, est["texto"], ancla="centro")
        y += t_ * 1.22
    if cfg.get("remate"):
        texto(c, cfg["remate"], xc, y + 4, "cursiva", 60 if vertical else 52, est["texto"], ancla="centro")
        y += 90
    # tarjeta con el mundo
    if vertical:
        tx, ty, tw, th = 70, y + 40, 940, 560
    else:
        tx, ty, tw, th = W * 0.53, 120, W * 0.43, W * 0.27
    nombre = cfg.get("mundo") or (next(iter(E.mundos)) if E.mundos else None)
    c.save(); c.translate(tx + tw / 2, ty + th / 2); c.rotate(cfg.get("rot", -2)); c.translate(-tw / 2, -th / 2)
    inner = K.tarjeta_marco(c, 0, 0, tw, th, est)
    ix, iy, iw, ih, ir = inner
    c.save(); c.clipRRect(rrect(ix, iy, iw, ih, ir), True)
    if nombre:
        m = E.mundos[nombre]
        sc = max(iw / MW, ih / MH)
        c.translate(ix + (iw - MW * sc) / 2, iy + (ih - MH * sc) / 2); c.scale(sc, sc)
        m.dibujar(c, cfg.get("segundo", 3.0), escala=sc)
    c.restore()
    if cfg.get("pegatina"):
        K.pegatina(c, cfg["pegatina"], tw - 170, th - 4, est, rot=-6, k=1.0, tam=40)
    c.restore()
    # personaje
    pj = cfg.get("personaje") or (V.get("mascota") or {}).get("personaje")
    if pj and pj in E.pj:
        spec = E.pj[pj]
        if spec.get("forma") == "humano":
            px, py, pt = (W * 0.22, min(H - 200, ty + th + 470), 560) if vertical else (W * 0.12, H - 40, 520)
        else:
            px, py, pt = (W * 0.2, ty + th + 160, 260) if vertical else (W * 0.12, H - 200, 260)
        if cfg.get("personaje_pos"):
            px, py, pt = cfg["personaje_pos"][:3]
        P.dibujar(c, spec, px, py, pt, 1.2, {"pose": cfg.get("pose", "celebra"), "cara": cfg.get("cara", "sorpresa"), "mirar": (0.4, -0.3)})
    os.makedirs(os.path.join(E.dir, "salida"), exist_ok=True)
    ruta = os.path.join(E.dir, "salida", "portada.png")
    with open(ruta, "wb") as fh:
        fh.write(bytes(s.makeImageSnapshot().encodeToData()))
    # recorte de la cuadrícula
    img = s.makeImageSnapshot()
    if vertical:
        rs = skia.Surface(540, 720)
        rs.getCanvas().drawImageRect(img, skia.Rect(0, 240, 1080, 1680), skia.Rect(0, 0, 540, 720), skia.SamplingOptions(skia.FilterMode.kLinear))
        with open(os.path.join(E.dir, "salida", "portada_recorte.png"), "wb") as fh:
            fh.write(bytes(rs.makeImageSnapshot().encodeToData()))
    print("Guardado:", ruta)
    if vertical:
        print("Comprueba portada_recorte.png: es lo que se ve en la cuadrícula del perfil (3:4). Título y cara tienen que caber.")


if __name__ == "__main__":
    main()
