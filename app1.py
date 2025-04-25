from flask import Flask, render_template, request, jsonify
import subprocess

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

if __name__ == "__main__":
    app.run(debug=True)
