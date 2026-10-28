# Problemas y soluciones

| Problema | Solución |
| --- | --- |
| `comprobar.py` no puede instalar skia-python | Prueba `pip install --break-system-packages skia-python` o `pip install --user skia-python`. Necesita Python 3.9+ de 64 bits (Linux, Mac o Windows) |
| `Permission denied` al escribir | La copia conserva los permisos de solo lectura de la skill: `chmod -R u+w ~/explicador` (ya va en el comando de SKILL.md y `comprobar.py` lo arregla). Si estás dentro de la carpeta de la skill, copia antes la skill a `~/explicador` |
| `Fontconfig warning … unknown element "reset-dirs"` | Es un aviso del sistema, no de la skill: ignóralo |
| Un texto sale con cuadraditos | Ese carácter no existe en las fuentes (flechas como «→», emojis). El render avisa: cámbialo por texto |
| `ritmo.py` dice «subtitulos quieta X s» pero OK | Normal en los planos sin subtítulos (el final). Lo que importa es la última línea |
| La versión de TikTok falla con una palabra del final | Usa `"cambia_desde_frase"` en `tiktok.json`: los planos, poses y acciones que dependían del final cambiado se ignoran solos |
| «La palabra X no aparece en el guion» | Revisa el `"en"`: tiene que ser una palabra de `guion.txt` que se diga después de que empiece el plano. Para la segunda vez, `X#2` |
| «La frase N no existe» | Las frases se cuentan desde 1 y son las líneas de `guion.txt` que no están vacías |
| Palabras reconocidas por debajo del 80 % | El guion no coincide con la voz. Corrige `guion.txt` para que diga lo mismo (los números como se dicen) y vuelve a alinear |
| No se descarga el modelo de voz | Sin conexión a Hugging Face, `alinear.py` lo baja de npm. Si tampoco hay npm, reparte las palabras por los tramos con voz (avisa). El vídeo sale igual, con subtítulos algo menos exactos |
| Los subtítulos van antes o después de la voz | Vuelve a alinear (el guion cambió y `palabras.json` es viejo) |
| Algo se pisa (tarjeta, subtítulos, mascota) | Mira `muestras.png`. Mueve la tarjeta con `caja` (o elige otra), baja la tarjeta pequeña o usa `"subtitulos": {"y": …}` en ese plano |
| La zona de abajo está vacía | Añade píldoras, un contador, una nota o una `tarjeta` con `"caja": "pequena_der"` |
| Una etiqueta del mundo sale cortada | Las tarjetas recortan un poco los lados del escenario: deja 0,06 de margen |
| `ritmo.py` avisa de un tramo quieto | En ese segundo, añade algo con `"en"` (una píldora, una pegatina, una acción del mundo) |
| El render va lento | Normal con mundos llenos: 12–25 fotogramas por segundo con 2 núcleos. Menos miembros en los enjambres, menos partículas y sin `camara` lo aceleran. Para revisar, renderiza un tramo con `--desde` y `--hasta` |
| El vídeo pesa más de 28 MB | `ffmpeg -i video.mp4 -c:v libx264 -crf 22 -preset veryfast -c:a copy video_ligero.mp4` |
| El usuario quiere un personaje famoso o de otro canal | No lo copies: propón uno original con la misma idea (por ejemplo, «una bacteria gruñona con flagelos» en vez de un personaje conocido) |
