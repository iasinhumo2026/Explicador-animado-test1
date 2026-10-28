---
name: explicador-animado
description: Vídeos explicativos animados con personajes con cara, hechos con código a partir de un tema. Guion, voz con subtítulos, escenas, portada y textos, en vertical u horizontal.
---

# explicador-animado

Hace vídeos animados de divulgación: personajes con cara y carácter (células, planetas, gotas, monstruos, personas) que actúan solos dentro de tarjetas, con subtítulos palabra a palabra, una mascota que mueve la boca con la voz, píldoras, notas a mano, contadores y una llamada a la acción final.

- **Formatos:** 1080×1920 (reels, TikTok, Shorts) o 1920×1080 (YouTube), a 30 fps.
- **Todo con código:** Python + Skia (dibujo vectorial) + ffmpeg. Sin generar imágenes ni vídeo con IA, sin navegador y sin herramientas de pago.
- **Lo que hace el usuario:** el tema y, si quiere, su voz. **Lo que haces tú:** guion, personajes, mundos, plan, render, portada y textos.

## Antes de empezar
1. Copia la skill a una carpeta de trabajo (la carpeta de la skill es de solo lectura) y comprueba el entorno:
   ```bash
   mkdir -p ~/explicador && cp -r <carpeta de esta skill>/. ~/explicador/ && chmod -R u+w ~/explicador && cd ~/explicador && python3 scripts/comprobar.py
   ```
   Si algo sale con ✗, arréglalo antes de seguir; la comprobación instala lo que puede (skia-python, numpy, pillow). Si `~` no se puede escribir, usa otra carpeta de trabajo que sí (los comandos van siempre desde ella).
2. Crea una carpeta por vídeo: `~/explicador/proyectos/<tema>/`. Todos los comandos se lanzan desde `~/explicador`.
3. **¿Primera vez?** Haz el ejemplo («¿Por qué llueve?», 20 s, sin voz) para ver que todo funciona (1 minuto más o menos):
   ```bash
   mkdir -p proyectos && cp -r ejemplo proyectos/prueba
   python3 scripts/alinear.py --guion proyectos/prueba/guion.txt --sin-voz --salida proyectos/prueba/voz
   python3 scripts/render.py proyectos/prueba/video.json
   ```

## El trabajo, paso a paso

### 1. Qué pide el usuario
Pregunta solo lo que falte, en un único mensaje:
- **Tema** (una frase basta: «anima cómo se defiende el cuerpo de una bacteria»).
- **Formato:** vertical (reel) u horizontal (YouTube).
- **Voz:** si tiene un audio, si quiere el texto para generarla (por ejemplo, en ElevenLabs) o si lo quiere sin voz.
- **Palabra para comentar**, si quiere un final «Comenta PALABRA». Si no, el final es «sígueme».
- **Idioma** del vídeo, si no es español (`"idioma": "en"` en `video.json` cambia los textos fijos y los números).
- **Mascota** (opcional): una persona con su pelo, piel y ropa (`referencias/personajes.md` → «humano»).

Si no contesta, sigue con lo razonable (vertical, sin voz, estilo `crema`, mascota humana neutra) y dilo.

### 2. Guion → `referencias/guion-y-voz.md`
- `guion.txt`: **una frase por línea**, 6–12 frases, unas 190–200 palabras por minuto (30–45 s en un reel). **Sin voz**, mejor 165–175 (`--sin-voz --ppm 170`): la gente tiene que leer los subtítulos.
- Estructura: gancho con algo concreto (un número, una pregunta, una imagen rara) → explicación por pasos, con una idea por frase → remate → llamada a la acción.
- Marca entre `*asteriscos*` las palabras clave: salen en una caja de color en los subtítulos y hacen saltar a la mascota. Una o dos por frase.
- Si la voz sale de ElevenLabs, dale también el texto con etiquetas de emoción.

### 3. Voz y tiempos
```bash
python3 scripts/alinear.py --guion P/guion.txt --voz audio.mp3 --salida P/voz --idioma es   # con voz
python3 scripts/alinear.py --guion P/guion.txt --sin-voz --salida P/voz                     # sin voz
```
- Recorta las pausas largas, deja la voz a −14 LUFS y saca el tiempo de cada palabra con Whisper (la primera vez descarga unos 240 MB).
- Si el usuario pide no tocar su voz, añade `--sin-recorte` (y no uses `--velocidad`). Para YouTube, `--formato youtube`.
- Si salen menos del 80 % de palabras reconocidas, el guion no es lo que dice la voz: corrígelo y repite.

### 4. Personajes y mundos → `referencias/personajes.md` y `referencias/mundos.md`
- **Personajes:** 18 formas (gota, cápsula, fantasma, virus, nube, planeta, hoja, flor, volcán, humano…), 13 caras, 17 accesorios, patas, alas y trompa, detalles y colores. La mascota también puede ser un personaje no humano (un robot, una gota…). Diseña los del tema: una bacteria verde con flagelos y cara pícara, un macrófago con babero, un neutrófilo con casco y lanza…
- **Mundos:** el escenario que sale dentro de las tarjetas, con un fondo (vaso sanguíneo, mar, cielo, espacio…), partículas y actores que **actúan solos**: enjambres que nadan hacia un objetivo, defensores que comen, golpean o disparan, planetas que orbitan y acciones a tiempo de la voz (cambiar de cara, saltar, moverse, bocadillos).
- **Personajes originales siempre:** no copies personajes, escenas ni estilos reconocibles de otros canales, películas o marcas.

### 5. Plan del vídeo → `referencias/plan.md`
Escribe `P/video.json`, copiando la estructura de `ejemplo/video.json`:
- **Un plano por frase** (`"frase": n`, contando desde 1). Si una frase es larga, pártela con otro plano que empiece en una palabra (`"en": "palabra"`).
- **Cada plano tiene una tarjeta principal** (un mundo, el prompt que se escribe solo, código, gente, pasos o una imagen) y **algo en la zona de abajo**, a la derecha de la mascota: píldoras, un contador, una tarjeta pequeña o una nota a mano.
- **Algo nuevo cada 1–1,5 s:** usa `"en": "palabra"` para que cada elemento entre justo cuando se dice.
- **Mismo elemento en dos planos seguidos** (mismo `id`, sin `"en"`): no vuelve a entrar y conserva lo que ya salió; una tarjeta se desliza a su nuevo sitio. Úsalo para que un mundo o unas píldoras sigan mientras cambia lo demás.
- **Dos finales** (Instagram «comenta» y TikTok «sígueme»): un segundo `video.json` con `"hereda"`, con otra voz final o con un final sin voz (ver «Dos finales» en `plan.md`).
- **Trozos de un vídeo o capturas del usuario:** contenidos `clip` e `imagen` (solo si el usuario los aporta y tiene derecho a usarlos, por ejemplo para citar y comparar).

### 6. Revisar y renderizar
```bash
python3 scripts/render.py P/video.json --muestras      # un fotograma por plano → P/salida/muestras.png
python3 scripts/render.py P/video.json --en 12.5       # un fotograma concreto
python3 scripts/render.py P/video.json                 # vídeo → P/salida/video.mp4
python3 scripts/ritmo.py P/salida/video.mp4            # avisa si algo se queda quieto más de 0,6 s
python3 scripts/portada.py P/video.json                # portada + cómo se ve recortada en la cuadrícula 3:4
```
- **Mira `muestras.png` con la herramienta de leer imágenes antes del render completo** (cada plano sale cuando ya ha entrado todo). Revisa que nada se pise, que los textos quepan, que se lean los subtítulos y que la zona de abajo no esté vacía. `--muestras` también escribe avisos automáticos (cosas que pisan los subtítulos o la mascota, zonas vacías, caracteres que no existen en la fuente): arréglalos todos.
- Si algo no cuadra en un plano, saca ese segundo con `--en` y ajusta `caja`, `pos` o `tam`.
- El render va a unos 12–25 fotogramas por segundo con 2 núcleos en vertical (un reel de 40 s tarda 1–2 minutos) y a unos 7–10 en horizontal.

### 7. Entrega → `referencias/publicar.md`
- Manda al usuario el vídeo y la portada, y escríbele el texto de Instagram y el de TikTok (o el título y la descripción de YouTube).
- Si la voz es sintética, recuérdale marcar el vídeo como contenido hecho con IA.
- Si el vídeo dice «comenta PALABRA», pregúntale qué va a mandar a quien comente.

## Reglas
- No inventes datos ni cifras en el guion: lo que se explica tiene que ser correcto. Si el usuario da un dato, úsalo tal cual. Si un dato puede haber cambiado, compruébalo.
- No uses logos, personajes ni capturas de otros dentro del vídeo salvo que el usuario las aporte; nombra las marcas solo como texto. No redibujes escenas ni personajes de otros canales o películas, aunque te lo pidan: crea los tuyos.
- Sin emojis ni símbolos raros dentro del vídeo (las fuentes no los tienen y salen cuadraditos). En los textos para publicar, sí.
- Los subtítulos, la tarjeta principal y la mascota no se pisan. Las muestras lo enseñan: míralas siempre.
- Si algo falla, mira `referencias/problemas.md` antes de improvisar.

## Archivos
- `scripts/`: `comprobar.py`, `alinear.py`, `render.py` (motor), `kit.py` (tarjetas, píldoras, notas, subtítulos…), `personajes.py`, `mundo.py`, `sonidos.py` (efectos sintetizados), `ritmo.py`, `portada.py` y `comun.py` (estilos y utilidades).
- `referencias/`: `guion-y-voz.md`, `plan.md`, `personajes.md`, `mundos.md`, `publicar.md` y `problemas.md`.
- `ejemplo/`: proyecto completo («¿Por qué llueve?»).
- `fuentes/`: Poppins, Caveat, Lora y JetBrains Mono, con licencia OFL.
