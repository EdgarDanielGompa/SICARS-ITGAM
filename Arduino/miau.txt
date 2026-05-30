# SICARS-ITGAM 🐣📷

### Sistema Inteligente de Clasificación y Automatización de Residuos Sólidos

SICARS es un prototipo mecatrónico de nivel ingeniería diseñado para la clasificación automatización de residuos sólidos mediante Inteligencia Artificial (Visión Artificial) y hardware abierto. El sistema integra un modelo de detección en tiempo real basado en YOLOv8 que se comunica vía puerto serial con un microcontrolador Arduino Mega 2560 para controlar compuertas automatizadas mediante servomotores, indicadores visuales (Aro Neopixel) y alertas sonoras de voz asíncronas.

---

## 📋 Características Principales

* 
**Clasificación Autónoma por IA**: Detección y categorización de residuos (Orgánico, Reciclable, No Reciclable) con un modelo YOLOv8 optimizado y entrenado con un 94% de eficiencia.


* 
**Puente de Comunicación Serial**: Integración interactiva entre scripts de Python en la computadora y el firmware de Arduino mediante transmisión asíncrona de bytes por el cable USB.


* 
**Interfaz de Usuario Física**: Control de visualización mediante pantalla LCD 16x2 y un sistema de iluminación inteligente con Aro LED Neopixel (16 bits) que asiste a la cámara.


* 
**Modo Economizador Inteligente**: Filtro de promedio para lecturas estables del sensor ultrasónico frontal, permitiendo la hibernación o suspensión automática del sistema tras 1 minuto de inactividad para proteger los componentes.


* 
**Doble Respaldo de Seguridad**: Operación híbrida mediante procesamiento de IA y botones físicos de respaldo para una apertura manual inmediata con prioridad absoluta.



---

## 🛠️ Requisitos del Sistema

Antes de comenzar la configuración, asegúrate de contar con los siguientes elementos instalados en tu computadora de diagnóstico:

* Python 3.10 o superior 


* Arduino IDE (para la carga del firmware al Mega)
* Webcam funcional (integrada o externa) 


* Windows PowerShell con permisos de ejecución de scripts de entornos virtuales 



---

## 🚀 Arquitectura de Conexión Eléctrica

Para garantizar una estabilidad impecable y evitar fallas descontroladas por caídas de tensión al activarse los componentes dinámicos, el sistema separa la lógica de procesamiento de la etapa de potencia:

1. 
**Cerebro (Arduino Mega 2560)**: Alimentado mediante el cable USB azul directo a la computadora de diagnóstico. Se encarga de la lectura de sensores chiquitos, la pantalla LCD y el módulo de audio de forma limpia.


2. 
**Músculos (Servos y Aro LED)**: Alimentados de forma independiente mediante una Fuente de Poder de Protoboard (Negra) conectada a un cargador de pared de 9V fijo (Kit RexQualis) que suministra 1 Amperio constante y estable.


3. 
**Unión de Tierras (GND) - EL PASO MÁS IMPORTANTE**: Un cable jumper conecta la hilera azul (-) de la fuente de la protoboard directamente con un pin GND libre del Arduino Mega. Sin esta unión, las dos fuentes no hablan el mismo idioma y los motores o luces Neopixel se vuelven locos.



---

## 📦 Instalación y Configuración (Python)

Sigue estos pasos detallados desde tu terminal de Windows PowerShell para desplegar el entorno de visión artificial:

### 1. Navegar a la Carpeta del Proyecto

Abre PowerShell y dirígete al directorio raíz donde se encuentran tus archivos descargados:
cd C:\Users\Ricardo\Downloads\sicars1\sicars

### 2. Crear el Entorno Virtual

Aísla las librerías del proyecto ejecutando el módulo de entorno virtual de Python:
python -m venv venv

### 3. Habilitar la Directiva de Ejecución de Windows

Para permitir la activación de scripts de entornos virtuales de forma segura en la sesión actual, ejecuta:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
*(Selecciona "O" [Sí a todo] cuando la consola de Windows solicite confirmación).*

### 4. Activar el Entorno Virtual

Inicializa el entorno virtual recién creado:
venv\Scripts\activate
*(Notarás el prefijo "(venv)" al inicio de la línea de comandos en tu terminal).*

### 5. Instalar Paquetería y Dependencias Core

Descarga y actualiza los frameworks de IA y procesamiento de imagen (ultralytics, opencv-python, numpy):
pip install -r requirements.txt

### 6. Instalar el Puente de Comunicación Serial

Instala la librería necesaria para el intercambio de información bidireccional con el hardware de Arduino:
pip install pyserial

---

## 💻 Configuración del Script de Visión (deteccion_tiempo_real.py)

Abre tu archivo principal de Python en tu editor de código y valida que los siguientes parámetros apunten al hardware correcto:

import serial

# 1. Configuración del índice de la cámara

# Configurar CAMARA_INDEX = 1 para activar con éxito la webcam integrada de la laptop o 0 para periféricos externos

CAMARA_INDEX = 1

# 2. Configuración del Puerto COM de Windows

# Reemplaza 'COM8' por el puerto exacto asignado por Windows para tu Arduino Mega (ejemplo: COM3, COM8)

# El baudrate DEBE ser estricto a 9600 para que coincida con el setup del firmware

arduino = serial.Serial('COM8', 9600, timeout=1)

# Envío del byte físico al Arduino Mega cuando la confianza supera el umbral

if BYTE_ARDUINO != '-':
arduino.write(BYTE_ARDUINO.encode()) # Convierte la letra física en un byte real

---

## 🔌 Mapeo de Pines del Arduino Mega 2560

Asegúrate de que tus cables jumpers físicos estén distribuidos en los conectores del microcontrolador tal como se definió en el código de tu firmware formal:

* 
**Pin 5**: Módulo de Voz Azul (Patita PLAYE para activar el mensaje de audio de forma asíncrona).


* 
**Pin 6**: Anillo de LEDs Neopixel (Cable soldado al punto de entrada de datos DI).


* 
**Pines 9, 10, 11**: Los 3 Servomotores de las compuertas (Orgánico, Reciclable y No Reciclable respectivamente).


* 
**Pines 22 al 27**: Pantalla LCD de la interfaz física conectada en modo paralelo.


* 
**Pines 34 y 35**: Sensor Ultrasónico Frontal (Pines Trig y Echo para el cálculo de distancia y activación del circuito).


* 
**Pines 36, 38, 40**: Los 3 Sensores Ópticos Reflectivos TCRT5000 para el control automático de llenado/saturación de botes.


* 
**Pines 42, 44, 46**: Tus 3 Botones de colores para la apertura e interrupción manual de respaldo.



---

## 🏃‍♀️ Ejecución del Sistema

Una vez cargado el código corregido y blindado v1.5 a tu placa Arduino Mega y configurado el entorno virtual, puedes arrancar el software del sistema integral siguiendo este orden:

1. Conecta el cable USB azul del Arduino Mega a la computadora (verás cómo prende la pantalla LCD y los sensores chiquitos).


2. Conecta el cargador de 9V a la luz de la pared y presiona el botón blanco de encendido de la fuente negra en la protoboard para energizar los servos y el aro LED.


3. Desde la consola de PowerShell (con el entorno venv activo), lanza la Inteligencia Artificial en tiempo real:
python deteccion_tiempo_real.py



El script desplegará un HUD gráfico con un cuadro delimitador central en pantalla. Al colocar un residuo en la zona de escaneo (como una manzana o una lata de refresco) y superar el nivel de confianza, Python inyectará el byte correspondiente por el cable USB. El Arduino recibirá la letra, activará el pulso de audio en la bocina y abrirá el servomotor correcto de forma espectacular y fluida.

Para detener de forma limpia el procesamiento de imágenes de la IA y liberar por completo el puerto COM de Windows, presiona la tecla **q** en la ventana de visualización de Python.

---

**Desarrollado institucionalmente por Dircora para el Tecnológico de Gustavo A. Madero (ITGAM).**
