# SICARS-ITGAM - Sprint 03

## Sistema Inteligente de Clasificacion Automatizada de Residuos Solidos

Proyecto academico del Instituto Tecnologico de Gustavo A. Madero para clasificar residuos solidos en tres categorias compatibles con el prototipo SICARS:

- `organico`
- `reciclable`
- `no_reciclable`

La version actual corresponde al **Sprint 03**. El sistema usa **YOLOv8 classify**, una webcam y una zona central de lectura para clasificar el residuo colocado por el usuario.

> Nota importante: esta version no usa bounding boxes. El modelo actual clasifica una zona recortada de la imagen, no detecta la ubicacion exacta del objeto.

---

## 1. Estado actual del proyecto

| Componente | Estado | Descripcion |
|---|---|---|
| Clasificacion en tiempo real | Funcional | Usa webcam, ROI central y modelo YOLOv8 classify. |
| Modelo entrenado | Funcional | `runs/classify/sicars/weights/best.pt`. |
| Dataset classify | Preparado | `dataset/train`, `dataset/val`, `dataset/test`. |
| Umbral de confianza | Aplicado | `CONFIANZA_MIN = 0.70`. |
| Estabilizacion | Aplicada | Moda de las ultimas 8 lecturas confiables. |
| Arduino | Preparado logicamente | Mapeo `O`, `R`, `N` listo en codigo. |
| Flutter | Pendiente | Recomendado consumir una API local de Python. |
| Bounding boxes | No implementado | Requiere dataset YOLO detect con labels `.txt`. |

---

## 2. Por que se usa YOLOv8 classify

Durante el desarrollo se evaluo usar deteccion con cajas (`detect`), pero el dataset disponible estaba organizado por carpetas de clase:

```text
dataset/
  train/
    organico/
    reciclable/
    no_reciclable/
  val/
    organico/
    reciclable/
    no_reciclable/
  test/
    organico/
    reciclable/
    no_reciclable/
```

Esa estructura es ideal para **clasificacion**, no para deteccion.

Por eso el flujo final del Sprint 03 usa:

```text
yolov8n-cls.pt
```

y genera un modelo:

```text
runs/classify/sicars/weights/best.pt
```

Este modelo no responde "donde esta el residuo", sino "que categoria tiene la imagen o recorte que se le dio".

---

## 3. Como funciona actualmente

1. Se abre la webcam.
2. Se dibuja una zona central de lectura.
3. El usuario coloca el residuo dentro del recuadro.
4. El sistema recorta solo esa zona.
5. `model.predict()` clasifica el recorte.
6. Si la confianza es menor a 70%, se muestra:

```text
Baja confianza / Sin residuo
```

7. Si la confianza es mayor o igual a 70%, se muestra la categoria.
8. Se estabiliza la salida usando un historial de 8 predicciones.
9. Se prepara el byte para Arduino:

| Categoria | Byte |
|---|---|
| `organico` | `O` |
| `reciclable` | `R` |
| `no_reciclable` | `N` |
| baja confianza | no se envia byte |

---

## 4. Estructura recomendada del repositorio

```text
sicars/
  deteccion_tiempo_real.py
  requirements.txt
  README.md
  MANUAL_INSTALACION_Y_CONTINUACION.md
  clasificador.py
  runs/
    classify/
      sicars/
        weights/
          best.pt
```

Archivos opcionales:

```text
documentacion_arreglos_sicars.docx
sicars_web_p5js.html
preparar_dataset.py
preparar_lote_etiquetado_detect.py
```

No se recomienda subir a GitHub:

```text
dataset/
dataset_raw/
archive.zip
dataset.rar
venv/
__pycache__/
*.cache
render_sprint03/
docx_render_arreglos/
```

---

## 5. Instalacion

### Requisitos

- Python 3.10 o superior.
- Webcam funcional.
- Windows, Linux o macOS.
- Modelo entrenado `best.pt` en la ruta esperada.

### Crear entorno virtual

```powershell
cd C:\Users\TU_USUARIO\Desktop\sicars
python -m venv venv
venv\Scripts\activate
```

En Linux/macOS:

```bash
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

Si se va a integrar Arduino por puerto serial:

```bash
pip install pyserial
```

---

## 6. Ejecucion principal

Con el entorno virtual activado:

```bash
python deteccion_tiempo_real.py
```

Controles:

| Tecla | Accion |
|---|---|
| `q` | Cerrar la ventana |
| `s` | Guardar captura |

El residuo debe colocarse dentro del recuadro central. Si se coloca fuera del recuadro o el fondo domina la imagen, la prediccion puede fallar.

---

## 7. Comandos disponibles

### Ver dataset

```bash
python deteccion_tiempo_real.py --ver-dataset
```

Muestra el conteo por split y categoria.

### Preparar dataset

```bash
python deteccion_tiempo_real.py --preparar-dataset
```

Descomprime `archive.zip` si hace falta y mezcla imagenes de:

```text
dataset_raw/
fotos_itgam/
```

Genera estructura:

```text
dataset/train
dataset/val
dataset/test
```

### Entrenar localmente

```bash
python deteccion_tiempo_real.py --entrenar
```

Entrena con:

```text
yolov8n-cls.pt
```

Salida esperada:

```text
runs/classify/sicars/weights/best.pt
```

Recomendacion: para entrenamientos largos, usar Google Colab con GPU y despues copiar `best.pt` a la ruta local.

---

## 8. Configuracion importante

En `deteccion_tiempo_real.py`:

```python
MODELO_PATH = "runs/classify/sicars/weights/best.pt"
IMG_SIZE = 224
CONFIANZA_MIN = 0.70
ROI_ANCHO = 0.55
ROI_ALTO = 0.55
ROI_CENTRO_Y = 0.60
HISTORIAL_PREDICCIONES = 8
```

### Significado

| Variable | Uso |
|---|---|
| `MODELO_PATH` | Ruta del modelo entrenado. |
| `IMG_SIZE` | Tamano de entrada para YOLO classify. |
| `CONFIANZA_MIN` | Umbral minimo para aceptar una lectura. |
| `ROI_ANCHO` | Ancho relativo del recuadro central. |
| `ROI_ALTO` | Alto relativo del recuadro central. |
| `ROI_CENTRO_Y` | Posicion vertical del centro del recuadro. |
| `HISTORIAL_PREDICCIONES` | Cantidad de lecturas usadas para estabilizar salida. |

---

## 9. Integracion con Arduino

El codigo actual ya calcula el byte que se debe enviar:

```python
<<<<<<< HEAD:README(OLD).md
import serial
arduino = serial.Serial("COM3", 9600)
arduino.write(b"R")   # enviar categoría al Arduino
=======
BYTE_ARDUINO = {
    "organico": "O",
    "reciclable": "R",
    "no_reciclable": "N",
}
```

El HUD muestra:

```text
Arduino: O
Arduino: R
Arduino: N
Arduino: -
```

El simbolo `-` significa que no se debe enviar nada.

### Logica recomendada

Arduino debe:

1. Leer Serial a 9600 baudios.
2. Recibir un byte.
3. Mover el servo correspondiente.
4. Ignorar cualquier valor diferente de `O`, `R` o `N`.

### Recomendacion de seguridad

No mover servos si:

- La confianza es menor a 70%.
- El HUD muestra `Baja confianza / Sin residuo`.
- El byte mostrado es `-`.

---

## 10. Integracion con Flutter

Flutter no debe ejecutar el modelo directamente. La arquitectura recomendada es:

```text
Flutter -> API local Python -> YOLOv8 classify -> resultado -> Flutter
                                      |
                                      -> Arduino
```

Python debe seguir siendo el modulo de inteligencia artificial.

Flutter puede mostrar:

- Categoria detectada.
- Confianza.
- Contenedor recomendado.
- Estado de Arduino.
- Mensaje de baja confianza.

### Importante

El modelo actual no reconoce items especificos como:

```text
zanahoria
lechuga
botella
carton
banana
```

Solo reconoce:

```text
organico
reciclable
no_reciclable
```

Si Flutter manda una foto completa sin recorte, con mucho fondo, rotada o comprimida, el resultado puede fallar. Lo ideal es que Flutter envie una imagen recortada y centrada, equivalente al ROI usado por Python.

---

## 11. Problemas comunes

### No encuentra el modelo

Verificar que exista:

```text
runs/classify/sicars/weights/best.pt
```

Si el modelo viene de Colab, copiarlo manualmente a esa carpeta.

### La camara no abre

Cambiar en `deteccion_tiempo_real.py`:

```python
CAMARA_INDEX = 0
```

por:

```python
CAMARA_INDEX = 1
```

Tambien cerrar aplicaciones como Zoom, Meet o Teams.

### Predice mal

Revisar:

- El residuo esta dentro del recuadro.
- Hay buena iluminacion.
- El residuo esta cerca y enfocado.
- El fondo no domina la zona central.
- La confianza supera 70%.

### Flutter no reconoce verduras

No es necesariamente un error de ejecucion. El modelo actual no reconoce nombres de verduras; solo decide si la imagen pertenece a `organico`, `reciclable` o `no_reciclable`.

---

## 12. Documentacion incluida

Documentos generados durante el proyecto:

```text
MANUAL_INSTALACION_Y_CONTINUACION.md
documentacion_arreglos_sicars.docx
```

Documentos externos generados en `Downloads`:

```text
reporte_tecnico_sprint03_SICARS.docx
explicacion_proyecto_sicars_y_fallas_flutter.docx
anexo_participacion_edgar_daniel_sicars.docx
>>>>>>> ebce50a (Descripción de los cambios):README.md
```

---

## 13. Limitaciones actuales

- No hay bounding boxes.
- No reconoce objetos especificos, solo categorias generales.
- Requiere que el residuo este dentro de la zona central.
- La integracion fisica con Arduino todavia debe completarse.
- Flutter debe conectarse mediante una API o puente local, no directamente al modelo.

---

## 14. Siguiente trabajo recomendado

1. Integrar comunicacion serial con Arduino.
2. Probar servomotores con bytes `O`, `R`, `N`.
3. Crear una API local en Python para que Flutter consulte la categoria actual.
4. Hacer que Flutter muestre categoria, confianza y contenedor recomendado.
5. Recolectar mas fotos propias del campus para mejorar el modelo.
6. Si se desea deteccion real por objeto, crear un dataset YOLO detect con bounding boxes.

---

## 15. Resumen rapido

Instalar:

```bash
pip install -r requirements.txt
```

Ejecutar:

```bash
python deteccion_tiempo_real.py
```

Modelo requerido:

```text
runs/classify/sicars/weights/best.pt
```

Salida:

```text
organico -> O
reciclable -> R
no_reciclable -> N
baja confianza -> sin envio
```

---

## Creditos

Proyecto academico SICARS-ITGAM  
Tecnologico Nacional de Mexico - Campus Gustavo A. Madero  
Sprint 03 - Clasificacion de residuos, ROI central, confianza minima y preparacion Arduino/Flutter

