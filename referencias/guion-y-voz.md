# Guion y voz

## guion.txt
- **Una frase por línea.** Cada línea suele ser un plano.
- 6–12 frases. En un reel, 30–45 s a 190–200 palabras por minuto (unas 100–150 palabras). En YouTube puede ser más largo: divide el guion en bloques y sigue la misma regla de una idea por frase.
- Las líneas que empiezan por `#` se ignoran. Las etiquetas de ElevenLabs (`[excited]`) también.
- Marca 1–2 **palabras clave por frase** entre asteriscos: `*25 millones*`, `*una sola frase:*`. La puntuación puede ir dentro. Un grupo de varias palabras no se parte entre dos líneas de subtítulos y su caja crece palabra a palabra.
- Escribe los números como se leen en pantalla (`25 millones`, `70 personas`).

## Estructura que funciona
1. **Gancho (0–3 s):** algo concreto y visual. Un número, una pregunta o una situación rara. «¿Por qué llueve? Te lo cuento en 30 segundos.»
2. **Explicación:** una idea por frase, cada una con su imagen literal (si dice «vapor», se ve el vapor).
3. **Remate:** un giro gracioso o una frase que resume.
4. **Llamada a la acción:** «Comenta PALABRA y te mando…» o «Sígueme para más».

Tono: cercano, de tú, frases cortas. Lo que se explica tiene que ser correcto: si dudas de un dato, búscalo o quítalo.

## Voz con ElevenLabs (si el usuario la usa)
Dale el guion con etiquetas de emoción en inglés al principio de cada frase:
```
[excited] ¿Por qué llueve? Te lo cuento en 30 segundos.
[curious] El sol calienta el agua del mar... y la convierte en vapor.
[confident] Comenta LLUVIA y te paso más ciencia así.
```
- Etiquetas útiles: `[excited]`, `[confident]`, `[curious]`, `[playfully]`, `[mischievously]`, `[impressed]`, `[whispers]`. Sin risas ni suspiros (alargan las pausas).
- Palabras extranjeras: escríbelas como se pronuncian en el texto para la voz (por ejemplo, «Clod» para Claude) y déjalas bien escritas en `guion.txt`.
- Que descargue MP3 o WAV y te lo pase.

## alinear.py
```bash
python3 scripts/alinear.py --guion P/guion.txt --voz voz.mp3 --salida P/voz --idioma es
```
- `--pausa-max 0.26`: recorta las pausas más largas (por defecto 0,26 s).
- `--velocidad 1.05`: acelera un 5 % sin cambiar el tono, si la voz va lenta (menos de 185 palabras por minuto).
- `--sin-voz --ppm 195`: sin audio, estima los tiempos (195 por defecto).
- `--sin-recorte`: no toca las pausas (para «deja mi voz como está»). `--formato youtube`: sin consejos pensados para reels.
- Deja `voz_final.wav` (−14 LUFS) y `palabras.json` (cada palabra con su inicio y fin).
- Si el reconocimiento de voz no se puede instalar o descargar, reparte las palabras por los tramos con voz (menos preciso) y avisa.

## Dos finales con una sola voz
El usuario genera dos audios: el guion completo con el final de Instagram y, aparte, solo la frase final de TikTok, con la misma voz.
1. Alinea el audio completo → `P/voz`.
2. Corta el audio justo antes de la última frase (mira su `ini` en `P/voz/palabras.json` → `frases`) y pega el final de TikTok con 0,12 s de silencio:
   ```bash
   ffmpeg -y -i P/voz/voz_final.wav -t <ini de la última frase − 0.05> -ar 48000 -ac 1 P/cuerpo.wav
   ffmpeg -y -f lavfi -i anullsrc=r=48000:cl=mono -t 0.12 P/silencio.wav
   ffmpeg -y -i P/cuerpo.wav -i P/silencio.wav -i final_tiktok.mp3 -filter_complex "[2:a]aresample=48000,aformat=channel_layouts=mono[f];[0:a][1:a][f]concat=n=3:v=0:a=1" P/voz_tiktok.wav
   ```
3. Copia `guion.txt` a `guion_tiktok.txt` cambiando la última línea y alinea `P/voz_tiktok.wav` con `--salida P/voz_tiktok`.
