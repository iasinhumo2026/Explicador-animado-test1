"""Utilidades comunes de explicador-animado: rutas, ffmpeg, fuentes, colores, estilos, curvas y dibujo básico."""
import json, math, os, shutil, subprocess, sys, unicodedata
from functools import lru_cache

import numpy as np

try:
    import skia
except ImportError:  # comprobar.py lo instala
    skia = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "fuentes")
FPS = 30


# ------------------------------------------------------------------ ffmpeg
def _ffmpeg():
    ruta = shutil.which("ffmpeg")
    if ruta:
        return ruta
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    print("  ffmpeg no está instalado: instalo imageio-ffmpeg (una sola vez)…")
    for extra in (["--break-system-packages"], []):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", *extra, "imageio-ffmpeg"], capture_output=True)
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            continue
    sys.exit("No hay ffmpeg y no se ha podido instalar. Instálalo (apt install ffmpeg o pip install imageio-ffmpeg).")


FFMPEG = _ffmpeg()


# ------------------------------------------------------------------ json y texto
def normaliza(p):
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return "".join(c for c in p if c.isalnum())


def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ fuentes
PESOS = {
    "medium": "Poppins-Medium.ttf", "semibold": "Poppins-SemiBold.ttf", "bold": "Poppins-Bold.ttf",
    "extrabold": "Poppins-ExtraBold.ttf", "black": "Poppins-Black.ttf",
    "mano": "Caveat-Bold.ttf", "cursiva": "Lora-SemiBoldItalic.ttf",
    "mono": "JetBrainsMono-Medium.ttf", "monobold": "JetBrainsMono-Bold.ttf",
}


@lru_cache(maxsize=32)
def _typeface(peso):
    ruta = os.path.join(FUENTES, PESOS.get(peso, PESOS["bold"]))
    tf = skia.Typeface.MakeFromFile(ruta)
    if tf is None:
        sys.exit(f"No puedo abrir la fuente {ruta}.")
    return tf


@lru_cache(maxsize=512)
def fuente(peso, tam):
    f = skia.Font(_typeface(peso), float(max(1, round(tam * 2) / 2)))
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def ancho(txt, peso, tam):
    return fuente(peso, tam).measureText(txt)


def metricas(peso, tam):
    m = fuente(peso, tam).getMetrics()
    return -m.fAscent, m.fDescent


def ajustar(txt, peso, tam, ancho_max, tam_min=10):
    while tam > tam_min and ancho(txt, peso, tam) > ancho_max:
        tam -= 1
    return tam


def partir(txt, peso, tam, ancho_max):
    """Parte un texto en líneas que quepan en ancho_max."""
    lineas, actual = [], ""
    for w in txt.split():
        prueba = (actual + " " + w).strip()
        if actual and ancho(prueba, peso, tam) > ancho_max:
            lineas.append(actual); actual = w
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas


# ------------------------------------------------------------------ colores
def hex_rgba(h, a=1.0):
    if isinstance(h, (tuple, list)):
        r, g, b = h[:3]
        aa = h[3] / 255 if len(h) > 3 else 1.0
        return (r, g, b, aa * a)
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    aa = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), aa * a)


@lru_cache(maxsize=4096)
def _col(h, a):
    r, g, b, aa = hex_rgba(h, a)
    return skia.Color(int(r), int(g), int(b), int(max(0, min(1, aa)) * 255))


def col(h, a=1.0):
    if isinstance(h, str):
        return _col(h, round(a, 3))
    r, g, b, aa = hex_rgba(h, a)
    return skia.Color(int(r), int(g), int(b), int(max(0, min(1, aa)) * 255))


def mezcla(c1, c2, t):
    a, b = hex_rgba(c1), hex_rgba(c2)
    t = max(0.0, min(1.0, t))
    r = [a[i] + (b[i] - a[i]) * t for i in range(4)]
    return "#%02X%02X%02X%02X" % (int(r[0]), int(r[1]), int(r[2]), int(r[3] * 255))


def oscurece(c, t=0.25):
    return mezcla(c, "#000000", t)


def aclara(c, t=0.3):
    return mezcla(c, "#FFFFFF", t)


def luminancia(c):
    r, g, b, _ = hex_rgba(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def texto_sobre(c, oscuro="#14161C", claro="#FFFFFF"):
    return oscuro if luminancia(c) > 0.62 else claro


# ------------------------------------------------------------------ estilos
ESTILOS = {
    # fondo, manchas (2 colores difuminados), puntos (trama), tarjeta, texto, acento, suave, etiqueta (píldora), ok, linea
    "crema": dict(fondo="#F3E8DA", manchas=["#F2B597", "#F5CDA9"], puntos="#D8C6B2", tarjeta="#FFFFFF",
                  texto="#1E1A17", acento="#E2683C", suave="#8B7F74", etiqueta="#1E1A17", ok="#2F9E5B", linea="#E6DAD0"),
    "noche": dict(fondo="#121826", manchas=["#2B3A67", "#41295E"], puntos="#252F48", tarjeta="#1E2638",
                  texto="#F3F5FA", acento="#FFB547", suave="#8E98AF", etiqueta="#F3F5FA", ok="#4CC38A", linea="#2B3550"),
    "menta": dict(fondo="#E6F3EC", manchas=["#BDE5D1", "#CBE7F1"], puntos="#C4DDD0", tarjeta="#FFFFFF",
                  texto="#10302A", acento="#0F9D6E", suave="#6B8079", etiqueta="#10302A", ok="#0F9D6E", linea="#D3E7DD"),
    "lavanda": dict(fondo="#EEEAFB", manchas=["#D4CBF6", "#F5D2E5"], puntos="#D3CBEA", tarjeta="#FFFFFF",
                    texto="#22183F", acento="#6B4EE6", suave="#7D7596", etiqueta="#22183F", ok="#2F9E5B", linea="#E1DBF5"),
    "limon": dict(fondo="#FBF5DA", manchas=["#F6E08F", "#F8CFA0"], puntos="#E6DBB0", tarjeta="#FFFFFF",
                  texto="#2B2410", acento="#D98E04", suave="#8A7F5E", etiqueta="#2B2410", ok="#2F9E5B", linea="#EEE5C3"),
}


def estilo(e):
    if isinstance(e, dict):
        base = dict(ESTILOS[e.get("base", "crema")])
        base.update({k: v for k, v in e.items() if k != "base"})
        return base
    if e not in ESTILOS:
        sys.exit(f"El estilo «{e}» no existe. Usa uno de: {', '.join(ESTILOS)} o un objeto con colores.")
    return dict(ESTILOS[e])


# ------------------------------------------------------------------ curvas de animación
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, dur):
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / dur)


def suave(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def sale(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p


def entra(x, p=3):
    x = clamp(x)
    return x ** p


def rebote(x):
    """Sobrepasa un poco y vuelve (back out)."""
    x = clamp(x)
    s = 1.70158
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def muelle(x, fuerza=8.0, freno=5.0):
    x = clamp(x)
    return 1 - math.exp(-freno * x) * math.cos(fuerza * x)


def lerp(a, b, t):
    return a + (b - a) * t


def ruido1(x, semilla=0):
    """Ruido suave determinista entre -1 y 1."""
    return (math.sin(x * 1.7 + semilla * 12.9898) * 0.5 + math.sin(x * 2.9 + semilla * 4.1414 + 1.3) * 0.3
            + math.sin(x * 4.3 + semilla * 7.77 + 2.1) * 0.2)


# ------------------------------------------------------------------ pinceles
def relleno(c, a=1.0):
    return skia.Paint(AntiAlias=True, Color=col(c, a))


def trazo(c, ancho_, a=1.0, redondo=True):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=ancho_)
    if redondo:
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def sombra_paint(c="#000000", a=0.18, difuso=18):
    p = skia.Paint(AntiAlias=True, Color=col(c, a))
    if difuso > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, difuso))
    return p


def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def caja(c, x, y, w, h, r, color, sombra=0.0, sombra_y=14, difuso=22, borde=None, borde_ancho=0, a=1.0):
    if sombra > 0:
        c.drawRRect(rrect(x, y + sombra_y, w, h, r), sombra_paint(a=sombra * a, difuso=difuso))
    c.drawRRect(rrect(x, y, w, h, r), relleno(color, a))
    if borde and borde_ancho > 0:
        c.drawRRect(rrect(x, y, w, h, r), trazo(borde, borde_ancho, a))


_AVISADOS = set()
_VISTOS = set()


def comprobar_letras(s, peso):
    """Avisa (una vez) si un texto usa caracteres que la fuente no tiene: saldrían como cuadraditos."""
    f = fuente(peso, 40)
    try:
        glifos = f.textToGlyphs(s)
    except Exception:  # noqa: BLE001
        return
    for ch, g in zip(s, glifos):
        if g == 0 and not ch.isspace() and (ch, peso) not in _AVISADOS:
            _AVISADOS.add((ch, peso))
            print(f"  AVISO: el carácter «{ch}» (en «{s[:40]}») no existe en la fuente y sale como un cuadradito. "
                  "Cámbialo por texto (por ejemplo «→» por «a» o «:»). Los emojis tampoco se pueden usar en el vídeo.")


def texto(c, s, x, y, peso, tam, color, ancla="izq", a=1.0, base="centro"):
    """Dibuja texto. base='centro' centra en vertical en y; 'linea' usa y como línea base."""
    f = fuente(peso, tam)
    if s and s not in _VISTOS:
        _VISTOS.add(s)
        comprobar_letras(s, peso)
    w = f.measureText(s)
    if ancla == "centro":
        x -= w / 2
    elif ancla == "der":
        x -= w
    if base == "centro":
        asc, desc = metricas(peso, tam)
        y = y + (asc - desc) / 2 - asc * 0.04
    c.drawString(s, x, y, f, relleno(color, a))
    return w


def pildora(c, s, x, y, peso, tam, fondo, color, pad_x=None, pad_y=None, a=1.0, ancla="izq", sombra=0.0, r=None):
    """Píldora con texto; y es el centro vertical. Devuelve (x, y0, w, h)."""
    pad_x = tam * 0.6 if pad_x is None else pad_x
    pad_y = tam * 0.34 if pad_y is None else pad_y
    w = ancho(s, peso, tam) + 2 * pad_x
    h = tam * 1.18 + 2 * pad_y
    if ancla == "centro":
        x -= w / 2
    elif ancla == "der":
        x -= w
    caja(c, x, y - h / 2, w, h, h / 2 if r is None else r, fondo, sombra=sombra, sombra_y=6, difuso=10, a=a)
    texto(c, s, x + pad_x, y, peso, tam, color, a=a)
    return x, y - h / 2, w, h


class Capa:
    """Agrupa dibujos con transparencia: with Capa(c, 0.5): ..."""

    def __init__(self, c, alfa=1.0, rect=None):
        self.c, self.alfa, self.rect = c, alfa, rect

    def __enter__(self):
        if self.alfa < 0.999:
            r = self.rect
            if r is not None and not isinstance(r, skia.Rect):
                r = skia.Rect.MakeXYWH(*r)
            self.c.saveLayerAlpha(r, int(clamp(self.alfa) * 255))
        else:
            self.c.save()
        return self.c

    def __exit__(self, *a):
        self.c.restore()


def matriz_giro_y(x, y, w, h, angulo, dist=2200):
    """Matriz de perspectiva que gira un rectángulo sobre su eje vertical (ángulo en grados)."""
    a = math.radians(angulo)
    cx = x + w / 2
    pts = []
    for (px, py) in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
        dx = (px - cx) * math.cos(a)
        dz = (px - cx) * math.sin(a)
        k = dist / (dist + dz)
        cy = y + h / 2
        pts.append(skia.Point(cx + dx * k, cy + (py - cy) * k))
    m = skia.Matrix()
    m.setPolyToPoly([skia.Point(x, y), skia.Point(x + w, y), skia.Point(x + w, y + h), skia.Point(x, y + h)], pts)
    return m


def nuevo_lienzo(w, h):
    info = skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    return skia.Surface.MakeRaster(info), info


def abrir_imagen(ruta):
    if not os.path.exists(ruta):
        sys.exit(f"No encuentro la imagen {ruta}.")
    img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(ruta))
    if img is None:
        sys.exit(f"No puedo abrir la imagen {ruta} (usa PNG o JPG).")
    return img


MUESTREO = None


def muestreo():
    global MUESTREO
    if MUESTREO is None:
        MUESTREO = skia.SamplingOptions(skia.CubicResampler.Mitchell())
    return MUESTREO


# ------------------------------------------------------------------ textos fijos según el idioma
TEXTOS = {
    "es": {"comenta": "Comenta", "sigueme": "Sígueme", "personas": "{n} personas", "chat": "Nuevo chat",
           "creando": "Creando la escena…", "lista": "¡Escena lista!", "miles": ".", "decimal": ","},
    "en": {"comenta": "Comment", "sigueme": "Follow for more", "personas": "{n} people", "chat": "New chat",
           "creando": "Creating the scene…", "lista": "Scene ready!", "miles": ",", "decimal": "."},
    "pt": {"comenta": "Comenta", "sigueme": "Segue-me", "personas": "{n} pessoas", "chat": "Novo chat",
           "creando": "A criar a cena…", "lista": "Cena pronta!", "miles": ".", "decimal": ","},
    "fr": {"comenta": "Commente", "sigueme": "Abonne-toi", "personas": "{n} personnes", "chat": "Nouveau chat",
           "creando": "Création de la scène…", "lista": "Scène prête !", "miles": " ", "decimal": ","},
    "it": {"comenta": "Commenta", "sigueme": "Seguimi", "personas": "{n} persone", "chat": "Nuova chat",
           "creando": "Creo la scena…", "lista": "Scena pronta!", "miles": ".", "decimal": ","},
    "de": {"comenta": "Kommentiere", "sigueme": "Folge mir", "personas": "{n} Personen", "chat": "Neuer Chat",
           "creando": "Szene wird erstellt…", "lista": "Szene fertig!", "miles": ".", "decimal": ","},
}
IDIOMA = {"actual": "es"}


def tx(clave):
    return TEXTOS.get(IDIOMA["actual"], TEXTOS["es"]).get(clave, TEXTOS["es"][clave])


def numero(v, dec=0):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "\x00").replace(".", tx("decimal")).replace("\x00", tx("miles"))
