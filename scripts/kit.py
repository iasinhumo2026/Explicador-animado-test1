"""Piezas del vídeo: fondo de página, tarjetas, prompt, código, gente, pasos, píldoras, notas a mano,
titulares, contador, pegatinas, móvil, llamada a la acción y subtítulos.

Todas dibujan sobre el lienzo del fotograma (1080 × 1920 o 1920 × 1080) con Skia.
"""
import math
import os
import random

import skia

import personajes as P
from comun import (tx, numero, IDIOMA, Capa, aclara, ancho, caja, clamp, col, fuente, lerp, metricas, mezcla, oscurece, partir, pildora,
                   rebote, relleno, rrect, sale, sombra_paint, suave, texto, texto_sobre, trazo, abrir_imagen, muestreo,
                   matriz_giro_y, normaliza, entra)

# ------------------------------------------------------------------ maquetas
LAYOUTS = {
    "9:16": dict(W=1080, H=1920,
                 cajas={
                     "arriba": [60, 230, 960, 620, 0],
                     "grande": [36, 200, 1008, 700, 0],
                     "arriba_izq": [36, 200, 780, 470, -3],
                     "abajo_der": [264, 482, 780, 470, 2.5],
                     "centro": [60, 560, 960, 620, 0],
                     "mitad_izq": [36, 330, 492, 520, -2],
                     "mitad_der": [552, 330, 492, 520, 2],
                     "pequena_izq": [40, 1110, 470, 300, -3],
                     "pequena_der": [410, 1100, 600, 400, 2],
                     "baja": [60, 1100, 960, 430, 0],
                     "vertical_der": [700, 260, 340, 604, 2],
                 },
                 subtitulos=dict(y=1000, tam=64, ancho=960),
                 extras=[400, 1095, 600, 440],
                 extras_ancho=[60, 1095, 960, 440],
                 mascota=dict(x=215, y=1700, tam=540),
                 cta=dict(x=540, y=560)),
    "16:9": dict(W=1920, H=1080,
                 cajas={
                     "arriba": [300, 50, 1150, 730, 0],
                     "grande": [290, 30, 1340, 790, 0],
                     "arriba_izq": [290, 46, 860, 540, -3],
                     "abajo_der": [840, 300, 900, 540, 2.5],
                     "centro": [370, 120, 1180, 700, 0],
                     "mitad_izq": [290, 140, 760, 540, -2],
                     "mitad_der": [1080, 140, 760, 540, 2],
                     "vertical_der": [1480, 60, 400, 711, 2],
                     "pequena_izq": [1470, 520, 420, 290, -3],
                     "pequena_der": [1470, 480, 420, 300, 2],
                     "baja": [400, 620, 1120, 300, 0],
                 },
                 subtitulos=dict(y=950, tam=58, ancho=1500),
                 extras=[1470, 140, 410, 640],
                 extras_ancho=[250, 820, 1180, 100],
                 mascota=dict(x=125, y=1055, tam=410),
                 cta=dict(x=960, y=420)),
}


def caja_de(layout, c):
    """Convierte un preset ("arriba") o una lista [x, y, w, h(, rot)] en (x, y, w, h, rot)."""
    if isinstance(c, str):
        if c not in layout["cajas"]:
            raise SystemExit(f"La caja «{c}» no existe. Usa una de: {', '.join(layout['cajas'])} o [x, y, ancho, alto].")
        v = layout["cajas"][c]
    else:
        v = list(c)
    if len(v) == 4:
        v = v + [0]
    return [float(k) for k in v]


# ------------------------------------------------------------------ fondo de página (se pinta una vez y se reutiliza)
_FONDO = {}


def fondo_pagina(c, est, W, H, variante=0):
    clave = (W, H, est["fondo"], tuple(est["manchas"]), est["puntos"], variante)
    img = _FONDO.get(clave)
    if img is None:
        s = skia.Surface(W, H)
        k = s.getCanvas()
        k.clear(col(est["fondo"]))
        rnd = random.Random(4 + variante)
        for i, m in enumerate(est["manchas"] * 2):
            x = rnd.random() * W
            y = (0.1 + 0.8 * rnd.random()) * H
            r = (0.35 + 0.25 * rnd.random()) * max(W, H) * 0.5
            p = relleno(m, 0.55)
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.45))
            k.drawCircle(x, y, r, p)
        paso = 34
        pp = relleno(est["puntos"], 0.9)
        for yy in range(paso // 2, H, paso):
            for xx in range(paso // 2, W, paso):
                k.drawCircle(xx, yy, 2.0, pp)
        img = s.makeImageSnapshot()
        _FONDO[clave] = img
    c.drawImage(img, 0, 0)


# ------------------------------------------------------------------ sombra de tarjeta en caché
_SOMBRAS = {}


def sombra_tarjeta(c, x, y, w, h, r, a=0.22):
    clave = (int(w), int(h), int(r), round(a, 2))
    img = _SOMBRAS.get(clave)
    m = 40
    if img is None:
        s = skia.Surface(int(w) + 2 * m, int(h) + 2 * m)
        k = s.getCanvas()
        k.drawRRect(rrect(m, m, w, h, r), sombra_paint("#3A2A1A", a, 18))
        img = s.makeImageSnapshot()
        _SOMBRAS[clave] = img
    c.drawImage(img, x - m, y - m + 16)


# ------------------------------------------------------------------ tarjeta
def tarjeta_marco(c, x, y, w, h, est, etiqueta=None, etq_color=None, a=1.0, borde=10, radio=34):
    sombra_tarjeta(c, x, y, w, h, radio)
    c.drawRRect(rrect(x, y, w, h, radio), relleno(est["tarjeta"]))
    if etiqueta:
        pass
    return (x + borde, y + borde, w - 2 * borde, h - 2 * borde, radio - borde * 0.6)


def etiqueta_tarjeta(c, s, x, y, est, color=None, tam=30):
    fondo = color or est["etiqueta"]
    pildora(c, s, x + 18, y, "bold", tam, fondo, texto_sobre(fondo), pad_x=tam * 0.55, pad_y=tam * 0.22, sombra=0.25)


def pegatina(c, s, x, y, est, color=None, rot=-6, k=1.0, tam=30):
    fondo = color or est["acento"]
    esc = rebote(k)
    c.save(); c.translate(x, y); c.rotate(rot * (1 - 0.3 * (1 - k))); c.scale(esc, esc)
    pildora(c, s, 0, 0, "extrabold", tam, fondo, texto_sobre(fondo), ancla="centro", pad_x=tam * 0.6, pad_y=tam * 0.25, sombra=0.3)
    c.restore()


# ------------------------------------------------------------------ contenidos de tarjeta
def contenido_prompt(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno(mezcla(est["tarjeta"], est["fondo"], 0.35)))
    grande = h > 330
    if grande:
        # cabecera de chat
        c.drawRect(skia.Rect(x, y, x + w, y + h * 0.15), relleno("#FFFFFF", 0.7))
        c.drawLine(x, y + h * 0.15, x + w, y + h * 0.15, trazo(est["linea"], 2))
        for j in range(3):
            c.drawCircle(x + w - 40 - j * 26, y + h * 0.075, 6, relleno(est["suave"], 0.7))
        texto(c, dat.get("titulo", tx("chat")), x + 36, y + h * 0.075, "bold", h * 0.05, est["suave"])
    ymed = y + h * (0.48 if grande else 0.5)
    alto = caja_prompt(c, x + w * 0.06, ymed, w * 0.88, t, dat, est, ctx, alto=None)
    # al terminar de escribir: se envía y aparece una barra de «creando…»
    t1 = dat.get("_t1", 0)
    if grande and t >= t1 and dat.get("enviar", True):
        k = clamp((t - t1) / dat.get("creando", 1.6))
        by = ymed + alto / 2 + h * 0.1
        bw = w * 0.62
        bx = x + (w - bw) / 2
        caja(c, bx, by, bw, h * 0.05, h * 0.025, "#FFFFFF", borde=est["linea"], borde_ancho=2)
        caja(c, bx, by, max(h * 0.05, bw * sale(k, 2)), h * 0.05, h * 0.025, est["acento"])
        msg = dat.get("listo", tx("lista")) if k >= 1 else dat.get("creando_texto", tx("creando"))
        texto(c, msg, x + w / 2, by + h * 0.12, "bold", h * 0.055, est["ok"] if k >= 1 else est["texto"], ancla="centro")


def caja_prompt(c, x, ymed, w, t, dat, est, ctx, alto=None):
    """Caja de chat que se escribe sola. dat: texto, t_ini, t_fin, icono."""
    s = dat.get("texto", "")
    t0, t1 = dat.get("_t0", 0), dat.get("_t1", 1)
    k = clamp((t - t0) / max(0.05, t1 - t0))
    n = int(len(s) * k)
    tam = dat.get("tam", 38 if ctx["formato"] == "9:16" else 40)
    lineas = partir(s, "medium", tam, w - tam * 4.2)
    alto = alto or (tam * 1.45 * len(lineas) + tam * 1.4)
    yy = ymed - alto / 2
    caja(c, x, yy, w, alto, min(28, alto / 2), "#FFFFFF", sombra=0.16, sombra_y=8, difuso=14)
    c.drawRRect(rrect(x, yy, w, alto, min(28, alto / 2)), trazo(est["linea"], 2.5))
    # botón de enviar
    bx_, by_ = x + w - tam * 1.1, yy + alto - tam * 1.0
    enviado = k >= 1
    c.drawCircle(bx_, by_, tam * 0.55, relleno(est["acento"] if enviado or n > 0 else est["linea"]))
    pf = skia.Path(); pf.moveTo(bx_, by_ - tam * 0.28); pf.lineTo(bx_, by_ + tam * 0.26)
    pf.moveTo(bx_ - tam * 0.22, by_ - tam * 0.06); pf.lineTo(bx_, by_ - tam * 0.28); pf.lineTo(bx_ + tam * 0.22, by_ - tam * 0.06)
    c.drawPath(pf, trazo("#FFFFFF", tam * 0.11))
    # icono propio (destello de 8 puntas)
    ix, iy = x + tam * 1.05, yy + tam * 0.7 + tam * 0.45
    for j in range(8):
        an = j * math.pi / 4 + t * 0.6
        c.drawLine(ix, iy, ix + math.cos(an) * tam * 0.42, iy + math.sin(an) * tam * 0.42, trazo(est["acento"], tam * 0.11))
    # texto escrito hasta n letras
    resto = n
    for i, ln in enumerate(lineas):
        trozo = ln[:max(0, resto)]
        resto -= len(ln) + 1
        texto(c, trozo, x + tam * 2.0, yy + tam * 0.7 + tam * 1.45 * i + tam * 0.45, "medium", tam, est["texto"])
        if 0 <= resto + len(ln) + 1 <= len(ln) + 1 and k < 1:
            cx = x + tam * 2.0 + ancho(trozo, "medium", tam) + 4
            if int(t * 3) % 2 == 0 or k < 1:
                c.drawRect(skia.Rect(cx, yy + tam * 0.7 + tam * 1.45 * i - tam * 0.1, cx + 3, yy + tam * 0.7 + tam * 1.45 * i + tam * 1.0), relleno(est["acento"]))
    return alto


CODIGO_EJEMPLO = [
    ("def", " escena(t):"),
    ("", "    fondo(\"vaso\", luz=0.8)"),
    ("", "    for b in bacterias:"),
    ("", "        b.nada_hacia(macrofago)"),
    ("", "        b.cara = \"picaro\""),
    ("if", " macrofago.cerca(b):"),
    ("", "        macrofago.come(b)  # ñam"),
    ("", "    neutrofilo.escudo.sube()"),
    ("", "    linfocito.dispara(\"anticuerpo\")"),
    ("", "    camara.zoom(1.1, t)"),
    ("return", " fotograma"),
]


CODE_EXAMPLE = [
    ("def", " scene(t):"),
    ("", "    background(\"vessel\", light=0.8)"),
    ("", "    for b in bacteria:"),
    ("", "        b.swim_to(macrophage)"),
    ("", "        b.face = \"cheeky\""),
    ("if", " macrophage.near(b):"),
    ("", "        macrophage.eat(b)  # yum"),
    ("", "    neutrophil.shield.up()"),
    ("", "    b_cell.shoot(\"antibody\")"),
    ("", "    camera.zoom(1.1, t)"),
    ("return", " frame"),
]


def contenido_codigo(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno("#161A26"))
    tam = dat.get("tam", 30 if ctx["formato"] == "9:16" else 32)
    lineas = dat.get("lineas") or ["".join(p) for p in (CODIGO_EJEMPLO if IDIOMA["actual"] == "es" else CODE_EXAMPLE)]
    largo = max(len(l) for l in lineas)
    while tam > 14 and ancho("M" * largo, "mono", tam) > w - 24 - tam * 2.6:
        tam -= 1
    t0 = dat.get("_t0", 0)
    vel = dat.get("lineas_por_segundo", 6)
    nvis = int((t - t0) * vel) + 1
    paso = tam * 1.5
    caben = int((h - tam * 2.4) / paso)
    ini = max(0, min(nvis, len(lineas) * 100) - caben)
    # barra de título
    for j, cc in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        c.drawCircle(x + 34 + j * 30, y + 32, 9, relleno(cc))
    texto(c, dat.get("archivo", "escena.py"), x + w / 2, y + 32, "mono", tam * 0.8, "#8A93A8", ancla="centro")
    claves = ("def ", "for ", "if ", "return", "import ", "class ", "while ", "in ")
    for i in range(caben):
        idx = ini + i
        if idx >= nvis:
            break
        ln = lineas[idx % len(lineas)]
        yy = y + tam * 2.4 + i * paso
        texto(c, str(idx + 1).rjust(2), x + 24, yy, "mono", tam * 0.85, "#4E566B")
        xx = x + 24 + tam * 2.0
        # coloreado sencillo
        resto = ln
        if idx == nvis - 1:
            vis = int(len(ln) * clamp(((t - t0) * vel) % 1 * 1.6))
            resto = ln[:vis]
        tok = resto.split("\"")
        for j, trozo in enumerate(tok):
            if j % 2 == 1:
                trozo = "\"" + trozo + "\""
                color = "#9BE58A"
            else:
                color = "#E6E9F2"
            if j % 2 == 0:
                for kw in claves:
                    pass
            if "#" in trozo and j % 2 == 0:
                a, b = trozo.split("#", 1)
                xx += texto(c, a, xx, yy, "mono", tam, color)
                xx += texto(c, "#" + b, xx, yy, "mono", tam, "#6C7690")
                continue
            primera = trozo.strip().split(" ")[0] + " " if trozo.strip() else ""
            if j % 2 == 0 and any(trozo.lstrip().startswith(kw.strip()) for kw in claves):
                sangria = trozo[:len(trozo) - len(trozo.lstrip())]
                kw = trozo.lstrip().split(" ")[0]
                xx += texto(c, sangria, xx, yy, "mono", tam, color)
                xx += texto(c, kw, xx, yy, "monobold", tam, "#FF9D5C")
                xx += texto(c, trozo.lstrip()[len(kw):], xx, yy, "mono", tam, color)
            else:
                xx += texto(c, trozo, xx, yy, "mono", tam, color)
        if idx == nvis - 1 and int(t * 4) % 2 == 0:
            c.drawRect(skia.Rect(xx + 3, yy - tam * 0.55, xx + 3 + tam * 0.5, yy + tam * 0.55), relleno("#FF9D5C", 0.85))


def icono_persona(c, x, y, s, color, linea=None):
    c.drawCircle(x, y - s * 0.28, s * 0.22, relleno(color))
    p = skia.Path()
    p.moveTo(x - s * 0.36, y + s * 0.42)
    p.cubicTo(x - s * 0.36, y - s * 0.12, x + s * 0.36, y - s * 0.12, x + s * 0.36, y + s * 0.42)
    p.close()
    c.drawPath(p, relleno(color))


def contenido_gente(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno(dat.get("fondo", mezcla(est["tarjeta"], est["fondo"], 0.25))))
    gente(c, x + w * 0.05, y + h * 0.08, w * 0.9, h * (0.66 if dat.get("contador", True) else 0.84), t, dat, est)
    if dat.get("contador", True):
        n_tot = int(dat.get("n", 70))
        k = clamp((t - dat.get("_t0", 0)) / dat.get("dur", 1.6))
        n = int(round(n_tot * sale(k, 2)))
        fmt = dat.get("formato", tx("personas"))
        s = fmt.replace("{n}", numero(n))
        tam = h * 0.13
        cx = x + w / 2
        texto(c, s, cx, y + h * 0.86, "black", tam, est["texto"], ancla="centro")


def gente(c, x, y, w, h, t, dat, est):
    n = int(dat.get("n", 70))
    cols = int(dat.get("columnas", 14))
    filas = math.ceil(n / cols)
    paso = min(w / cols, h / filas)
    s = paso * 0.92
    ox = x + (w - paso * cols) / 2
    t0 = dat.get("_t0", 0)
    dur = dat.get("dur", 1.6)
    rnd = random.Random(9)
    destacados = set(rnd.sample(range(n), max(1, n // 9)))
    for i in range(n):
        fi, ci = divmod(i, cols)
        ti = t0 + dur * (i / n) ** 0.8
        if t < ti:
            continue
        k = clamp((t - ti) / 0.22)
        cx = ox + (ci + 0.5) * paso
        cy = y + (h - paso * filas) / 2 + (fi + 0.55) * paso
        color = est["acento"] if i in destacados else est["texto"]
        if i in destacados and dat.get("brillan", True):
            color = mezcla(est["texto"], est["acento"], 0.5 + 0.5 * math.sin(t * 3 + i))
        c.save(); c.translate(cx, cy + (1 - sale(k)) * s * 0.4); c.scale(rebote(k), rebote(k))
        icono_persona(c, 0, 0, s * 0.95, color)
        c.restore()


ICONOS = ["guion", "personajes", "escenas", "montaje", "voz", "musica", "portada", "texto", "ok", "rayo", "reloj", "dinero",
          "corazon", "estrella", "mundo", "camara", "pincel", "codigo", "chat", "lupa", "gota", "nube", "sol"]


def icono(c, nombre, x, y, s, color, linea="#1D1B2E"):
    lw = max(2.0, s * 0.07)
    if nombre == "guion":
        caja(c, x - s * 0.34, y - s * 0.42, s * 0.68, s * 0.84, s * 0.08, "#FFFFFF", borde=linea, borde_ancho=lw)
        for j in range(4):
            c.drawLine(x - s * 0.2, y - s * 0.22 + j * s * 0.15, x + s * (0.2 if j < 3 else 0.05), y - s * 0.22 + j * s * 0.15, trazo(color, lw))
    elif nombre == "personajes":
        P.dibujar(c, {"forma": "gota", "color": color, "cara": "feliz", "sombreado": False, "grosor": 0.8}, x, y, s * 0.85, 1.0, {"fase": 1})
    elif nombre == "escenas":
        caja(c, x - s * 0.44, y - s * 0.32, s * 0.88, s * 0.64, s * 0.08, color, borde=linea, borde_ancho=lw)
        p = skia.Path(); p.moveTo(x - s * 0.1, y - s * 0.16); p.lineTo(x + s * 0.2, y); p.lineTo(x - s * 0.1, y + s * 0.16); p.close()
        c.drawPath(p, relleno("#FFFFFF"))
    elif nombre == "montaje":
        for j, (a, b, cc) in enumerate(((0.0, 0.5, color), (0.3, 0.9, aclara(color, 0.35)), (0.1, 0.7, oscurece(color, 0.2)))):
            yy = y - s * 0.3 + j * s * 0.3
            caja(c, x - s * 0.45 + a * s * 0.9, yy - s * 0.1, (b - a) * s * 0.9, s * 0.2, s * 0.06, cc, borde=linea, borde_ancho=lw * 0.8)
        c.drawLine(x + s * 0.05, y - s * 0.48, x + s * 0.05, y + s * 0.48, trazo("#E8475B", lw * 1.1))
    elif nombre == "voz":
        for j in range(7):
            hh = s * (0.15 + 0.3 * abs(math.sin(j * 1.3)))
            c.drawLine(x - s * 0.36 + j * s * 0.12, y - hh, x - s * 0.36 + j * s * 0.12, y + hh, trazo(color, lw * 1.4))
    elif nombre == "ok":
        c.drawCircle(x, y, s * 0.42, relleno(color))
        p = skia.Path(); p.moveTo(x - s * 0.2, y); p.lineTo(x - s * 0.04, y + s * 0.16); p.lineTo(x + s * 0.22, y - s * 0.14)
        c.drawPath(p, trazo("#FFFFFF", lw * 1.6))
    elif nombre == "codigo":
        texto(c, "</>", x, y, "monobold", s * 0.5, color, ancla="centro")
    elif nombre == "chat":
        caja(c, x - s * 0.42, y - s * 0.3, s * 0.84, s * 0.5, s * 0.16, color, borde=linea, borde_ancho=lw)
        p = skia.Path(); p.moveTo(x - s * 0.2, y + s * 0.18); p.lineTo(x - s * 0.3, y + s * 0.38); p.lineTo(x, y + s * 0.18); p.close()
        c.drawPath(p, relleno(color))
    elif nombre == "corazon":
        P._corazon(c, x, y, s * 0.36, color, linea, lw)
    elif nombre == "estrella":
        P.proyectil(c, "estrella", x, y, s * 0.9, 0, color, linea)
    elif nombre == "reloj":
        c.drawCircle(x, y, s * 0.4, relleno("#FFFFFF")); c.drawCircle(x, y, s * 0.4, trazo(linea, lw))
        c.drawLine(x, y, x, y - s * 0.26, trazo(color, lw * 1.2)); c.drawLine(x, y, x + s * 0.18, y + s * 0.06, trazo(color, lw * 1.2))
    elif nombre == "rayo":
        p = skia.Path(); p.moveTo(x + s * 0.08, y - s * 0.45); p.lineTo(x - s * 0.22, y + s * 0.05); p.lineTo(x, y + s * 0.05)
        p.lineTo(x - s * 0.1, y + s * 0.45); p.lineTo(x + s * 0.24, y - s * 0.08); p.lineTo(x + s * 0.02, y - s * 0.08); p.close()
        c.drawPath(p, relleno(color)); c.drawPath(p, trazo(linea, lw * 0.8))
    elif nombre == "lupa":
        c.drawCircle(x - s * 0.08, y - s * 0.08, s * 0.26, trazo(color, lw * 1.6))
        c.drawLine(x + s * 0.12, y + s * 0.12, x + s * 0.34, y + s * 0.34, trazo(color, lw * 2.2))
    elif nombre == "pincel":
        c.drawLine(x - s * 0.3, y + s * 0.3, x + s * 0.25, y - s * 0.25, trazo(linea, lw * 3))
        c.drawLine(x - s * 0.3, y + s * 0.3, x + s * 0.25, y - s * 0.25, trazo(color, lw * 1.6))
    elif nombre == "camara":
        caja(c, x - s * 0.42, y - s * 0.24, s * 0.62, s * 0.48, s * 0.08, color, borde=linea, borde_ancho=lw)
        p = skia.Path(); p.moveTo(x + s * 0.2, y - s * 0.05); p.lineTo(x + s * 0.44, y - s * 0.2); p.lineTo(x + s * 0.44, y + s * 0.2); p.lineTo(x + s * 0.2, y + s * 0.05); p.close()
        c.drawPath(p, relleno(color)); c.drawPath(p, trazo(linea, lw))
    elif nombre == "gota":
        p = skia.Path(); p.moveTo(x, y - s * 0.45)
        p.cubicTo(x + s * 0.18, y - s * 0.15, x + s * 0.34, y + s * 0.05, x + s * 0.32, y + s * 0.18)
        p.cubicTo(x + s * 0.3, y + s * 0.48, x - s * 0.3, y + s * 0.48, x - s * 0.32, y + s * 0.18)
        p.cubicTo(x - s * 0.34, y + s * 0.05, x - s * 0.18, y - s * 0.15, x, y - s * 0.45); p.close()
        c.drawPath(p, relleno(color)); c.drawPath(p, trazo(linea, lw))
    elif nombre == "nube":
        for (dx, dy, r) in ((-0.2, 0.05, 0.2), (0.05, -0.08, 0.26), (0.26, 0.06, 0.18)):
            c.drawCircle(x + dx * s, y + dy * s, r * s, relleno(color))
        c.drawRect(skia.Rect(x - s * 0.2, y + s * 0.02, x + s * 0.26, y + s * 0.24), relleno(color))
    elif nombre == "sol":
        for j in range(8):
            a = j * math.pi / 4
            c.drawLine(x + math.cos(a) * s * 0.3, y + math.sin(a) * s * 0.3, x + math.cos(a) * s * 0.46, y + math.sin(a) * s * 0.46, trazo(color, lw * 1.2))
        c.drawCircle(x, y, s * 0.24, relleno(color)); c.drawCircle(x, y, s * 0.24, trazo(linea, lw))
    elif nombre == "mundo":
        c.drawCircle(x, y, s * 0.4, relleno(color)); c.drawCircle(x, y, s * 0.4, trazo(linea, lw))
        c.drawOval(skia.Rect(x - s * 0.18, y - s * 0.4, x + s * 0.18, y + s * 0.4), trazo("#FFFFFF", lw * 0.9))
        c.drawLine(x - s * 0.4, y, x + s * 0.4, y, trazo("#FFFFFF", lw * 0.9))
    elif nombre == "dinero":
        c.drawCircle(x, y, s * 0.4, relleno(color)); c.drawCircle(x, y, s * 0.4, trazo(linea, lw))
        texto(c, "€", x, y, "black", s * 0.5, "#FFFFFF", ancla="centro")
    elif nombre == "musica":
        c.drawLine(x + s * 0.15, y - s * 0.35, x + s * 0.15, y + s * 0.2, trazo(color, lw * 1.4))
        c.drawCircle(x, y + s * 0.22, s * 0.15, relleno(color))
        c.drawLine(x + s * 0.15, y - s * 0.35, x + s * 0.35, y - s * 0.25, trazo(color, lw * 1.4))
    elif nombre == "portada":
        caja(c, x - s * 0.3, y - s * 0.42, s * 0.6, s * 0.84, s * 0.08, color, borde=linea, borde_ancho=lw)
        c.drawCircle(x, y - s * 0.08, s * 0.14, relleno("#FFFFFF"))
    elif nombre == "texto":
        texto(c, "Aa", x, y, "black", s * 0.55, color, ancla="centro")
    else:
        c.drawCircle(x, y, s * 0.36, relleno(color))


def contenido_pasos(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno(mezcla(est["tarjeta"], est["fondo"], 0.25)))
    items = dat.get("items", [])
    n = len(items)
    cols = dat.get("columnas")
    if cols is None:
        # elige columnas para que las casillas sean anchas
        cols = 2 if n == 4 else (1 if (w / max(1, n) < h * 0.9) and n <= 3 else min(3, n))
    filas = math.ceil(n / cols)
    gap = w * 0.03
    cw = (w - gap * (cols + 1)) / cols
    ch = (h - gap * (filas + 1)) / filas
    for i, it in enumerate(items):
        fi, ci = divmod(i, cols)
        bx = x + gap + ci * (cw + gap)
        by = y + gap + fi * (ch + gap)
        ti = it.get("_t", 0)
        activo = t >= ti
        k = clamp((t - ti) / 0.3)
        fondo = mezcla("#FFFFFF", aclara(est["acento"], 0.75), k)
        caja(c, bx, by, cw, ch, 22, fondo, sombra=0.1, sombra_y=5, difuso=8)
        c.drawRRect(rrect(bx, by, cw, ch, 22), trazo(est["acento"] if activo else est["linea"], 4 if activo else 2.5))
        lbl = it.get("texto", "")
        vertical = cw < ch * 1.25  # casilla estrecha: icono arriba y texto debajo
        if vertical:
            s = min(cw * 0.55, ch * 0.42)
            ix, iy = bx + cw / 2, by + ch * 0.38
        else:
            s = min(cw * 0.3, ch * 0.6)
            ix, iy = bx + s * 0.75 + 12, by + ch * 0.5
        c.save(); c.translate(ix, iy); esc = 1 + 0.18 * math.sin(math.pi * k); c.scale(esc, esc)
        icono(c, it.get("icono", "ok"), 0, 0, s, est["acento"] if activo else est["suave"])
        c.restore()
        if vertical:
            disp = cw * 0.88
            tt = min(ch * 0.17, 54)
            while tt > 22 and ancho(lbl, "extrabold", tt) > disp:
                tt -= 1
            texto(c, lbl, bx + cw / 2, by + ch * 0.8, "extrabold", tt, est["texto"] if activo else est["suave"], ancla="centro")
        else:
            x_txt = ix + s * 0.7 + 10
            disp = bx + cw - x_txt - 16
            tt = min(ch * 0.3, 56)
            while tt > 22 and ancho(lbl, "extrabold", tt) > disp:
                tt -= 1
            texto(c, lbl, x_txt, by + ch * 0.5, "extrabold", tt, est["texto"] if activo else est["suave"])
        if activo:
            ok = rebote(clamp((t - ti) / 0.35))
            c.save(); c.translate(bx + cw - 28, by + 28); c.scale(ok, ok)
            icono(c, "ok", 0, 0, 42, est["ok"])
            c.restore()


def contenido_imagen(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    img = ctx["imagenes"].get(dat["imagen"])
    if img is None:
        img = abrir_imagen(dat["_ruta"])
        ctx["imagenes"][dat["imagen"]] = img
    iw, ih = img.width(), img.height()
    modo = dat.get("ajuste", "cubrir")
    esc = max(w / iw, h / ih) if modo == "cubrir" else min(w / iw, h / ih)
    # zoom con fotogramas clave [{"_t", "zoom", "centro": [u, v]}]
    z, cu, cv = 1.0, 0.5, 0.5
    if dat.get("deriva", True):  # acercamiento lento para que una captura nunca se quede quieta
        z *= 1 + 0.05 * clamp((t - dat.get("_t_ini", 0)) / 6)
    for kf in dat.get("zoom", []):
        if t >= kf["_t"]:
            kk = suave(clamp((t - kf["_t"]) / kf.get("dur", 0.8)))
            z = lerp(z, kf.get("zoom", 1.0), kk)
            cu = lerp(cu, kf.get("centro", [0.5, 0.5])[0], kk)
            cv = lerp(cv, kf.get("centro", [0.5, 0.5])[1], kk)
    e = esc * z
    dw, dh = iw * e, ih * e
    ox = x + w / 2 - cu * dw
    oy = y + h / 2 - cv * dh
    ox = min(x, max(x + w - dw, ox)) if dw >= w else x + (w - dw) / 2
    oy = min(y, max(y + h - dh, oy)) if dh >= h else y + (h - dh) / 2
    c.save()
    c.clipRRect(rrect(x, y, w, h, r), True)
    c.drawRect(skia.Rect(x, y, x + w, y + h), relleno("#FFFFFF"))
    c.drawImageRect(img, skia.Rect(ox, oy, ox + dw, oy + dh), skia.SamplingOptions(skia.FilterMode.kLinear))
    # rodear a mano
    for ro in dat.get("rodear", []):
        if t < ro["_t"]:
            continue
        k = clamp((t - ro["_t"]) / 0.5)
        u0, v0, u1, v1 = ro["rect"]
        rx0, ry0, rx1, ry1 = ox + u0 * dw, oy + v0 * dh, ox + u1 * dw, oy + v1 * dh
        rodear(c, rx0, ry0, rx1, ry1, k, ro.get("color", est["acento"]), max(5, min(w, h) * 0.012))
    c.restore()
    if dat.get("fuente"):
        pildora(c, dat["fuente"], x + w - 14, y + h - 30, "semibold", 22, "#000000", "#FFFFFF", ancla="der", a=0.55)


_CLIPS = {}


def _frames_clip(dat, carpeta):
    """Saca (una vez) los fotogramas de un trozo de vídeo del usuario a JPG y devuelve la lista de rutas."""
    import hashlib, subprocess
    from comun import FFMPEG
    clave = hashlib.md5(f"{dat['_ruta']}|{dat.get('desde', 0)}|{dat.get('dur', 4)}".encode()).hexdigest()[:12]
    if clave in _CLIPS:
        return _CLIPS[clave]
    dest = os.path.join(carpeta, "_clips", clave)
    if not os.path.exists(os.path.join(dest, "listo")):
        os.makedirs(dest, exist_ok=True)
        r = subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", str(dat.get("desde", 0)), "-t", str(dat.get("dur", 4)), "-i", dat["_ruta"],
                            "-vf", "fps=30,scale=960:-2", "-q:v", "3", os.path.join(dest, "f%05d.jpg")], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"No he podido leer el vídeo {dat['_ruta']}: {r.stderr[-300:]}")
        open(os.path.join(dest, "listo"), "w").close()
    lista = sorted(os.path.join(dest, f) for f in os.listdir(dest) if f.endswith(".jpg"))
    if not lista:
        raise SystemExit(f"El trozo de {dat['_ruta']} (desde {dat.get('desde', 0)} s) no tiene fotogramas: revisa «desde».")
    _CLIPS[clave] = lista
    return lista


def contenido_clip(c, rect, t, dat, est, ctx):
    """Trozo de un vídeo del usuario (sin su sonido), en bucle o parado en el último fotograma."""
    x, y, w, h, r = rect
    frames = _frames_clip(dat, ctx["carpeta"])
    n = len(frames)
    i = int(max(0.0, t - dat.get("_t0", 0)) * 30)
    i = i % n if dat.get("bucle", True) else min(i, n - 1)
    cache = ctx.setdefault("_img_clip", {})
    img = cache.get(frames[i])
    if img is None:
        if len(cache) > 12:
            cache.clear()
        img = abrir_imagen(frames[i])
        cache[frames[i]] = img
    iw, ih = img.width(), img.height()
    e = max(w / iw, h / ih) if dat.get("ajuste", "cubrir") == "cubrir" else min(w / iw, h / ih)
    dw, dh = iw * e, ih * e
    c.drawRect(skia.Rect(x, y, x + w, y + h), relleno("#000000"))
    c.drawImageRect(img, skia.Rect(x + (w - dw) / 2, y + (h - dh) / 2, x + (w + dw) / 2, y + (h + dh) / 2), skia.SamplingOptions(skia.FilterMode.kLinear))
    if dat.get("fuente"):
        pildora(c, dat["fuente"], x + w - 14, y + h - 30, "semibold", 22, "#000000", "#FFFFFF", ancla="der", a=0.6)


def rodear(c, x0, y0, x1, y1, k, color, lw):
    """Óvalo dibujado a mano que se traza de 0 a k."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2 * 1.12, (y1 - y0) / 2 * 1.35
    p = skia.Path()
    n = 60
    tot = int(n * 1.12 * k)
    for i in range(tot + 1):
        a = -2.4 + 2 * math.pi * 1.12 * i / n
        wob = 1 + 0.04 * math.sin(i * 0.7)
        px, py = cx + math.cos(a) * rx * wob, cy + math.sin(a) * ry * wob
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, trazo(color, lw))


def contenido_texto(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno(dat.get("fondo", est["tarjeta"])))
    lineas = dat.get("lineas", [dat.get("texto", "")])
    tam = dat.get("tam", h * 0.16)
    for i, ln in enumerate(lineas):
        texto(c, ln, x + w / 2, y + h / 2 + (i - (len(lineas) - 1) / 2) * tam * 1.25, "black", tam, est["texto"], ancla="centro")


def contenido_vacio(c, rect, t, dat, est, ctx):
    x, y, w, h, r = rect
    c.drawRRect(rrect(x, y, w, h, r), relleno(dat.get("fondo", mezcla(est["tarjeta"], est["fondo"], 0.3))))
    # puntos de «cargando»
    for j in range(3):
        a = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 6 - j * 0.9))
        c.drawCircle(x + w / 2 + (j - 1) * 40, y + h / 2, 12, relleno(est["acento"], a))


# ------------------------------------------------------------------ elementos sueltos
def lista_pildoras(c, x, y, w, h, t, items, est, ctx, tam=40):
    # si alguna píldora no cabe en el ancho de la zona, baja el tamaño de todas
    while tam > 22 and any(ancho(it.get("texto", ""), "extrabold", tam) + tam * (2.4 if it.get("ok") else 1.3) + tam * 0.9 > w for it in items):
        tam -= 1
    paso = tam * 1.85
    for i, it in enumerate(items):
        ti = it["_t"]
        if t < ti:
            continue
        k = clamp((t - ti) / 0.3)
        yy = y + tam * 0.9 + i * paso
        xx = x + (i % 2) * tam * 0.9
        ok = it.get("ok")
        fondo = est["acento"] if ok else "#FFFFFF"
        col_t = texto_sobre(fondo)
        s = it.get("texto", "")
        esc = rebote(k)
        c.save(); c.translate(xx, yy); c.rotate((-2 if i % 2 else 1.5) * (1 if not ok else 0)); c.scale(esc, esc)
        icon_w = tam * 1.15 if ok else 0
        tw = ancho(s, "extrabold", tam)
        pad = tam * 0.6
        ww, hh = tw + 2 * pad + icon_w, tam * 1.18 + tam * 0.56
        caja(c, 0, -hh / 2, ww, hh, hh / 2, fondo, sombra=0.22, sombra_y=6, difuso=10)
        c.drawRRect(rrect(0, -hh / 2, ww, hh, hh / 2), trazo(est["texto"], 3))
        if ok:
            cx_ = pad * 0.7 + tam * 0.42
            c.drawCircle(cx_, 0, tam * 0.42, relleno("#FFFFFF"))
            p = skia.Path(); p.moveTo(cx_ - tam * 0.2, 0); p.lineTo(cx_ - tam * 0.05, tam * 0.15); p.lineTo(cx_ + tam * 0.22, -tam * 0.15)
            c.drawPath(p, trazo(est["acento"], tam * 0.12))
        texto(c, s, pad + icon_w, 0, "extrabold", tam, col_t)
        tt = it.get("_tachar")
        if tt is not None and t >= tt:
            kt = clamp((t - tt) / 0.25)
            ya = math.sin(i * 1.7) * tam * 0.08
            c.drawLine(pad * 0.5, ya + 2, pad * 0.5 + (ww - pad) * sale(kt), -ya + 2, trazo(est["acento"], tam * 0.13))
        c.restore()


def nota_mano(c, s, x, y, tx, ty, t, t0, est, tam=46, color=None, curva=0.25, hueco=None):
    """Texto a mano y una flecha curva que se dibuja hacia (tx, ty)."""
    color = color or est["acento"]
    tx_, ty_ = tx, ty
    k = clamp((t - t0) / 0.5)
    if k <= 0:
        return
    # texto: aparece letra a letra
    n = int(len(s) * clamp((t - t0) / 0.6))
    c.save(); c.translate(x, y); c.rotate(-4)
    texto(c, s[:n], 0, 0, "mano", tam, color, ancla="centro")
    c.restore()
    if tx is None:
        return
    # flecha desde el borde del texto
    w = ancho(s, "mano", tam)
    sx = x + (w * 0.2 if tx > x else -w * 0.2)
    sy = y - tam * 0.7 if ty < y else y + tam * 0.6
    mx, my = (sx + tx) / 2 + (ty - sy) * curva, (sy + ty) / 2 - (tx - sx) * curva
    kk = clamp((t - t0 - 0.15) / 0.4)
    if kk <= 0:
        return
    pts = []
    for i in range(31):
        u = i / 30 * kk
        px = (1 - u) ** 2 * sx + 2 * (1 - u) * u * mx + u * u * tx
        py = (1 - u) ** 2 * sy + 2 * (1 - u) * u * my + u * u * ty
        pts.append((px, py))
    p = skia.Path(); p.moveTo(*pts[0])
    dentro = False
    for q in pts[1:]:
        en_hueco = hueco is not None and hueco[0] <= q[1] <= hueco[1]
        if en_hueco:
            dentro = True
            continue
        if dentro:
            p.moveTo(*q); dentro = False
        else:
            p.lineTo(*q)
    c.drawPath(p, trazo(color, max(4, tam * 0.11)))
    if kk >= 1:
        ex, ey = pts[-1]; bx, by = pts[-4]
        a = math.atan2(ey - by, ex - bx)
        L = tam * 0.45
        for d in (2.6, -2.6):
            c.drawLine(ex, ey, ex + math.cos(a + d) * L, ey + math.sin(a + d) * L, trazo(color, max(4, tam * 0.11)))


def titular(c, lineas, x, y, w, t, est, tam=96, ancla="centro"):
    """Líneas grandes. Cada línea: {"t": texto, "clave": bool, "_t": segundo}."""
    yy = y
    for ln in lineas:
        ti = ln.get("_t", 0)
        if t < ti:
            yy += tam * 1.22
            continue
        k = clamp((t - ti) / 0.3)
        s = ln["t"]
        tt = min(tam, tam * w / max(1, ancho(s, "black", tam) + (tam * 0.7 if ln.get("clave") else 0)))
        c.save(); c.translate(x, yy); esc = lerp(0.85, 1, rebote(k)); c.scale(esc, esc)
        if ln.get("clave"):
            ww = ancho(s, "black", tt) + tt * 0.6
            c.save(); c.rotate(-2)
            caja(c, -ww / 2, -tt * 0.7, ww, tt * 1.35, 18, est["acento"], sombra=0.25, sombra_y=8, difuso=10)
            texto(c, s, 0, 0, "black", tt, texto_sobre(est["acento"]), ancla="centro")
            c.restore()
        else:
            texto(c, s, 0, 0, "black", tt, est["texto"], ancla="centro")
        c.restore()
        yy += tam * 1.3


def contador(c, x, y, t, dat, est, tam=110):
    t0 = dat["_t"]
    if t < t0:
        return
    k = clamp((t - t0) / dat.get("dur", 1.2))
    a, b = dat.get("de", 0), dat.get("a", 100)
    v = a + (b - a) * sale(k, 3)
    dec = dat.get("decimales", 0)
    num = numero(v, dec)
    s = dat.get("formato", "{n}").replace("{n}", num)
    esc = rebote(clamp((t - t0) / 0.35))
    c.save(); c.translate(x, y); c.scale(esc, esc)
    texto(c, s, 0, 0, "black", tam, est["acento"], ancla="centro")
    if dat.get("etiqueta"):
        texto(c, dat["etiqueta"], 0, tam * 0.85, "bold", tam * 0.34, est["texto"], ancla="centro")
    c.restore()


def movil(c, x, y, w, t, dat, est, ctx):
    """Marco de móvil con una captura dentro (vertical). (x, y) = esquina superior izquierda."""
    img = ctx["imagenes"].get(dat["imagen"])
    if img is None:
        img = abrir_imagen(dat["_ruta"])
        ctx["imagenes"][dat["imagen"]] = img
    h = w * 2.05
    r = w * 0.13
    sombra_tarjeta(c, x, y, w, h, r, 0.28)
    c.drawRRect(rrect(x, y, w, h, r), relleno("#15171D"))
    b = w * 0.035
    inner = (x + b, y + b, w - 2 * b, h - 2 * b, r - b)
    dat2 = dict(dat); dat2.setdefault("ajuste", "cubrir")
    contenido_imagen(c, inner, t, dat2, est, ctx)
    c.drawRRect(rrect(x + w * 0.36, y + b + w * 0.03, w * 0.28, w * 0.065, w * 0.033), relleno("#15171D"))
    return h


def _cabe(s, peso, tam, w):
    while tam > 16 and ancho(s, peso, tam) > w:
        tam -= 1
    return tam


def cta(c, x, y, t, t0, palabra, linea, nota, est, ctx, tam=1.0, titulo=None):
    k = clamp((t - t0) / 0.45)
    if k <= 0:
        return
    Wf = ctx.get("W", 1080)
    W = min(Wf - 80, (820 if ctx["formato"] == "9:16" else 900) * tam)
    H = 330 * tam
    titulo = titulo or tx("comenta")
    esc = rebote(k)
    c.save(); c.translate(x, y + (1 - sale(k)) * 60); c.scale(esc, esc)
    # bocadillo
    c.drawRRect(rrect(-W / 2, -H / 2 + 16, W, H, 46), sombra_paint("#3A2A1A", 0.25, 20))
    cola = skia.Path(); cola.moveTo(-40, H / 2 - 4); cola.lineTo(0, H / 2 + 50); cola.lineTo(40, H / 2 - 4); cola.close()
    c.drawRRect(rrect(-W / 2, -H / 2, W, H, 46), relleno("#FFFFFF"))
    c.drawPath(cola, relleno("#FFFFFF"))
    texto(c, titulo, 0, -H * 0.22, "black", _cabe(titulo, "black", 76 * tam, W * 0.9), est["texto"], ancla="centro")
    tp = _cabe(f"“{palabra}”", "black", 92 * tam, W * 0.86 - 90 * tam)
    pw = ancho(f"“{palabra}”", "black", tp) + 90 * tam
    ph = 128 * tam
    lat = 1 + 0.03 * math.sin(t * 5)
    c.save(); c.translate(0, H * 0.17); c.rotate(-2.5); c.scale(lat, lat)
    caja(c, -pw / 2, -ph / 2, pw, ph, ph / 2, est["acento"], sombra=0.3, sombra_y=8, difuso=12)
    texto(c, f"“{palabra}”", 0, 0, "black", tp, texto_sobre(est["acento"]), ancla="centro")
    c.restore()
    c.restore()
    if linea:
        k2 = clamp((t - t0 - 0.35) / 0.35)
        if k2 > 0:
            tl = _cabe(linea, "extrabold", 56 * tam, Wf - 100)
            with Capa(c, k2):
                texto(c, linea, x, y + H / 2 + 120 * tam, "extrabold", tl, est["texto"], ancla="centro")
                w = ancho(linea, "extrabold", tl)
                yy = y + H / 2 + 120 * tam + tl * 0.72
                p = skia.Path(); p.moveTo(x - w / 2, yy)
                for i in range(1, 21):
                    p.lineTo(x - w / 2 + w * i / 20 * sale(k2), yy + math.sin(i * 0.9) * 4)
                c.drawPath(p, trazo(est["acento"], 9, 0.9))
    if nota:
        nota_mano(c, nota, x, y + H / 2 + 230 * tam, None, None, t, t0 + 0.7, est, tam=_cabe(nota, "mano", 50 * tam, Wf - 100))


def siguenos(c, x, y, t, t0, lineas, est, ctx, tam=1.0, icono_=None):
    """Final «sígueme»: tarjeta con la primera línea y un corazón que late; hasta 2 líneas más debajo."""
    k = clamp((t - t0) / 0.45)
    if k <= 0:
        return
    lineas = list(lineas or [tx("sigueme")])
    Wf = ctx.get("W", 1080)
    W = min(Wf - 80, 820 * tam)
    H = 420 * tam
    esc = rebote(k)
    c.save(); c.translate(x, y); c.scale(esc, esc)
    c.drawRRect(rrect(-W / 2, -H / 2 + 16, W, H, 46), sombra_paint("#3A2A1A", 0.25, 20))
    c.drawRRect(rrect(-W / 2, -H / 2, W, H, 46), relleno("#FFFFFF"))
    texto(c, lineas[0], 0, -H * 0.2, "black", _cabe(lineas[0], "black", 92 * tam, W * 0.88), est["texto"], ancla="centro")
    lat = 1 + 0.12 * max(0, math.sin(t * 6)) ** 8
    c.save(); c.translate(0, H * 0.14); c.scale(lat, lat)
    if icono_ == "campana":
        rot_ = math.sin(t * 9) * 12 * max(0, math.sin(t * 2))
        c.rotate(rot_)
        q = skia.Path(); s_ = 62 * tam
        q.moveTo(-s_ * 0.9, s_ * 0.5); q.cubicTo(-s_ * 0.6, s_ * 0.3, -s_ * 0.75, -s_ * 0.9, 0, -s_ * 0.9)
        q.cubicTo(s_ * 0.75, -s_ * 0.9, s_ * 0.6, s_ * 0.3, s_ * 0.9, s_ * 0.5); q.close()
        c.drawPath(q, relleno(est["acento"])); c.drawPath(q, trazo("#1D1B2E", 6))
        c.drawCircle(0, s_ * 0.62, s_ * 0.2, relleno(est["acento"])); c.drawCircle(0, s_ * 0.62, s_ * 0.2, trazo("#1D1B2E", 5))
    elif icono_ and icono_ != "corazon":
        icono(c, icono_, 0, 0, 130 * tam, est["acento"])
    else:
        P._corazon(c, 0, 0, 62 * tam, "#FF3B5C", "#1D1B2E", 6)
    c.restore()
    c.restore()
    for j, ln in enumerate(lineas[1:3]):
        k2 = clamp((t - t0 - 0.4 - 0.3 * j) / 0.35)
        if k2 > 0:
            with Capa(c, k2):
                texto(c, ln, x, y + H / 2 + (100 + 80 * j) * tam, "extrabold" if j == 0 else "cursiva",
                      _cabe(ln, "extrabold", (56 if j == 0 else 48) * tam, Wf - 100), est["texto"], ancla="centro")
    if len(lineas) > 3:
        print("  AVISO: «siguenos» enseña como mucho 3 líneas; sobran", len(lineas) - 3)


# ------------------------------------------------------------------ subtítulos
ENLACES = {"de", "la", "el", "en", "que", "y", "a", "los", "las", "un", "una", "con", "por", "para", "del", "al", "su",
           "sus", "tu", "mi", "se", "lo", "o", "e", "ni", "le", "les", "the", "of", "to", "and", "an", "in", "on", "for"}


def marcar_claves(palabras):
    """Marca cada palabra con _clave (va en caja) y _grupo (palabras clave seguidas forman un grupo)."""
    en_clave, grupo = False, 0
    for w in palabras:
        s = w["t"]
        if s.startswith("*") or s.startswith("¿*") or s.startswith("¡*"):
            en_clave = True
            grupo += 1
        w["_clave"] = en_clave
        w["_grupo"] = grupo if en_clave else 0
        if s.rstrip(",.;:?!»”\"").endswith("*"):
            en_clave = False
    return palabras


def trozos_subtitulos(palabras, tam, ancho_max, max_pal=5):
    """Agrupa las palabras de cada frase en trozos de una línea, sin partir un grupo de palabras clave."""
    marcar_claves(palabras)
    salida = []
    for fi in sorted(set(p["frase"] for p in palabras)):
        ws = [p for p in palabras if p["frase"] == fi]
        actual = []
        for w in ws:
            prueba = actual + [w]
            txt = " ".join(limpia(p["t"]) for p in prueba)
            ancho_ = ancho(txt, "extrabold", tam)
            corta = actual and (ancho_ > ancho_max or len(prueba) > max_pal)
            mismo_grupo = actual and w["_grupo"] and actual[-1]["_grupo"] == w["_grupo"]
            if corta and mismo_grupo and ancho_ <= ancho_max * 1.12 and len(prueba) <= max_pal + 2:
                corta = False  # deja que el grupo clave termine en la misma línea
            if corta:
                # no partir el grupo clave: mueve el grupo entero al trozo siguiente
                if mismo_grupo:
                    j = len(actual)
                    while j > 0 and actual[j - 1]["_grupo"] == w["_grupo"]:
                        j -= 1
                    if j > 0:
                        salida.append(actual[:j]); actual = actual[j:] + [w]
                        continue
                # no acabar en palabra de enlace
                if len(actual) > 1 and normaliza(actual[-1]["t"]) in ENLACES:
                    w_ = actual.pop()
                    salida.append(actual); actual = [w_, w]
                else:
                    salida.append(actual); actual = [w]
            else:
                actual = prueba
            if w["t"].rstrip("*»”")[-1:] in ",.;:?!" and len(actual) >= 2 and not (w["_grupo"] and not w["t"].rstrip(",.;:?!»”").endswith("*")):
                salida.append(actual); actual = []
        if actual:
            salida.append(actual)
    return salida


def limpia(t):
    return t.replace("*", "")


def subtitulos(c, trozos, t, cfg, est, W):
    """Enseña el último trozo que ha empezado; se queda en pantalla hasta que empieza el siguiente (o 0,6 s)."""
    actual = None
    for i, tr in enumerate(trozos):
        if tr[0]["ini"] - 0.05 <= t:
            actual = i
        else:
            break
    if actual is None:
        return
    tr = trozos[actual]
    if t > tr[-1]["fin"] + 0.6:
        return
    _dibuja_trozo(c, tr, t, W / 2, cfg["y"], cfg["tam"], est)


def _dibuja_trozo(c, tr, t, cx, y, tam, est):
    grupos = []
    for w in tr:
        txt = limpia(w["t"])
        clave = w.get("_clave", False)
        if grupos and clave and grupos[-1]["clave"] and grupos[-1]["grupo"] == w.get("_grupo"):
            grupos[-1]["ws"].append((txt, w))
        else:
            grupos.append({"clave": clave, "grupo": w.get("_grupo"), "ws": [(txt, w)]})
    esp = ancho(" ", "extrabold", tam)
    anchos = []
    for g in grupos:
        s = " ".join(x for x, _ in g["ws"])
        anchos.append(ancho(s, "extrabold", tam) + (tam * 0.42 if g["clave"] else 0))
    total = sum(anchos) + esp * (len(grupos) - 1)
    x = cx - total / 2
    for g, wg in zip(grupos, anchos):
        ini = g["ws"][0][1]["ini"]
        if g["clave"]:
            k = clamp((t - ini + 0.06) / 0.16)
            if k > 0:
                # la caja crece palabra a palabra
                dichas = [(txt, w) for txt, w in g["ws"] if t >= w["ini"] - 0.06]
                s_dicho = " ".join(x_ for x_, _ in dichas)
                w_obj = ancho(s_dicho, "extrabold", tam) + tam * 0.42
                ult = dichas[-1][1]
                kk = clamp((t - ult["ini"] + 0.06) / 0.12) if len(dichas) > 1 else 1.0
                prev_w = ancho(" ".join(x_ for x_, _ in dichas[:-1]), "extrabold", tam) + tam * 0.42 if len(dichas) > 1 else w_obj
                wc = lerp(prev_w, w_obj, sale(kk))
                c.save(); c.translate(x + wc / 2, y); c.rotate(-1.5); c.scale(lerp(0.6, 1, rebote(k)), lerp(0.6, 1, rebote(k)))
                caja(c, -wc / 2, -tam * 0.66, wc, tam * 1.3, 14, est["acento"], sombra=0.25, sombra_y=6, difuso=8)
                xx = -wc / 2 + tam * 0.21
                for j, (txt, w) in enumerate(dichas):
                    a_ = sale(kk) if (j == len(dichas) - 1 and len(dichas) > 1) else 1.0
                    texto(c, txt, xx, 0, "extrabold", tam, texto_sobre(est["acento"]), a=a_)
                    xx += ancho(txt + " ", "extrabold", tam)
                c.restore()
        else:
            xx = x
            for txt, w in g["ws"]:
                k = clamp((t - w["ini"] + 0.06) / 0.12)
                if k > 0:
                    c.save(); c.translate(xx, y + (1 - sale(k)) * 10)
                    texto(c, txt, 0, 0, "extrabold", tam, est["texto"], a=k)
                    c.restore()
                xx += ancho(txt + " ", "extrabold", tam)
        x += wg + esp
