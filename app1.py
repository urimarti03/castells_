import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import cv2.aruco as aruco
import numpy as np
import math
import threading

# Función para calcular ángulos
def calcular_angulo_360(p1, p2, p3):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    angulo_rad = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    angulo_deg = math.degrees(angulo_rad)
    return int(round(angulo_deg + 360)) % 360

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Detección de ArUco y Ángulos")

# Parte izquierda - Info
frame_izquierdo = tk.Frame(ventana, width=800, bg="grey")
frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

titulo = tk.Label(frame_izquierdo, text="Detección de Ángulos", font=("Helvetica", 18))
titulo.pack(pady=10)

texto_info = tk.Label(
    frame_izquierdo,
    text="Esperando detección de ángulos...",
    wraplength=280,
    justify="left",
    font=("Helvetica", 64),
    bg="grey"
)
texto_info.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Parte derecha - Video
frame_derecho = tk.Frame(ventana)
frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

canvas = tk.Canvas(frame_derecho, width=854, height=480)
canvas.pack(pady=20)

angulos_label = tk.Label(frame_derecho, text="Ángulos detectados: ", font=("Helvetica", 64), bg="lightgray")
angulos_label.pack(pady=5)

# Inicializar OpenCV
cap = None
is_live_video = True  # Estado de video en vivo o archivo cargado
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

archivo_angulos = "angulos_detectados.txt"
with open(archivo_angulos, "w") as f:
    f.write("ID | Ángulo 1 (p1→p2→p3) | Ángulo 2 (p2→p3→p4)\n")
    f.write("---------------------------------------------\n")

ultimos_centros = {}  # {id: [puntos]}
frame_interval = 2  # Procesar cada n fotogramas (reduce la carga de procesamiento)
frame_count = 0

# Función para procesar video
def procesar_video():
    global angulos_label, cap, is_live_video, frame_count
    if cap is None:
        print("No se ha inicializado la fuente de video correctamente.")
        return
    
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el fotograma")
        return

    frame_count += 1
    
    # Procesar cada 'frame_interval' fotogramas
    if frame_count % frame_interval != 0:
        ventana.after(1, procesar_video)
        return
    
    # Reducir el tamaño de la imagen para acelerar el procesamiento
    frame = cv2.resize(frame, (640, 480))  # Redimensiona a 640x480 para mejorar el rendimiento

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    marcadores_actuales = {}
    angulos_detectados = []

    if ids is not None:
        for i, marker_id in enumerate(ids.flatten()):
            c = corners[i][0]
            cX, cY = int(np.mean(c[:, 0])), int(np.mean(c[:, 1]))

            if marker_id not in marcadores_actuales:
                marcadores_actuales[marker_id] = []
            marcadores_actuales[marker_id].append((cX, cY))

    for marker_id in marcadores_actuales:
        puntos_actuales = marcadores_actuales[marker_id]
        if len(puntos_actuales) == 4:
            ultimos_centros[marker_id] = sorted(puntos_actuales, key=lambda p: p[1])
        else:
            if marker_id not in ultimos_centros:
                ultimos_centros[marker_id] = puntos_actuales

    for marker_id, puntos in ultimos_centros.items():
        if len(puntos) > 1:
            for i in range(len(puntos) - 1):
                cv2.line(frame, puntos[i], puntos[i + 1], (0, 255, 255), 2)
            for punto in puntos:
                cv2.circle(frame, punto, 5, (255, 0, 255), -1)

            if len(puntos) == 4:
                p1, p2, p3, p4 = puntos
                angulo1 = calcular_angulo_360(p1, p2, p3)
                angulo2 = calcular_angulo_360(p2, p3, p4)

                cv2.putText(frame, f"{angulo1}°", p2,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(frame, f"{angulo2}°", p3,
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                with open(archivo_angulos, "a") as f:
                    f.write(f"{marker_id} | {angulo1:>17} | {angulo2:>17}\n")
                
                angulos_detectados.append(f"Ángulo 1: {angulo1}°, Ángulo 2: {angulo2}°")

    # Actualizar el texto de la etiqueta angulos_label con los ángulos detectados
    if angulos_detectados:
        angulos_label.config(text="\n".join(angulos_detectados))
    else:
        angulos_label.config(text="Esperando detección de ángulos...")

    # Mostrar frame en tkinter
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(frame_rgb)
    img_tk = ImageTk.PhotoImage(image=img_pil)

    canvas.create_image(0, 0, image=img_tk, anchor=tk.NW)
    canvas.img_tk = img_tk  # Importante para que no se elimine la imagen

    # Procesar video en un hilo separado para no bloquear la interfaz de usuario
    ventana.after(1, procesar_video)  # Llamar a esta función nuevamente después de 1 ms

# Función para cambiar entre video en vivo y cargar un archivo
def cambiar_fuente_video():
    global cap, is_live_video, video_file
    if is_live_video:
        # Detener la captura de video en vivo
        if cap is not None:
            cap.release()

        # Cambiar a archivo de video
        video_file = filedialog.askopenfilename(filetypes=[("Archivos de video", "*.mp4 *.avi")])
        if video_file:
            cap = cv2.VideoCapture(video_file)
            is_live_video = False
            texto_info.config(text="Cargando video...")
            # Iniciar procesamiento de video en un hilo separado
            threading.Thread(target=procesar_video, daemon=True).start()  # Ejecutar procesar_video en un hilo
        else:
            texto_info.config(text="No se seleccionó ningún archivo.")
    else:
        # Volver a la cámara en vivo
        cap.release()
        cap = cv2.VideoCapture(1)
        is_live_video = True
        texto_info.config(text="Capturando video en vivo...")
        threading.Thread(target=procesar_video, daemon=True).start()  # Ejecutar procesar_video en un hilo

# Crear botón para cambiar entre fuentes de video
boton_cambiar_fuente = tk.Button(frame_izquierdo, text="Cambiar fuente de video", font=("Helvetica", 12), command=cambiar_fuente_video)
boton_cambiar_fuente.pack(pady=10)

# Iniciar la función de procesamiento de video para el video en vivo en un hilo
cap = cv2.VideoCapture(1)  # Inicializa la cámara en vivo al principio
thread = threading.Thread(target=procesar_video, daemon=True)
thread.start()

# Ejecutar la aplicación
ventana.mainloop()

# Liberar la cámara
cap.release()
cv2.destroyAllWindows()
