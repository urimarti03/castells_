import cv2
import cv2.aruco as aruco
import numpy as np
import math

# Iniciar captura de video
cap = cv2.VideoCapture(0)  # Cambia a 0, 1 o 2 según la cámara disponible

# Crear el diccionario y el detector de ArUco con la nueva API
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

# Archivo donde se guardarán los ángulos detectados
archivo_angulos = "angulos_detectados.txt"

# Limpiar archivo al inicio
with open(archivo_angulos, "w", encoding="utf-8") as f:
    f.write("ID | Ángulo 1 (p1→p2→p3) | Ángulo 2 (p2→p3→p4)\n")
    f.write("---------------------------------------------\n")

def calcular_angulo_360(p1, p2, p3):
    """ Calcula el ángulo en el rango de 0° a 360° entre los vectores p1->p2 y p2->p3 """
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)

    angulo_rad = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    angulo_deg = math.degrees(angulo_rad)

    if angulo_deg < 0:
        angulo_deg += 360

    return int(round(angulo_deg))  # Retorna un número entero

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el fotograma")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detectar marcadores ArUco
    corners, ids, _ = detector.detectMarkers(gray)

    # Diccionario para almacenar los centros por ID
    centros_por_id = {}

    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)

        for i, marker_id in enumerate(ids.flatten()):
            c = corners[i][0]
            cX = int(np.mean(c[:, 0]))
            cY = int(np.mean(c[:, 1]))

            if marker_id not in centros_por_id:
                centros_por_id[marker_id] = []
            centros_por_id[marker_id].append((cX, cY))

            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"ID:{marker_id}", (cX + 10, cY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        for marker_id, centros in centros_por_id.items():
            if len(centros) >= 4:
                for i in range(len(centros) - 3):
                    p1, p2, p3, p4 = centros[i:i+4]

                    # Verificar alineación vertical antes de conectar
                    def estan_alineados_verticalmente(p1, p2):
                        return abs(p1[0] - p2[0]) < 15  # Umbral de alineación en X

                    if estan_alineados_verticalmente(p1, p2):
                        cv2.line(frame, p1, p2, (255, 0, 0), 2)

                    if estan_alineados_verticalmente(p2, p3):
                        cv2.line(frame, p2, p3, (255, 0, 0), 2)

                    if estan_alineados_verticalmente(p3, p4):
                        cv2.line(frame, p3, p4, (255, 0, 0), 2)


                    # Calcular ángulos
                    angulo1 = calcular_angulo_360(p1, p2, p3)
                    angulo2 = calcular_angulo_360(p2, p3, p4)

                    # Mostrar ángulos en pantalla
                    cv2.putText(frame, f"{angulo1}°", p2, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    cv2.putText(frame, f"{angulo2}°", p3, 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    # Guardar en el archivo
                    with open(archivo_angulos, "a") as f:
                        f.write(f"ID: {marker_id} | Ángulo 1: {angulo1}° | Ángulo 2: {angulo2}°\n")

    cv2.imshow("Detección de ArUco", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()