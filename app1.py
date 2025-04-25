from flask import Flask, render_template,Response, request, jsonify
import subprocess
import cv2
import cv2.aruco as aruco
import math
import numpy as np

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/iniciar-deteccion", methods=["POST"])
def iniciar_deteccion():
    try:
        subprocess.Popen(["python", "scripts/detector_aruco.py"])
        return jsonify({"estado": "La detección se ha iniciado"})
    except Exception as e:
        return jsonify({"estado": f"Error al iniciar la detección: {e}"}), 500

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
def calcular_angulo_360(p1, p2, p3):
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    angulo_rad = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    angulo_deg = math.degrees(angulo_rad)
    return int(round(angulo_deg + 360)) % 360

def gen_frames():
    cap = cv2.VideoCapture(0)
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, parameters)

    ultimos_centros = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)

        marcadores_actuales = {}

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
        else:
            ultimos_centros.clear()

        # 🖍️ Dibujo
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

                cv2.putText(frame, f"{angulo1}°", p2, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                cv2.putText(frame, f"{angulo2}°", p3, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 🔁 Enviar frame modificado al navegador
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()



if __name__ == "__main__":
    app.run(debug=True)

