#!/usr/bin/env python3
"""Comprueba que el ordenador tiene lo necesario y lo instala si falta.

Uso:  python3 comprobar.py
"""
import importlib, os, subprocess, sys

ok = True


def instala(paquete):
    for extra in (["--break-system-packages"], []):
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *extra, paquete], capture_output=True, text=True)
        if r.returncode == 0:
            return True
    return False


print(f"Python {sys.version.split()[0]}")
if sys.version_info < (3, 9):
    print("  ✗ Hace falta Python 3.9 o más nuevo."); ok = False
for mod, pkg in (("numpy", "numpy"), ("skia", "skia-python"), ("PIL", "pillow")):
    try:
        m = importlib.import_module(mod)
        print(f"  ✓ {pkg} {getattr(m, '__version__', '')}")
    except ImportError:
        print(f"  … instalando {pkg} (una sola vez)")
        if not instala(pkg):
            print(f"  ✗ No se pudo instalar {pkg}."); ok = False
        else:
            try:
                importlib.import_module(mod)
                print(f"  ✓ {pkg} instalado")
            except ImportError as e:
                print(f"  ✗ {pkg} instalado pero no se puede abrir: {e}"); ok = False
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import skia
    from comun import FFMPEG, fuente, nuevo_lienzo
    r = subprocess.run([FFMPEG, "-version"], capture_output=True, text=True)
    print("  ✓ ffmpeg:", r.stdout.split("\n")[0][:60])
    tiene_x264 = "libx264" in subprocess.run([FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    print("  ✓ codificador H.264" if tiene_x264 else "  ✗ ffmpeg sin libx264"); ok = ok and tiene_x264
    for p in ("black", "mano", "mono", "cursiva"):
        fuente(p, 40)
    s, _ = nuevo_lienzo(64, 64)
    s.getCanvas().clear(skia.Color(255, 0, 0))
    print("  ✓ fuentes (Poppins, Caveat, Lora y JetBrains Mono) y dibujo con Skia")
except SystemExit as e:
    print("  ✗", e); ok = False
except Exception as e:  # noqa: BLE001
    print("  ✗ Skia no funciona en este ordenador:", str(e)[:200]); ok = False
try:
    import faster_whisper  # noqa: F401
    print("  ✓ faster-whisper (reconocimiento de voz)")
except ImportError:
    print("  · faster-whisper no está: alinear.py lo instalará si hay voz (sin voz no hace falta).")
print(f"  · núcleos: {os.cpu_count()} (el render usa hasta 4 a la vez)")
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.access(raiz, os.W_OK):
    try:
        subprocess.run(["chmod", "-R", "u+w", raiz], check=True)
        print("  ✓ permisos de escritura arreglados en", raiz)
    except Exception:  # noqa: BLE001
        print(f"  ✗ No puedo escribir en {raiz}. ¿Es la carpeta de la skill? Copia la skill a otra carpeta y haz chmod -R u+w."); ok = False
else:
    print("  ✓ la carpeta de trabajo se puede escribir")
print("  · Si ves «Fontconfig warning … reset-dirs», ignóralo: es del sistema y no afecta.")
print("TODO LISTO" if ok else "FALTA ALGO: mira los ✗ de arriba.")
sys.exit(0 if ok else 1)
