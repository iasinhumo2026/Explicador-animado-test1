"""Personajes vectoriales con cara, dibujados con Skia.

Un personaje es un dict (ver referencias/personajes.md):
  {"forma": "gota", "color": "#FFD27A", "color2": "#F2A93B", "detalle": "nucleo",
   "accesorios": ["babero"], "cara": "feliz", "ojos": 2, "mejillas": true}

dibujar(c, spec, x, y, tam, t, est) lo pinta centrado en (x, y) con diámetro tam
(en «humano», (x, y) son los pies y tam es la altura total).
est (opcional): cara, boca (0–1, para hablar o comer), redondez (0–1), mirar (dx, dy),
parpadeo (0–1), rot (grados), escala, squash (−0,3…0,3), lado (1 o −1), fase, pose, alfa.
"""
import math

import skia

from comun import (Capa, aclara, clamp, col, fuente, mezcla, oscurece, relleno, ruido1, trazo)

CONTORNO = "#1D1B2E"
_AVISO_ACC = set()
FORMAS = ["circulo", "gota", "capsula", "fantasma", "virus", "disco", "estrella", "cuadrado", "nube",
          "gota_agua", "corazon", "planeta", "hoja", "flor", "maceta", "montana", "volcan", "humano"]
EXPRESIONES = ["neutro", "feliz", "risa", "enfadado", "sorpresa", "miedo", "picaro", "triste", "decidido",
               "dormido", "hambre", "mareado", "enamorado"]
ACCESORIOS = ["casco", "escudo", "lanza", "espada", "gafas", "corona", "cinta", "babero", "bandera",
              "sombrero", "gorro_chef", "auriculares", "antena", "tornillos", "bigote", "capa", "chip"]


# ------------------------------------------------------------------ utilidades
def _lum(c_):
    from comun import luminancia
    return luminancia(c_)


def _parpadeo_auto(t, fase):
    """Parpadeo natural: cada 2,5–4 s, 0,12 s cerrado."""
    periodo = 2.6 + (fase * 7.31 % 1.4)
    x = (t + fase * 3.1) % periodo
    if x < 0.06:
        return x / 0.06
    if x < 0.12:
        return 1 - (x - 0.06) / 0.06
    return 0.0


def _ancho_contorno(spec, R):
    if spec.get("contorno") is False:
        return 0
    k = spec.get("grosor", 1.0)
    return max(2.0, R * 0.075 * k)


def _pintar(c, path, color, lw, linea=CONTORNO, sombreado=True, R=50, cx=0, cy=0, brillo=True):
    c.drawPath(path, relleno(color))
    if sombreado:
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, False)
        p = relleno(oscurece(color, 0.16), 0.9)
        c.drawOval(skia.Rect(cx - R * 1.25 + R * 0.35, cy - R * 0.2 + R * 0.55, cx + R * 1.25 + R * 0.35, cy + R * 2.0), p)
        if brillo:
            c.drawOval(skia.Rect(cx - R * 0.72, cy - R * 0.78, cx - R * 0.22, cy - R * 0.48), relleno("#FFFFFF", 0.45))
        c.restore()
    if lw > 0:
        c.drawPath(path, trazo(linea, lw))


def _path_poligono(puntos, cerrar=True):
    p = skia.Path()
    p.moveTo(*puntos[0])
    for q in puntos[1:]:
        p.lineTo(*q)
    if cerrar:
        p.close()
    return p


def _path_suave(puntos):
    """Curva cerrada suave (Catmull-Rom) por una lista de puntos."""
    n = len(puntos)
    p = skia.Path()
    p.moveTo(*puntos[0])
    for i in range(n):
        p0, p1, p2, p3 = puntos[(i - 1) % n], puntos[i], puntos[(i + 1) % n], puntos[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    p.close()
    return p


# ------------------------------------------------------------------ cuerpos
def cuerpo(forma, R, t, fase, spec):
    """Devuelve (path, centro_cara_y, escala_cara) en coordenadas locales (centro en 0,0)."""
    if forma == "circulo" or forma == "planeta":
        p = skia.Path(); p.addCircle(0, 0, R)
        return p, -R * 0.05, R
    if forma == "gota":
        pts = []
        for k in range(28):
            a = 2 * math.pi * k / 28
            r = R * (1 + 0.055 * math.sin(3 * a + t * 1.6 + fase * 5) + 0.035 * math.sin(5 * a - t * 2.3 + fase * 3)
                     + 0.025 * math.sin(7 * a + t * 3.1))
            pts.append((math.cos(a) * r, math.sin(a) * r * 0.94))
        return _path_suave(pts), -R * 0.05, R
    if forma == "capsula":
        L, H = R * 1.15, R * 0.68
        curva = math.sin(t * 3 + fase * 6) * R * 0.06
        pts = []
        for k in range(32):
            a = 2 * math.pi * k / 32
            x = math.cos(a); y = math.sin(a)
            # superelipse para un cuerpo de píldora
            ex = math.copysign(abs(x) ** 0.6, x) * L
            ey = math.copysign(abs(y) ** 0.9, y) * H
            ey += curva * (ex / L) ** 2
            pts.append((ex, ey))
        return _path_suave(pts), -R * 0.02, R * 0.78
    if forma == "fantasma":
        p = skia.Path()
        w, top, bot = R * 0.92, -R * 1.0, R * 0.92
        p.moveTo(-w, 0)
        p.cubicTo(-w, top * 1.33, w, top * 1.33, w, 0)
        p.lineTo(w, bot * 0.7)
        n = 3
        for k in range(n):
            x0 = w - 2 * w * k / n
            x1 = w - 2 * w * (k + 1) / n
            ola = math.sin(t * 5 + k * 1.7 + fase * 4) * R * 0.08
            p.quadTo((x0 + x1) / 2, bot + R * 0.18 + ola, x1, bot * 0.7)
        p.close()
        return p, -R * 0.12, R
    if forma == "virus":
        p = skia.Path(); p.addCircle(0, 0, R * 0.82)
        return p, 0, R * 0.85
    if forma == "disco":
        p = skia.Path(); p.addOval(skia.Rect(-R, -R * 0.78, R, R * 0.78))
        return p, -R * 0.02, R * 0.8
    if forma == "estrella":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + math.pi * k / 5
            r = R if k % 2 == 0 else R * 0.5
            pts.append((math.cos(a) * r, math.sin(a) * r + R * 0.08))
        return _path_suave_esquinas(pts, R * 0.12), R * 0.12, R * 0.62
    if forma == "cuadrado":
        p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.92, -R * 0.92, R * 0.92, R * 0.92), R * 0.32, R * 0.32))
        return p, -R * 0.05, R
    if forma == "nube":
        p = skia.Path()
        for (bx, by, br) in ((-0.55, 0.12, 0.5), (0.0, -0.18, 0.62), (0.55, 0.1, 0.52), (0.0, 0.25, 0.55),
                             (-0.95, 0.32, 0.34), (0.95, 0.32, 0.34)):
            q = skia.Path(); q.addCircle(bx * R, by * R + math.sin(t * 1.5 + bx * 3 + fase) * R * 0.02, br * R)
            p = skia.Op(p, q, skia.PathOp.kUnion_PathOp) if not p.isEmpty() else q
        return p, R * 0.08, R * 0.85
    if forma == "gota_agua":
        p = skia.Path()
        p.moveTo(0, -R * 1.15)
        p.cubicTo(R * 0.35, -R * 0.55, R * 0.95, -R * 0.05, R * 0.9, R * 0.3)
        p.cubicTo(R * 0.85, R * 0.85, -R * 0.85, R * 0.85, -R * 0.9, R * 0.3)
        p.cubicTo(-R * 0.95, -R * 0.05, -R * 0.35, -R * 0.55, 0, -R * 1.15)
        p.close()
        return p, R * 0.22, R * 0.78
    if forma == "corazon":
        p = skia.Path()
        p.moveTo(0, R * 0.95)
        p.cubicTo(-R * 1.4, -R * 0.05, -R * 0.75, -R * 1.15, 0, -R * 0.45)
        p.cubicTo(R * 0.75, -R * 1.15, R * 1.4, -R * 0.05, 0, R * 0.95)
        p.close()
        return p, -R * 0.08, R * 0.75
    if forma in ("montana", "volcan"):
        p = skia.Path()
        top = -R * 0.95
        crater = R * (0.28 if forma == "volcan" else 0.0)
        p.moveTo(-R * 1.35, R * 0.85)
        p.cubicTo(-R * 0.9, R * 0.3, -R * 0.45, top + R * 0.25, -crater - R * 0.08, top)
        if forma == "volcan":
            p.quadTo(0, top + R * 0.12, crater + R * 0.08, top)
        else:
            p.quadTo(0, top - R * 0.12, R * 0.08, top)
        p.cubicTo(R * 0.45, top + R * 0.25, R * 0.9, R * 0.3, R * 1.35, R * 0.85)
        p.close()
        return p, R * 0.25, R * 0.62
    if forma == "hoja":
        p = skia.Path()
        sw = math.sin(t * 2 + fase) * R * 0.03
        p.moveTo(0, -R * 1.1)
        p.cubicTo(R * 0.95 + sw, -R * 0.6, R * 0.85, R * 0.6, 0, R * 1.05)
        p.cubicTo(-R * 0.85, R * 0.6, -R * 0.95 + sw, -R * 0.6, 0, -R * 1.1)
        p.close()
        return p, R * 0.05, R * 0.72
    if forma == "flor":
        p = skia.Path(); p.addCircle(0, 0, R * 0.62)
        return p, 0, R * 0.62
    if forma == "maceta":
        p = skia.Path()
        p.moveTo(-R * 0.85, -R * 0.35); p.lineTo(R * 0.85, -R * 0.35)
        p.lineTo(R * 0.62, R * 0.95); p.lineTo(-R * 0.62, R * 0.95); p.close()
        return p, R * 0.25, R * 0.62
    p = skia.Path(); p.addCircle(0, 0, R)
    return p, 0, R


def _path_suave_esquinas(pts, radio):
    p = _path_poligono(pts)
    q = skia.Path()
    eff = skia.CornerPathEffect.Make(radio)
    paint = skia.Paint(PathEffect=eff)
    ok = paint.getFillPath(p, q)
    return q if ok else p


# ------------------------------------------------------------------ cara
def _expresion(nombre):
    """(ceja_ang, ceja_alto, ojo_escala, ojo_medio, boca)."""
    tabla = {
        "neutro": (0, 0, 1.0, 0, "linea"),
        "feliz": (-6, 0.02, 1.0, 0, "sonrisa"),
        "risa": (-8, 0.05, 0.95, 0.25, "risa"),
        "enfadado": (24, -0.04, 0.95, 0.28, "dientes"),
        "sorpresa": (-10, 0.12, 1.22, 0, "o"),
        "miedo": (-22, 0.08, 1.15, 0, "ola"),
        "picaro": (14, 0.0, 1.0, 0.42, "ladeada"),
        "triste": (-20, 0.03, 1.0, 0.2, "pena"),
        "decidido": (16, -0.02, 1.0, 0.25, "firme"),
        "dormido": (0, 0, 1.0, 1.0, "linea"),
        "hambre": (-4, 0.06, 1.12, 0, "bocaza"),
        "mareado": (0, 0.02, 1.0, 0, "ola"),
        "enamorado": (-8, 0.04, 1.0, 0, "sonrisa"),
    }
    return tabla.get(nombre, tabla["neutro"])


def cara(c, cx, cy, s, t, est, spec, lw):
    nombre = est.get("cara") or spec.get("cara", "feliz")
    ceja_ang, ceja_alto, ojo_k, medio, boca_tipo = _expresion(nombre)
    linea = spec.get("linea", CONTORNO)
    nojos = int(spec.get("ojos", 2))
    mdx, mdy = est.get("mirar", (0.0, 0.0))
    parp = max(est.get("parpadeo", 0.0), _parpadeo_auto(t, est.get("fase", 0.0)) if spec.get("parpadea", True) else 0)
    sep = s * 0.36 * spec.get("ojos_sep", 1.0)
    ry = s * 0.2 * ojo_k * spec.get("ojos_tam", 1.0)
    rx = ry * 0.86
    ey = cy - s * 0.12
    xs = [0] if nojos == 1 else ([-sep, sep] if nojos == 2 else [-sep * 1.2, 0, sep * 1.2])
    if nojos == 1:
        rx, ry = rx * 1.45, ry * 1.45
    lwo = max(1.6, min(lw * 0.8, s * 0.07))
    for i, ex in enumerate(xs):
        ox = cx + ex
        cerrado = max(parp, medio if nombre != "dormido" else 1.0)
        if nombre == "mareado":
            p = skia.Path()
            for k in range(30):
                a = k / 29 * math.pi * 4 + t * 6
                r = rx * 0.9 * k / 29
                if k == 0:
                    p.moveTo(ox, ey)
                p.lineTo(ox + math.cos(a) * r, ey + math.sin(a) * r)
            c.drawPath(p, trazo(linea, lwo))
            continue
        if nombre == "enamorado":
            _corazon(c, ox, ey, rx * 1.05, "#E8475B", linea, lwo)
            continue
        if cerrado >= 0.92:
            p = skia.Path()
            if nombre in ("risa", "dormido", "feliz") or medio >= 0.9:
                p.moveTo(ox - rx, ey + ry * 0.1)
                p.quadTo(ox, ey - ry * 0.9 if nombre == "risa" else ey + ry * 0.55, ox + rx, ey + ry * 0.1)
            else:
                p.moveTo(ox - rx, ey); p.lineTo(ox + rx, ey)
            c.drawPath(p, trazo(linea, lwo * 1.1))
            continue
        # blanco del ojo
        c.drawOval(skia.Rect(ox - rx, ey - ry, ox + rx, ey + ry), relleno("#FFFFFF"))
        # pupila
        pr = rx * (0.62 if spec.get("pupila", "grande") == "grande" else 0.42)
        px = ox + mdx * (rx - pr) * 0.8
        py = ey + mdy * (ry - pr) * 0.8 + ry * 0.08
        c.save()
        clip = skia.Path(); clip.addOval(skia.Rect(ox - rx, ey - ry, ox + rx, ey + ry))
        c.clipPath(clip, skia.ClipOp.kIntersect, False)
        c.drawCircle(px, py, pr, relleno(spec.get("color_ojos", "#1D1B2E")))
        c.drawCircle(px - pr * 0.35, py - pr * 0.38, pr * 0.32, relleno("#FFFFFF"))
        c.drawCircle(px + pr * 0.3, py + pr * 0.3, pr * 0.13, relleno("#FFFFFF", 0.8))
        # párpado (parpadeo o mirada entornada)
        k = max(cerrado, 0)
        if k > 0.02:
            c.drawRect(skia.Rect(ox - rx - 2, ey - ry - 2, ox + rx + 2, ey - ry + 2 * ry * k), relleno(spec.get("_parpado", spec.get("color", "#FFFFFF"))))
        c.restore()
        c.drawOval(skia.Rect(ox - rx, ey - ry, ox + rx, ey + ry), trazo(linea, lwo))
        if spec.get("pestanas") and k < 0.5:
            sgn_ = -1 if ex < 0 else 1
            for j in range(3):
                a0 = math.radians(-60 - j * 22) if sgn_ > 0 else math.radians(-120 + j * 22)
                px0, py0 = ox + math.cos(a0) * rx, ey + math.sin(a0) * ry
                c.drawLine(px0, py0, px0 + math.cos(a0) * rx * 0.45, py0 + math.sin(a0) * ry * 0.4, trazo(linea, lwo * 0.9))
        if k > 0.02:
            yy = ey - ry + 2 * ry * k
            c.drawLine(ox - rx * math.sqrt(max(0, 1 - ((yy - ey) / ry) ** 2)), yy,
                       ox + rx * math.sqrt(max(0, 1 - ((yy - ey) / ry) ** 2)), yy, trazo(linea, lwo))
    # cejas
    if spec.get("cejas", True):
        for i, ex in enumerate(xs):
            sgn = -1 if ex < 0 else 1
            if nojos == 1:
                sgn = 1
            ox = cx + ex
            by = ey - ry - s * (0.08 - ceja_alto)
            ang = math.radians(ceja_ang) * (sgn if nombre != "picaro" else (1 if i == 0 else -0.6))
            L = rx * 1.0
            dx, dy = math.cos(ang) * L, math.sin(ang) * L
            c.drawLine(ox - dx * sgn, by - dy, ox + dx * sgn, by + dy, trazo(linea, lwo * 1.25))
    # mejillas
    if spec.get("mejillas", True) and nombre not in ("enfadado", "mareado"):
        mc = spec.get("color_mejillas", "#FF7B8A")
        for ex in (xs[0], xs[-1]):
            ox = cx + ex * 1.32
            c.drawOval(skia.Rect(ox - rx * 0.75, ey + ry * 1.05, ox + rx * 0.75, ey + ry * 1.55), relleno(mc, 0.45))
    # boca
    boca(c, cx, cy + s * 0.28, s, est, boca_tipo, linea, lwo, t)
    # extras
    if nombre == "miedo":
        _gota_sudor(c, cx + s * 0.62, cy - s * 0.35, s * 0.13, lwo, linea)
    if nombre == "dormido":
        texto_z = fuente("extrabold", s * 0.32)
        a = (t * 0.8) % 1
        c.drawString("z", cx + s * 0.55 + a * s * 0.2, cy - s * 0.5 - a * s * 0.4, texto_z, relleno(linea, 1 - a))


def boca(c, cx, cy, s, est, tipo, linea, lw, t):
    ab = est.get("boca")
    red = est.get("redondez", 0.3)
    w = s * 0.34
    oscuro = "#5B1A2A"
    lengua = "#FF7B8A"
    if ab is not None and tipo not in ("bocaza",):
        # hablando: la forma depende de la abertura y la redondez
        if ab < 0.06:
            tipo = "sonrisa" if tipo in ("sonrisa", "risa", "feliz") else ("linea" if tipo not in ("dientes", "pena") else tipo)
        else:
            hh = s * 0.06 + s * 0.26 * ab
            ww = w * (1.1 - 0.5 * red)
            p = skia.Path()
            p.moveTo(cx - ww, cy - hh * 0.15)
            p.cubicTo(cx - ww, cy + hh * 1.1, cx + ww, cy + hh * 1.1, cx + ww, cy - hh * 0.15)
            p.cubicTo(cx + ww * 0.6, cy - hh * 0.45, cx - ww * 0.6, cy - hh * 0.45, cx - ww, cy - hh * 0.15)
            p.close()
            c.drawPath(p, relleno(oscuro))
            c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
            c.drawOval(skia.Rect(cx - ww * 0.6, cy + hh * 0.35, cx + ww * 0.6, cy + hh * 1.2), relleno(lengua))
            c.restore()
            c.drawPath(p, trazo(linea, lw))
            return
    if tipo == "linea":
        p = skia.Path(); p.moveTo(cx - w * 0.6, cy); p.quadTo(cx, cy + s * 0.05, cx + w * 0.6, cy)
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "sonrisa":
        p = skia.Path(); p.moveTo(cx - w, cy - s * 0.04); p.quadTo(cx, cy + s * 0.2, cx + w, cy - s * 0.04)
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "risa":
        p = skia.Path(); p.moveTo(cx - w * 1.05, cy - s * 0.06)
        p.cubicTo(cx - w, cy + s * 0.34, cx + w, cy + s * 0.34, cx + w * 1.05, cy - s * 0.06); p.close()
        c.drawPath(p, relleno(oscuro))
        c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
        c.drawOval(skia.Rect(cx - w * 0.55, cy + s * 0.1, cx + w * 0.55, cy + s * 0.34), relleno(lengua))
        c.restore()
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "dientes":
        h = s * 0.16
        p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect(cx - w, cy - h * 0.4, cx + w, cy + h * 0.75), h * 0.4, h * 0.4))
        c.drawPath(p, relleno("#FFFFFF"))
        c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
        zig = skia.Path(); zig.moveTo(cx - w, cy + h * 0.15)
        n = 6
        for k in range(n + 1):
            x = cx - w + 2 * w * k / n
            zig.lineTo(x, cy + h * (0.15 + (0.22 if k % 2 else -0.18)))
        c.drawPath(zig, trazo(linea, lw * 0.8, redondo=False))
        c.restore()
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "o":
        rr = s * 0.11 * (1 + 0.1 * math.sin(t * 8))
        c.drawOval(skia.Rect(cx - rr * 0.85, cy - rr * 0.6, cx + rr * 0.85, cy + rr * 1.2), relleno(oscuro))
        c.drawOval(skia.Rect(cx - rr * 0.85, cy - rr * 0.6, cx + rr * 0.85, cy + rr * 1.2), trazo(linea, lw))
    elif tipo == "ola":
        p = skia.Path(); p.moveTo(cx - w * 0.8, cy + s * 0.03)
        for k in range(1, 9):
            x = cx - w * 0.8 + 1.6 * w * k / 8
            p.lineTo(x, cy + s * 0.03 + (s * 0.035 if k % 2 else -s * 0.035))
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "ladeada":
        p = skia.Path(); p.moveTo(cx - w * 0.7, cy + s * 0.02); p.quadTo(cx + w * 0.2, cy + s * 0.12, cx + w * 0.85, cy - s * 0.08)
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "pena":
        p = skia.Path(); p.moveTo(cx - w * 0.7, cy + s * 0.08); p.quadTo(cx, cy - s * 0.06, cx + w * 0.7, cy + s * 0.08)
        c.drawPath(p, trazo(linea, lw))
    elif tipo == "firme":
        p = skia.Path(); p.moveTo(cx - w * 0.75, cy); p.quadTo(cx, cy + s * 0.07, cx + w * 0.75, cy - s * 0.02)
        c.drawPath(p, trazo(linea, lw * 1.1))
    elif tipo == "bocaza":
        ab = 0.35 if ab is None else ab
        rw = w * (1.0 + 1.1 * ab)
        rh = s * (0.08 + 0.42 * ab)
        p = skia.Path(); p.addOval(skia.Rect(cx - rw, cy - rh * 0.55, cx + rw, cy + rh))
        c.drawPath(p, relleno(oscuro))
        c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
        c.drawOval(skia.Rect(cx - rw * 0.62, cy + rh * 0.35, cx + rw * 0.62, cy + rh * 1.25), relleno(lengua))
        # dientecillos arriba
        for k in (-1, 1):
            tri = _path_poligono([(cx + k * rw * 0.45 - rw * 0.13, cy - rh * 0.55), (cx + k * rw * 0.45 + rw * 0.13, cy - rh * 0.55),
                                  (cx + k * rw * 0.45, cy - rh * 0.55 + rh * 0.35)])
            c.drawPath(tri, relleno("#FFFFFF"))
        c.restore()
        c.drawPath(p, trazo(linea, lw))


def _corazon(c, x, y, r, color, linea, lw):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.5, y - r * 0.1, x - r * 0.7, y - r * 1.2, x, y - r * 0.4)
    p.cubicTo(x + r * 0.7, y - r * 1.2, x + r * 1.5, y - r * 0.1, x, y + r * 0.9)
    p.close()
    c.drawPath(p, relleno(color))
    if lw:
        c.drawPath(p, trazo(linea, lw))


def _gota_sudor(c, x, y, r, lw, linea):
    p = skia.Path()
    p.moveTo(x, y - r * 1.4)
    p.cubicTo(x + r * 0.9, y - r * 0.2, x + r, y + r, x, y + r)
    p.cubicTo(x - r, y + r, x - r * 0.9, y - r * 0.2, x, y - r * 1.4)
    p.close()
    c.drawPath(p, relleno("#9FD8FF"))
    c.drawPath(p, trazo(linea, lw * 0.8))


# ------------------------------------------------------------------ detalles del cuerpo
def detalles(c, forma, path, R, t, fase, spec, lw):
    det = spec.get("detalle")
    c2 = spec.get("color2") or oscurece(spec.get("color", "#CCCCCC"), 0.18)
    linea = spec.get("linea", CONTORNO)
    if not det:
        return
    c.save(); c.clipPath(path, skia.ClipOp.kIntersect, False)
    if det == "manchas":
        for k, (ax, ay, ar) in enumerate(((-0.55, 0.35, 0.16), (0.6, 0.4, 0.12), (0.2, 0.55, 0.1), (-0.15, -0.55, 0.09), (0.7, -0.3, 0.1))):
            c.drawCircle(ax * R, ay * R, ar * R, relleno(c2, 0.8))
    elif det == "puntos":
        for k in range(9):
            a = k * 2.399 + fase
            r = R * 0.75 * math.sqrt((k + 0.5) / 9)
            c.drawCircle(math.cos(a) * r, math.sin(a) * r * 0.8 + R * 0.1, R * 0.05, relleno(c2, 0.9))
    elif det == "nucleo":
        # núcleo con lóbulos, detrás de la cara (abajo a un lado)
        for k, (ax, ay) in enumerate(((0.5, 0.5), (0.68, 0.22), (0.3, 0.68))):
            c.drawCircle(ax * R, ay * R, R * 0.19, relleno(c2, 0.95))
    elif det == "rayas":
        for k in range(-3, 4):
            c.drawLine(k * R * 0.32 - R * 0.3, -R * 1.2, k * R * 0.32 + R * 0.3, R * 1.2, trazo(c2, R * 0.09, 0.8))
    elif det == "crater":
        for (ax, ay, ar) in ((-0.45, -0.35, 0.18), (0.4, 0.45, 0.14), (0.55, -0.2, 0.09)):
            c.drawCircle(ax * R, ay * R, ar * R, relleno(c2, 0.9))
            c.drawCircle(ax * R, ay * R, ar * R, trazo(linea, lw * 0.45, 0.5))
    elif det == "bandas":
        for k, yy in enumerate((-0.5, -0.1, 0.35)):
            c.drawRect(skia.Rect(-R * 1.2, yy * R, R * 1.2, yy * R + R * 0.16), relleno(c2, 0.7))
    c.restore()


def extras_forma(c, forma, R, t, fase, spec, lw, detras):
    """Cosas que salen del cuerpo: flagelos, pinchos, anillo, rayos."""
    linea = spec.get("linea", CONTORNO)
    color = spec.get("color", "#CCCCCC")
    if detras and spec.get("flagelos"):
        n = int(spec["flagelos"])
        for k in range(n):
            y0 = (k - (n - 1) / 2) * R * 0.28
            p = skia.Path(); p.moveTo(-R * 1.05, y0)
            for j in range(1, 13):
                x = -R * 1.05 - j * R * 0.11
                p.lineTo(x, y0 + math.sin(j * 0.9 - t * 12 - fase * 5 - k) * R * 0.12 * (j / 12) + j * R * 0.015 * (k - 1))
            c.drawPath(p, trazo(linea, max(1.5, lw * 0.75)))
    if detras and (forma == "virus" or spec.get("pinchos")):
        n = int(spec.get("pinchos") or 10)
        for k in range(n):
            a = 2 * math.pi * k / n + t * 0.4 + fase
            r0, r1 = R * 0.8, R * 1.08 + math.sin(t * 4 + k) * R * 0.03
            x0, y0, x1, y1 = math.cos(a) * r0, math.sin(a) * r0, math.cos(a) * r1, math.sin(a) * r1
            c.drawLine(x0, y0, x1, y1, trazo(linea, lw * 1.6))
            c.drawLine(x0, y0, x1, y1, trazo(oscurece(color, 0.1), lw * 0.7))
            c.drawCircle(x1, y1, R * 0.11, relleno(spec.get("color2", aclara(color, 0.2))))
            c.drawCircle(x1, y1, R * 0.11, trazo(linea, lw * 0.8))
    if forma == "planeta" and spec.get("anillo"):
        rect = skia.Rect(-R * 1.65, -R * 0.38, R * 1.65, R * 0.38)
        if detras:
            c.save(); c.rotate(-14)
            c.drawArc(rect, 180, 180, False, trazo(linea, lw * 2.4))
            c.drawArc(rect, 180, 180, False, trazo(spec.get("color2", "#F6C36B"), lw * 1.2))
            c.restore()
        else:
            c.save(); c.rotate(-14)
            c.drawArc(rect, 0, 180, False, trazo(linea, lw * 2.4))
            c.drawArc(rect, 0, 180, False, trazo(spec.get("color2", "#F6C36B"), lw * 1.2))
            c.restore()
    if detras and spec.get("patas"):
        n = int(spec["patas"])
        for k in range(n):
            x0 = (k - (n - 1) / 2) * R * 0.32
            ola = math.sin(t * 5 + k * 1.3 + fase) * R * 0.05
            q = skia.Path(); q.moveTo(x0, R * 0.55)
            q.quadTo(x0 + (k - (n - 1) / 2) * R * 0.5, R * 0.95 + ola, x0 + (k - (n - 1) / 2) * R * 0.45, R * 1.45)
            c.drawPath(q, trazo(linea, max(1.5, lw * 0.8)))
    if detras and spec.get("alas"):
        bat = math.sin(t * 38 + fase * 7) * 14
        for k, (dx, ang) in enumerate(((-R * 0.15, -32), (R * 0.2, -12))):
            c.save(); c.translate(dx, -R * 0.55); c.rotate(ang + bat * (1 if k else -1))
            r = skia.Rect(-R * 0.32, -R * 1.25, R * 0.32, 0)
            c.drawOval(r, relleno(spec.get("color_alas", "#DDF2FF"), 0.75)); c.drawOval(r, trazo(linea, lw * 0.8))
            c.drawLine(0, -R * 0.1, 0, -R * 1.1, trazo(linea, lw * 0.5, 0.5))
            c.restore()
    if not detras and (spec.get("trompa") or spec.get("_trompa")):
        L = spec.get("_trompa") or (float(spec["trompa"]) if not isinstance(spec["trompa"], bool) else 1.0)
        x0, y0 = R * 0.72, R * 0.2
        x1, y1 = x0 + R * 0.9 * L, y0 + R * 0.75 * L
        c.drawLine(x0, y0, x1, y1, trazo(linea, lw * 2.4))
        c.drawLine(x0, y0, x1, y1, trazo(spec.get("color_trompa", "#2E3140"), lw * 1.0))
    if forma == "volcan" and not detras:
        lava = spec.get("color2", "#FF6A2B")
        top = -R * 0.95
        q = skia.Path()
        q.moveTo(-R * 0.36, top + R * 0.02)
        q.quadTo(0, top + R * 0.16, R * 0.36, top + R * 0.02)
        for j, (dx, L) in enumerate(((0.22, 0.55), (-0.12, 0.38), (0.05, 0.75))):
            pass
        q.lineTo(R * 0.3, top + R * 0.25); q.quadTo(R * 0.24, top + R * 0.62 + math.sin(t * 2) * R * 0.03, R * 0.14, top + R * 0.3)
        q.lineTo(R * 0.02, top + R * 0.28); q.quadTo(-R * 0.06, top + R * 0.5, -R * 0.14, top + R * 0.26)
        q.lineTo(-R * 0.3, top + R * 0.2); q.close()
        c.drawPath(q, relleno(lava)); c.drawPath(q, trazo(linea, lw * 0.8))
    if forma == "montana" and not detras and spec.get("nieve", True):
        top = -R * 0.95
        q = skia.Path(); q.moveTo(-R * 0.3, top + R * 0.35); q.lineTo(-R * 0.08, top + R * 0.02); q.lineTo(R * 0.08, top + R * 0.02)
        q.lineTo(R * 0.3, top + R * 0.35); q.lineTo(R * 0.12, top + R * 0.27); q.lineTo(0, top + R * 0.38); q.lineTo(-R * 0.14, top + R * 0.27); q.close()
        c.drawPath(q, relleno("#FFFFFF")); c.drawPath(q, trazo(linea, lw * 0.7))
    if forma == "flor" and detras:
        pc = spec.get("color2", "#FF8FB1")
        for k in range(7):
            a = 2 * math.pi * k / 7 + math.sin(t * 1.5 + fase) * 0.05
            px, py = math.cos(a) * R * 0.8, math.sin(a) * R * 0.8
            c.drawCircle(px, py, R * 0.42, relleno(pc)); c.drawCircle(px, py, R * 0.42, trazo(linea, lw))
    if forma == "hoja" and not detras:
        c.drawLine(0, -R * 0.95, 0, R * 0.9, trazo(oscurece(color, 0.25), lw * 0.9))
        for k in (-1, 1):
            for j in range(3):
                y0 = -R * 0.45 + j * R * 0.45
                c.drawLine(0, y0, k * R * 0.42, y0 - R * 0.22, trazo(oscurece(color, 0.25), lw * 0.7))
        c.drawLine(0, R * 1.02, 0, R * 1.35, trazo(linea, lw * 1.4))
    if forma == "maceta" and detras:
        hc = spec.get("color2", "#6CC36A")
        c.drawLine(0, -R * 0.35, 0, -R * 1.15, trazo(linea, lw * 2.2)); c.drawLine(0, -R * 0.35, 0, -R * 1.15, trazo(hc, lw * 1.0))
        for k in (-1, 1):
            q = skia.Path(); bx, by = k * R * 0.38, -R * 1.0 + math.sin(t * 2 + k) * R * 0.03
            q.moveTo(0, -R * 0.75); q.cubicTo(k * R * 0.2, -R * 1.25, bx + k * R * 0.45, by - R * 0.15, bx + k * R * 0.5, by + R * 0.1)
            q.cubicTo(bx, by + R * 0.25, k * R * 0.1, -R * 0.6, 0, -R * 0.75); q.close()
            c.drawPath(q, relleno(hc)); c.drawPath(q, trazo(linea, lw))
    if forma == "maceta" and not detras:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.95, -R * 0.5, R * 0.95, -R * 0.2), R * 0.08, R * 0.08), relleno(oscurece(color, 0.1)))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.95, -R * 0.5, R * 0.95, -R * 0.2), R * 0.08, R * 0.08), trazo(linea, lw))
    if detras and spec.get("rayos"):
        n = 10
        for k in range(n):
            a = 2 * math.pi * k / n + t * 0.5
            r0, r1 = R * 1.12, R * 1.45 + math.sin(t * 3 + k) * R * 0.05
            c.drawLine(math.cos(a) * r0, math.sin(a) * r0, math.cos(a) * r1, math.sin(a) * r1,
                       trazo(spec.get("color2", "#FFB020"), lw * 1.4))


# ------------------------------------------------------------------ accesorios
def accesorios(c, R, t, fase, spec, lw, cara_y, s, delante, forma):
    linea = spec.get("linea", CONTORNO)
    acc = spec.get("accesorios", [])
    acol = spec.get("color_accesorio", "#FF7A1A")
    metal = "#C9D2DE"
    arriba = -R * (1.25 if forma == "fantasma" else 0.98)
    for a in acc:
        if a == "lanza" and not delante:
            x = R * 1.02
            c.drawLine(x, -R * 1.7, x, R * 1.05, trazo(linea, lw * 2.6))
            c.drawLine(x, -R * 1.7, x, R * 1.05, trazo("#B07A43", lw * 1.3))
            tip = _path_poligono([(x - R * 0.16, -R * 1.62), (x, -R * 2.05), (x + R * 0.16, -R * 1.62)])
            c.drawPath(tip, relleno(metal)); c.drawPath(tip, trazo(linea, lw * 0.9))
        if a == "bandera" and not delante:
            x = R * 1.0
            c.drawLine(x, -R * 1.9, x, R * 0.9, trazo(linea, lw * 2.4))
            c.drawLine(x, -R * 1.9, x, R * 0.9, trazo("#B07A43", lw * 1.1))
            p = skia.Path(); p.moveTo(x, -R * 1.85)
            for j in range(9):
                xx = x + R * 0.9 * j / 8
                p.lineTo(xx, -R * 1.85 + math.sin(j * 0.8 - t * 7) * R * 0.06)
            for j in range(8, -1, -1):
                xx = x + R * 0.9 * j / 8
                p.lineTo(xx, -R * 1.35 + math.sin(j * 0.8 - t * 7) * R * 0.06)
            p.close()
            c.drawPath(p, relleno(acol)); c.drawPath(p, trazo(linea, lw * 0.9))
        if a == "espada" and not delante:
            x = R * 1.0
            hoja = _path_poligono([(x - R * 0.08, -R * 0.15), (x - R * 0.08, -R * 1.45), (x, -R * 1.62), (x + R * 0.08, -R * 1.45), (x + R * 0.08, -R * 0.15)])
            c.drawPath(hoja, relleno(metal)); c.drawPath(hoja, trazo(linea, lw * 0.9))
            c.drawLine(x - R * 0.26, -R * 0.15, x + R * 0.26, -R * 0.15, trazo(linea, lw * 2.2))
            c.drawLine(x, -R * 0.15, x, R * 0.25, trazo(linea, lw * 2.2))
        if a == "capa" and not delante:
            p = skia.Path(); p.moveTo(-R * 0.7, -R * 0.4)
            p.quadTo(-R * 1.5, R * 0.4 + math.sin(t * 4) * R * 0.1, -R * 1.2, R * 1.15)
            p.lineTo(R * 1.2, R * 1.15); p.quadTo(R * 1.5, R * 0.4, R * 0.7, -R * 0.4); p.close()
            c.drawPath(p, relleno(acol)); c.drawPath(p, trazo(linea, lw))
        if not delante:
            continue
        if a == "casco":
            p = skia.Path()
            p.moveTo(-R * 0.86, arriba + R * 0.52)
            p.cubicTo(-R * 0.86, arriba - R * 0.18, R * 0.86, arriba - R * 0.18, R * 0.86, arriba + R * 0.52)
            p.close()
            c.drawPath(p, relleno(metal))
            c.drawOval(skia.Rect(-R * 0.45, arriba + R * 0.02, -R * 0.12, arriba + R * 0.16), relleno("#FFFFFF", 0.7))
            c.drawPath(p, trazo(linea, lw))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.98, arriba + R * 0.44, R * 0.98, arriba + R * 0.6), R * 0.08, R * 0.08), relleno(oscurece(metal, 0.15)))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.98, arriba + R * 0.44, R * 0.98, arriba + R * 0.6), R * 0.08, R * 0.08), trazo(linea, lw))
            c.drawLine(0, arriba + R * 0.0, 0, arriba - R * 0.2, trazo(linea, lw * 1.2))
            c.drawCircle(0, arriba - R * 0.24, R * 0.09, relleno(acol)); c.drawCircle(0, arriba - R * 0.24, R * 0.09, trazo(linea, lw * 0.8))
        elif a == "escudo":
            x, y = -R * 0.72, R * 0.35
            p = skia.Path()
            p.moveTo(x - R * 0.42, y - R * 0.48); p.lineTo(x + R * 0.42, y - R * 0.48)
            p.cubicTo(x + R * 0.44, y + R * 0.2, x + R * 0.2, y + R * 0.5, x, y + R * 0.66)
            p.cubicTo(x - R * 0.2, y + R * 0.5, x - R * 0.44, y + R * 0.2, x - R * 0.42, y - R * 0.48); p.close()
            c.drawPath(p, relleno(metal)); c.drawPath(p, trazo(linea, lw))
            c.drawLine(x, y - R * 0.36, x, y + R * 0.45, trazo(acol, lw * 1.7))
            c.drawLine(x - R * 0.28, y - R * 0.12, x + R * 0.28, y - R * 0.12, trazo(acol, lw * 1.7))
        elif a == "gafas":
            ey = cara_y - s * 0.12
            sep = s * 0.36 * spec.get("ojos_sep", 1.0)
            r = s * 0.25
            for ex in (-sep, sep):
                c.drawCircle(ex, ey, r, trazo(linea, lw * 1.1))
                c.drawCircle(ex, ey, r, relleno("#BDE3FF", 0.25))
            c.drawLine(-sep + r, ey, sep - r, ey, trazo(linea, lw))
        elif a == "corona":
            y0 = arriba + R * 0.08
            p = _path_poligono([(-R * 0.5, y0), (-R * 0.55, y0 - R * 0.5), (-R * 0.25, y0 - R * 0.25), (0, y0 - R * 0.62),
                                (R * 0.25, y0 - R * 0.25), (R * 0.55, y0 - R * 0.5), (R * 0.5, y0)])
            c.drawPath(p, relleno("#FFCC33")); c.drawPath(p, trazo(linea, lw))
            c.drawCircle(0, y0 - R * 0.18, R * 0.07, relleno("#E8475B"))
        elif a == "cinta":
            y0 = cara_y - s * 0.62
            band = skia.Path(); band.addRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.9, y0 - R * 0.11, R * 0.9, y0 + R * 0.11), R * 0.06, R * 0.06))
            c.save()
            body = skia.Path(); body.addCircle(0, 0, R * 1.02)
            c.clipPath(body, skia.ClipOp.kIntersect, False)
            c.drawPath(band, relleno(acol)); c.drawPath(band, trazo(linea, lw * 0.8))
            c.restore()
            for k in (0, 1):
                p = skia.Path(); p.moveTo(R * 0.85, y0)
                p.quadTo(R * 1.15, y0 + R * (0.05 + 0.25 * k) + math.sin(t * 5 + k) * R * 0.06, R * 1.35, y0 + R * (0.1 + 0.35 * k))
                c.drawPath(p, trazo(linea, lw * 2.4)); c.drawPath(p, trazo(acol, lw * 1.2))
        elif a == "babero":
            y0 = cara_y + s * 0.6
            p = skia.Path(); p.moveTo(-s * 0.48, y0)
            p.quadTo(0, y0 + s * 0.08, s * 0.48, y0)
            p.quadTo(s * 0.35, y0 + s * 0.65, 0, y0 + s * 0.72)
            p.quadTo(-s * 0.35, y0 + s * 0.65, -s * 0.48, y0); p.close()
            c.drawPath(p, relleno("#FFFFFF"))
            c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
            for (bx, by) in ((-0.2, 0.25), (0.15, 0.3), (0.0, 0.5), (0.28, 0.12), (-0.3, 0.1)):
                c.drawCircle(bx * s, y0 + by * s, s * 0.05, relleno(acol))
            c.restore()
            c.drawPath(p, trazo(linea, lw * 0.9))
        elif a == "sombrero":
            y0 = arriba + R * 0.18
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.75, y0 - R * 0.12, R * 0.75, y0 + R * 0.08), R * 0.06, R * 0.06), relleno("#2A2A35"))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.75, y0 - R * 0.12, R * 0.75, y0 + R * 0.08), R * 0.06, R * 0.06), trazo(linea, lw))
            c.drawRect(skia.Rect(-R * 0.45, y0 - R * 0.8, R * 0.45, y0 - R * 0.1), relleno("#2A2A35"))
            c.drawRect(skia.Rect(-R * 0.45, y0 - R * 0.32, R * 0.45, y0 - R * 0.2), relleno(acol))
            c.drawRect(skia.Rect(-R * 0.45, y0 - R * 0.8, R * 0.45, y0 - R * 0.1), trazo(linea, lw))
        elif a == "gorro_chef":
            y0 = arriba + R * 0.15
            for (bx, by, br) in ((-0.38, -0.55, 0.34), (0.0, -0.75, 0.4), (0.38, -0.55, 0.34)):
                c.drawCircle(bx * R, y0 + by * R, br * R, relleno("#FFFFFF")); c.drawCircle(bx * R, y0 + by * R, br * R, trazo(linea, lw))
            for (bx, by, br) in ((-0.38, -0.55, 0.3), (0.0, -0.75, 0.36), (0.38, -0.55, 0.3)):
                c.drawCircle(bx * R, y0 + by * R, br * R, relleno("#FFFFFF"))
            rr = skia.RRect.MakeRectXY(skia.Rect(-R * 0.62, y0 - R * 0.4, R * 0.62, y0 + R * 0.05), R * 0.06, R * 0.06)
            c.drawRRect(rr, relleno("#FFFFFF")); c.drawRRect(rr, trazo(linea, lw))
        elif a == "antena":
            y0 = arriba + R * 0.05
            c.drawLine(0, y0, 0, y0 - R * 0.45, trazo(linea, lw * 1.3))
            brillo = 0.6 + 0.4 * math.sin(t * 5 + fase)
            c.drawCircle(0, y0 - R * 0.52, R * 0.13, relleno(mezcla(acol, "#FFFFFF", 1 - brillo)))
            c.drawCircle(0, y0 - R * 0.52, R * 0.13, trazo(linea, lw * 0.9))
        elif a == "tornillos":
            for k in (-1, 1):
                x0 = k * R * 0.98
                c.drawCircle(x0, cara_y, R * 0.13, relleno("#C9D2DE")); c.drawCircle(x0, cara_y, R * 0.13, trazo(linea, lw * 0.9))
                c.drawLine(x0 - R * 0.07, cara_y, x0 + R * 0.07, cara_y, trazo(linea, lw * 0.8))
        elif a == "auriculares":
            c.drawArc(skia.Rect(-R * 0.95, arriba - R * 0.15, R * 0.95, arriba + R * 1.5), 190, 160, False, trazo(linea, lw * 2.6))
            c.drawArc(skia.Rect(-R * 0.95, arriba - R * 0.15, R * 0.95, arriba + R * 1.5), 190, 160, False, trazo(acol, lw * 1.2))
            for k in (-1, 1):
                rr = skia.RRect.MakeRectXY(skia.Rect(k * R * 0.92 - R * 0.17, cara_y - R * 0.3, k * R * 0.92 + R * 0.17, cara_y + R * 0.1), R * 0.1, R * 0.1)
                c.drawRRect(rr, relleno(acol)); c.drawRRect(rr, trazo(linea, lw))
        elif a == "bigote":
            y0 = cara_y + s * 0.2
            for k in (-1, 1):
                p = skia.Path(); p.moveTo(0, y0)
                p.cubicTo(k * s * 0.2, y0 - s * 0.1, k * s * 0.42, y0 - s * 0.02, k * s * 0.5, y0 - s * 0.14)
                p.cubicTo(k * s * 0.42, y0 + s * 0.12, k * s * 0.15, y0 + s * 0.1, 0, y0 + s * 0.04); p.close()
                c.drawPath(p, relleno("#3A2A20"))
        elif a == "chip":
            _chip(c, 0, cara_y + s * 0.95, s * 0.26, acol, linea, lw)


def _chip(c, x, y, r, color, linea, lw):
    for k in range(3):
        for sgn in (-1, 1):
            yy = y - r * 0.5 + r * 0.5 * k
            c.drawLine(x + sgn * r * 0.7, yy, x + sgn * r * 1.05, yy, trazo(linea, max(1.5, lw * 0.7)))
    rr = skia.RRect.MakeRectXY(skia.Rect(x - r * 0.75, y - r * 0.75, x + r * 0.75, y + r * 0.75), r * 0.2, r * 0.2)
    c.drawRRect(rr, relleno(color)); c.drawRRect(rr, trazo(linea, max(1.5, lw * 0.8)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35), r * 0.1, r * 0.1), relleno("#FFFFFF", 0.9))


# ------------------------------------------------------------------ humano (estilo chibi)
POSES = {
    # (hombro_izq, codo_izq, hombro_der, codo_der) en grados: 0 = hacia abajo, 90 = hacia fuera, 180 = arriba
    "neutro": (14, -10, 14, -10),
    "saluda": (14, -10, 140, 18),
    "senala": (14, -10, 88, 4),
    "senala_arriba": (14, -10, 145, 12),
    "celebra": (150, 12, 150, 12),
    "presenta": (14, -10, 58, -45),
    "piensa": (14, -10, 30, -140),
    "sorpresa": (105, -70, 105, -70),
    "bandera": (14, -10, 150, 10),
    "brazos_jarra": (42, 105, 42, 105),
}


def _brazo(c, sx, sy, a_hombro, a_codo, L1, L2, grosor, piel, manga, linea, lw, lado):
    a1 = math.radians(a_hombro)
    ex = sx + lado * math.sin(a1) * L1
    ey = sy + math.cos(a1) * L1
    a2 = math.radians(a_hombro + a_codo)
    hx = ex + lado * math.sin(a2) * L2
    hy = ey + math.cos(a2) * L2
    p = skia.Path(); p.moveTo(sx, sy); p.lineTo(ex, ey); p.lineTo(hx, hy)
    c.drawPath(p, trazo(linea, grosor + 2 * lw))
    c.drawPath(p, trazo(piel, grosor))
    # manga corta
    mx = sx + (ex - sx) * 0.42; my = sy + (ey - sy) * 0.42
    c.drawLine(sx, sy, mx, my, trazo(linea, grosor * 1.25 + 2 * lw))
    c.drawLine(sx, sy, mx, my, trazo(manga, grosor * 1.25))
    c.drawCircle(hx, hy, grosor * 0.8, relleno(piel))
    c.drawCircle(hx, hy, grosor * 0.8, trazo(linea, lw))
    return hx, hy


def _pelo(hw, hh, hy, t, fase, peinado="puntas"):
    """Pelo: «puntas» (despeinado con un mechón grande hacia arriba), «corto», «largo» o «rizado»."""
    if peinado == "melena":
        peinado = "rizado"
    elif peinado in ("coleta", "mono"):
        peinado = "corto"
    if peinado in ("corto", "largo", "rizado"):
        return _pelo_suave(hw, hh, hy, t, fase, peinado)
    cx, cy = 0.0, hy - hh * 0.16
    rx, ry = hw * 1.04, hh * 1.0
    sway = math.sin(t * 2.4 + fase) * 3.0

    def pt(ang, r):
        a = math.radians(ang)
        return (cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r)

    puntas = [(212, 1.24), (232, 1.3), (252, 1.3), (277, 1.95), (300, 1.3), (320, 1.27), (338, 1.18)]
    bases = [200, 222, 242, 263, 289, 310, 329, 348]
    p = skia.Path()
    x0, y0 = -hw * 1.05, hy + hh * 0.14
    p.moveTo(x0, y0)
    b0 = pt(bases[0], 1.0)
    p.quadTo(-hw * 1.12, hy - hh * 0.1, b0[0], b0[1])
    for i, (ang, r) in enumerate(puntas):
        b_ini = pt(bases[i], 1.0)
        b_fin = pt(bases[i + 1], 1.0)
        barrido = 10 + (sway if ang == 277 else sway * 0.4)
        tip = pt(ang + barrido, r)
        c1 = pt((bases[i] + ang) / 2, 1.08 + (r - 1) * 0.35)
        c2 = pt((bases[i + 1] + ang) / 2 + 4, 1.04 + (r - 1) * 0.3)
        if ang == 277:  # mechón grande, curvado hacia la derecha
            c1 = pt(ang - 8, 1.45)
            c2 = pt(ang + 22, 1.35)
        p.quadTo(c1[0], c1[1], tip[0], tip[1])
        p.quadTo(c2[0], c2[1], b_fin[0], b_fin[1])
    xr, yr = hw * 1.05, hy + hh * 0.14
    p.quadTo(hw * 1.12, hy - hh * 0.1, xr, yr)
    # flequillo: puntas que bajan por la frente, de derecha a izquierda
    flequillo = [(hw * 0.9, hy - hh * 0.24), (hw * 0.76, hy - hh * 0.02), (hw * 0.58, hy - hh * 0.38),
                 (hw * 0.36, hy - hh * 0.06), (hw * 0.16, hy - hh * 0.42), (-hw * 0.08, hy - hh * 0.04),
                 (-hw * 0.3, hy - hh * 0.4), (-hw * 0.52, hy - hh * 0.08), (-hw * 0.7, hy - hh * 0.38),
                 (-hw * 0.86, hy - hh * 0.02), (-hw * 0.96, hy - hh * 0.24)]
    prev = (xr, yr)
    for i, q in enumerate(flequillo):
        mx = (prev[0] + q[0]) / 2 + hw * 0.03
        my = (prev[1] + q[1]) / 2
        p.quadTo(mx, my, q[0], q[1])
        prev = q
    p.quadTo(-hw * 1.0, hy - hh * 0.05, x0, y0)
    p.close()
    return p


def _pelo_suave(hw, hh, hy, t, fase, peinado):
    cx, cy = 0.0, hy - hh * 0.16
    rx, ry = hw * 1.07, hh * 1.02
    p = skia.Path()
    if peinado == "rizado":
        for k in range(13):
            a = math.radians(185 + 170 * k / 12)
            q = skia.Path(); q.addCircle(cx + math.cos(a) * rx * 1.02, cy + math.sin(a) * ry * 1.02, hw * 0.24)
            p = skia.Op(p, q, skia.PathOp.kUnion_PathOp) if not p.isEmpty() else q
        q = skia.Path(); q.addOval(skia.Rect(-rx, cy - ry, rx, hy - hh * 0.2))
        return skia.Op(p, q, skia.PathOp.kUnion_PathOp)
    p.moveTo(-hw * 1.06, hy + hh * 0.1)
    p.cubicTo(-hw * 1.2, hy - hh * 1.35, hw * 1.2, hy - hh * 1.35, hw * 1.06, hy + hh * 0.1)
    # flequillo de lado
    p.quadTo(hw * 0.9, hy - hh * 0.3, hw * 0.55, hy - hh * 0.36)
    p.quadTo(hw * 0.05, hy - hh * 0.2, -hw * 0.45, hy - hh * 0.05)
    p.quadTo(-hw * 0.8, hy - hh * 0.2, -hw * 1.06, hy + hh * 0.1)
    p.close()
    return p


def _pelo_largo_detras(c, hw, hh, hy, pelo, linea, lw, t):
    p = skia.Path()
    p.moveTo(-hw * 1.05, hy - hh * 0.4)
    p.cubicTo(-hw * 1.3, hy + hh * 0.6, -hw * 1.15, hy + hh * 1.3, -hw * 0.7, hy + hh * 1.45)
    p.lineTo(hw * 0.7, hy + hh * 1.45)
    p.cubicTo(hw * 1.15, hy + hh * 1.3, hw * 1.3, hy + hh * 0.6, hw * 1.05, hy - hh * 0.4)
    p.close()
    c.drawPath(p, relleno(oscurece(pelo, 0.08))); c.drawPath(p, trazo(linea, lw))


def _pelo_detras(c, peinado, hw, hh, hy, pelo, linea, lw, t):
    if peinado == "largo":
        _pelo_largo_detras(c, hw, hh, hy, pelo, linea, lw, t)
    elif peinado == "melena":
        q = skia.Path()
        for j in range(7):
            for sgn in (-1, 1):
                bx = sgn * hw * (0.95 + 0.12 * (j % 2))
                by = hy - hh * 0.2 + j * hh * 0.26
                cc = skia.Path(); cc.addCircle(bx, by, hw * 0.3)
                q = skia.Op(q, cc, skia.PathOp.kUnion_PathOp) if not q.isEmpty() else cc
        cc = skia.Path(); cc.addRect(skia.Rect(-hw * 0.95, hy - hh * 0.4, hw * 0.95, hy + hh * 1.35))
        q = skia.Op(q, cc, skia.PathOp.kUnion_PathOp)
        c.drawPath(q, relleno(oscurece(pelo, 0.08))); c.drawPath(q, trazo(linea, lw))


def humano(c, x, y, H, t, est, spec):
    linea = spec.get("linea", CONTORNO)
    lw = max(2.0, H * 0.0105 * spec.get("grosor", 1.0))
    piel = spec.get("piel", "#FFE3D1")
    pelo = spec.get("pelo", "#F3E7C3")
    camiseta = spec.get("camiseta", "#FFFFFF")
    pantalon = spec.get("pantalon", "#22252E")
    zapatillas = spec.get("zapatillas", "#22252E")
    cinta = spec.get("cinta")
    fase = est.get("fase", 0.0)
    pose = est.get("pose") or spec.get("pose", "neutro")
    brazos = est.get("brazos") or POSES.get(pose, POSES["neutro"])
    lado = est.get("lado", 1)
    salto = est.get("salto", 0.0)
    resp = math.sin(t * 2.2 + fase) * H * 0.004
    c.save()
    c.translate(x, y - salto * H * 0.12)
    if lado < 0:
        c.scale(-1, 1)
    c.rotate(est.get("rot", 0.0))
    # sombra en el suelo
    c.drawOval(skia.Rect(-H * 0.2, -H * 0.02 + salto * H * 0.12, H * 0.2, H * 0.025 + salto * H * 0.12), relleno("#000000", 0.12 * (1 - salto * 0.5)))
    # piernas
    for sgn in (-1, 1):
        lx = sgn * H * 0.062
        c.drawLine(lx, -H * 0.2, lx, -H * 0.035, trazo(linea, H * 0.058 + 2 * lw))
        c.drawLine(lx, -H * 0.2, lx, -H * 0.035, trazo(piel, H * 0.058))
        zap = skia.RRect.MakeRectXY(skia.Rect(lx - H * 0.05 + sgn * H * 0.012, -H * 0.058, lx + H * 0.056 + sgn * H * 0.012, H * 0.0), H * 0.027, H * 0.027)
        c.drawRRect(zap, relleno(zapatillas)); c.drawRRect(zap, trazo(linea, lw))
        c.drawLine(lx - H * 0.044 + sgn * H * 0.012, -H * 0.007, lx + H * 0.05 + sgn * H * 0.012, -H * 0.007, trazo("#FFFFFF", lw * 1.1))
    # pantalón corto
    sh = skia.Path()
    if spec.get("falda"):
        fc = spec["falda"] if isinstance(spec["falda"], str) else pantalon
        sh.moveTo(-H * 0.135, -H * 0.31 + resp); sh.lineTo(H * 0.135, -H * 0.31 + resp)
        sh.lineTo(H * 0.18, -H * 0.17); sh.quadTo(0, -H * 0.155, -H * 0.18, -H * 0.17); sh.close()
        c.drawPath(sh, relleno(fc)); c.drawPath(sh, trazo(linea, lw))
    else:
        sh.moveTo(-H * 0.135, -H * 0.31 + resp); sh.lineTo(H * 0.135, -H * 0.31 + resp)
        sh.lineTo(H * 0.13, -H * 0.17); sh.lineTo(H * 0.012, -H * 0.17); sh.lineTo(0, -H * 0.215); sh.lineTo(-H * 0.012, -H * 0.17)
        sh.lineTo(-H * 0.13, -H * 0.17); sh.close()
        c.drawPath(sh, relleno(pantalon)); c.drawPath(sh, trazo(linea, lw))
    # pelo largo de detrás (antes del cuerpo, para que no tape la camiseta)
    if spec.get("peinado") in ("largo", "melena"):
        hy_ = -H * 0.71 + resp * 1.4
        _pelo_detras(c, spec["peinado"], H * 0.235, H * 0.23, hy_, pelo, linea, lw, t)
    hs, cs, hd, cd = brazos
    if pose == "saluda":
        cd = cd + math.sin(t * 9) * 22
    hombro_y = -H * 0.47 + resp
    levantado_izq = hs > 70
    levantado_der = hd > 70
    def brazo_izq():
        return _brazo(c, -H * 0.125, hombro_y, hs, cs, H * 0.12, H * 0.11, H * 0.05, piel, camiseta, linea, lw, -1)
    def brazo_der():
        return _brazo(c, H * 0.125, hombro_y, hd, cd, H * 0.12, H * 0.11, H * 0.05, piel, camiseta, linea, lw, 1)
    mano_izq = mano_der = None
    if not levantado_izq:
        mano_izq = brazo_izq()
    # torso (camiseta)
    to = skia.Path()
    to.moveTo(-H * 0.135, hombro_y - H * 0.02)
    to.quadTo(0, hombro_y - H * 0.045, H * 0.135, hombro_y - H * 0.02)
    to.quadTo(H * 0.155, hombro_y + H * 0.02, H * 0.145, -H * 0.29 + resp)
    to.quadTo(0, -H * 0.272 + resp, -H * 0.145, -H * 0.29 + resp)
    to.quadTo(-H * 0.155, hombro_y + H * 0.02, -H * 0.135, hombro_y - H * 0.02)
    to.close()
    c.drawPath(to, relleno(camiseta))
    c.save(); c.clipPath(to, skia.ClipOp.kIntersect, False)
    c.drawRect(skia.Rect(H * 0.06, hombro_y - H * 0.05, H * 0.2, -H * 0.26), relleno(oscurece(camiseta, 0.07)))
    c.restore()
    c.drawPath(to, trazo(linea, lw))
    if spec.get("chip", True):
        _chip(c, -H * 0.005, -H * 0.38 + resp, H * 0.03, spec.get("color_chip", cinta or "#FF7A1A"), linea, lw * 0.8)
    if not levantado_der:
        mano_der = brazo_der()
    # cabeza
    hy = -H * 0.71 + resp * 1.4
    hw, hh = H * 0.235, H * 0.23
    inclina = math.sin(t * 1.3 + fase) * 1.2 + est.get("inclina", 0.0)
    c.save()
    c.translate(0, hy + hh)
    c.rotate(inclina)
    c.translate(0, -(hy + hh))
    # cuello
    c.drawRect(skia.Rect(-H * 0.03, hy + hh * 0.75, H * 0.03, hombro_y - H * 0.012), relleno(piel))
    c.drawLine(-H * 0.03, hy + hh * 0.85, -H * 0.03, hombro_y - H * 0.015, trazo(linea, lw))
    c.drawLine(H * 0.03, hy + hh * 0.85, H * 0.03, hombro_y - H * 0.015, trazo(linea, lw))
    # puntas de la cinta (detrás de la cabeza)
    if cinta:
        by = hy - hh * 0.42
        kx = hw * 1.0
        for k in (0, 1):
            ola = math.sin(t * 6 + k * 1.4 + fase) * hh * 0.08
            p = skia.Path(); p.moveTo(kx, by)
            p.cubicTo(kx + hw * 0.3, by + hh * (0.05 + 0.2 * k) + ola, kx + hw * 0.5, by + hh * (0.3 + 0.25 * k) - ola,
                      kx + hw * 0.72, by + hh * (0.25 + 0.4 * k) + ola)
            c.drawPath(p, trazo(linea, hh * 0.14 + 2 * lw)); c.drawPath(p, trazo(cinta, hh * 0.14))
        c.drawCircle(kx + hw * 0.04, by, hh * 0.1, relleno(cinta)); c.drawCircle(kx + hw * 0.04, by, hh * 0.1, trazo(linea, lw))
    peinado = spec.get("peinado", "puntas")
    if False:
        pass
    elif peinado == "coleta":
        q = skia.Path()
        ola = math.sin(t * 3 + fase) * hw * 0.05
        q.moveTo(hw * 0.75, hy - hh * 0.75)
        q.cubicTo(hw * 1.6 + ola, hy - hh * 0.7, hw * 1.55 + ola, hy + hh * 0.6, hw * 1.15 + ola, hy + hh * 0.95)
        q.cubicTo(hw * 1.2, hy + hh * 0.3, hw * 1.05, hy - hh * 0.3, hw * 0.75, hy - hh * 0.45)
        q.close()
        c.drawPath(q, relleno(pelo)); c.drawPath(q, trazo(linea, lw))
        c.drawCircle(hw * 0.98, hy - hh * 0.62, hh * 0.09, relleno(spec.get("color_lazo", cinta or "#FF5C8A")))
        c.drawCircle(hw * 0.98, hy - hh * 0.62, hh * 0.09, trazo(linea, lw))
    elif peinado == "mono":
        c.drawCircle(0, hy - hh * 1.18, hh * 0.32, relleno(pelo)); c.drawCircle(0, hy - hh * 1.18, hh * 0.32, trazo(linea, lw))
    # orejas
    for sgn in (-1, 1):
        r = skia.Rect(sgn * hw * 0.97 - hw * 0.13, hy + hh * 0.06, sgn * hw * 0.97 + hw * 0.13, hy + hh * 0.38)
        c.drawOval(r, relleno(piel)); c.drawOval(r, trazo(linea, lw))
    # cara (barbilla algo en punta)
    f = skia.Path()
    f.moveTo(-hw, hy - hh * 0.1)
    f.cubicTo(-hw, hy - hh * 1.2, hw, hy - hh * 1.2, hw, hy - hh * 0.1)
    f.cubicTo(hw * 0.98, hy + hh * 0.55, hw * 0.42, hy + hh * 0.93, 0, hy + hh * 1.0)
    f.cubicTo(-hw * 0.42, hy + hh * 0.93, -hw * 0.98, hy + hh * 0.55, -hw, hy - hh * 0.1)
    f.close()
    c.drawPath(f, relleno(piel)); c.drawPath(f, trazo(linea, lw))
    # pelo
    p = _pelo(hw, hh, hy, t, fase, peinado)
    c.drawPath(p, relleno(pelo))
    c.save(); c.clipPath(p, skia.ClipOp.kIntersect, False)
    c.drawOval(skia.Rect(-hw * 0.75, hy - hh * 1.3, -hw * 0.05, hy - hh * 0.95), relleno(aclara(pelo, 0.25 if _lum(pelo) < 0.3 else 0.45), 0.18 if _lum(pelo) < 0.3 else 0.6))
    c.restore()
    c.drawPath(p, trazo(linea, lw))
    # cinta deportiva sobre el pelo
    if cinta:
        by = hy - hh * 0.6
        band = skia.Path()
        band.moveTo(-hw * 1.1, by + hh * 0.1)
        band.quadTo(0, by - hh * 0.2, hw * 1.1, by + hh * 0.1)
        band.lineTo(hw * 1.08, by + hh * 0.3)
        band.quadTo(0, by + hh * 0.0, -hw * 1.08, by + hh * 0.3)
        band.close()
        c.drawPath(band, relleno(cinta))
        c.save(); c.clipPath(band, skia.ClipOp.kIntersect, False)
        c.drawRect(skia.Rect(-hw * 1.2, by + hh * 0.18, hw * 1.2, by + hh * 0.4), relleno(oscurece(cinta, 0.12)))
        c.restore()
        c.drawPath(band, trazo(linea, lw))
    # cara: ojos grandes con brillo, una ceja por ojo, nariz de un trazo
    sub = dict(spec)
    sub.update({"_parpado": piel, "ojos_tam": 1.1, "ojos_sep": 1.05, "mejillas": spec.get("mejillas", True),
                "color_ojos": spec.get("color_ojos", "#2B3A67")})
    cara(c, 0, hy + hh * 0.44, hw * 0.92, t, est, sub, lw)
    c.drawLine(hw * 0.03, hy + hh * 0.44, -hw * 0.03, hy + hh * 0.52, trazo(linea, lw * 0.8))
    acc = spec.get("accesorios", [])
    if "gafas" in acc:
        gs = hw * 0.92
        gey = hy + hh * 0.44 - gs * 0.12
        gsep = gs * 0.36 * 1.05
        gr = gs * 0.27
        gcol = spec.get("color_gafas", linea)
        for ex in (-gsep, gsep):
            c.drawCircle(ex, gey, gr, relleno("#BDE3FF", 0.18))
            c.drawCircle(ex, gey, gr, trazo(gcol, lw * 1.25))
        c.drawLine(-gsep + gr, gey, gsep - gr, gey, trazo(gcol, lw * 1.1))
        for sg in (-1, 1):
            c.drawLine(sg * (gsep + gr), gey, sg * hw * 0.97, gey + hh * 0.08, trazo(gcol, lw * 1.1))
    if "bigote" in acc:
        y0 = hy + hh * 0.62
        for k in (-1, 1):
            q = skia.Path(); q.moveTo(0, y0)
            q.cubicTo(k * hw * 0.15, y0 - hh * 0.07, k * hw * 0.3, y0 - hh * 0.01, k * hw * 0.36, y0 - hh * 0.1)
            q.cubicTo(k * hw * 0.3, y0 + hh * 0.08, k * hw * 0.1, y0 + hh * 0.07, 0, y0 + hh * 0.03); q.close()
            c.drawPath(q, relleno(oscurece(pelo, 0.35)))
    if "auriculares" in acc:
        acol = spec.get("color_accesorio", "#FF7A1A")
        c.drawArc(skia.Rect(-hw * 1.08, hy - hh * 1.25, hw * 1.08, hy + hh * 0.8), 195, 150, False, trazo(linea, lw * 3.2))
        c.drawArc(skia.Rect(-hw * 1.08, hy - hh * 1.25, hw * 1.08, hy + hh * 0.8), 195, 150, False, trazo(acol, lw * 1.6))
        for k in (-1, 1):
            rr = skia.RRect.MakeRectXY(skia.Rect(k * hw * 1.0 - hw * 0.16, hy - hh * 0.05, k * hw * 1.0 + hw * 0.16, hy + hh * 0.45), hw * 0.1, hw * 0.1)
            c.drawRRect(rr, relleno(acol)); c.drawRRect(rr, trazo(linea, lw))
    for a in acc:
        if a not in ("gafas", "bigote", "auriculares", "bandera") and (a, "humano") not in _AVISO_ACC:
            _AVISO_ACC.add((a, "humano"))
            print(f"  AVISO: el humano no dibuja el accesorio «{a}». En personas sirven gafas, bigote, auriculares y bandera (y cinta como campo aparte).")
    c.restore()  # cabeza
    if levantado_izq:
        mano_izq = brazo_izq()
    if levantado_der:
        mano_der = brazo_der()
    if pose == "bandera":
        mx, my = mano_der
        c.drawLine(mx, my + H * 0.08, mx, my - H * 0.3, trazo(linea, lw * 2.6))
        c.drawLine(mx, my + H * 0.08, mx, my - H * 0.3, trazo("#B07A43", lw * 1.2))
        p = skia.Path(); p.moveTo(mx, my - H * 0.3)
        for j in range(9):
            p.lineTo(mx + H * 0.17 * j / 8, my - H * 0.3 + math.sin(j * 0.8 - t * 7) * H * 0.01)
        for j in range(8, -1, -1):
            p.lineTo(mx + H * 0.17 * j / 8, my - H * 0.2 + math.sin(j * 0.8 - t * 7) * H * 0.01)
        p.close()
        c.drawPath(p, relleno(spec.get("color_bandera", cinta or "#FF7A1A"))); c.drawPath(p, trazo(linea, lw))
        c.drawCircle(mx, my, H * 0.04, relleno(piel)); c.drawCircle(mx, my, H * 0.04, trazo(linea, lw))
    c.restore()
    return {"mano_der": mano_der, "mano_izq": mano_izq}


# ------------------------------------------------------------------ entrada principal
def dibujar(c, spec, x, y, tam, t=0.0, est=None):
    est = est or {}
    alfa = est.get("alfa", 1.0)
    if alfa <= 0.01 or tam <= 1:
        return
    forma = spec.get("forma", "gota")
    if forma == "humano":
        with Capa(c, alfa, (x - tam * 0.7, y - tam * 1.3, tam * 1.4, tam * 1.45)):
            c.save()
            esc = est.get("escala", 1.0)
            c.translate(x, y); c.scale(esc, esc); c.translate(-x, -y)
            humano(c, x, y, tam, t, est, spec)
            c.restore()
        return
    R = tam / 2
    fase = est.get("fase", 0.0)
    lw = _ancho_contorno(spec, R)
    linea = spec.get("linea", CONTORNO)
    color = spec.get("color", "#9AD0F5")
    sq = est.get("squash", 0.0) + (math.sin(t * 3.2 + fase * 6) * 0.025 if spec.get("respira", True) else 0)
    with Capa(c, alfa, (x - tam * 1.6, y - tam * 1.6, tam * 3.2, tam * 3.2)):
        c.save()
        c.translate(x, y)
        esc = est.get("escala", 1.0)
        c.scale(esc * (1 + sq * 0.6) * est.get("lado", 1), esc * (1 - sq))
        c.rotate(est.get("rot", 0.0))
        if est.get("trompa") is not None:
            spec = dict(spec); spec["_trompa"] = est["trompa"]
        path, cara_y, s = cuerpo(forma, R, t, fase, spec)
        accesorios(c, R, t, fase, spec, lw, cara_y, s * spec.get("cara_tam", 1.0), False, forma)
        extras_forma(c, forma, R, t, fase, spec, lw, True)
        _pintar(c, path, color, lw, linea, spec.get("sombreado", True), R, 0, 0, spec.get("brillo", True))
        if forma == "disco":
            c.drawOval(skia.Rect(-R * 0.5, -R * 0.32, R * 0.5, R * 0.32), relleno(oscurece(color, 0.18)))
            c.drawOval(skia.Rect(-R * 0.5, -R * 0.32, R * 0.5, R * 0.32), trazo(linea, lw * 0.6, 0.6))
        detalles(c, forma, path, R, t, fase, spec, lw)
        extras_forma(c, forma, R, t, fase, spec, lw, False)
        if spec.get("cara", "feliz") != "ninguna" and est.get("cara") != "ninguna":
            if est.get("lado", 1) < 0:
                c.scale(-1, 1)
            sp = dict(spec)
            sp["_parpado"] = color
            cara(c, 0, cara_y, s * spec.get("cara_tam", 1.0), t, est, sp, lw)
            if est.get("lado", 1) < 0:
                c.scale(-1, 1)
        accesorios(c, R, t, fase, spec, lw, cara_y, s * spec.get("cara_tam", 1.0), True, forma)
        c.restore()


def proyectil(c, tipo, x, y, tam, ang, color, linea=CONTORNO):
    """Cosas que se lanzan: anticuerpo (Y), burbuja, estrella, chispa, flecha."""
    c.save(); c.translate(x, y); c.rotate(ang)
    lw = max(1.5, tam * 0.12)
    if tipo == "anticuerpo":
        p = skia.Path(); p.moveTo(-tam * 0.5, 0); p.lineTo(0, 0); p.lineTo(tam * 0.4, -tam * 0.32); p.moveTo(0, 0); p.lineTo(tam * 0.4, tam * 0.32)
        c.drawPath(p, trazo(linea, lw * 2.4)); c.drawPath(p, trazo(color, lw * 1.2))
    elif tipo == "burbuja":
        c.drawCircle(0, 0, tam * 0.4, relleno("#FFFFFF", 0.35)); c.drawCircle(0, 0, tam * 0.4, trazo(linea, lw * 0.6, 0.7))
    elif tipo == "estrella":
        pts = [(math.cos(-math.pi / 2 + math.pi * k / 5) * (tam * 0.5 if k % 2 == 0 else tam * 0.22),
                math.sin(-math.pi / 2 + math.pi * k / 5) * (tam * 0.5 if k % 2 == 0 else tam * 0.22)) for k in range(10)]
        p = _path_poligono(pts); c.drawPath(p, relleno(color)); c.drawPath(p, trazo(linea, lw * 0.6))
    elif tipo == "flecha":
        c.drawLine(-tam * 0.5, 0, tam * 0.4, 0, trazo(linea, lw * 1.4))
        p = _path_poligono([(tam * 0.5, 0), (tam * 0.25, -tam * 0.15), (tam * 0.25, tam * 0.15)])
        c.drawPath(p, relleno(color)); c.drawPath(p, trazo(linea, lw * 0.6))
    else:  # chispa
        for k in range(4):
            a = k * math.pi / 2
            c.drawLine(0, 0, math.cos(a) * tam * 0.5, math.sin(a) * tam * 0.5, trazo(color, lw))
    c.restore()


def puf(c, x, y, tam, p, color="#FFFFFF", linea=CONTORNO):
    """Nube de humo al desaparecer algo (p de 0 a 1)."""
    if p <= 0 or p >= 1:
        return
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.4
        d = tam * (0.2 + 0.6 * p)
        r = tam * 0.18 * (1 - p) + 2
        c.drawCircle(x + math.cos(a) * d, y + math.sin(a) * d, r, relleno(color, 1 - p))
        c.drawCircle(x + math.cos(a) * d, y + math.sin(a) * d, r, trazo(linea, max(1, tam * 0.025), (1 - p) * 0.8))
