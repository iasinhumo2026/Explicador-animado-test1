# Cambios

## v1.2 · 28-10-2026
- Formas `volcan` y `montana`; insectos con `patas`, `alas` y `trompa` (que se alarga con la acción `estira`).
- El humano dibuja `gafas`, `bigote` y `auriculares`, y avisa si un accesorio no sale.
- Enjambres en `flujo` continuo y `franjas` de color en los mundos (vasos sanguíneos, capas, ríos).
- Bocadillos con tamaño propio y siempre dentro del escenario.
- Final `siguenos` con `icono` (corazón, campana o cualquier icono de `pasos`) para YouTube.
- Caja `vertical_der` para vídeos verticales y maqueta horizontal en la que nada pisa a la mascota; muestras horizontales más grandes.
- Portada con `personaje_pos`; las muestras dicen cuándo no hay avisos.
- Documentación: `mkdir -p proyectos` en el ejemplo, ritmo sin voz (165–175 palabras por minuto), velocidad de render en horizontal, etiquetas (`texto_color`), `pos` de los humanos en los mundos y todas las opciones de `clip`.

## v1.1 · 28-10-2026
- Copia con permisos de escritura (`chmod -R u+w`) y `comprobar.py` los arregla si hace falta.
- Muestras en el momento en que ya ha entrado todo, más grandes, y avisos automáticos: cosas que pisan los subtítulos o la mascota, zonas de abajo vacías, textos que se salen y caracteres que no existen en la fuente.
- Continuidad real: un elemento con el mismo `id` en el plano siguiente conserva sus tiempos y no repite sonidos.
- Dos finales más fiables: `hereda` coloca bien los planos con `"en"`, ignora poses y acciones del final cambiado y admite un final sin voz (`voz_hasta_frase`).
- `"idioma"`: textos fijos y números en español, inglés, portugués, francés, italiano o alemán; `titulo` en el final «Comenta».
- Subtítulos que no parten un grupo de palabras clave; la caja crece palabra a palabra.
- `alinear.py --sin-recorte` (no toca la voz) y `--formato youtube`.
- Contenido `clip`: trozos de un vídeo del usuario dentro de una tarjeta.
- Personajes: formas `hoja`, `flor` y `maceta`; peinados `melena`, `coleta` y `mono`; pestañas y falda; accesorios `gorro_chef`, `antena` y `tornillos`; brillo correcto en el pelo oscuro.
- Mascotas no humanas colocadas por los pies y a su tamaño.
- Etiquetas de mundo más grandes, con `hasta`, dentro del escenario y que se esconden cuando su actor se va.
- `pasos` con icono encima del texto en casillas estrechas; píldoras, finales y notas que se ajustan al ancho; flecha de las notas que no tacha los subtítulos.
- Rejilla de `gente` centrada, portada horizontal alineada, maqueta horizontal nueva y prompt con aspecto de chat.

## v1.0 · 28-10-2026
- Primera versión: motor Skia + ffmpeg en vertical (1080×1920) y horizontal (1920×1080).
- 13 formas de personaje, 13 caras, 14 accesorios y humano chibi con 4 peinados y 10 poses.
- Mundos con 10 fondos, 7 tipos de partículas, enjambres, comer, golpear, disparar, órbitas y acciones a tiempo de la voz.
- Tarjetas con mundo, prompt, código, gente, pasos, imagen o texto; volteo 3D, pegatinas y continuidad entre planos.
- Píldoras con tachado y ✓, notas a mano con flecha, contador, titular, llamada a la acción y «sígueme».
- Subtítulos palabra a palabra con palabras clave en caja de color, mascota que habla con la voz.
- Alineado de voz con Whisper, efectos sintetizados, control de ritmo, portada con recorte 3:4 y dos finales.
