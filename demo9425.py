import cv2
import cv2.aruco as aruco
import numpy as np
import math

cap = cv2.VideoCapture(1)  # Ajusta a 0, 1 o 2 según tu cámara

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

archivo_angulos = "angulos_detectados.txt"
with open(archivo_angulos, "w") as f:
    f.write("ID | Ángulo 1 (p1→p2→p3) | Ángulo 2 (p2→p3→p4)\n")
    f.write("---------------------------------------------\n")

ultimos_centros = {}    # {id: [puntos]}

def calcular_angulo_360(p1, p2, p3):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    angulo_rad = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    angulo_deg = math.degrees(angulo_rad)
    return int(round(angulo_deg + 360)) % 360

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el fotograma")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    marcadores_actuales = {}

    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)

        for i, marker_id in enumerate(ids.flatten()):
            c = corners[i][0]
            cX, cY = int(np.mean(c[:, 0])), int(np.mean(c[:, 1]))

            if marker_id not in marcadores_actuales:
                marcadores_actuales[marker_id] = []
            marcadores_actuales[marker_id].append((cX, cY))

            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)
            cv2.putText(frame, f"ID:{marker_id}", (cX + 10, cY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Actualizar los puntos de cada ID
    for marker_id in marcadores_actuales:
        puntos_actuales = marcadores_actuales[marker_id]

        # Si hay exactamente 4, reemplazar y ordenar verticalmente
        if len(puntos_actuales) == 4:
            ultimos_centros[marker_id] = sorted(puntos_actuales, key=lambda p: p[1])
        else:
            # Si no se detectaron los 4, mantener los últimos conocidos
            if marker_id not in ultimos_centros:
                ultimos_centros[marker_id] = puntos_actuales

    # Dibujar y calcular para los IDs conocidos
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

    cv2.imshow("Detección de ArUco", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
