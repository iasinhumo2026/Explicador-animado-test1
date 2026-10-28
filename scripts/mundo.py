"""Mundos animados: un escenario con fondo, partículas y personajes que actúan solos.

Un mundo se describe en video.json → "mundos" (ver referencias/mundos.md) y se pinta dentro de una tarjeta.
El escenario mide siempre 1600 × 1000 (proporción 16:10); las posiciones van de 0 a 1 y los tamaños,
en fracción del alto (0.1 = 100 px del escenario).
La simulación es determinista: el mismo segundo da siempre el mismo fotograma.
"""
import math
import random

import skia

import personajes as P
from comun import (Capa, aclara, clamp, col, fuente, lerp, mezcla, oscurece, relleno, rrect, ruido1, sale, suave, texto,
                   trazo, ancho, rebote, sombra_paint)

W, H = 1600, 1000
DT = 1 / 30


# ------------------------------------------------------------------ fondos
FONDOS = ["vaso", "agua", "cielo", "mar", "espacio", "noche", "papel", "liso", "tierra", "laboratorio"]


_CACHE_GRAD = {}


def _grad_v(c, colores, x0=0, y0=0, x1=W, y1=H):
    clave = (tuple(colores), x0, y0, x1, y1)
    img = _CACHE_GRAD.get(clave)
    if img is None:
        w, h = max(1, int((x1 - x0) / 4)), max(2, int((y1 - y0) / 4))
        s = skia.Surface(w, h)
        sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, h)], [col(k) for k in colores])
        s.getCanvas().drawRect(skia.Rect(0, 0, w, h), skia.Paint(Shader=sh))
        img = s.makeImageSnapshot()
        _CACHE_GRAD[clave] = img
    c.drawImageRect(img, skia.Rect(x0, y0, x1, y1), skia.SamplingOptions(skia.FilterMode.kLinear))


def _brillo(c, x, y, r, color, a):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [col(color, a), col(color, 0)])
    c.drawCircle(x, y, r, skia.Paint(Shader=sh))


def fondo(c, tipo, t, colores=None, linea=P.CONTORNO):
    if tipo == "vaso":
        a, b = (colores or ["#F9C9B6", "#EE9A8E"])[:2]
        _grad_v(c, [a, b])
        for k in range(4):  # rayos de luz suaves
            x = 200 + k * 420 + math.sin(t * 0.3 + k) * 40
            p = skia.Path(); p.moveTo(x, 0); p.lineTo(x + 160, 0); p.lineTo(x - 140, H); p.lineTo(x - 300, H); p.close()
            c.drawPath(p, relleno("#FFFFFF", 0.07))
        # paredes del vaso con células
        for (y0, sgn) in ((0, 1), (H, -1)):
            pared = skia.Path(); pared.moveTo(0, y0)
            for i in range(0, 17):
                x = i * 100
                pared.quadTo(x + 50, y0 + sgn * (70 + 18 * math.sin(i * 1.7)), x + 100, y0 + sgn * 62)
            pared.lineTo(W, y0); pared.close()
            c.drawPath(pared, relleno(oscurece(b, 0.12)))
            c.drawPath(pared, trazo(linea, 5, 0.55))
    elif tipo == "agua":
        a, b = (colores or ["#9FDDF5", "#3C8FD1"])[:2]
        _grad_v(c, [a, b])
        for k in range(5):
            y = 80 + k * 70
            p = skia.Path(); p.moveTo(0, y)
            for x in range(0, W + 1, 40):
                p.lineTo(x, y + math.sin(x / 90 + t * 1.2 + k) * 10)
            c.drawPath(p, trazo("#FFFFFF", 6, 0.12))
    elif tipo == "cielo":
        a, b = (colores or ["#8FD3FF", "#DDF3FF"])[:2]
        _grad_v(c, [a, b])
        _brillo(c, 1320, 190, 260, "#FFF3B0", 0.8)
    elif tipo in ("espacio", "noche"):
        a, b = (colores or (["#0B1030", "#241A4D"] if tipo == "espacio" else ["#0E1B33", "#25365E"]))[:2]
        _grad_v(c, [a, b])
        _brillo(c, 400, 300, 520, "#6B4EE6", 0.25)
        _brillo(c, 1250, 760, 480, "#E25C9C", 0.18)
        rnd = random.Random(5)
        for k in range(120):
            x, y = rnd.random() * W, rnd.random() * H
            r = rnd.random() * 2.4 + 0.8
            a_ = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * (1 + rnd.random() * 3) + k))
            c.drawCircle(x, y, r, relleno("#FFFFFF", a_))
    elif tipo == "mar":
        cie, cie2, mar, mar2 = (colores or ["#8FD3FF", "#E3F6FF", "#2F8FD8", "#1D5FA8"])[:4]
        _grad_v(c, [cie, cie2], 0, 0, W, 560)
        _grad_v(c, [mar, mar2], 0, 560, W, H)
        for k in range(4):
            y = 585 + k * 90
            p = skia.Path(); p.moveTo(0, y)
            for x in range(0, W + 1, 40):
                p.lineTo(x, y + math.sin(x / 70 + k * 1.3) * 9)
            c.drawPath(p, trazo("#FFFFFF", 6, 0.35 - k * 0.07))
        c.drawLine(0, 560, W, 560, trazo(linea, 5))
    elif tipo == "papel":
        a = (colores or ["#FBF6EC"])[0]
        c.drawRect(skia.Rect(0, 0, W, H), relleno(a))
        for x in range(0, W, 50):
            c.drawLine(x, 0, x, H, trazo("#D9CDB8", 1.5, 0.6, redondo=False))
        for y in range(0, H, 50):
            c.drawLine(0, y, W, y, trazo("#D9CDB8", 1.5, 0.6, redondo=False))
    elif tipo == "tierra":
        cie, hie, t1, t2 = (colores or ["#A9DCFF", "#7CC45A", "#B07A4A", "#8A5A34"])[:4]
        _grad_v(c, [cie, aclara(cie, 0.4)], 0, 0, W, 330)
        c.drawRect(skia.Rect(0, 330, W, 380), relleno(hie))
        c.drawRect(skia.Rect(0, 380, W, 680), relleno(t1))
        c.drawRect(skia.Rect(0, 680, W, H), relleno(t2))
        rnd = random.Random(3)
        for k in range(30):
            x, y = rnd.random() * W, 400 + rnd.random() * 580
            c.drawOval(skia.Rect(x, y, x + 24 + rnd.random() * 30, y + 14 + rnd.random() * 16), relleno(oscurece(t2, 0.2), 0.7))
        c.drawLine(0, 330, W, 330, trazo(linea, 5))
    elif tipo == "laboratorio":
        a, b = (colores or ["#EAF2F8", "#C9D9E6"])[:2]
        _grad_v(c, [a, b])
        c.drawRect(skia.Rect(0, 760, W, H), relleno(oscurece(b, 0.1)))
        c.drawLine(0, 760, W, 760, trazo(linea, 5))
    else:  # liso
        c.drawRect(skia.Rect(0, 0, W, H), relleno((colores or ["#F4EFE6"])[0]))


# ------------------------------------------------------------------ partículas (sin estado)
def particulas(c, spec, t, capa):
    tipo = spec.get("tipo", "globulos")
    n = int(spec.get("n", 14))
    semilla = spec.get("semilla", 11)
    rnd = random.Random(semilla + (0 if capa == "lejos" else 99))
    if capa == "cerca":
        n = max(1, n // 4)
    vel = spec.get("vel", 1.0)
    color = spec.get("color")
    for k in range(n):
        u, v, r0, ph = rnd.random(), rnd.random(), rnd.random(), rnd.random() * 6.28
        if tipo == "globulos":
            tam = (34 + r0 * 30) * (1.0 if capa == "lejos" else 1.55)
            vx = (60 + r0 * 60) * vel * (1 if capa == "lejos" else 1.8)
            x = (u * (W + 400) + t * vx) % (W + 400) - 200
            y = 120 + v * (H - 240) + math.sin(t * 0.9 + ph) * 25
            rot = math.sin(t * 0.7 + ph) * 30
            a = 0.55 if capa == "lejos" else 0.5
            if capa == "cerca" and 0.22 * H < y < 0.78 * H:
                y = 0.1 * H if v < 0.5 else 0.92 * H  # las de delante pasan por los bordes, nunca por el centro
            c.save(); c.translate(x, y); c.rotate(rot)
            cc = color or "#D9474F"
            fondo_ = mezcla("#F2A090", cc, a)  # color ya mezclado: sin capas transparentes (mucho más rápido)
            c.drawOval(skia.Rect(-tam, -tam * 0.62, tam, tam * 0.62), relleno(fondo_))
            c.drawOval(skia.Rect(-tam * 0.52, -tam * 0.3, tam * 0.52, tam * 0.3), relleno(oscurece(fondo_, 0.15)))
            c.drawOval(skia.Rect(-tam, -tam * 0.62, tam, tam * 0.62), trazo(P.CONTORNO, max(2, tam * 0.08), 0.35 + 0.45 * a))
            c.drawOval(skia.Rect(-tam * 0.7, -tam * 0.5, -tam * 0.2, -tam * 0.25), relleno("#FFFFFF", 0.3))
            c.restore()
        elif tipo == "burbujas":
            tam = 8 + r0 * 18
            y = H + 40 - ((v * (H + 80) + t * (40 + r0 * 60) * vel) % (H + 80))
            x = u * W + math.sin(t * 1.5 + ph) * 20
            c.drawCircle(x, y, tam, relleno("#FFFFFF", 0.25)); c.drawCircle(x, y, tam, trazo("#FFFFFF", 2.5, 0.7))
        elif tipo == "polvo":
            x = (u * W + math.sin(t * 0.4 + ph) * 40) % W
            y = (v * H + t * 12 * vel) % H
            c.drawCircle(x, y, 2 + r0 * 4, relleno(color or "#FFFFFF", 0.5))
        elif tipo == "lluvia":
            x = (u * W + t * 40) % W
            y = (v * H + t * (700 + r0 * 300) * vel) % (H + 60) - 30
            c.drawLine(x, y, x - 6, y + 34, trazo(color or "#5AA9E6", 5, 0.8))
        elif tipo == "nubes":
            x = (u * (W + 600) + t * 25 * vel) % (W + 600) - 300
            y = 60 + v * 380
            for (dx, dy, rr) in ((0, 0, 60), (60, -20, 75), (125, 0, 58), (60, 20, 60)):
                c.drawCircle(x + dx, y + dy, rr * (0.7 + r0 * 0.6), relleno("#FFFFFF", 0.85))
        elif tipo == "estrellas":
            x, y = u * W, v * H
            a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 3 + ph))
            P.proyectil(c, "estrella", x, y, 14 + r0 * 18, 0, color or "#FFE27A")
        elif tipo == "chispas":
            x, y = u * W, v * H
            a = 0.5 + 0.5 * math.sin(t * 4 + ph)
            P.proyectil(c, "chispa", x, y, (18 + r0 * 16) * a, 45, color or "#FFFFFF")


# ------------------------------------------------------------------ simulación
class _Nada:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


class Miembro:
    __slots__ = ("x", "y", "tam", "fase", "cara", "estado", "t_ev", "ox", "oy", "vivo", "carril", "parada", "vx", "rot", "ev_actor")

    def __init__(self):
        self.vivo = True; self.estado = "nada"; self.t_ev = 0.0; self.rot = 0.0; self.ev_actor = None


class Mundo:
    def __init__(self, nombre, spec, personajes, tiempo):
        self.nombre = nombre
        self.spec = spec
        self.pj = personajes
        self.tiempo = tiempo  # función que convierte "en" en segundos
        self.t0 = tiempo(spec.get("desde", 0)) if spec.get("desde") is not None else 0.0
        self.actores = []
        self.enjambres = []
        self.sonidos = []  # (segundo, nombre)
        for i, a in enumerate(spec.get("actores", [])):
            if "enjambre" in a:
                self.enjambres.append(dict(a))
            else:
                d = dict(a)
                d.setdefault("id", f"actor{i}")
                self.actores.append(d)
        self.por_id = {a["id"]: a for a in self.actores}
        for a in self.actores:
            if a.get("personaje") not in self.pj:
                raise SystemExit(f"El mundo «{nombre}» usa el personaje «{a.get('personaje')}», que no está en «personajes».")
            for acc in a.get("acciones", []):
                acc["_t"] = self.tiempo(acc.get("en", 0))
            a["_aparece"] = self.tiempo(a["aparece"]) if a.get("aparece") is not None else -1e9
            a["_desaparece"] = self.tiempo(a["desaparece"]) if a.get("desaparece") is not None else 1e9
        for e in self.enjambres:
            if e["enjambre"] not in self.pj:
                raise SystemExit(f"El mundo «{nombre}» usa el personaje «{e['enjambre']}» en un enjambre, que no está en «personajes».")
            e["_aparece"] = self.tiempo(e["aparece"]) if e.get("aparece") is not None else -1e9
        self.camara = []
        for k in spec.get("camara", []):
            self.camara.append((self.tiempo(k.get("en", 0)), k.get("zoom", 1.0), k.get("foco", [0.5, 0.5])))
        self.reiniciar()

    # -------------------------------------------------------------- estado
    def reiniciar(self):
        self.t_sim = self.t0 - DT
        self.rnd = random.Random(self.spec.get("semilla", 7))
        self.miembros = []
        for ei, e in enumerate(self.enjambres):
            lista = []
            n = int(e.get("n", 20))
            zx0, zy0, zx1, zy1 = e.get("zona", [0.02, 0.12, 0.45, 0.88])
            tmin, tmax = (e.get("tam", [0.07, 0.1]) if isinstance(e.get("tam"), list) else [e.get("tam", 0.08)] * 2)
            caras = e.get("caras", [self.pj[e["enjambre"]].get("cara", "feliz")])
            for k in range(n):
                m = Miembro()
                m.x = lerp(zx0, zx1, self.rnd.random()) * W
                m.y = lerp(zy0, zy1, self.rnd.random()) * H
                m.tam = lerp(tmin, tmax, self.rnd.random()) * H
                m.fase = self.rnd.random() * 6.28
                m.cara = caras[k % len(caras)]
                m.carril = self.rnd.random()
                m.parada = self.rnd.random()
                m.vx = 0.0
                lista.append(m)
            self.miembros.append(lista)
        self.proyectiles = []
        self.efectos = []
        self.ult_come = {}
        self.ult_disparo = {}
        self.ult_golpe = {}
        self.eventos_boca = {}

    def pos_actor(self, a, t):
        x, y = a.get("pos", [0.5, 0.5])
        x, y = x * W, y * H
        tam = a.get("tam", 0.3) * H
        lado = a.get("lado", 1)
        cara = a.get("cara")
        pose = a.get("pose")
        alfa, esc, rot, salto, squash = 1.0, 1.0, 0.0, 0.0, 0.0
        boca = None
        burbuja = None
        trompa_v = None
        for acc in a.get("acciones", []):
            ti = acc["_t"]
            if t < ti:
                continue
            dur = acc.get("dur", 0.6)
            p = clamp((t - ti) / max(1e-3, dur))
            tipo = acc.get("tipo")
            if tipo == "mover":
                tx, ty = acc["a"]
                k = suave(p)
                x, y = lerp(x, tx * W, k), lerp(y, ty * H, k)
                if "lado" in acc:
                    lado = acc["lado"]
            elif tipo == "cara":
                cara = acc["cara"]
            elif tipo == "pose":
                pose = acc["pose"]
            elif tipo == "lado":
                lado = acc["lado"]
            elif tipo == "crece":
                esc *= lerp(1.0, acc.get("a", 1.3), sale(p))
            elif tipo == "salta":
                salto = max(salto, math.sin(math.pi * p) * acc.get("alto", 1.0)) if p < 1 else salto
            elif tipo == "tiembla" and p < 1:
                x += math.sin(t * 60) * 8 * (1 - p)
            elif tipo == "gira" and p < 1:
                rot += 360 * suave(p)
            elif tipo == "bocadillo":
                if t - ti < acc.get("dur", 1.4):
                    burbuja = (acc.get("texto", "!"), (t - ti) / acc.get("dur", 1.4), acc.get("tam"))
            elif tipo == "estira":
                trompa_v = lerp(acc.get("de", 1.0), acc.get("a", 3.0), suave(p))
            elif tipo == "habla":
                if t - ti < dur:
                    boca = 0.5 + 0.5 * math.sin((t - ti) * 22)
        # entrada y salida
        ap, de = a["_aparece"], a["_desaparece"]
        modo = a.get("entra", "pop")
        if t < ap:
            return None
        pe = clamp((t - ap) / 0.45)
        if pe < 1:
            if modo == "pop":
                esc *= rebote(pe) if pe > 0 else 0
            elif modo == "abajo":
                y += (1 - sale(pe)) * H * 0.6
            elif modo == "izq":
                x -= (1 - sale(pe)) * W * 0.6
            elif modo == "der":
                x += (1 - sale(pe)) * W * 0.6
            elif modo == "salta":
                y -= math.sin(math.pi * pe) * H * 0.25
                esc *= lerp(0.4, 1.0, sale(pe))
            alfa = min(alfa, clamp(pe * 3))
        if t > de:
            ps = clamp((t - de) / 0.35)
            if ps >= 1:
                return None
            esc *= 1 - ps * ps
        if a.get("orbita"):
            o = a["orbita"]
            ang = (t * o.get("vel", 0.25) + o.get("fase", 0.0)) * 2 * math.pi
            cxo, cyo = o.get("centro", [0.5, 0.5])
            rx, ry = (o.get("radio", [0.3, 0.12]) if isinstance(o.get("radio"), list) else [o.get("radio", 0.3)] * 2)
            x, y = cxo * W + math.cos(ang) * rx * W, cyo * H + math.sin(ang) * ry * H
            esc *= 1 + 0.12 * math.sin(ang)  # más grande cuando pasa por delante
        flot = a.get("flota", 0.012) * H
        y += math.sin(t * 2.0 + a.get("fase", 0)) * flot
        return dict(x=x, y=y, tam=tam, lado=lado, cara=cara, pose=pose, alfa=alfa, esc=esc, rot=rot, salto=salto,
                    squash=squash, boca=boca, burbuja=burbuja, trompa=trompa_v)

    def objetivo(self, e, t, k=0):
        h = e.get("hacia")
        if isinstance(h, list) and h and isinstance(h[0], str):
            h = h[k % len(h)]
        if isinstance(h, str) and h in self.por_id:
            st = self.pos_actor(self.por_id[h], t)
            if st:
                return st["x"], st["y"], st["tam"]
            a = self.por_id[h]
            return a["pos"][0] * W, a["pos"][1] * H, a.get("tam", 0.3) * H
        if isinstance(h, list):
            return h[0] * W, h[1] * H, 0.0
        return W * 0.85, H * 0.5, 0.0

    def paso(self, t):
        # movimiento de los enjambres
        for ei, e in enumerate(self.enjambres):
            if t < e["_aparece"]:
                continue
            vel = e.get("vel", 0.07) * W
            varios = isinstance(e.get("hacia"), list) and e.get("hacia") and isinstance(e["hacia"][0], str)
            ancho_carril = e.get("dispersion", 0.3 if varios else 0.75) * H
            parar = e.get("parar", 0.42)
            objetivos = {}
            if e.get("flujo"):
                # flujo continuo: avanzan en una dirección y al salir vuelven a entrar por el otro lado
                d = e.get("dir", 1)
                zx0, zy0, zx1, zy1 = e.get("zona", [0.0, 0.0, 1.0, 1.0])
                for m in self.miembros[ei]:
                    if m.estado != "nada":
                        continue
                    m.x += d * vel * DT * (0.75 + 0.5 * ((m.fase * 13) % 1))
                    m.y = lerp(zy0, zy1, m.carril) * H + math.sin(t * 2 + m.fase) * 6
                    if d > 0 and m.x > W + m.tam:
                        m.x = -m.tam
                    elif d < 0 and m.x < -m.tam:
                        m.x = W + m.tam
                continue
            for mi, m in enumerate(self.miembros[ei]):
                if m.estado == "nada":
                    k = mi if varios else 0
                    if k % 97 not in objetivos:
                        objetivos[k % 97] = self.objetivo(e, t, k)
                    tx, ty, tr = objetivos[k % 97]
                    dy = ty + (m.carril - 0.5) * ancho_carril
                    stop_x = tx - tr * parar - m.parada * e.get("fila", 0.08) * W
                    if e.get("dir", 1) < 0:
                        stop_x = tx + tr * parar + m.parada * e.get("fila", 0.08) * W
                    dx = stop_x - m.x
                    paso_x = max(-vel * DT, min(vel * DT, dx)) * (0.7 + 0.6 * ((m.fase * 13) % 1))
                    m.x += paso_x
                    m.y += (dy - m.y) * 0.02 + math.sin(t * 3 + m.fase) * 0.6
                    m.vx = paso_x / DT
                elif m.estado == "golpe":
                    m.x += m.ox * DT; m.y += m.oy * DT; m.oy += 900 * DT; m.rot += 600 * DT
                    if t - m.t_ev > 0.75:
                        m.estado = "muerto"; m.t_ev = t
                        self.efectos.append(("puf", t, m.x, m.y, m.tam))
                elif m.estado == "pinchado":
                    m.x -= 25 * DT
                    if t - m.t_ev > 0.9:
                        m.estado = "muerto"; m.t_ev = t
                        self.efectos.append(("puf", t, m.x, m.y, m.tam))
                elif m.estado == "comido":
                    if t - m.t_ev > 0.38:
                        m.estado = "muerto"; m.t_ev = t
                elif m.estado == "muerto" and e.get("continuo", True):
                    if t - m.t_ev > e.get("reaparece", 1.0):
                        zx0, zy0, zx1, zy1 = e.get("zona", [0.02, 0.12, 0.45, 0.88])
                        m.x = (-0.08 if e.get("dir", 1) > 0 else 1.08) * W
                        m.y = lerp(zy0, zy1, self.rnd.random()) * H
                        m.estado = "nada"; m.rot = 0.0; m.carril = self.rnd.random()
        # acciones automáticas de los actores
        for a in self.actores:
            st = self.pos_actor(a, t)
            if not st:
                continue
            ax, ay, ar = st["x"], st["y"], st["tam"] / 2
            if a.get("come"):
                cfg = a["come"] if isinstance(a["come"], dict) else {}
                cada = cfg.get("cada", 0.8)
                radio = cfg.get("radio", 1.45) * ar + 40
                if t - self.ult_come.get(a["id"], -9) >= cada:
                    mejor = None
                    for lista in self.miembros:
                        for m in lista:
                            if m.estado == "nada":
                                d = math.hypot(m.x - ax, m.y - ay)
                                if d < radio and (mejor is None or d < mejor[0]):
                                    mejor = (d, m)
                    if mejor:
                        m = mejor[1]
                        m.estado = "comido"; m.t_ev = t; m.ox, m.oy = m.x, m.y; m.ev_actor = a["id"]
                        self.ult_come[a["id"]] = t
                        self.eventos_boca.setdefault(a["id"], []).append(t)
                        self.sonidos.append((t + 0.3, "nam"))
            if a.get("golpea"):
                cfg = a["golpea"] if isinstance(a["golpea"], dict) else {}
                radio = cfg.get("radio", 1.6) * ar + 30
                if t - self.ult_golpe.get(a["id"], -9) >= cfg.get("cada", 0.55):
                    for lista in self.miembros:
                        hecho = False
                        for m in lista:
                            if m.estado == "nada" and math.hypot(m.x - ax, m.y - ay) < radio:
                                m.estado = "golpe"; m.t_ev = t
                                sgn = -1 if m.x < ax else 1
                                m.ox, m.oy = sgn * (500 + 300 * self.rnd.random()), -500 - 300 * self.rnd.random()
                                self.ult_golpe[a["id"]] = t
                                self.efectos.append(("pum", t, m.x, m.y, m.tam))
                                self.sonidos.append((t, "boing"))
                                hecho = True
                                break
                        if hecho:
                            break
            if a.get("dispara"):
                cfg = a["dispara"] if isinstance(a["dispara"], dict) else {}
                if t - self.ult_disparo.get(a["id"], -9) >= cfg.get("cada", 0.5) and t >= self.tiempo(cfg.get("en", 0)):
                    vivos = [m for lista in self.miembros for m in lista if m.estado == "nada" and 0 < m.x < W]
                    if vivos:
                        m = vivos[int(self.rnd.random() * len(vivos))]
                        self.proyectiles.append(dict(x=ax, y=ay, m=m, t0=t, tipo=cfg.get("proyectil", "anticuerpo"),
                                                     color=cfg.get("color", "#FF7A1A"), tam=cfg.get("tam", 0.05) * H,
                                                     vel=cfg.get("vel", 1.1) * W))
                        self.ult_disparo[a["id"]] = t
                        self.sonidos.append((t, "piu"))
        # proyectiles
        vivos = []
        for p in self.proyectiles:
            m = p["m"]
            dx, dy = m.x - p["x"], m.y - p["y"]
            d = math.hypot(dx, dy)
            paso_ = p["vel"] * DT
            if m.estado != "nada" and m.estado != "pinchado":
                p["x"] += (p.get("ux", 1)) * paso_
                if t - p["t0"] > 2 or p["x"] > W + 50:
                    continue
                vivos.append(p); continue
            if d < m.tam * 0.45 + paso_:
                m.estado = "pinchado"; m.t_ev = t
                self.efectos.append(("chispa", t, m.x, m.y, m.tam))
                continue
            p["ux"], p["uy"] = dx / max(d, 1e-3), dy / max(d, 1e-3)
            p["x"] += p["ux"] * paso_; p["y"] += p["uy"] * paso_
            p["ang"] = math.degrees(math.atan2(dy, dx))
            vivos.append(p)
        self.proyectiles = vivos
        self.efectos = [e for e in self.efectos if t - e[1] < 0.8]

    def avanzar(self, t):
        if t < self.t_sim - 1e-6:
            self.reiniciar()
        while self.t_sim + DT <= t + 1e-6:
            self.t_sim += DT
            self.paso(self.t_sim)

    # -------------------------------------------------------------- dibujo
    def boca_actor(self, a, t):
        ev = [e for e in self.eventos_boca.get(a["id"], []) if t - e < 0.6 and t >= e]
        if not ev:
            return None
        x = t - ev[-1]
        if x < 0.28:
            return sale(x / 0.28)
        return max(0.0, 1 - (x - 0.28) / 0.12)

    def _fondo(self, c, escala):
        """El fondo es fijo: se pinta una vez al tamaño real de la tarjeta (con la viñeta) y se reutiliza."""
        if not hasattr(self, "_cache_fondo"):
            self._cache_fondo = {}
        clave = round(escala, 3)
        img = self._cache_fondo.get(clave)
        if img is None:
            w, h = max(2, int(W * escala + 0.999)), max(2, int(H * escala + 0.999))
            s = skia.Surface(w, h)
            k = s.getCanvas()
            k.scale(escala, escala)
            fondo(k, self.spec.get("fondo", "liso"), 0.0, self.spec.get("colores"))
            for fr in self.spec.get("franjas", []):
                # bandas de color dentro del escenario: un vaso sanguíneo, una capa de la piel, un camino, un río
                y0, y1 = fr.get("y", [0.4, 0.6])
                x0, x1 = fr.get("x", [0.0, 1.0])
                r = skia.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
                k.drawRRect(skia.RRect.MakeRectXY(r, fr.get("radio", 0) * H, fr.get("radio", 0) * H), relleno(fr.get("color", "#E36A5C"), fr.get("alfa", 1.0)))
                if fr.get("borde", True):
                    k.drawRRect(skia.RRect.MakeRectXY(r, fr.get("radio", 0) * H, fr.get("radio", 0) * H), trazo(P.CONTORNO, 5, 0.7))
                if fr.get("texto"):
                    texto(k, fr["texto"], r.left() + 30, r.top() + 34, "extrabold", 30, fr.get("texto_color", "#FFFFFF"))
            sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.72, [col("#000000", 0), col("#000000", 0), col("#000000", 0.16)], [0, 0.7, 1.0])
            k.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
            img = s.makeImageSnapshot()
            self._cache_fondo[clave] = img
        c.save(); c.scale(1 / escala, 1 / escala); c.drawImage(img, 0, 0); c.restore()

    def dibujar(self, c, t, alfa=1.0, escala=1.0):
        self.avanzar(t)
        sp = self.spec
        c.save()
        # cámara
        if self.camara:
            z, fx, fy = self._camara(t)
            c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-fx * W, -fy * H)
        self._fondo(c, escala)
        for ps in sp.get("particulas", []):
            if self._t_part(ps) <= t < ps["_hasta"]:
                with Capa(c, clamp((t - self._t_part(ps)) / 0.4), (0, 0, W, H)) if t - self._t_part(ps) < 0.4 else _Nada():
                    particulas(c, ps, t, "lejos")
        # lista de cosas a dibujar, ordenadas por y
        cosas = []
        for ei, e in enumerate(self.enjambres):
            spec = self.pj[e["enjambre"]]
            for m in self.miembros[ei]:
                if m.estado == "muerto" or t < e["_aparece"]:
                    continue
                cosas.append((m.y + m.tam * 0.5, "m", (spec, m, e)))
        for a in self.actores:
            st = self.pos_actor(a, t)
            if st:
                cosas.append((st["y"] + st["tam"] * 0.5 + (2 if self.pj[a["personaje"]].get("forma") == "humano" else 0), "a", (a, st)))
        cosas.sort(key=lambda k: k[0])
        for _, tipo, dat in cosas:
            if tipo == "m":
                spec, m, e = dat
                est = {"fase": m.fase, "cara": m.cara, "lado": e.get("dir", 1)}
                x, y, tam = m.x, m.y, m.tam
                if m.estado == "nada":
                    # se enfadan o se asustan al acercarse a un defensor
                    for a in self.actores:
                        if a.get("come") or a.get("golpea"):
                            st = self.pos_actor(a, t)
                            if st and math.hypot(x - st["x"], y - st["y"]) < st["tam"] * 0.9:
                                est["cara"] = e.get("cara_cerca", "miedo")
                    est["rot"] = math.sin(t * 6 + m.fase) * 6
                elif m.estado == "comido":
                    a = self.por_id.get(m.ev_actor)
                    st = self.pos_actor(a, t) if a else None
                    k = clamp((t - m.t_ev) / 0.38)
                    if st:
                        bx, by = st["x"], st["y"] + st["tam"] * 0.12
                        x, y = lerp(m.ox, bx, suave(k)), lerp(m.oy, by, suave(k))
                    tam = m.tam * (1 - 0.85 * k)
                    est["cara"] = "miedo"
                elif m.estado == "golpe":
                    est["cara"] = "mareado"; est["rot"] = m.rot
                elif m.estado == "pinchado":
                    est["cara"] = "mareado"; est["rot"] = math.sin(t * 30) * 8
                P.dibujar(c, spec, x, y, tam, t, est)
                if m.estado == "pinchado":
                    P.proyectil(c, "anticuerpo", x - m.tam * 0.45, y - m.tam * 0.1, m.tam * 0.55, 200, "#FF7A1A")
            else:
                a, st = dat
                spec = self.pj[a["personaje"]]
                est = {"fase": a.get("fase", 0.0), "cara": st["cara"], "lado": st["lado"], "alfa": st["alfa"] * alfa,
                       "escala": st["esc"], "rot": st["rot"], "pose": st["pose"], "salto": st["salto"], "trompa": st.get("trompa")}
                b = self.boca_actor(a, t)
                if b is not None:
                    est["boca"] = b
                    if spec.get("forma") != "humano":
                        est["cara"] = "hambre"
                        est["squash"] = -0.08 * b
                elif st["boca"] is not None:
                    est["boca"] = st["boca"]
                if a.get("mira", True) and self.miembros:
                    vivos = [m for lista in self.miembros for m in lista if m.estado == "nada"]
                    if vivos:
                        m = min(vivos, key=lambda m: abs(m.x - st["x"]) + abs(m.y - st["y"]))
                        dx, dy = m.x - st["x"], m.y - st["y"]
                        d = math.hypot(dx, dy) + 1e-3
                        est["mirar"] = (dx / d * st["lado"], dy / d)
                if spec.get("forma") == "humano":
                    P.dibujar(c, spec, st["x"], st["y"] + st["tam"] * 0.5, st["tam"], t, est)
                else:
                    P.dibujar(c, spec, st["x"], st["y"], st["tam"], t, est)
                if st["burbuja"]:
                    txt_b, prog_b, tam_b = st["burbuja"]
                    bx_ = st["x"] + st["tam"] * 0.45
                    by_ = st["y"] - st["tam"] * 0.55
                    bocadillo(c, txt_b, min(max(bx_, 160), W - 160), max(by_, 70), prog_b, st["tam"], tam_b)
        for p in self.proyectiles:
            P.proyectil(c, p["tipo"], p["x"], p["y"], p["tam"], p.get("ang", 0), p["color"])
        for (tipo, te, x, y, tam) in self.efectos:
            k = (t - te) / 0.5
            if tipo == "puf":
                P.puf(c, x, y, tam * 1.2, k)
            elif tipo in ("pum", "chispa"):
                if k < 1:
                    for j in range(6):
                        an = j * math.pi / 3 + 0.3
                        r0, r1 = tam * (0.3 + 0.5 * k), tam * (0.5 + 0.7 * k)
                        c.drawLine(x + math.cos(an) * r0, y + math.sin(an) * r0, x + math.cos(an) * r1, y + math.sin(an) * r1,
                                   trazo("#FFFFFF" if tipo == "pum" else "#FFE27A", max(3, tam * 0.08), 1 - k))
        for ps in sp.get("particulas", []):
            if ps.get("cerca", True) and ps.get("tipo", "globulos") == "globulos":
                particulas(c, ps, t, "cerca")
        for et in sp.get("etiquetas", []):
            etiqueta(c, et, self, t)
        c.restore()

    def _t_part(self, ps):
        if "_t" not in ps:
            ps["_t"] = self.tiempo(ps["aparece"]) if ps.get("aparece") is not None else -1e9
            ps["_hasta"] = self.tiempo(ps["desaparece"]) if ps.get("desaparece") is not None else 1e9
        return ps["_t"]

    def _camara(self, t):
        ks = sorted(self.camara)
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2][0], ks[0][2][1]
        for (t0, z0, f0), (t1, z1, f1) in zip(ks[:-1], ks[1:]):
            if t0 <= t <= t1:
                k = suave((t - t0) / max(1e-3, min(0.8, t1 - t0)))
                return lerp(z0, z1, k), lerp(f0[0], f1[0], k), lerp(f0[1], f1[1], k)
        return ks[-1][1], ks[-1][2][0], ks[-1][2][1]

    def punto(self, actor_id, t):
        """Posición (u, v) de un actor en el escenario, de 0 a 1."""
        a = self.por_id.get(actor_id)
        if not a:
            return None
        st = self.pos_actor(a, t)
        if not st:
            return None
        return st["x"] / W, (st["y"] - st["tam"] * 0.1) / H


def etiqueta(c, et, mundo, t):
    t0 = mundo.tiempo(et.get("en", 0)) if et.get("en") is not None else -1e9
    t1 = mundo.tiempo(et["hasta"]) if et.get("hasta") is not None else 1e9
    if t < t0 or t >= t1:
        return
    k = clamp((t - t0) / 0.3) * clamp((t1 - t) / 0.2)
    s = et.get("texto", "")
    tam = et.get("tam", 44)
    color = et.get("color", "#FF7A1A")
    w = ancho(s, "extrabold", tam) + tam * 1.0
    hh = tam * 1.5
    if et.get("actor"):
        a = mundo.por_id.get(et["actor"])
        if not a:
            return
        st = mundo.pos_actor(a, t)
        if not st or st["esc"] < 0.85 or t >= a["_desaparece"]:
            return  # el actor no está (o se está yendo): la etiqueta se esconde
        humano = mundo.pj[a["personaje"]].get("forma") == "humano"
        arriba = st["tam"] * (0.62 if not humano else 0.55)
        x, y = st["x"], st["y"] - arriba - hh * 0.6
        if y - hh / 2 < 70:  # no cabe encima: va debajo
            y = st["y"] + st["tam"] * (0.62 if not humano else 0.55) + hh * 0.6
        x -= w / 2
    else:
        x, y = et.get("pos", [0.06, 0.1])[0] * W, et.get("pos", [0.06, 0.1])[1] * H
        if et.get("ancla", "izq") == "centro":
            x -= w / 2
    # siempre dentro del escenario, con margen para el recorte de la tarjeta
    x = min(max(x, W * 0.05), W * 0.95 - w)
    y = min(max(y, hh / 2 + H * 0.04), H * 0.96 - hh / 2)
    if k <= 0:
        return
    with Capa(c, k, (x - 20, y - hh, w + 40, hh * 2)):
        c.save(); c.translate(x + w / 2, y); c.scale(lerp(0.7, 1, sale(clamp((t - t0) / 0.3))), lerp(0.7, 1, sale(clamp((t - t0) / 0.3)))); c.translate(-(x + w / 2), -y)
        c.drawRRect(rrect(x, y - hh / 2 + 5, w, hh, 10), relleno("#000000", 0.18))
        c.drawRRect(rrect(x, y - hh / 2, w, hh, 10), relleno(color))
        c.drawRRect(rrect(x, y - hh / 2, w, hh, 10), trazo(P.CONTORNO, 4))
        texto(c, s, x + tam * 0.5, y, "extrabold", tam, et.get("texto_color", "#FFFFFF"))
        c.restore()


def bocadillo(c, s, x, y, p, tam, tam_texto=None):
    """Bocadillo de cómic encima de un personaje. p: progreso de 0 a 1 de su vida. Texto de 54 px del escenario por defecto."""
    a = clamp(p / 0.12) * clamp((1 - p) / 0.15)
    esc = rebote(clamp(p / 0.2))
    t_ = tam_texto or 54
    w = ancho(s, "black", t_) + t_ * 1.2
    h = t_ * 1.7
    with Capa(c, a):
        c.save(); c.translate(x, y); c.scale(esc, esc)
        cola = skia.Path(); cola.moveTo(-w * 0.15, h * 0.4); cola.lineTo(-w * 0.32, h * 0.95); cola.lineTo(w * 0.05, h * 0.4); cola.close()
        c.drawRRect(rrect(-w / 2, -h / 2, w, h, h / 2), relleno("#FFFFFF"))
        c.drawPath(cola, relleno("#FFFFFF"))
        c.drawRRect(rrect(-w / 2, -h / 2, w, h, h / 2), trazo(P.CONTORNO, 4))
        c.drawPath(cola, trazo(P.CONTORNO, 4))
        c.drawRect(skia.Rect(-w * 0.17, h * 0.34, w * 0.07, h * 0.47), relleno("#FFFFFF"))
        texto(c, s, 0, 0, "black", t_, P.CONTORNO, ancla="centro")
        c.restore()
