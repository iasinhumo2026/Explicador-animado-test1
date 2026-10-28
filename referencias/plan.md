# video.json: el plan del vídeo

Copia `ejemplo/video.json` y cámbialo. Este documento explica cada parte.

## Estructura general
```json
{
  "formato": "9:16",                  // "9:16" (1080×1920) o "16:9" (1920×1080)
  "idioma": "es",                     // es, en, pt, fr, it, de: cambia «Comenta», «Sígueme», «personas», los textos del chat y los separadores de los números
  "estilo": "crema",                  // crema, noche, menta, lavanda, limon, o un objeto (ver «Estilo»)
  "linea": "#1D1B2E",                 // color del contorno de todos los personajes (opcional)
  "voz": "voz",                       // carpeta que dejó alinear.py (con palabras.json)
  "cola": 1.2,                        // segundos que sigue el vídeo después de la última palabra
  "duracion": 40,                     // opcional: fuerza la duración total (si no, voz + cola)
  "personajes": { ... },              // referencias/personajes.md
  "mundos": { ... },                  // referencias/mundos.md
  "mascota": { ... },                 // opcional, ver «Mascota»
  "subtitulos": {"y": 1000, "tam": 64},   // o false para quitarlos
  "volumen_efectos": 1.0,             // 0 = sin efectos de sonido
  "sonidos_mundo": true,              // bocados, golpes y disparos de los mundos (suaves)
  "planos": [ ... ],
  "portada": { ... }                  // referencias/publicar.md
}
```

## Tiempos: el campo «en»
Casi todo lleva `"en"` para entrar justo cuando la voz lo dice:
| Valor | Significa |
| --- | --- |
| `"bacteria"` | cuando empieza esa palabra (la primera vez desde que empieza el plano) |
| `"25 millones"` | varias palabras seguidas |
| `">bacteria"` | cuando **acaba** esa palabra |
| `"bacteria#2"` | la segunda vez que sale |
| `"bacteria+0.3"`, `"bacteria-0.2"` | con un margen en segundos |
| `"frase 3"`, `"fin frase 3"` | principio o final de la frase 3 (se cuentan desde 1) |
| `"+0.8"` | 0,8 s después de que empiece el plano |
| `4.2` | segundo exacto del vídeo |

Las palabras se comparan sin tildes, mayúsculas ni signos. Si una palabra no está en el guion, el render lo dice.
Dentro de los mundos, la palabra se busca desde el principio del vídeo (usa `#2` si se repite).

## Planos
```json
{"frase": 3, "elementos": [ ... ]}
{"en": "canal", "elementos": [ ... ]}             // plano que empieza a mitad de frase
{"frase": 9, "mascota": false, "elementos": [ ... ]}          // esconde la mascota en este plano
{"frase": 4, "antes": 0.12, "elementos": [ ... ]}             // el plano empieza 0,12 s antes de la frase (por defecto)
{"frase": 11, "subtitulos": false, "mascota": {"x": 540, "y": 1760, "tam": 600, "pose": "saluda"}, "elementos": [ ... ]}
```
- Un plano dura hasta que empieza el siguiente. Al cambiar, lo que no sigue sale con un fundido corto.
- **Continuidad:** si el plano siguiente tiene un elemento con el **mismo `id`** y sin `"en"`, no vuelve a entrar y **conserva sus tiempos** (las píldoras que ya salieron siguen ahí y no vuelven a sonar). Las tarjetas se deslizan de su caja vieja a la nueva. Así un mundo sigue animándose mientras cambia el resto.
- Lo que entra con la **última palabra de una frase** dura poco: el plano siguiente empieza 0,12 s antes de la frase siguiente. Mejor que entre una o dos palabras antes.
- `"subtitulos": {"y": 1150}` mueve los subtítulos solo en ese plano.

## Cajas (dónde va cada tarjeta)
`"caja"` acepta un nombre o `[x, y, ancho, alto, giro]` en píxeles del fotograma.

**Vertical (9:16).** Zona de la tarjeta principal: y 200–900. Subtítulos: y ≈ 1000. Zona de abajo libre: x 400–1000, y 1095–1535 (a la izquierda está la mascota, de y 1160 a 1700).
| Nombre | x, y, ancho, alto, giro | Para qué |
| --- | --- | --- |
| `grande` | 36, 200, 1008, 700, 0 | gancho, momentos fuertes |
| `arriba` | 60, 230, 960, 620, 0 | la tarjeta normal |
| `arriba_izq` + `abajo_der` | 36, 200, 780, 470, −3 · 264, 482, 780, 470, 2,5 | dos tarjetas apiladas: «antes / ahora», «el suyo / el mío» |
| `mitad_izq` / `mitad_der` | 36, 330, 492, 520, −2 · 552, 330, 492, 520, 2 | dos tarjetas lado a lado |
| `pequena_der` | 410, 1100, 600, 400, 2 | tarjeta pequeña en la zona de abajo |
| `centro`, `baja`, `pequena_izq` | ver `kit.py` → LAYOUTS | |

**Horizontal (16:9).** Tarjeta `arriba`: 300, 50, 1150, 730 (`grande`: 290, 30, 1340, 790; `vertical_der`: 1480, 60, 400, 711 para un vídeo vertical). Ninguna caja pisa a la mascota. Subtítulos abajo (y ≈ 950). Mascota abajo a la izquierda (x ≈ 125). Zona libre a la derecha: x 1470–1880, y 140–780, para píldoras (`"zona": [1490, 200, 400, 420]`), un contador (`"pos": [1680, 420]`) o una tarjeta `pequena_der`. Comparaciones: `arriba_izq` + `abajo_der` o `mitad_izq` + `mitad_der`.

## Elementos
Todos aceptan `"id"`, `"en"`, `"hasta"` y `"sonido": false`.

### tarjeta
```json
{"tipo": "tarjeta", "id": "batalla", "caja": "arriba", "entra": "pop", "sale": "fundido",
 "etiqueta": "Claude · en código", "etiqueta_color": "#FF7A1A",
 "contenido": {"mundo": "batalla"},
 "voltear": [{"en": "código", "contenido": {"codigo": {}}, "etiqueta": "El código"}],
 "pegatinas": [{"texto": "1 frase", "en": "frase", "esquina": "abajo_der"}]}
```
- `entra`: `sube` (por defecto), `pop`, `izq`, `der`, `gira`, `fundido`. `sale`: `fundido`, `izq`, `der`, `baja`.
- `voltear`: la tarjeta gira en 3D y enseña otro contenido.
- `pegatinas`: etiquetas inclinadas pegadas a una esquina (`arriba_izq`, `arriba_der`, `abajo_izq`, `abajo_der`), con `color` opcional.

**Contenidos** (uno por tarjeta):
| Contenido | Ejemplo | Notas |
| --- | --- | --- |
| mundo | `{"mundo": "batalla", "zoom": 1.0}` | `referencias/mundos.md`. El escenario es 16:10 y se recorta para llenar la tarjeta |
| prompt | `{"prompt": {"texto": "Anima cómo…", "en": "Anima", "hasta": ">bacteria", "tam": 44}}` | caja de chat que se escribe sola; con `hasta`, termina justo ahí |
| código | `{"codigo": {"archivo": "escena.py", "lineas": ["…"], "lineas_por_segundo": 5, "tam": 27}}` | sin `lineas` usa un código de ejemplo |
| gente | `{"gente": {"n": 70, "columnas": 14, "dur": 1.4, "formato": "{n} personas"}}` | iconos que se llenan con contador |
| pasos | `{"pasos": {"items": [{"texto": "Guion", "icono": "guion", "en": "guion"}, …], "columnas": 2}}` | 2–6 casillas que se encienden con ✓. `columnas` es opcional; en casillas estrechas el icono va encima del texto |
| clip | `{"clip": {"archivo": "su_video.mp4", "desde": 74.5, "dur": 5, "en": "palabra", "ajuste": "cubrir", "bucle": true, "fuente": "Fuente: …"}}` | trozo de un vídeo del usuario, sin su sonido. `ajuste`: `cubrir` (llena y recorta) o `contener` (entero, con bandas). `bucle: false` lo deja parado en el último fotograma. Un vídeo vertical dentro de uno horizontal va mejor en la caja `vertical_der` |
| imagen | `{"imagen": {"imagen": "captura.png", "ajuste": "cubrir", "zoom": [{"en": "25", "zoom": 1.6, "centro": [0.3, 0.4]}], "rodear": [{"en": "25", "rect": [0.05, 0.38, 0.75, 0.46]}], "fuente": "Fuente: YouTube"}}` | imagen del usuario, con acercamientos y un óvalo a mano. Coordenadas de 0 a 1 sobre la imagen |
| texto | `{"texto": {"lineas": ["70", "personas"]}}` | texto grande |
| vacío | `{}` | puntos de «cargando» |

Las capturas y trozos de vídeo de otros, solo si los aporta el usuario y son para citar o comparar; ponles siempre `fuente`.

Iconos de `pasos`: guion, personajes, escenas, montaje, voz, musica, portada, texto, ok, rayo, reloj, dinero, corazon, estrella, mundo, camara, pincel, codigo, chat, lupa, gota, nube, sol.

### pildoras
```json
{"tipo": "pildoras", "zona": [420, 1100, 580, 440], "tam": 40, "items": [
  {"texto": "Animadores", "en": "animadores", "tachar": "animadores+0.35"},
  {"texto": "Solo Claude", "en": "Solo", "ok": true}]}
```
Lista que entra palabra a palabra; `tachar` la tacha en ese momento y `ok` la pone en color con ✓.

### nota (texto a mano con flecha)
```json
{"tipo": "nota", "texto": "también lo hizo Claude", "en": "también", "pos": [560, 1240], "tam": 60,
 "apunta": {"tarjeta": "batalla", "actor": "becario"}, "curva": -0.2}
```
`apunta` puede ser `[x, y]`, `{"tarjeta": id, "punto": [u, v]}` (de 0 a 1 dentro de la tarjeta) o `{"tarjeta": id, "actor": id}` (sigue a un personaje del mundo). Sin `apunta`, solo el texto. La flecha se corta al pasar por la franja de los subtítulos, para no tacharlos. Con `"hasta"`, la nota se desvanece justo antes de ese momento.

### contador
```json
{"tipo": "contador", "en": "25 millones", "de": 0, "a": 25000000, "dur": 1.1, "formato": "{n}", "etiqueta": "suscriptores", "pos": [715, 1230], "tam": 84}
```

### titular
```json
{"tipo": "titular", "zona": [60, 1100, 960, 400], "tam": 96, "lineas": [{"t": "Si puedes", "en": "Si"}, {"t": "DESCRIBIRLO", "clave": true, "en": "describirlo"}]}
```

### cta y siguenos (finales)
```json
{"tipo": "cta", "palabra": "ANIMA", "titulo": "Comenta", "linea": "Te mando la skill gratis", "nota": "por privado", "pos": [540, 600]}
{"tipo": "siguenos", "lineas": ["Sígueme", "1 skill nueva cada semana", "y dale like"], "icono": "corazon", "pos": [540, 600]}
```
Para YouTube: `{"tipo": "siguenos", "lineas": ["Suscríbete", "para más ciencia animada"], "icono": "campana"}`.
`titulo` cambia «Comenta» (por defecto sale en el idioma del vídeo). `siguenos` admite hasta 3 líneas. Los textos se encogen solos si no caben.
En ese plano suele quedar mejor `"subtitulos": false` y la mascota grande en el centro.

### movil y pegatina sueltas
```json
{"tipo": "movil", "imagen": "captura.png", "caja": [620, 260, 380], "rot": -3, "zoom": [...], "rodear": [...]}
{"tipo": "pegatina", "texto": "GRATIS", "pos": [800, 1200], "rot": -6}
```

## Mascota
```json
"mascota": {"personaje": "presentadora", "x": 215, "y": 1700, "tam": 540, "lado": 1,
            "poses": [{"en": 0, "pose": "senala_arriba", "cara": "sorpresa"}, {"en": "frase 2", "pose": "presenta", "cara": "feliz"}]}
```
- Mueve la boca con la voz (o con los tiempos estimados si no hay voz), parpadea, respira y salta un poco en cada palabra clave.
- Poses del humano: neutro, saluda, senala, senala_arriba, celebra, presenta, piensa, sorpresa, bandera, brazos_jarra. Cambia de pose en cada frase o en las palabras clave.
- La mascota puede ser cualquier personaje (una gota, un robot…), no solo un humano. `x` e `y` son siempre el punto de apoyo (los pies); si no es humana y no le das `tam`, sale a la mitad de tamaño.

## Estilo
```json
"estilo": {"base": "crema", "fondo": "#EBDDC6", "manchas": ["#F7B98E", "#F3C9A0"], "puntos": "#D9C5A6",
           "texto": "#0E1B33", "acento": "#FF7A1A", "etiqueta": "#0E1B33"}
```
`acento` es el color de las cajas de palabras clave, las píldoras con ✓ y las pegatinas. `manchas` son dos colores que se difuminan en el fondo.

## Dos finales (Instagram y TikTok)
El cuerpo se hace una vez; solo cambia el final. `tiktok.json` hereda todo de `video.json` y cambia los planos desde una frase (`cambia_desde_frase`). Los planos, poses y acciones que dependían de esa frase se ignoran solos.

**A. Con otra frase de voz al final** (el usuario grabó aparte el final de TikTok):
1. Corta la voz antes de la última frase y pégale el final nuevo (`referencias/guion-y-voz.md` → «Dos finales»), y alinéala con `--salida P/voz_tiktok`.
2. `tiktok.json`:
   ```json
   {"hereda": "video.json", "voz": "voz_tiktok", "cambia_desde_frase": 11,
    "planos": [{"frase": 11, "subtitulos": false, "elementos": [{"tipo": "siguenos", "lineas": ["Sígueme", "1 skill nueva cada semana"]}]}]}
   ```

**B. Final sin voz** (una tarjeta muda en lugar de la última frase):
```json
{"hereda": "video.json", "voz_hasta_frase": 11, "cambia_desde_frase": 11, "cola": 3.0,
 "planos": [{"en": "fin frase 10+0.2", "subtitulos": false, "elementos": [{"tipo": "siguenos", "lineas": ["Sígueme"], "sonido": false}]}]}
```
`voz_hasta_frase` corta la misma voz justo antes de esa frase; `cola` es lo que dura la tarjeta final.

`python3 scripts/render.py P/tiktok.json` → `P/salida/tiktok.mp4`. Si el original es horizontal, para TikTok es mejor un plan vertical aparte (`"formato": "9:16"`), no heredado.

## Consejos de diseño
- **Nada simple:** cada plano lleva tarjeta + algo en la zona de abajo. Mira `muestras.png` y rellena huecos con píldoras, un contador, una nota o una tarjeta pequeña.
- **Una imagen literal por frase:** si la voz dice «70 personas», que se vean 70 personitas; si dice «una frase», que se vea el prompt.
- **El gancho, vivo desde el primer fotograma:** un mundo animado en `grande`, no un título sobre fondo vacío.
- **Comparaciones:** `arriba_izq` + `abajo_der` con etiquetas «Antes / Ahora» o «El suyo / El mío».
- Texto de las tarjetas corto: 2–5 palabras por etiqueta o píldora.
