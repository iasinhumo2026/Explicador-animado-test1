---

# README: Explicador-animado-test1

```markdown
# 🎭 Explicador-animado-test1

Un marco de trabajo (framework) automatizado para la creación de videos explicativos e instructivos animados mediante código. Diseñado para transformar datos estructurados, guiones o texto en piezas visuales dinámicas con elementos infográficos, sincronización de voz e ilustraciones animadas.

---

## 📋 Descripción General

`Explicador-animado-test1` está optimizado para simplificar el proceso de creación de contenido educativo y promocional. Integra módulos de renderizado gráfico de alta calidad, motores de síntesis de voz (TTS) y timelines programables para coordinar animaciones vectoriales con audio narrativa de forma fluida.

---

## ✨ Características Principales

- **Renderizado de Animaciones Vectoriales:** Generación de gráficos, diagramas, resaltados de texto y transiciones en 2D.
- **Sincronización por Timestamps:** Alineación automática entre gráficos animados y la locución mediante puntos de tiempo precisos.
- **Integración con Text-to-Speech (TTS):** Compatibilidad con motores de generación de voz por IA para locuciones automáticas en varios idiomas.
- **Sistema de Plantillas Dinámicas:** Escenas reutilizables para intros, diagramas de flujo, resúmenes y llamadas a la acción (CTA).
- **Procesamiento de Guiones en JSON/YAML:** Posibilidad de definir la estructura visual y narrativa entera desde un único archivo de configuración.

---

## 🏗️ Estructura del Proyecto

```text
Explicador-animado-test1/
├── assets/                  # Ilustraciones, vectores (SVG), tipografías e imágenes
│   ├── icons/               # Iconografía vectorial
│   └── templates/           # Plantillas visuales predefinidas
├── config/                  # Definiciones de estilos global y paletas de color
│   └── theme.json           # Estilos visuales, colores y tipografías
├── scripts/                 # Guiones de animación (archivos JSON o YAML con los eventos)
│   └── script_example.json
├── src/                     # Código fuente del motor de animación
│   ├── animator.py          # Renderizador y generador de escenas
│   ├── audio_sync.py        # Generador de TTS y alineación de audio
│   ├── builder.py           # Ensamblador del timeline del explicador
│   └── scene_elements.py    # Definición de formas, textos e infografías
├── output/                  # Videos finalizados en formato digital
├── requirements.txt         # Dependencias del sistema
├── generate_explainer.py    # Script principal de ejecución
└── README.md
🛠️ Requisitos Previos e Instalación
Requisitos del Sistema
Python 3.9+ o Node.js (según las librerías de renderizado subyacentes).

FFmpeg instalado globalmente.

Bibliotecas de renderizado gráfico adicionales (p. ej., Cairo, Pillow o Manim según dependencias).

Instalación
Clonar el repositorio:

Bash
git clone [https://github.com/iasinhumo2026/Explicador-animado-test1.git](https://github.com/iasinhumo2026/Explicador-animado-test1.git)
cd Explicador-animado-test1
Configurar el entorno de Python:

Bash
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate
pip install -r requirements.txt
⚙️ Configuración del Guión
Crea un archivo de guión en scripts/mi_explicador.json especificando las escenas y el texto de locución:

JSON
{
  "title": "Explicación de Conceptos",
  "theme": "dark_mode",
  "scenes": [
    {
      "id": "scene_1",
      "text": "Bienvenidos a la explicación de nuestro sistema.",
      "animation": "fade_in_text",
      "duration": 4.5
    },
    {
      "id": "scene_2",
      "text": "El paso uno consiste en procesar la información recibida.",
      "animation": "diagram_flow",
      "duration": 6.0
    }
  ]
}
🚀 Guía de Uso Paso a Paso
Define tu guión en la carpeta scripts/.

Asegúrate de incluir los vectores o recursos personalizados en assets/.

Renderiza el video explicativo completo ejecutando:

Bash
python generate_explainer.py --script scripts/mi_explicador.json --output output/explicador_final.mp4
🔍 Solución de Problemas
Desfase entre audio y animación: Revisa la duración asignada en las escenas dentro del archivo .json para asegurarte de que coincida con la longitud total calculada por el motor de TTS.

Falta de fuentes tipográficas: Asegúrate de que las fuentes declaradas en config/theme.json estén instaladas en tu sistema o agregadas en assets/fonts/.

📄 Licencia
Este proyecto está distribuido bajo la licencia MIT.
