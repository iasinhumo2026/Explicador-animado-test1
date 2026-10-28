# explicador-animado · guía rápida

Skill para Claude que hace **vídeos explicativos animados** con personajes con cara y carácter, todo con código: guion, voz con subtítulos, escenas que se animan solas, mascota que habla, portada y textos para publicar. En vertical (reels, TikTok, Shorts) o en horizontal (YouTube).

Versión 1.2 · 28-10-2026 · hecha por @elbecariodemurphy.ia

## Instalar
1. En Claude, activa **Ajustes → Capacidades → Ejecución de código y creación de archivos**.
2. Ve a **Personalizar → Skills → + → Crear skill → Subir una skill** y sube este ZIP tal cual.
3. Activa la skill en la lista.

Funciona en todos los planes de Claude, también el gratis, siempre que tenga la ejecución de código. Un vídeo completo usa bastante uso del plan: en el gratis puede que tengas que hacerlo en dos tandas.

## Probar
Escríbele a Claude:
> Usa la skill explicador-animado y haz el vídeo de ejemplo.

Después, con un tema tuyo:
> Usa la skill explicador-animado: anima cómo se defiende el cuerpo de una bacteria. Vertical, sin voz.

Si tienes tu voz (grabada o de ElevenLabs), pídele primero el guion, genera el audio y pásaselo.

## Qué hace
- Escribe el guion (una idea por frase) y, si quieres, el texto con emociones para ElevenLabs.
- Alinea tu voz palabra a palabra y monta subtítulos con las palabras clave en caja de color.
- Diseña personajes originales (células, planetas, plantas, insectos, volcanes, monstruos, personas) con 13 caras y 17 accesorios.
- Monta mundos que se animan solos: enjambres, defensores que comen o disparan, planetas que orbitan…
- Añade tarjetas, prompts que se escriben solos, contadores, listas tachadas, notas a mano y el final «Comenta PALABRA».
- Controla el ritmo, hace la portada y te escribe los textos para Instagram, TikTok o YouTube.

## Si algo falla
Dile a Claude «mira referencias/problemas.md». Lo más común: la ejecución de código está apagada, o el guion no coincide con lo que dice tu voz.

## Licencias
- Fuentes Poppins, Caveat, Lora y JetBrains Mono: SIL Open Font License (OFL), uso comercial permitido.
- skia-python (BSD), numpy (BSD), ffmpeg (LGPL/GPL, se usa como programa aparte).
- Reconocimiento de voz: faster-whisper y el modelo Whisper small de OpenAI (MIT). Si no se puede bajar de Hugging Face, se baja de una copia en npm y se comprueba su huella sha256 antes de usarlo.
- Personajes, efectos de sonido y ejemplo: propios, libres para tus vídeos.
