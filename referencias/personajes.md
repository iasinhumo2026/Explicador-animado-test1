# Personajes

Se definen en `video.json` → `"personajes"`, cada uno con un nombre:
```json
"personajes": {
  "bacteria": {"forma": "capsula", "color": "#8BD450", "color2": "#6DB33A", "detalle": "manchas", "flagelos": 3, "cara": "picaro"},
  "macrofago": {"forma": "gota", "color": "#FFD27A", "color2": "#F2A93B", "detalle": "nucleo", "accesorios": ["babero"]}
}
```
Para ver cómo quedan antes de montar nada, haz una hoja de prueba (ver el final).

## Formas
| Forma | Qué es | Va bien para |
| --- | --- | --- |
| `gota` | mancha blanda que se deforma sola | células, monstruos blanditos, slime |
| `circulo` | bola | células, pelotas, caras, átomos |
| `capsula` | píldora alargada (mira a la derecha) | bacterias, píldoras, coches de juguete |
| `fantasma` | cúpula con faldón ondulado | glóbulos blancos, fantasmas, guardianes |
| `virus` | bola con pinchos | virus, erizos, minas |
| `disco` | óvalo con hueco | glóbulos rojos, platos, monedas |
| `estrella` | estrella redondeada | premios, ideas, estrellas |
| `cuadrado` | cubo redondeado | robots, cajas, datos, píxeles |
| `nube` | nube | nubes, ideas, humo |
| `gota_agua` | gota de agua | agua, lágrimas, aceite |
| `corazon` | corazón | amor, salud, likes |
| `planeta` | bola (con `"anillo": true`, anillo) | planetas, lunas |
| `hoja` | hoja con nervios y rabito | plantas, fotosíntesis, otoño |
| `flor` | flor con pétalos (`color2`) y la cara en el centro | plantas, primavera, polinización |
| `maceta` | maceta con brote (`color2` = hojas) y la cara en la maceta | plantas, cuidados, crecimiento |
| `volcan` | cono con cráter y lava (`color2`) | volcanes, erupciones, geología |
| `montana` | montaña con nieve (`"nieve": false` para quitarla) | paisajes, geografía, el clima |
| `humano` | persona estilo chibi (ver abajo) | presentador, mascota |

## Campos
| Campo | Valores |
| --- | --- |
| `color`, `color2` | color principal y de los detalles (hex) |
| `cara` | expresión por defecto (ver abajo) o `"ninguna"` |
| `detalle` | `manchas`, `puntos`, `nucleo`, `rayas`, `crater`, `bandas` |
| `accesorios` | lista de: `casco`, `escudo`, `lanza`, `espada`, `gafas`, `corona`, `cinta`, `babero`, `bandera`, `sombrero` (chistera), `gorro_chef`, `auriculares`, `antena`, `tornillos`, `bigote`, `capa`, `chip`. Para un robot: `cuadrado` o `gota` con `antena`, `tornillos` y `auriculares` |
| `color_accesorio` | color de cruz del escudo, bandera, cinta, capa… (por defecto, naranja) |
| `flagelos` | número de colas que se mueven (bacterias, espermatozoides) |
| `patas`, `alas`, `trompa` | insectos: número de patas, `"alas": true` (baten solas; `color_alas`), largo de la trompa (1.0 = normal; se alarga con la acción `estira` del mundo) |
| `pinchos` | número de pinchos con bolita (virus) |
| `rayos` | `true`: rayos alrededor (soles) |
| `ojos` | 1, 2 o 3 · `ojos_tam`, `ojos_sep` (1.0 = normal) · `pupila`: `grande` o `pequena` |
| `cara_tam` | tamaño de la cara (1.0 = normal) |
| `mejillas`, `cejas`, `parpadea`, `respira`, `sombreado`, `brillo` | `true` / `false` |
| `contorno` | `false` para quitar la línea · `grosor`: 1.0 = normal · `linea`: color del contorno |

## Caras (expresiones)
`neutro`, `feliz`, `risa`, `enfadado` (dientes apretados), `sorpresa` (boca en O), `miedo` (con gota de sudor), `picaro`, `triste`, `decidido`, `dormido` (con «z»), `hambre` (boca enorme con dientes), `mareado` (ojos en espiral), `enamorado` (ojos de corazón).
- Todas parpadean solas y respiran un poco.
- En un mundo, los que comen ponen `hambre` al morder y los golpeados ponen `mareado`.

## Humano
```json
"presentador": {"forma": "humano", "peinado": "corto", "pelo": "#3B2A20", "piel": "#F3CDB0",
                "camiseta": "#4C9EEB", "pantalon": "#24415F", "zapatillas": "#22252E",
                "cinta": "#FF7A1A", "chip": false}
```
- `peinado`: `puntas` (despeinado con mechón hacia arriba), `corto`, `largo` (melena lisa), `melena` (melena rizada), `rizado` (afro corto), `coleta`, `mono` (moño arriba).
- `pestanas`: `true` para pestañas · `falda`: color de una falda en lugar del pantalón corto · `color_lazo`: el de la coleta.
- Accesorios que dibuja el humano: `gafas` (`color_gafas`), `bigote`, `auriculares` (`color_accesorio`) y la bandera de la pose `bandera`. Los demás accesorios son para las otras formas (el render avisa si pides uno que no sale).
- `cinta`: color de una cinta deportiva en la frente (opcional) · `chip`: dibujito en la camiseta (`true`/`false`) · `color_chip`.
- Poses: `neutro`, `saluda` (mueve la mano), `senala`, `senala_arriba`, `celebra`, `presenta`, `piensa`, `sorpresa`, `bandera` (con banderita), `brazos_jarra`.
- Si el usuario quiere parecerse a sí mismo, pregúntale color de pelo, peinado, piel y ropa. No intentes copiar a una persona famosa ni a un personaje conocido.

## Diseñar los personajes de un tema
1. **Una forma y un color por papel**, que se distingan de lejos: los malos en un color (verde ácido, morado), los buenos en otro (azules, amarillos).
2. **Un accesorio que cuente su trabajo:** el que defiende lleva casco y lanza, el que come lleva babero, el listo lleva gafas, el jefe lleva corona.
3. **Una cara que cuente su carácter:** pícaro el villano, decidido el guardián, feliz el glotón.
4. **Originales siempre:** no copies personajes de canales, series, juegos ni marcas, aunque te lo pidan. Inventa los tuyos.
5. Tamaños en el mundo: protagonista 0,3–0,4; secundarios 0,15–0,25; enjambre 0,07–0,12 (fracción del alto del escenario).

Recetas:
| Tema | Personajes |
| --- | --- |
| Sistema inmune | bacteria `capsula` verde con flagelos; macrófago `gota` amarilla con babero; neutrófilo `fantasma` azul con casco, escudo y lanza; linfocito `circulo` morado con gafas que dispara anticuerpos |
| Sistema solar | sol `circulo` con rayos; planetas `circulo`/`planeta` con `detalle` (manchas, bandas, cráter) |
| Ciclo del agua | sol, gotas `gota_agua`, nube `nube` |
| Internet | datos `cuadrado` de colores, virus `virus`, cortafuegos `fantasma` con escudo |
| Dinero | monedas `disco` doradas, hucha `gota` rosa con corona |

## Hoja de prueba
```bash
python3 - <<'EOF'
import sys, json; sys.path.insert(0, "scripts")
from comun import nuevo_lienzo, col, texto
import personajes as P
V = json.load(open("proyectos/mi-video/video.json"))
pj = V["personajes"]
s, _ = nuevo_lienzo(300 * len(pj), 420); c = s.getCanvas(); c.clear(col("#F3E8DA"))
for i, (n, sp) in enumerate(pj.items()):
    if sp.get("forma") == "humano":
        P.dibujar(c, sp, 150 + i * 300, 390, 360, 1.0, {"pose": "saluda"})
    else:
        P.dibujar(c, sp, 150 + i * 300, 200, 180, 1.0, {})
    texto(c, n, 150 + i * 300, 400, "bold", 26, "#222222", ancla="centro")
open("proyectos/mi-video/salida_personajes.png", "wb").write(bytes(s.makeImageSnapshot().encodeToData()))
EOF
```
Mira la imagen con la herramienta de leer imágenes y ajusta colores y accesorios.
