#!/usr/bin/env python3
"""Renderiza un vídeo explicativo animado a partir de video.json.

Uso:
  python3 render.py P/video.json                  # vídeo completo → P/salida/video.mp4
  python3 render.py P/video.json --muestras       # un fotograma por plano → P/salida/muestras.png
  python3 render.py P/video.json --en 12.5        # un fotograma concreto → P/salida/en_12.5.png
  python3 render.py P/video.json --desde 10 --hasta 16   # solo un tramo (para revisar)
Opciones: --salida ruta.mp4 · --procesos N (por defecto, los núcleos que haya, hasta 4) · --sin-audio
"""
import argparse, copy, json, math, os, re, subprocess, sys, tempfile, time, wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia  # noqa: E402

import kit as K  # noqa: E402
import personajes as P  # noqa: E402
import sonidos  # noqa: E402
from comun import (IDIOMA, FFMPEG, FPS, Capa, clamp, estilo, leer_json, lerp, matriz_giro_y, normaliza, nuevo_lienzo, rebote,  # noqa: E402
                   rrect, relleno, sale, suave, texto, trazo, col, entra)
from mundo import Mundo, W as MW, H as MH  # noqa: E402


# ------------------------------------------------------------------ tiempos
class Reloj:
    """Convierte «en» en segundos: 12.4 · "+0.5" · "frase 3" · "fin frase 3" · "palabra" · "dos palabras" · "palabra#2" · "palabra+0.2"."""

    def __init__(self, voz):
        self.palabras = voz.get("palabras", [])
        self.frases = voz.get("frases", [])
        self.norm = [normaliza(p["t"]) for p in self.palabras]

    def frase(self, n):
        if not self.frases:
            raise SystemExit("No hay frases: ejecuta antes alinear.py.")
        if n < 1 or n > len(self.frases):
            raise SystemExit(f"La frase {n} no existe: el guion tiene {len(self.frases)} frases (se cuentan desde 1).")
        return self.frases[n - 1]

    def en(self, spec, desde=0.0):
        if spec is None:
            return desde
        if isinstance(spec, (int, float)):
            return float(spec)
        s = str(spec).strip()
        m = re.match(r"^([+-]\d+(\.\d+)?)$", s)
        if m:
            return desde + float(s)
        m = re.match(r"^(fin\s+)?frase\s+(\d+)\s*([+-]\d+(\.\d+)?)?$", s)
        if m:
            f = self.frase(int(m.group(2)))
            base = f["fin"] if m.group(1) else f["ini"]
            return base + (float(m.group(3)) if m.group(3) else 0.0)
        m = re.match(r"^(.*?)(#(\d+))?\s*([+-]\d+(\.\d+)?)?$", s)
        frase_txt, n_occ = m.group(1), int(m.group(3) or 1)
        off = float(m.group(4)) if m.group(4) else 0.0
        fin = frase_txt.startswith(">")
        frase_txt = frase_txt.lstrip(">").strip()
        objetivo = [normaliza(w) for w in frase_txt.split() if normaliza(w)]
        if not objetivo:
            raise SystemExit(f"No entiendo el tiempo «{spec}».")
        for inicio in (desde - 0.3, -1):
            vistos = 0
            for i in range(len(self.norm) - len(objetivo) + 1):
                if self.palabras[i]["ini"] < inicio:
                    continue
                if all(self.norm[i + j] == objetivo[j] for j in range(len(objetivo))):
                    vistos += 1
                    if vistos == n_occ:
                        p = self.palabras[i + len(objetivo) - 1] if fin else self.palabras[i]
                        return (p["fin"] if fin else p["ini"]) + off
        raise SystemExit(f"La palabra «{frase_txt}» no aparece en el guion"
                         + (f" (la busco desde el segundo {desde:.1f} y luego desde el principio)" if desde > 0 else "")
                         + ". Revisa que esté en guion.txt tal cual se dice.")


# ------------------------------------------------------------------ carga del proyecto
def cargar(ruta):
    V = leer_json(ruta)
    base_dir = os.path.dirname(os.path.abspath(ruta))
    if V.get("hereda"):
        B = leer_json(os.path.join(base_dir, V["hereda"]))
        desde = V.get("cambia_desde_frase")
        planos = B.get("planos", [])
        if desde is not None:
            # cada plano heredado se queda solo si empieza antes de la frase que cambia
            # (los planos con "en" se sitúan con la voz del vídeo base)
            reloj_b = None
            ruta_b = os.path.join(base_dir, B.get("voz", "voz"), "palabras.json")
            if os.path.exists(ruta_b):
                reloj_b = Reloj(leer_json(ruta_b))
            quedan = []
            for p in planos:
                if "frase" in p:
                    f = int(p["frase"])
                elif reloj_b is not None:
                    try:
                        t = reloj_b.en(p.get("en", 0.0))
                    except SystemExit:
                        t = 1e9
                    f = 1 + sum(1 for fr in reloj_b.frases[1:] if fr["ini"] - 0.15 <= t)
                else:
                    f = 0
                if f < desde:
                    quedan.append(p)
            planos = quedan
        B.update({k: v for k, v in V.items() if k not in ("hereda", "planos", "cambia_desde_frase")})
        B["planos"] = planos + V.get("planos", [])
        B["_heredado"] = True
        V = B
    V["_dir"] = base_dir
    return V


class Escena:
    def __init__(self, V):
        self.V = V
        self.dir = V["_dir"]
        self.formato = V.get("formato", "9:16")
        if self.formato not in K.LAYOUTS:
            raise SystemExit("formato tiene que ser \"9:16\" o \"16:9\".")
        self.L = K.LAYOUTS[self.formato]
        self.W, self.H = self.L["W"], self.L["H"]
        self.est = estilo(V.get("estilo", "crema"))
        voz_dir = os.path.join(self.dir, V.get("voz", "voz"))
        ruta_pal = os.path.join(voz_dir, "palabras.json")
        if not os.path.exists(ruta_pal):
            raise SystemExit(f"No encuentro {ruta_pal}. Ejecuta antes alinear.py con --salida {voz_dir}.")
        self.voz = leer_json(ruta_pal)
        IDIOMA["actual"] = V.get("idioma", "es")
        self.voz_wav = os.path.join(voz_dir, self.voz["voz"]) if self.voz.get("voz") else None
        self.corte_voz = None
        if V.get("voz_hasta_frase"):
            # final sin voz: usa la misma voz, cortada justo antes de esa frase
            n = int(V["voz_hasta_frase"])
            fr = self.voz["frases"]
            if not 1 < n <= len(fr):
                raise SystemExit(f"voz_hasta_frase tiene que estar entre 2 y {len(fr)}.")
            corte = fr[n - 1]["ini"] - 0.06
            self.voz = dict(self.voz)
            self.voz["frases"] = fr[:n - 1]
            self.voz["palabras"] = [p for p in self.voz["palabras"] if p["frase"] < n - 1]
            self.voz["duracion"] = corte
            self.corte_voz = corte
        self.reloj = Reloj(self.voz)
        self.heredado = bool(V.get("_heredado"))
        self.dur = float(V.get("duracion") or (self.voz["duracion"] + V.get("cola", 0.7)))
        self.nf = int(round(self.dur * FPS))
        self.pj = V.get("personajes", {})
        for k, s in self.pj.items():
            s.setdefault("linea", V.get("linea", P.CONTORNO))
        self.mundos = {}
        for nombre, spec in V.get("mundos", {}).items():
            self.mundos[nombre] = Mundo(nombre, spec, self.pj, self._tiempo_mundo)
        self.imagenes = {}
        self.preparar_planos()
        self.preparar_mascota()
        st = V.get("subtitulos", {})
        self.sub = None if st is False else dict(self.L["subtitulos"], **(st or {}))
        if self.sub:
            self.trozos = K.trozos_subtitulos(self.voz["palabras"], self.sub["tam"], self.sub["ancho"])
        self.ctx = {"formato": self.formato, "imagenes": self.imagenes, "geo": {}, "W": self.W, "H": self.H,
                    "carpeta": os.path.join(self.dir, "salida")}
        self.sonidos = []
        self.calcular_sonidos()

    def _tiempo_mundo(self, x):
        try:
            return self.reloj.en(x, 0.0)
        except SystemExit:
            if self.heredado:
                return 1e9  # en la segunda versión, lo que dependía del final cambiado ya no pasa
            raise

    # -------------------------------------------------------------- planos y elementos
    def preparar_planos(self):
        planos = copy.deepcopy(self.V.get("planos", []))
        if not planos:
            raise SystemExit("video.json no tiene planos.")
        for p in planos:
            if "frase" in p:
                p["_ini"] = max(0.0, self.reloj.frase(int(p["frase"]))["ini"] - p.get("antes", 0.12))
            else:
                p["_ini"] = self.reloj.en(p.get("en", 0.0))
        planos[0]["_ini"] = 0.0
        planos.sort(key=lambda p: p["_ini"])
        for i, p in enumerate(planos):
            p["_fin"] = planos[i + 1]["_ini"] if i + 1 < len(planos) else self.dur + 1
            previos = {e.get("id"): e for e in planos[i - 1]["elementos"]} if i > 0 else {}
            for j, e in enumerate(p.get("elementos", [])):
                e.setdefault("id", f"p{i}e{j}")
            ids_siguientes = {e.get("id", f"p{i + 1}e{j}") for j, e in enumerate(planos[i + 1]["elementos"])} if i + 1 < len(planos) else set()
            nombre = f"plano {i + 1} ({'frase ' + str(p['frase']) if 'frase' in p else 'en «' + str(p.get('en')) + '»'})"
            for j, e in enumerate(p.get("elementos", [])):
                try:
                    pe = previos.get(e["id"])
                    e["_continua"] = pe is not None and e.get("en") is None
                    if e["_continua"]:
                        # sigue del plano anterior: conserva sus tiempos (lo que ya salió no vuelve a salir)
                        e["_base"] = pe["_base"]
                        e["_t"] = pe["_t"]
                    else:
                        e["_base"] = p["_ini"]
                        e["_t"] = max(p["_ini"], self.reloj.en(e.get("en"), p["_ini"]))
                    e["_hasta"] = self.reloj.en(e["hasta"], p["_ini"]) if e.get("hasta") is not None else p["_fin"]
                    e["_hasta_propio"] = e.get("hasta") is not None
                    e["_sigue"] = e["id"] in ids_siguientes and e.get("hasta") is None
                    e["_plano_ini"] = p["_ini"]
                    self.resolver(e, e["_base"])
                except SystemExit as ex:
                    raise SystemExit(f"{ex}\n  → en el {nombre}, elemento «{e.get('id')}» ({e.get('tipo', 'tarjeta')}).")
        self.planos = planos

    def resolver(self, e, base):
        R = self.reloj
        tipo = e.get("tipo", "tarjeta")
        cont = e.get("contenido")
        if tipo == "tarjeta":
            if cont is None:
                raise SystemExit(f"La tarjeta «{e['id']}» no tiene «contenido».")
            self.resolver_contenido(cont, e["_t"])
            for v in e.get("voltear", []):
                v["_t"] = R.en(v.get("en"), base)
                self.resolver_contenido(v["contenido"], v["_t"])
            for pg in e.get("pegatinas", []):
                pg["_t"] = R.en(pg.get("en"), base)
        elif tipo == "pildoras":
            for it in e.get("items", []):
                it["_t"] = R.en(it.get("en"), base)
                it["_tachar"] = R.en(it["tachar"], base) if it.get("tachar") not in (None, False) else None
        elif tipo == "titular":
            for ln in e.get("lineas", []):
                ln["_t"] = R.en(ln.get("en"), base)
        elif tipo == "contador":
            e["_t"] = R.en(e.get("en"), base)
        elif tipo == "movil":
            e["imagen"], e["_ruta"] = e["imagen"], os.path.join(self.dir, e["imagen"])
            for kf in e.get("zoom", []):
                kf["_t"] = R.en(kf.get("en"), base)
            for ro in e.get("rodear", []):
                ro["_t"] = R.en(ro.get("en"), base)
        elif tipo == "nota":
            pass

    def resolver_contenido(self, cont, t0):
        R = self.reloj
        if "prompt" in cont:
            d = cont["prompt"] if isinstance(cont["prompt"], dict) else {"texto": cont["prompt"]}
            d["_t0"] = R.en(d.get("en"), t0)
            if d.get("hasta"):
                d["_t1"] = R.en(d["hasta"], t0)
            else:
                d["_t1"] = d["_t0"] + len(d.get("texto", "")) / d.get("letras_por_segundo", 28)
            cont["prompt"] = d
        if "codigo" in cont:
            d = cont["codigo"] if isinstance(cont["codigo"], dict) else {}
            d["_t0"] = R.en(d.get("en"), t0)
            cont["codigo"] = d
        if "gente" in cont:
            d = cont["gente"] if isinstance(cont["gente"], dict) else {"n": int(cont["gente"])}
            d["_t0"] = R.en(d.get("en"), t0)
            cont["gente"] = d
        if "pasos" in cont:
            d = cont["pasos"]
            for it in d.get("items", []):
                it["_t"] = R.en(it.get("en"), t0)
        if "imagen" in cont:
            d = cont["imagen"] if isinstance(cont["imagen"], dict) else {"imagen": cont["imagen"]}
            d["_ruta"] = os.path.join(self.dir, d["imagen"])
            d["_t_ini"] = t0
            if not os.path.exists(d["_ruta"]):
                raise SystemExit(f"No encuentro la imagen {d['_ruta']}.")
            for kf in d.get("zoom", []):
                kf["_t"] = R.en(kf.get("en"), t0)
            for ro in d.get("rodear", []):
                ro["_t"] = R.en(ro.get("en"), t0)
            cont["imagen"] = d
        if "clip" in cont:
            d = cont["clip"]
            d["_ruta"] = os.path.join(self.dir, d["archivo"])
            if not os.path.exists(d["_ruta"]):
                raise SystemExit(f"No encuentro el vídeo {d['_ruta']}.")
            d["_t0"] = R.en(d.get("en"), t0)
        if "mundo" in cont and cont["mundo"] not in self.mundos:
            raise SystemExit(f"El mundo «{cont['mundo']}» no está en «mundos».")

    def calcular_sonidos(self):
        for p in self.planos:
            for e in p["elementos"]:
                S = []
                self._sonidos_elemento(e, S)
                if e.get("_continua"):
                    S = [s for s in S if s[0] >= p["_ini"] - 0.01]
                self.sonidos.extend(S)

    def _sonidos_elemento(self, e, S):
        if True:
            if True:
                tipo = e.get("tipo", "tarjeta")
                t = e["_t"]
                if e.get("sonido") is False:
                    return
                if tipo == "tarjeta":
                    if not e["_continua"]:
                        S.append((t, "pasa"))
                    for v in e.get("voltear", []):
                        S.append((v["_t"], "voltea"))
                    for pg in e.get("pegatinas", []):
                        S.append((pg["_t"] + 0.05, "sello"))
                    for cont in [e["contenido"]] + [v["contenido"] for v in e.get("voltear", [])]:
                        if "prompt" in cont:
                            d = cont["prompt"]
                            tt = d["_t0"]
                            while tt < d["_t1"]:
                                S.append((tt, "tecla")); tt += 0.075
                        if "gente" in cont:
                            d = cont["gente"]
                            n = int(d.get("n", 70))
                            for i in range(0, n, max(1, n // 14)):
                                S.append((d["_t0"] + d.get("dur", 1.6) * (i / n) ** 0.8, "tic"))
                        if "pasos" in cont:
                            for it in cont["pasos"].get("items", []):
                                S.append((it["_t"], "check"))
                        if "imagen" in cont:
                            for ro in cont["imagen"].get("rodear", []):
                                S.append((ro["_t"], "boli"))
                elif tipo == "pildoras":
                    for it in e.get("items", []):
                        S.append((it["_t"], "check" if it.get("ok") else "pop"))
                        if it["_tachar"] is not None:
                            S.append((it["_tachar"], "tachar"))
                elif tipo == "nota":
                    S.append((t, "boli"))
                elif tipo == "titular":
                    for ln in e.get("lineas", []):
                        S.append((ln["_t"], "pop"))
                elif tipo == "contador":
                    d = e.get("dur", 1.2)
                    for k in range(8):
                        S.append((t + d * (k / 8) ** 1.5, "tic"))
                    S.append((t + d, "ding"))
                elif tipo == "cta":
                    S.append((t, "exito"))
                elif tipo == "siguenos":
                    S.append((t, "exito"))
                elif tipo == "movil":
                    if not e["_continua"]:
                        S.append((t, "pasa"))
                    for ro in e.get("rodear", []):
                        S.append((ro["_t"], "boli"))
                elif tipo == "pegatina":
                    S.append((t, "sello"))

    # -------------------------------------------------------------- mascota
    def preparar_mascota(self):
        m = self.V.get("mascota")
        self.masc = None
        if not m:
            return
        if m.get("personaje") not in self.pj:
            raise SystemExit(f"La mascota usa el personaje «{m.get('personaje')}», que no está en «personajes».")
        cfg = dict(self.L["mascota"])
        cfg.update(m)
        poses = []
        for kf in cfg.get("poses", []):
            try:
                kf["_t"] = self.reloj.en(kf.get("en"), 0)
                poses.append(kf)
            except SystemExit:
                if not self.heredado:
                    raise
        cfg["poses"] = sorted(poses, key=lambda k: k["_t"])
        # los personajes que no son humanos se colocan también por los pies
        if self.pj[cfg["personaje"]].get("forma") != "humano":
            if "tam" not in m:
                cfg["tam"] = self.L["mascota"]["tam"] * 0.5
            cfg["_no_humano"] = True
        self.masc = cfg
        # envolvente de la voz para mover la boca
        self.env = np.zeros(self.nf + 2)
        if self.voz_wav and os.path.exists(self.voz_wav):
            with wave.open(self.voz_wav) as w:
                sr = w.getframerate()
                a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            hop = sr // FPS
            n = min(self.nf + 2, len(a) // hop)
            rms = np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1))
            ref = np.percentile(rms[rms > 0.01], 90) if np.any(rms > 0.01) else 1
            self.env[:n] = np.clip(rms / max(ref, 1e-4), 0, 1.2)
        else:
            for p in self.voz["palabras"]:
                i0, i1 = int(p["ini"] * FPS), int(p["fin"] * FPS)
                for i in range(i0, min(self.nf, i1)):
                    self.env[i] = 0.4 + 0.5 * abs(math.sin(i * 1.7))
        claves = []
        for p in self.voz["palabras"]:
            if p["t"].startswith("*"):
                claves.append(p["ini"])
        self.saltos = claves

    def estado_mascota(self, t, plano):
        cfg = self.masc
        pose, cara = cfg.get("pose", "neutro"), cfg.get("cara", "feliz")
        for kf in cfg["poses"]:
            if t >= kf["_t"]:
                pose = kf.get("pose", pose); cara = kf.get("cara", cara)
        pm = plano.get("mascota")
        oculta = False
        if pm is False or (isinstance(pm, dict) and pm.get("oculta")):
            oculta = True
        elif isinstance(pm, dict):
            pose = pm.get("pose", pose); cara = pm.get("cara", cara)
        i = int(t * FPS)
        e = self.env[min(i, len(self.env) - 1)]
        hablando = any(p["ini"] - 0.03 <= t <= p["fin"] for p in self.voz["palabras"])
        boca = clamp((e - 0.08) * 1.15) if hablando else 0.0
        # redondez según la vocal que suena
        red = 0.3
        for p in self.voz["palabras"]:
            if p["ini"] <= t <= p["fin"]:
                s = normaliza(p["t"]) or "a"
                k = int((t - p["ini"]) / max(0.05, p["fin"] - p["ini"]) * len(s))
                ch = s[min(len(s) - 1, k)]
                red = 0.85 if ch in "ou" else (0.15 if ch == "a" else (0.45 if ch in "ei" else red))
                if ch in "mbp":
                    boca *= 0.15
                break
        salto = 0.0
        for ts in self.saltos:
            if 0 <= t - ts < 0.32:
                salto = math.sin(math.pi * (t - ts) / 0.32) * 0.6
        return dict(pose=pose, cara=cara, boca=boca, redondez=red, salto=salto, oculta=oculta)

    # -------------------------------------------------------------- dibujo de un fotograma
    def plano_en(self, t):
        for i, p in enumerate(self.planos):
            if p["_ini"] <= t < p["_fin"]:
                return i
        return len(self.planos) - 1

    def fotograma(self, c, t):
        K.fondo_pagina(c, self.est, self.W, self.H)
        self.ctx["geo"] = {}
        i = self.plano_en(t)
        p = self.planos[i]
        prev = self.planos[i - 1] if i > 0 else None
        # elementos del plano anterior que se van (los que no siguen)
        if prev and t - p["_ini"] < 0.22:
            for e in prev["elementos"]:
                if not e["_sigue"]:
                    self.elemento(c, e, t, prev, saliendo=clamp((t - p["_ini"]) / 0.2))
        orden = sorted(p["elementos"], key=lambda e: 1 if e.get("tipo", "tarjeta") in ("nota", "pegatina") else 0)
        for e in orden:
            if e.get("_hasta_propio"):
                # con "hasta" propio, el fundido termina justo en ese momento
                if e["_t"] - 0.001 <= t < e["_hasta"]:
                    sal = clamp((t - (e["_hasta"] - 0.2)) / 0.2)
                    self.elemento(c, e, t, p, saliendo=sal, previo=prev)
                continue
            if e["_t"] - 0.001 <= t < e["_hasta"]:
                self.elemento(c, e, t, p, saliendo=0.0, previo=prev)
        if self.masc:
            self.mascota(c, t, p)
        if self.sub and p.get("subtitulos", True) is not False:
            cfg = self.sub if not isinstance(p.get("subtitulos"), dict) else dict(self.sub, **p["subtitulos"])
            K.subtitulos(c, self.trozos, t, cfg, self.est, self.W)

    def mascota(self, c, t, plano):
        cfg = self.masc
        st = self.estado_mascota(t, plano)
        # aparecer / desaparecer suave al cambiar de plano
        i = self.plano_en(t)
        prev = self.planos[i - 1] if i > 0 else None
        k = 1.0
        if st["oculta"]:
            if prev and t - plano["_ini"] < 0.25 and not self.estado_mascota(plano["_ini"] - 0.01, prev)["oculta"]:
                k = 1 - clamp((t - plano["_ini"]) / 0.25)
            else:
                return
        elif prev and t - plano["_ini"] < 0.35 and self.estado_mascota(plano["_ini"] - 0.01, prev)["oculta"]:
            k = rebote(clamp((t - plano["_ini"]) / 0.35))
        spec = self.pj[cfg["personaje"]]
        est = {"pose": st["pose"], "cara": st["cara"], "boca": st["boca"], "redondez": st["redondez"], "salto": st["salto"],
               "lado": cfg.get("lado", 1), "escala": k, "fase": 0.3, "mirar": (0.35, -0.2)}
        x, y, tam = self.pos_mascota(plano)
        if prev is not None and t - plano["_ini"] < 0.45:
            x0, y0, t0 = self.pos_mascota(prev)
            kk = suave(clamp((t - plano["_ini"]) / 0.45))
            x, y, tam = lerp(x0, x, kk), lerp(y0, y, kk), lerp(t0, tam, kk)
        if spec.get("forma") != "humano":
            y = y - tam * 0.55 - st["salto"] * tam * 0.15
            est["squash"] = -0.06 * st["boca"]
        P.dibujar(c, spec, x, y, tam, t, est)

    def pos_mascota(self, plano):
        cfg = self.masc
        pm = plano.get("mascota") if isinstance(plano.get("mascota"), dict) else {}
        return pm.get("x", cfg["x"]), pm.get("y", cfg["y"]), pm.get("tam", cfg["tam"])

    def elemento(self, c, e, t, plano, saliendo=0.0, previo=None):
        tipo = e.get("tipo", "tarjeta")
        k_in = 1.0 if e.get("_continua") else clamp((t - e["_t"]) / 0.42)
        if tipo == "tarjeta":
            self.tarjeta(c, e, t, k_in, saliendo, previo)
        elif tipo == "pildoras":
            x, y, w, h = e.get("zona", self.L["extras"])
            with Capa(c, 1 - saliendo):
                K.lista_pildoras(c, x, y, w, h, t, e["items"], self.est, self.ctx, tam=e.get("tam", 40))
        elif tipo == "nota":
            self.nota(c, e, t, saliendo)
        elif tipo == "titular":
            x, y, w, h = e.get("zona", self.L["extras_ancho"])
            with Capa(c, 1 - saliendo):
                K.titular(c, e["lineas"], x + w / 2, y + e.get("tam", 96) * 0.6, w, t, self.est, tam=e.get("tam", 96))
        elif tipo == "contador":
            x, y = e.get("pos", [self.L["extras"][0] + self.L["extras"][2] / 2, self.L["extras"][1] + 120])
            with Capa(c, 1 - saliendo):
                K.contador(c, x, y, t, e, self.est, tam=e.get("tam", 110))
        elif tipo == "cta":
            x, y = e.get("pos", [self.L["cta"]["x"], self.L["cta"]["y"]])
            K.cta(c, x, y, t, e["_t"], e.get("palabra", "PALABRA"), e.get("linea"), e.get("nota"), self.est, self.ctx, tam=e.get("tam", 1.0),
                  titulo=e.get("titulo"))
        elif tipo == "siguenos":
            x, y = e.get("pos", [self.L["cta"]["x"], self.L["cta"]["y"]])
            K.siguenos(c, x, y, t, e["_t"], e.get("lineas"), self.est, self.ctx, tam=e.get("tam", 1.0), icono_=e.get("icono"))
        elif tipo == "movil":
            x, y, w = e.get("caja", [60, 220, 420])[:3]
            dx = (1 - sale(k_in)) * (-self.W * 0.7 if x < self.W / 2 else self.W * 0.7) if not e.get("_continua") else 0
            dx += saliendo * (-self.W * 0.7 if x < self.W / 2 else self.W * 0.7)
            c.save(); c.translate(x + dx, y); c.rotate(e.get("rot", -3)); c.translate(-x, -y)
            K.movil(c, x, y, w, t, e, self.est, self.ctx)
            c.restore()
        elif tipo == "pegatina":
            x, y = e.get("pos", [540, 900])
            K.pegatina(c, e.get("texto", ""), x, y, self.est, e.get("color"), e.get("rot", -6), clamp((t - e["_t"]) / 0.35), e.get("tam", 34))

    def geometria(self, e, t, previo, k_in):
        x, y, w, h, rot = K.caja_de(self.L, e.get("caja", "arriba"))
        if e.get("rot") is not None:
            rot = e["rot"]
        if e.get("_continua") and previo is not None:
            pe = next((q for q in previo["elementos"] if q.get("id") == e["id"]), None)
            if pe is not None:
                x0, y0, w0, h0, r0 = K.caja_de(self.L, pe.get("caja", "arriba"))
                if pe.get("rot") is not None:
                    r0 = pe["rot"]
                k = suave(clamp((t - self.planos[self.plano_en(t)]["_ini"]) / 0.45))
                x, y, w, h, rot = lerp(x0, x, k), lerp(y0, y, k), lerp(w0, w, k), lerp(h0, h, k), lerp(r0, rot, k)
        return x, y, w, h, rot

    def tarjeta(self, c, e, t, k_in, saliendo, previo):
        x, y, w, h, rot = self.geometria(e, t, previo, k_in)
        modo = e.get("entra", "sube")
        dx = dy = 0.0
        esc = 1.0
        alfa = 1.0
        giro = 0.0
        if k_in < 1:
            if modo == "sube":
                dy = (1 - sale(k_in)) * 160; alfa = clamp(k_in * 2.5)
            elif modo == "pop":
                esc = rebote(k_in)
            elif modo == "izq":
                dx = -(1 - sale(k_in)) * (x + w + 60)
            elif modo == "der":
                dx = (1 - sale(k_in)) * (self.W - x + 60)
            elif modo == "gira":
                giro = 90 * (1 - sale(k_in))
            elif modo == "fundido":
                alfa = k_in
        if saliendo > 0:
            modo_s = e.get("sale", "fundido")
            if modo_s == "izq":
                dx -= entra(saliendo) * (x + w + 60)
            elif modo_s == "der":
                dx += entra(saliendo) * (self.W - x + 60)
            elif modo_s == "baja":
                dy += entra(saliendo) * 200
            alfa *= 1 - saliendo
        if alfa <= 0.01:
            return
        # volteos
        cont, etq = e["contenido"], e.get("etiqueta")
        for v in e.get("voltear", []):
            if t >= v["_t"]:
                kv = clamp((t - v["_t"]) / 0.5)
                if kv < 0.5:
                    giro = max(giro, 180 * kv)
                else:
                    cont, etq = v["contenido"], v.get("etiqueta", etq)
                    giro = -180 * (1 - kv)
        cx, cy = x + w / 2, y + h / 2
        c.save()
        c.translate(cx + dx, cy + dy)
        c.rotate(rot)
        if esc != 1.0:
            c.scale(esc, esc)
        c.translate(-w / 2, -h / 2)
        if abs(giro) > 0.5:
            c.concat(matriz_giro_y(0, 0, w, h, giro))
        with Capa(c, alfa, (-60, -60, w + 120, h + 140)):
            inner = K.tarjeta_marco(c, 0, 0, w, h, self.est, radio=e.get("radio", 34), borde=e.get("borde", 10))
            ix, iy, iw, ih, ir = inner
            c.save()
            c.clipRRect(rrect(ix, iy, iw, ih, ir), True)
            self.contenido(c, cont, (ix, iy, iw, ih, ir), t)
            c.restore()
            if etq:
                K.etiqueta_tarjeta(c, etq, 0, 0, self.est, e.get("etiqueta_color"), tam=e.get("etiqueta_tam", 34 if self.formato == "9:16" else 30))
            for pg in e.get("pegatinas", []):
                if t >= pg["_t"]:
                    esq = pg.get("esquina", "abajo_der")
                    tam_pg = pg.get("tam", 32)
                    pw = K.ancho(pg.get("texto", ""), "extrabold", tam_pg) + tam_pg * 1.3
                    px = w - pw / 2 - 24 if "der" in esq else pw / 2 + 24
                    py = h - 6 if "abajo" in esq else 6
                    if pg.get("pos"):
                        px, py = pg["pos"][0] * w, pg["pos"][1] * h
                    K.pegatina(c, pg.get("texto", ""), px, py, self.est, pg.get("color"), pg.get("rot", -6),
                               clamp((t - pg["_t"]) / 0.35), tam_pg)
        c.restore()
        # geometría para las notas (sin giro ni rotación: aproximada)
        self.ctx["geo"][e["id"]] = dict(x=x + dx, y=y + dy, w=w, h=h, inner=inner, cont=cont)

    def contenido(self, c, cont, rect, t):
        ix, iy, iw, ih, ir = rect
        if "mundo" in cont:
            m = self.mundos[cont["mundo"]]
            s = max(iw / MW, ih / MH) * cont.get("zoom", 1.0)
            ox = ix + (iw - MW * s) / 2 + cont.get("desplaza", [0, 0])[0] * iw
            oy = iy + (ih - MH * s) / 2 + cont.get("desplaza", [0, 0])[1] * ih
            c.save(); c.translate(ox, oy); c.scale(s, s)
            m.dibujar(c, t, escala=s)
            c.restore()
        elif "prompt" in cont:
            K.contenido_prompt(c, rect, t, cont["prompt"], self.est, self.ctx)
        elif "codigo" in cont:
            K.contenido_codigo(c, rect, t, cont["codigo"], self.est, self.ctx)
        elif "gente" in cont:
            K.contenido_gente(c, rect, t, cont["gente"], self.est, self.ctx)
        elif "pasos" in cont:
            K.contenido_pasos(c, rect, t, cont["pasos"], self.est, self.ctx)
        elif "imagen" in cont:
            K.contenido_imagen(c, rect, t, cont["imagen"], self.est, self.ctx)
        elif "clip" in cont:
            K.contenido_clip(c, rect, t, cont["clip"], self.est, self.ctx)
        elif "texto" in cont:
            d = cont["texto"] if isinstance(cont["texto"], dict) else {"texto": cont["texto"]}
            K.contenido_texto(c, rect, t, d, self.est, self.ctx)
        else:
            K.contenido_vacio(c, rect, t, cont.get("vacio", {}) if isinstance(cont.get("vacio"), dict) else {}, self.est, self.ctx)

    def punto_tarjeta(self, ref, t):
        """Convierte {"tarjeta": id, "punto": [u, v]} o {"tarjeta": id, "actor": id} en píxeles del fotograma."""
        g = self.ctx["geo"].get(ref.get("tarjeta"))
        if not g:
            return None
        ix, iy, iw, ih, _ = g["inner"]
        if ref.get("actor") and "mundo" in g["cont"]:
            m = self.mundos[g["cont"]["mundo"]]
            uv = m.punto(ref["actor"], t)
            if not uv:
                return None
            s = max(iw / MW, ih / MH) * g["cont"].get("zoom", 1.0)
            ox = ix + (iw - MW * s) / 2
            oy = iy + (ih - MH * s) / 2
            return g["x"] + ox + uv[0] * MW * s, g["y"] + oy + uv[1] * MH * s
        u, v = ref.get("punto", [0.5, 0.5])
        return g["x"] + ix + u * iw, g["y"] + iy + v * ih

    def nota(self, c, e, t, saliendo):
        x, y = e.get("pos", [700, 1150])
        destino = e.get("apunta")
        tx = ty = None
        if isinstance(destino, dict):
            pt = self.punto_tarjeta(destino, t)
            if pt:
                tx, ty = pt
        elif isinstance(destino, list):
            tx, ty = destino
        with Capa(c, 1 - saliendo):
            hueco = None
            p_act = self.planos[self.plano_en(t)]
            if self.sub and p_act.get("subtitulos", True) is not False:
                sy = self.sub["y"] if not isinstance(p_act.get("subtitulos"), dict) else p_act["subtitulos"].get("y", self.sub["y"])
                hueco = (sy - self.sub["tam"] * 0.7, sy + self.sub["tam"] * 0.7)
            K.nota_mano(c, e.get("texto", ""), x, y, tx, ty, t, e["_t"], self.est, tam=e.get("tam", 50), color=e.get("color"),
                        curva=e.get("curva", 0.25), hueco=hueco)


# ------------------------------------------------------------------ revisión automática
def tiempos_elemento(e):
    """Todos los momentos en que entra algo de un elemento (para elegir bien el fotograma de muestra)."""
    ts = [e["_t"]]
    for it in e.get("items", []):
        ts.append(it.get("_t", e["_t"]))
        if it.get("_tachar") is not None:
            ts.append(it["_tachar"])
    for ln in e.get("lineas", []) if isinstance(e.get("lineas"), list) else []:
        if isinstance(ln, dict):
            ts.append(ln.get("_t", e["_t"]))
    for pg in e.get("pegatinas", []):
        ts.append(pg["_t"])
    for v in e.get("voltear", []):
        ts.append(v["_t"] + 0.5)
    cont = e.get("contenido") or {}
    if isinstance(cont.get("prompt"), dict):
        ts.append(cont["prompt"].get("_t1", e["_t"]))
    if isinstance(cont.get("gente"), dict):
        ts.append(cont["gente"].get("_t0", e["_t"]) + cont["gente"].get("dur", 1.6))
    if isinstance(cont.get("pasos"), dict):
        ts += [it.get("_t", e["_t"]) for it in cont["pasos"].get("items", [])]
    if e.get("tipo") == "contador":
        ts.append(e["_t"] + e.get("dur", 1.2))
    if e.get("tipo") in ("nota", "cta"):
        ts.append(e["_t"] + 1.0)
    hasta = e.get("_hasta", 1e9) - 0.25 if e.get("_hasta_propio") else 1e9
    return [min(x, hasta) for x in ts]


def _caja_elemento(E, e):
    """Rectángulo aproximado (x0, y0, x1, y1) de un elemento, o None."""
    tipo = e.get("tipo", "tarjeta")
    if tipo == "tarjeta":
        x, y, w, h, _ = K.caja_de(E.L, e.get("caja", "arriba"))
        return (x, y - 20, x + w, y + h + 6)
    if tipo == "pildoras":
        x, y, w, h = e.get("zona", E.L["extras"])
        tam = e.get("tam", 40)
        n = len(e.get("items", []))
        return (x, y, x + w, y + tam * 0.9 + n * tam * 1.85)
    if tipo == "contador":
        x, y = e.get("pos", [E.L["extras"][0] + E.L["extras"][2] / 2, E.L["extras"][1] + 120])
        tam = e.get("tam", 110)
        return (x - tam * 2.2, y - tam * 0.6, x + tam * 2.2, y + tam * 1.1)
    if tipo == "nota":
        x, y = e.get("pos", [700, 1150])
        tam = e.get("tam", 50)
        w = K.ancho(e.get("texto", ""), "mano", tam)
        return (x - w / 2, y - tam * 0.7, x + w / 2, y + tam * 0.7)
    if tipo == "movil":
        x, y, w = e.get("caja", [60, 220, 420])[:3]
        return (x, y, x + w, y + w * 2.05)
    return None


def _cruza(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def revisar(E):
    avisos = []
    sub_y = E.sub["y"] if E.sub else None
    for i, p in enumerate(E.planos):
        nombre = f"plano {i + 1}"
        dur = min(p["_fin"], E.dur) - p["_ini"]
        cajas = [(e, _caja_elemento(E, e)) for e in p["elementos"]]
        if sub_y is not None and p.get("subtitulos", True) is not False:
            sy = sub_y if not isinstance(p.get("subtitulos"), dict) else p["subtitulos"].get("y", sub_y)
            banda = (60, sy - E.sub["tam"] * 0.55, E.W - 60, sy + E.sub["tam"] * 0.55)
            for e, b in cajas:
                if b and _cruza(b, banda) and e.get("tipo") not in ("cta", "siguenos"):
                    avisos.append(f"{nombre}: «{e['id']}» ({e.get('tipo', 'tarjeta')}) puede pisar los subtítulos (y ≈ {sy}).")
        if E.masc and p.get("mascota") is not False:
            x, y, tam = E.pos_mascota(p)
            mb = (x - tam * 0.3, y - tam * 1.02, x + tam * 0.3, y)
            for e, b in cajas:
                if b and _cruza(b, mb) and e.get("tipo") not in ("cta", "siguenos"):
                    avisos.append(f"{nombre}: «{e['id']}» toca a la mascota.")
        if E.formato == "9:16" and dur > 1.8 and p.get("mascota") is not False:
            ex, ey, ew, eh = E.L["extras"]
            zona = (ex, ey, ex + ew, ey + eh)
            if not any(b and _cruza(b, zona) for e, b in cajas) and not any(e.get("tipo") in ("cta", "siguenos") for e in p["elementos"]):
                avisos.append(f"{nombre}: la zona de abajo (a la derecha de la mascota) está vacía {dur:.1f} s. Añade píldoras, un contador, una nota o una tarjeta pequeña.")
        for e, b in cajas:
            if b and (b[0] < -5 or b[2] > E.W + 5 or b[1] < (120 if E.formato == "9:16" else 10) or b[3] > E.H - 5) and e.get("tipo") != "tarjeta":
                avisos.append(f"{nombre}: «{e['id']}» se sale de la pantalla o queda muy arriba.")
    return avisos


# ------------------------------------------------------------------ salida
def guardar_png(surf, ruta):
    with open(ruta, "wb") as fh:
        fh.write(bytes(surf.makeImageSnapshot().encodeToData()))


def render_tramo(ruta_json, i0, i1, salida, cola=None):
    V = cargar(ruta_json)
    E = Escena(V)
    surf, info = nuevo_lienzo(E.W, E.H)
    c = surf.getCanvas()
    # pone al día los mundos antes del primer fotograma del tramo
    t_ini = i0 / FPS
    for m in E.mundos.values():
        m.avanzar(t_ini)
    cmd = [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{E.W}x{E.H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", salida]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        c.save()
        E.fotograma(c, i / FPS)
        c.restore()
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
        if cola is not None and (i - i0) % 15 == 0:
            cola.put(15)
    ff.stdin.close(); ff.wait()
    sonidos_mundo = []
    for m in E.mundos.values():
        sonidos_mundo += [(tt, n) for tt, n in m.sonidos if i0 / FPS <= tt < i1 / FPS]
    return sonidos_mundo


def _trabajo(args):
    ruta_json, i0, i1, salida, q = args
    return render_tramo(ruta_json, i0, i1, salida, q)


def visible_mundo(E, t):
    """Nombres de los mundos que se ven en el segundo t."""
    p = E.planos[E.plano_en(t)]
    vis = set()
    for e in p["elementos"]:
        if e.get("tipo", "tarjeta") == "tarjeta" and e["_t"] <= t < e["_hasta"]:
            cont = e["contenido"]
            for v in e.get("voltear", []):
                if t >= v["_t"] + 0.25:
                    cont = v["contenido"]
            if "mundo" in cont:
                vis.add(cont["mundo"])
    return vis


def mezclar_audio(E, sonidos_mundo, salida_wav, dur):
    sr = sonidos.SR
    voz = np.zeros(int(sr * dur), np.float32)
    if E.voz_wav and os.path.exists(E.voz_wav):
        with wave.open(E.voz_wav) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            if w.getframerate() != sr:
                idx = (np.arange(int(len(a) * sr / w.getframerate())) * w.getframerate() / sr).astype(int)
                a = a[np.minimum(idx, len(a) - 1)]
        if getattr(E, "corte_voz", None) is not None:
            n = int(E.corte_voz * sr)
            a = a[:n].copy()
            f = min(len(a), int(0.03 * sr))
            if f > 0:
                a[-f:] *= np.linspace(1, 0, f)
        voz[:min(len(voz), len(a))] = a[:len(voz)]
    ev = list(E.sonidos)
    if E.V.get("sonidos_mundo", True):
        ult = -9
        for tt, n in sorted(sonidos_mundo):
            if tt - ult < 0.35:
                continue
            ult = tt
            ev.append((tt, n))
    g = E.V.get("volumen_efectos", 1.0)
    fx = sonidos.pista(ev, dur, ganancia=0.9 * g) if g > 0 else np.zeros_like(voz)
    mezcla = voz + fx[:len(voz)]
    pico = np.max(np.abs(mezcla)) + 1e-6
    if pico > 0.98:
        mezcla = mezcla * (0.98 / pico)
    with wave.open(salida_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(mezcla, -1, 1) * 32767).astype(np.int16).tobytes())


def loudnorm(ent, sal):
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", ent, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    try:
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        f = ("loudnorm=I=-14:TP=-1.5:LRA=9:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
             % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]))
    except Exception:
        f = "loudnorm=I=-14:TP=-1.5:LRA=9"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", ent, "-af", f, "-ar", "48000", "-ac", "2", sal], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--muestras", action="store_true")
    ap.add_argument("--en", type=float)
    ap.add_argument("--desde", type=float)
    ap.add_argument("--hasta", type=float)
    ap.add_argument("--salida")
    ap.add_argument("--procesos", type=int, default=min(4, os.cpu_count() or 1))
    ap.add_argument("--sin-audio", action="store_true")
    a = ap.parse_args()
    ruta = os.path.abspath(a.video)
    V = cargar(ruta)
    E = Escena(V)
    carpeta = os.path.join(E.dir, "salida")
    os.makedirs(carpeta, exist_ok=True)
    base = os.path.splitext(os.path.basename(ruta))[0]

    if a.en is not None or a.muestras:
        surf, _ = nuevo_lienzo(E.W, E.H)
        c = surf.getCanvas()
        tiempos = [a.en] if a.en is not None else []
        if a.muestras:
            for p in E.planos:
                fin = min(p["_fin"], E.dur)
                ult = max([t_ for e in p["elementos"] for t_ in tiempos_elemento(e)] + [p["_ini"]])
                tiempos.append(min(fin - 0.08, max(p["_ini"] + 0.6, ult + 0.6)))
            avisos = revisar(E)
            for aviso in avisos:
                print("  AVISO:", aviso)
            if not avisos:
                print("  Sin avisos automáticos. Aun así, mira la hoja: los avisos no ven lo que se pisa dentro de una tarjeta.")
        imgs = []
        for t in tiempos:
            c.save(); E.fotograma(c, t); c.restore()
            if a.en is not None and not a.muestras:
                r = os.path.join(carpeta, (f"en_{t:.2f}.png" if base == "video" else f"{base}_en_{t:.2f}.png"))
                guardar_png(surf, r); print("Guardado:", r); return
            imgs.append((t, surf.makeImageSnapshot()))
        # hoja de muestras
        esc = 0.42 if E.formato == "9:16" else 0.46
        cols = 3 if E.formato == "9:16" else 2
        tw, th = int(E.W * esc), int(E.H * esc)
        filas = math.ceil(len(imgs) / cols)
        hoja = skia.Surface(cols * (tw + 16) + 16, filas * (th + 56) + 16)
        k = hoja.getCanvas(); k.clear(col("#FFFFFF"))
        for j, (t, im) in enumerate(imgs):
            fx, fy = 16 + (j % cols) * (tw + 16), 16 + (j // cols) * (th + 56)
            k.drawImageRect(im, skia.Rect(fx, fy + 40, fx + tw, fy + 40 + th), skia.SamplingOptions(skia.FilterMode.kLinear))
            texto(k, f"plano {j + 1} · {t:.1f} s", fx, fy + 20, "bold", 22, "#222222")
        r = os.path.join(carpeta, f"muestras_{base}.png" if base != "video" else "muestras.png")
        with open(r, "wb") as fh:
            fh.write(bytes(hoja.makeImageSnapshot().encodeToData()))
        print("Guardado:", r)
        return

    i0 = int((a.desde or 0) * FPS)
    i1 = min(E.nf, int((a.hasta * FPS) if a.hasta else E.nf))
    salida = a.salida or os.path.join(carpeta, f"{base}.mp4")
    tmp = tempfile.mkdtemp(prefix="render-", dir=carpeta)
    n = max(1, min(a.procesos, (i1 - i0) // 60 or 1))
    cortes = [i0 + (i1 - i0) * k // n for k in range(n + 1)]
    trozos = [os.path.join(tmp, f"trozo{k}.mp4") for k in range(n)]
    t_start = time.time()
    print(f"Renderizando {i1 - i0} fotogramas ({(i1 - i0) / FPS:.1f} s) con {n} proceso(s)…")
    sonidos_mundo = []
    if n == 1:
        sonidos_mundo = render_tramo(ruta, cortes[0], cortes[1], trozos[0])
    else:
        import multiprocessing as mp
        ctx = mp.get_context("fork")
        man = ctx.Manager()
        q = man.Queue()
        with ctx.Pool(n) as pool:
            res = pool.map_async(_trabajo, [(ruta, cortes[k], cortes[k + 1], trozos[k], q) for k in range(n)])
            hechos = 0
            ult = time.time()
            while not res.ready():
                res.wait(1.0)
                while not q.empty():
                    hechos += q.get()
                if time.time() - ult > 15:
                    v = hechos / max(1e-3, time.time() - t_start)
                    print(f"  {hechos}/{i1 - i0} fotogramas · {v:.1f} por segundo")
                    ult = time.time()
            for s in res.get():
                sonidos_mundo += s
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w") as fh:
        for tr in trozos:
            fh.write(f"file '{tr}'\n")
    video_mudo = os.path.join(tmp, "mudo.mp4")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video_mudo], check=True)
    if a.sin_audio:
        os.replace(video_mudo, salida)
    else:
        # solo suenan los mundos que se ven en ese momento
        sonidos_mundo = [(tt, n_) for tt, n_ in sonidos_mundo if any(True for _ in [0]) and visible_mundo(E, tt)]
        dur = (i1 - i0) / FPS
        wav = os.path.join(tmp, "mezcla.wav")
        E.sonidos = [(tt - i0 / FPS, n_) for tt, n_ in E.sonidos if i0 / FPS <= tt < i1 / FPS]
        sonidos_mundo = [(tt - i0 / FPS, n_) for tt, n_ in sonidos_mundo]
        if i0 > 0 and E.voz_wav:
            recorte = os.path.join(tmp, "voz_tramo.wav")
            subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", str(i0 / FPS), "-t", str(dur), "-i", E.voz_wav, recorte], check=True)
            E.voz_wav = recorte
            if E.corte_voz is not None:
                E.corte_voz -= i0 / FPS
        mezclar_audio(E, sonidos_mundo, wav, dur)
        wav2 = os.path.join(tmp, "mezcla_norm.wav")
        loudnorm(wav, wav2)
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", video_mudo, "-i", wav2, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", salida], check=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    mb = os.path.getsize(salida) / 1e6
    print(f"Listo: {salida} ({(i1 - i0) / FPS:.1f} s, {mb:.1f} MB, {time.time() - t_start:.0f} s de render)")
    if mb > 28:
        print("Aviso: pesa más de 28 MB. Para mandarlo por la app, recomprime: ffmpeg -i entrada.mp4 -c:v libx264 -crf 22 -c:a copy salida.mp4")


if __name__ == "__main__":
    main()
