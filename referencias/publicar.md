# Portada, textos y entrega

## Portada
`"portada"` en `video.json` y `python3 scripts/portada.py P/video.json`:
```json
"portada": {"etiqueta": "CIENCIA EN 30 S", "lineas": ["¿POR QUÉ", "LLUEVE?"], "clave": 1, "remate": "te lo explico animado",
            "mundo": "ciclo", "segundo": 12.0, "personaje": "presentadora", "pose": "senala_arriba", "cara": "sorpresa",
            "pegatina": "0 dibujos a mano"}
```
- Título de 2–3 líneas cortas (≤ 16 letras por línea); `clave` es la línea que va en la caja de color.
- `segundo`: el momento del mundo que sale en la tarjeta (elige uno con mucha acción).
- Mira `salida/portada_recorte.png`: es lo que se ve en la cuadrícula del perfil (3:4). Título y cara tienen que caber.
- La portada no promete más de lo que enseña el vídeo.
- Al publicar: en Instagram, «Editar portada» → elegir de la galería; en TikTok, se elige antes de publicar (después no se puede cambiar).

## Textos para publicar
**Instagram** (lo que se ve antes de «más» es la primera línea):
```
<gancho en primera persona, con el tema> 🧪
<2–4 líneas: qué se aprende, con un emoji cada una>
<llamada a la acción: «Comenta PALABRA y te lo mando por privado» o «Guárdalo para luego»>
#hashtag1 #hashtag2 #hashtag3   (como mucho 5)
```
**TikTok:** la primera línea (unos 100 caracteres) con lo que la gente busca («por qué llueve explicado fácil»), luego 2–3 líneas y 3–5 hashtags.
**YouTube (horizontal):** título de menos de 60 caracteres y descripción con un resumen. Capítulos (minuto:segundo por bloque) solo si el vídeo tiene al menos 3 bloques de 10 s o más, que es lo que pide YouTube.
- En YouTube no hay mensaje automático a quien comenta: si el final dice «comenta PALABRA», el usuario tiene que contestar a mano o poner el enlace en un comentario fijado o en la descripción. Avísale.
- Si te piden la versión de TikTok de un vídeo horizontal, recomienda un plan vertical aparte (los mismos mundos y personajes, otras cajas).

## Etiqueta de IA
Si la voz es sintética (ElevenLabs u otra), recomienda marcar el vídeo como hecho con IA: en Instagram, «Añadir etiqueta de IA»; en TikTok, «Más opciones» → «Contenido generado por IA»; en YouTube, «Contenido alterado o sintético» si la voz suena real.

## Música
El vídeo sale con voz y efectos, sin música. La música se pone al publicar, desde la biblioteca de cada app.

## Antes de mandarlo
- `ritmo.py` dice OK.
- Has mirado el vídeo en 3–4 momentos con `--en` (o la hoja de muestras).
- El archivo pesa menos de 28 MB (si no, el render dice cómo recomprimirlo).
- Si el vídeo dice «comenta PALABRA», pregunta al usuario qué va a mandar a quien comente.
