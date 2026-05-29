# SICARS-ITGAM — Sprint 01
## Sistema Inteligente de Clasificación Automatizada de Residuos Sólidos

> **Instituto Tecnológico de Gustavo A. Madero**  
> Prueba de factibilidad técnica: detección de objetos en tiempo real  
> Norma de referencia futura: NADF-024-AMBT-2013

---

## Estructura de carpetas

```
sicars/
├── deteccion_tiempo_real.py   ← script principal
├── clasificador.py            ← módulo de categorización NADF-024
├── requirements.txt           ← dependencias pip
├── README.md                  ← este archivo
│
├── models/                    ← pesos YOLO (se descargan automáticamente)
│   └── yolov8n.pt
│
├── dataset/                   ← imágenes capturadas para futuros datasets
│   ├── capturas/              ← raw (tecla 's' durante ejecución)
│   ├── organico/              ← imágenes etiquetadas manualmente
│   ├── reciclable/
│   └── no_reciclable/
│
└── logs/                      ← registros de ejecución (sprint futuro)
```

---

## 1. Instalación paso a paso

### Requisitos previos

- Python 3.9 o superior ([python.org](https://python.org))
- pip actualizado
- Webcam funcional

### Pasos

```bash
# 1. Ir a la carpeta del proyecto
cd C:\Users\DELL\Desktop\sicars

# 2. Crear entorno virtual (recomendado)
python -m venv venv

# 3. Activar entorno virtual
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 4. Instalar dependencias
pip install -r requirements.txt

# —— o manualmente ——
pip install ultralytics opencv-python
```

> La primera ejecución descargará automáticamente `yolov8n.pt` (~6 MB).

---

## 2. Ejecución

```bash
python deteccion_tiempo_real.py
```

| Tecla | Acción |
|-------|--------|
| `q`   | Salir del sistema |
| `s`   | Guardar fotograma en `dataset/capturas/` |

---

## 3. Descripción de cada módulo

### `deteccion_tiempo_real.py`

| Sección | Qué hace |
|---------|----------|
| **Configuración global** | Define rutas, resolución, umbral de confianza y colores por categoría |
| **`main()`** | Ciclo principal: abre cámara → infiere → anota → muestra |
| **`_dibujar_etiqueta()`** | Dibuja bounding box con etiqueta semitransparente |
| **`_dibujar_hud()`** | Muestra FPS, número de objetos y nombre del sistema |
| **`guardar_imagen()`** | Exporta fotograma + log de detecciones para construir dataset |

### `clasificador.py`

Mapea clases COCO a las tres categorías NADF-024-AMBT-2013:

| Categoría | Color HUD | Ejemplos de objetos |
|-----------|-----------|---------------------|
| `organico` | 🟢 verde | banana, apple, pizza, carrot |
| `reciclable` | 🔵 azul | bottle, laptop, book, cup |
| `no_reciclable` | 🔴 rojo | chair, toothbrush, teddy bear |
| `desconocido` | ⚫ gris | cualquier clase no mapeada |

---

## 4. Parámetros de rendimiento

### Variables ajustables en `deteccion_tiempo_real.py`

```python
IMG_SIZE      = 320    # ↓ reduce para más FPS; ↑ aumenta para más precisión
CONFIANZA_MIN = 0.45   # ↑ reduce falsos positivos; ↓ detecta más objetos
MODELO_PATH   = "yolov8n.pt"  # n=nano, s=small, m=medium (↑ precisión, ↓ FPS)
```

### Comparativa de modelos YOLOv8

| Modelo | Tamaño | FPS estimado (CPU) | Uso recomendado |
|--------|--------|--------------------|-----------------|
| `yolov8n.pt` | ~6 MB | 15–25 FPS | Sprint 01 (demo) |
| `yolov8s.pt` | ~22 MB | 8–15 FPS | Balance precisión/velocidad |
| `yolov8m.pt` | ~52 MB | 4–8 FPS | GPU recomendada |

### Técnicas de optimización adicionales

1. **Bajar resolución de inferencia**: `imgsz=224` (menos preciso pero más rápido)
2. **Saltar fotogramas**: procesar 1 de cada 2 con contador `frame_count % 2 == 0`
3. **GPU**: si tienes NVIDIA, instala `torch` con CUDA y YOLOv8 la detecta automáticamente
4. **Hilos separados**: captura en hilo dedicado con `threading.Thread` (sprint futuro)

---

## 5. Captura de imágenes para dataset futuro

Durante la ejecución, presiona **`s`** para guardar la imagen actual.  
Las capturas se almacenan en `dataset/capturas/` con nombre `captura_YYYYMMDD_HHMMSS.jpg`.

### Flujo de etiquetado recomendado

1. Capturar 50-100 imágenes por categoría
2. Etiquetar con [Roboflow](https://roboflow.com) o [Label Studio](https://labelstud.io)
3. Exportar en formato YOLO `.txt`
4. Colocar en `dataset/organico/`, `dataset/reciclable/`, `dataset/no_reciclable/`
5. Usar para Transfer Learning con `yolov8n.pt` como base (sprint futuro)

### Datasets externos recomendados

| Dataset | Clases | Enlace |
|---------|--------|--------|
| TrashNet | 6 categorías genéricas | [Stanford](http://cvgl.stanford.edu/projects/taco/) |
| TACO | 60 categorías de residuos | [tacodataset.org](http://tacodataset.org) |

---

## 6. Arquitectura futura del sistema

```
[Webcam / ESP32-CAM]
        │  stream de video
        ▼
[Python + YOLOv8]  ←─ este sprint
  • Detección de objeto
  • Clasificación NADF-024
        │  categoría vía Serial/USB
        ▼
[Arduino UNO / Mega]
  • Recibe categoría ("organico", "reciclable", etc.)
        │  señal PWM
        ▼
[Servomotores]
  • Compuerta A → contenedor orgánico
  • Compuerta B → contenedor reciclable
  • Compuerta C → contenedor no reciclable
```

### Protocolo Arduino (sprint futuro)

El módulo Python enviará por puerto Serial un byte de 1 carácter:

| Byte | Significado |
|------|-------------|
| `O`  | orgánico    |
| `R`  | reciclable  |
| `N`  | no reciclable |

```python
import serial
arduino = serial.Serial("COM3", 9600)
arduino.write(b"R")   # enviar categoría al Arduino
```

---

## 7. Buenas prácticas de escalabilidad

- **Módulos separados**: `clasificador.py` es independiente del loop de visión → fácil de sustituir por modelo entrenado
- **Configuración centralizada**: todos los parámetros en la sección `Configuración global`
- **Sin hardcoding de rutas**: usar `os.path` o `pathlib` en sprints futuros
- **Logging**: reemplazar `print()` por `logging` para producción
- **Tests unitarios**: probar `clasificar_objeto()` con `pytest` antes de integrar nuevo modelo
- **Control de versiones**: un commit por funcionalidad, ramas por sprint

---

## Créditos

Proyecto académico SICARS-ITGAM  
Tecnológico Nacional de México — Campus Gustavo A. Madero  

