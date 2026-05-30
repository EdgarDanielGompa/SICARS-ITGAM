"""
SICARS-ITGAM | Clasificacion de residuos en tiempo real

Version ajustada al dataset disponible:
- Waste Classification v2 de Kaggle viene por carpetas de clase.
- fotos_itgam tambien viene por carpetas de clase.
- Por eso el flujo mas simple y correcto es YOLOv8 classify.

El sistema clasifica el frame completo como:
  organico | reciclable | no_reciclable

Nota:
  Este modo NO dibuja bounding boxes. Para cajas se necesitarian labels YOLO
  con coordenadas, pero aqui evitamos ese trabajo para avanzar rapido.
"""

import serial  # Permite que Python mande bytes por el cable USB azul

import sys
import time
import zipfile
import shutil
import random
from collections import Counter, deque
from pathlib import Path

import cv2
from ultralytics import YOLO


# =========================
# Configuracion
# =========================

MODELO_PATH = "runs/classify/sicars/weights/best.pt"
MODELO_BASE = "yolov8n-cls.pt"
DATASET_ZIP = "archive.zip"
DATASET_RAW = "dataset_raw"
DATASET_DIR = "dataset"
FOTOS_ITGAM = "fotos_itgam"

CAMARA_INDEX = 1
IMG_SIZE = 224
CONFIANZA_MIN = 0.70
VENTANA_TITULO = "SICARS-ITGAM | Clasificacion de residuos"
# Abrir el puerto del Arduino Mega a 9600 baudios
arduino = serial.Serial('COM9', 9600, timeout=1)

EPOCHS = 30
BATCH = 16
SEMILLA = 42
ROI_ANCHO = 0.55
ROI_ALTO = 0.55
ROI_CENTRO_Y = 0.60
HISTORIAL_PREDICCIONES = 8

CATEGORIAS = ("organico", "reciclable", "no_reciclable")
CATEGORIAS_SET = set(CATEGORIAS)

COLORES = {
    "organico": (0, 200, 60),
    "reciclable": (255, 150, 0),
    "no_reciclable": (0, 70, 230),
    "desconocido": (150, 150, 150),
}

BYTE_ARDUINO = {
    "organico": "O",
    "reciclable": "R",
    "no_reciclable": "N",
}

EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

MAPA_CLASES = {
    "o": "organico",
    "organic": "organico",
    "organico": "organico",
    "r": "reciclable",
    "recyclable": "reciclable",
    "reciclable": "reciclable",
    "n": "no_reciclable",
    "nonrecyclable": "no_reciclable",
    "non-recyclable": "no_reciclable",
    "noreciclable": "no_reciclable",
    "no_reciclable": "no_reciclable",
}


def clave_clase(nombre_clase: str) -> str:
    return nombre_clase.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def normalizar_clase(nombre_clase: str) -> str:
    return MAPA_CLASES.get(clave_clase(nombre_clase), "desconocido")


def imagenes_en(carpeta: Path):
    if not carpeta.exists():
        return []
    return [p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONES]


def imagenes_recursivas(carpeta: Path):
    if not carpeta.exists():
        return []
    return [p for p in carpeta.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONES]


def descomprimir_archive():
    zip_path = Path(DATASET_ZIP)
    raw_path = Path(DATASET_RAW)
    if raw_path.exists():
        print(f"[SICARS] Dataset crudo existente: {raw_path}")
        return
    if not zip_path.exists():
        print(f"[WARN] No se encontro {DATASET_ZIP}. Se usaran solo fotos_itgam si existen.")
        return

    print(f"[SICARS] Descomprimiendo {DATASET_ZIP}...")
    raw_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(raw_path)
    print("[SICARS] Descompresion lista.")


def recolectar_fuentes():
    registros = []

    # Kaggle Waste Classification v2: dataset_raw/DATASET/TRAIN/O,R,N y TEST/O,R,N
    kaggle_base = Path(DATASET_RAW) / "DATASET"
    for split in ("TRAIN", "TEST"):
        for origen, categoria in (("O", "organico"), ("R", "reciclable"), ("N", "no_reciclable")):
            for img in imagenes_en(kaggle_base / split / origen):
                registros.append((categoria, img, "kaggle"))

    # Fotos ITGAM: fotos_itgam/organico, reciclable, no_reciclable
    itgam_base = Path(FOTOS_ITGAM)
    for categoria in CATEGORIAS:
        for img in imagenes_recursivas(itgam_base / categoria):
            registros.append((categoria, img, "itgam"))

    return registros


def preparar_dataset():
    """
    Crea dataset/train, dataset/val y dataset/test para YOLO classify.
    Mezcla Kaggle + fotos_itgam, priorizando las fotos propias cuando existan.
    """
    descomprimir_archive()
    registros = recolectar_fuentes()
    if not registros:
        print("[ERROR] No hay imagenes para preparar dataset.")
        return

    destino = Path(DATASET_DIR)
    if destino.exists():
        print(f"[SICARS] Limpiando dataset anterior: {destino}")
        shutil.rmtree(destino)

    for split in ("train", "val", "test"):
        for categoria in CATEGORIAS:
            (destino / split / categoria).mkdir(parents=True, exist_ok=True)

    por_clase = {categoria: [] for categoria in CATEGORIAS}
    for categoria, img, fuente in registros:
        por_clase[categoria].append((img, fuente))

    random.seed(SEMILLA)
    conteos = {split: {categoria: 0 for categoria in CATEGORIAS} for split in ("train", "val", "test")}

    for categoria, items in por_clase.items():
        # Poner ITGAM primero para que no se pierdan si luego se limita manualmente el dataset.
        itgam = [item for item in items if item[1] == "itgam"]
        kaggle = [item for item in items if item[1] == "kaggle"]
        random.shuffle(kaggle)
        items = itgam + kaggle

        n = len(items)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        splits = {
            "train": items[:n_train],
            "val": items[n_train:n_train + n_val],
            "test": items[n_train + n_val:],
        }

        for split, split_items in splits.items():
            for idx, (img, fuente) in enumerate(split_items, start=1):
                nombre = f"{categoria}_{fuente}_{idx:06d}{img.suffix.lower()}"
                shutil.copy2(img, destino / split / categoria / nombre)
                conteos[split][categoria] += 1

    print("\n[SICARS] Dataset classify preparado:\n")
    for split in ("train", "val", "test"):
        total = 0
        print(f"  {split.upper()}:")
        for categoria in CATEGORIAS:
            n = conteos[split][categoria]
            total += n
            print(f"    {categoria:<15}: {n}")
        print(f"    TOTAL          : {total}\n")


def ver_dataset():
    base = Path(DATASET_DIR)
    if not base.exists():
        print("[SICARS] No existe dataset/. Ejecuta: python deteccion_tiempo_real.py --preparar-dataset")
        return

    print("\n[SICARS] Dataset classify actual:\n")
    total_global = 0
    for split in ("train", "val", "test"):
        total = 0
        print(f"  {split.upper()}:")
        for categoria in CATEGORIAS:
            n = len(imagenes_en(base / split / categoria))
            total += n
            print(f"    {categoria:<15}: {n}")
        total_global += total
        print(f"    TOTAL          : {total}\n")
    print(f"  TOTAL GLOBAL    : {total_global}")


def entrenar_modelo():
    train_dir = Path(DATASET_DIR) / "train"
    if not train_dir.exists():
        print("[SICARS] Primero prepara el dataset:")
        print("  python deteccion_tiempo_real.py --preparar-dataset")
        return

    print("\n[SICARS] Entrenando modelo SICARS classify...")
    print(f"  Modelo base : {MODELO_BASE}")
    print(f"  Dataset     : {DATASET_DIR}")
    print(f"  Epochs      : {EPOCHS}")
    print(f"  Salida      : {MODELO_PATH}\n")

    model = YOLO(MODELO_BASE)
    model.train(
        data=DATASET_DIR,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        project="runs/classify",
        name="sicars",
        exist_ok=True,
        task="classify",
    )

    if Path(MODELO_PATH).exists():
        print(f"\n[SICARS] Modelo listo: {MODELO_PATH}")
    else:
        print("\n[WARN] Entrenamiento terminado, pero no se encontro best.pt en la ruta esperada.")


def obtener_roi(frame):
    alto, ancho = frame.shape[:2]
    roi_w = int(ancho * ROI_ANCHO)
    roi_h = int(alto * ROI_ALTO)
    cx = ancho // 2
    cy = int(alto * ROI_CENTRO_Y)

    x1 = max(0, cx - roi_w // 2)
    y1 = max(124, cy - roi_h // 2)
    x2 = min(ancho, x1 + roi_w)
    y2 = min(alto, y1 + roi_h)

    return frame[y1:y2, x1:x2], (x1, y1, x2, y2)


def dibujar_panel(img, categoria, confianza, fps, roi_coords, lectura_valida):
    alto, ancho = img.shape[:2]
    categoria_mostrar = categoria if lectura_valida else "Baja confianza / Sin residuo"
    color = COLORES.get(categoria, COLORES["desconocido"]) if lectura_valida else COLORES["desconocido"]
    byte = BYTE_ARDUINO.get(categoria, "-") if lectura_valida else "-"
    x1, y1, x2, y2 = roi_coords

    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (ancho, 118), (18, 18, 18), -1)
    cv2.addWeighted(overlay, 0.68, img, 0.32, 0, img)

    fuente = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "SICARS-ITGAM", (14, 25), fuente, 0.62, (0, 255, 180), 1)
    cv2.putText(img, "Modelo: classify (solo zona central)", (14, 49), fuente, 0.48, (230, 230, 230), 1)
    cv2.putText(img, f"Categoria: {categoria_mostrar}", (14, 78), fuente, 0.72, color, 2)
    cv2.putText(img, f"Confianza: {confianza:.0%}   FPS: {fps:.1f}   Arduino: {byte}", (14, 103), fuente, 0.52, (230, 230, 230), 1)

    borde = color if lectura_valida else COLORES["desconocido"]
    cv2.rectangle(img, (x1, y1), (x2, y2), borde, 5)
    cv2.rectangle(img, (x1 + 8, y1 + 8), (x2 - 8, y2 - 8), (255, 255, 255), 1)

    texto = "Coloca aqui el residuo"
    (tw, th), _ = cv2.getTextSize(texto, fuente, 0.55, 1)
    tx = x1 + max(8, ((x2 - x1) - tw) // 2)
    ty = max(y1 - 10, 132)
    cv2.putText(img, texto, (tx, ty), fuente, 0.55, (255, 255, 255), 1)


def main():
    if not Path(MODELO_PATH).exists():
        print("\n[SICARS] No existe el modelo entrenado:")
        print(f"  {MODELO_PATH}")
        print("\nEjecuta:")
        print("  python deteccion_tiempo_real.py --preparar-dataset")
        print("  python deteccion_tiempo_real.py --entrenar")
        return

    print(f"\n[SICARS] Cargando modelo: {MODELO_PATH}")
    model = YOLO(MODELO_PATH)
    if getattr(model, "task", "") != "classify":
        print("[ERROR] Este script esta ajustado para modelos classify.")
        return

    print(f"[SICARS] Clases: {model.names}")

    cap = cv2.VideoCapture(CAMARA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir la camara CAMARA_INDEX={CAMARA_INDEX}.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("[SICARS] Clasificacion iniciada. Q=salir | S=guardar captura")

    fps = 0.0
    prev = time.time()
    historial = deque(maxlen=HISTORIAL_PREDICCIONES)

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        roi, roi_coords = obtener_roi(frame)
        results = model.predict(roi, imgsz=IMG_SIZE, verbose=False)
        probs = results[0].probs
        clase_id = int(probs.top1)
        confianza = float(probs.top1conf)
        nombre_raw = model.names[clase_id]
        categoria_actual = normalizar_clase(nombre_raw)
        lectura_valida = confianza >= CONFIANZA_MIN and categoria_actual in CATEGORIAS_SET
        if lectura_valida:
            historial.append(categoria_actual)

        if lectura_valida and historial:
            categoria = Counter(historial).most_common(1)[0][0]
        else:
            categoria = "desconocido"

        now = time.time()
        elapsed = now - prev
        if elapsed > 0:
            fps = 1.0 / elapsed
        prev = now

        if lectura_valida and categoria in BYTE_ARDUINO:
            letra_salida = BYTE_ARDUINO[categoria]  # Obtiene 'O', 'R' o 'N'
            try:
                arduino.write(letra_salida.encode())  # Envía el byte físico por USB
            except Exception as e:
                pass  # Evita que el programa se cierre si hay un parpadeo en el cable
        anotado = frame.copy()
        dibujar_panel(anotado, categoria, confianza, fps, roi_coords, lectura_valida)
        cv2.imshow(VENTANA_TITULO, anotado)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            guardar_captura(frame, categoria, confianza, lectura_valida)

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()
    print("[SICARS] Sistema cerrado correctamente.")


def guardar_captura(frame, categoria, confianza, lectura_valida):
    subdir = categoria if lectura_valida and categoria in CATEGORIAS_SET else "sin_clasificar"
    carpeta = Path(DATASET_DIR) / "capturas" / subdir
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"captura_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(str(destino), frame)
    print(f"[SICARS] Captura guardada: {destino}")


def imprimir_ayuda():
    print(
        """
SICARS-ITGAM - flujo simple con clasificacion

  python deteccion_tiempo_real.py --preparar-dataset
      Descomprime archive.zip si hace falta y mezcla Kaggle + fotos_itgam.

  python deteccion_tiempo_real.py --ver-dataset
      Muestra conteos del dataset classify.

  python deteccion_tiempo_real.py --entrenar
      Entrena YOLOv8 classify con yolov8n-cls.pt.

  python deteccion_tiempo_real.py
      Abre la camara y clasifica solo la zona central marcada en pantalla.

Salida para Arduino:
  organico       -> O
  reciclable     -> R
  no_reciclable  -> N
  confianza < 70% -> no se prepara ningun byte

Nota:
  Este flujo no dibuja bounding boxes reales. El recuadro es una zona de lectura
  para colocar el residuo y evitar que el fondo/personas afecten la prediccion.
  La categoria mostrada se estabiliza con la moda de las ultimas 8 lecturas confiables.
"""
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--preparar-dataset" in args or "--agregar-fotos" in args:
        preparar_dataset()
    elif "--ver-dataset" in args:
        ver_dataset()
    elif "--entrenar" in args:
        entrenar_modelo()
    elif "--ayuda" in args or "--help" in args:
        imprimir_ayuda()
    else:
        main()
