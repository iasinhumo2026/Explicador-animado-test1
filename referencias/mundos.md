# Mundos

Un mundo es un escenario animado que se pinta dentro de una tarjeta (`"contenido": {"mundo": "nombre"}`).
- El escenario mide **1600 × 1000** (16:10). Las posiciones van de 0 a 1 (`[0.5, 0.5]` es el centro) y los tamaños, en fracción del alto (`0.3` = 300 px).
- Los personajes **actúan solos** (nadan, comen, golpean, disparan, orbitan) y además hacen **acciones a tiempo de la voz**.
- El tiempo del mundo es el del vídeo: si la misma tarjeta sale en varios planos, la animación sigue donde iba.
- La simulación es determinista: el mismo segundo sale siempre igual (las muestras coinciden con el vídeo).

```json
"mundos": {
  "batalla": {
    "fondo": "vaso",
    "particulas": [{"tipo": "globulos", "n": 12}],
    "actores": [
      {"enjambre": "bacteria", "n": 26, "zona": [0.0, 0.15, 0.5, 0.85], "hacia": ["macro", "n1"], "vel": 0.09,
       "tam": [0.09, 0.12], "caras": ["picaro", "enfadado", "risa"]},
      {"id": "macro", "personaje": "macrofago", "pos": [0.6, 0.5], "tam": 0.36, "come": {"cada": 1.1}},
      {"id": "n1", "personaje": "neutrofilo", "pos": [0.82, 0.25], "tam": 0.2, "golpea": {"cada": 0.6}, "lado": -1},
      {"id": "b1", "personaje": "linfocito", "pos": [0.93, 0.5], "tam": 0.17, "dispara": {"cada": 0.45}}
    ],
    "etiquetas": [{"texto": "BACTERIAS", "pos": [0.07, 0.1], "color": "#6DB33A"},
                  {"texto": "MACRÓFAGO", "actor": "macro", "color": "#F08A24"}]
  }
}
```

## Fondos
`vaso` (interior de un vaso sanguíneo), `agua`, `mar` (cielo arriba y mar abajo), `cielo`, `espacio`, `noche`, `papel` (cuadrícula), `liso`, `tierra` (corte del suelo), `laboratorio`.
`"colores": [...]` cambia sus colores (2 colores en casi todos; `mar` y `tierra` admiten 4).

**Franjas:** bandas de color encima del fondo para hacer un vaso sanguíneo, una capa de la piel, un río o un camino:
`"franjas": [{"y": [0.55, 0.85], "x": [0, 1], "color": "#E36A5C", "radio": 0.05, "texto": "VASO SANGUÍNEO"}]` (`borde`, `alfa` y `texto_color` opcionales). Junta una franja con un enjambre `flujo` para que algo corra por dentro.

## Partículas
| tipo | qué hace |
| --- | --- |
| `globulos` | glóbulos rojos que fluyen (algunos pasan por delante, por los bordes) |
| `burbujas` | suben |
| `polvo` | motas que flotan |
| `lluvia` | cae |
| `nubes` | cruzan el cielo |
| `estrellas`, `chispas` | brillan |
Campos: `n`, `vel`, `color`, `semilla`, `aparece` y `desaparece` (tiempos, como `"en"`).

## Actores
```json
{"id": "macro", "personaje": "macrofago", "pos": [0.6, 0.5], "tam": 0.36, "lado": 1, "cara": "feliz", "pose": "saluda",
 "aparece": "frase 3", "entra": "pop", "desaparece": "frase 5", "flota": 0.012, "mira": true, "acciones": [...]}
```
- `pos` es el **centro** del personaje (también en los humanos: con `tam` 0,5 y `pos` y 0,7, los pies quedan en 0,95). En la mascota, en cambio, `x` e `y` son los pies.
- `lado`: 1 mira a la derecha, −1 a la izquierda · `entra`: `pop`, `abajo`, `izq`, `der`, `salta` · `flota`: cuánto sube y baja · `mira`: los ojos siguen al enemigo más cercano.
- **Comportamientos solos:**
  - `"come": {"cada": 1.1}` → se traga a los del enjambre que se acercan (boca enorme y sonido de bocado).
  - `"golpea": {"cada": 0.6}` → manda volando a los que llegan (mareados y ¡puf!).
  - `"dispara": {"cada": 0.45, "proyectil": "anticuerpo", "color": "#FF7A1A", "en": "frase 4"}` → lanza proyectiles a un enemigo al azar. Proyectiles: `anticuerpo`, `burbuja`, `estrella`, `flecha`, `chispa`.
  - `"orbita": {"centro": [0.5, 0.5], "radio": [0.33, 0.28], "vel": 0.22, "fase": 0.5}` → da vueltas (planetas, electrones).
- **Acciones a tiempo de la voz** (`"acciones": [...]`, cada una con `"en"` y a veces `"dur"`):
  | tipo | campos |
  | --- | --- |
  | `mover` | `"a": [x, y]`, `dur`, `lado` opcional |
  | `cara` | `"cara": "risa"` |
  | `pose` | `"pose": "celebra"` (humanos) |
  | `salta` | `dur`, `alto` |
  | `tiembla` | `dur` |
  | `gira` | `dur` (una vuelta) |
  | `crece` | `"a": 1.3`, `dur` |
  | `bocadillo` | `"texto": "¡Ñam!"`, `dur`, `tam` (texto de 54 px del escenario por defecto) |
  | `estira` | `"de": 1.0, "a": 3.0`, `dur`: alarga la trompa de un insecto |
  | `habla` | `dur` (mueve la boca) |
  | `lado` | `"lado": -1` |

## Enjambres
```json
{"enjambre": "bacteria", "n": 26, "zona": [0.0, 0.15, 0.5, 0.85], "hacia": ["macro", "n1"], "vel": 0.09,
 "tam": [0.09, 0.12], "caras": ["picaro", "enfadado"], "dir": 1, "continuo": true, "reaparece": 1.0, "aparece": "frase 2"}
```
- Salen repartidos en `zona` ([x0, y0, x1, y1]) y van hacia `hacia`: un actor, una lista de actores (se reparten) o un punto `[x, y]`.
- Se paran cerca del objetivo y esperan su turno (`parar`, `fila`, `dispersion` para afinar).
- `continuo`: los que desaparecen vuelven a entrar por el borde, así la batalla no se acaba nunca.
- `dir`: 1 entran por la izquierda, −1 por la derecha.
- Cerca de un defensor ponen cara de miedo (`cara_cerca` para cambiarla).
- `"flujo": true`: en lugar de ir a un objetivo, avanzan siempre en la dirección `dir` dentro de `zona` y, al salir por un lado, vuelven por el otro (sangre por un vaso, coches, peces, una cinta transportadora).

## Etiquetas
`{"texto": "BACTERIAS", "pos": [0.07, 0.1], "color": "#6DB33A", "texto_color": "#FFFFFF", "en": "bacteria", "hasta": "frase 4", "tam": 44}` (`color` es el fondo de la etiqueta; el texto sale blanco salvo que pongas `texto_color`) o `{"texto": "MACRÓFAGO", "actor": "macro", "color": "#F08A24"}` (va encima del actor y lo sigue; si no cabe, debajo; se esconde cuando el actor se va). Siempre se quedan dentro del escenario. `tam` 44 se lee bien en el móvil; no bajes de 36.

## Cámara (opcional)
`"camara": [{"en": 0, "zoom": 1.0, "foco": [0.5, 0.5]}, {"en": "macrófago", "zoom": 1.6, "foco": [0.6, 0.5]}]` acerca la vista. Con cámara el render va más lento: úsala poco.

## Recetas
- **Batalla:** fondo `vaso`, glóbulos, enjambre de malos hacia 2–3 defensores (uno `come`, otro `golpea`, otro `dispara`), etiquetas.
- **Fila de presentación:** fondo `liso`, 3–5 personajes en fila a la misma altura (`pos` y = 0.6), con `cara`, `salta`, `gira` y `bocadillo` en las palabras de la frase, y etiquetas con `actor` que salen con `en`.
- **Sistema solar:** fondo `espacio`, sol en el centro y planetas con `orbita`.
- **Ciclo del agua:** fondo `mar`, sol, gotas que suben con `mover`, nube que aparece con `aparece` y lluvia con `aparece`.
- **Proceso paso a paso:** fondo `papel`, personajes que se mueven de un punto a otro con `mover` en cada palabra clave.
