from flask import Flask, request, jsonify
from analyse_img import extraction_intensite
from traitement import calibration
import tempfile
import os
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = None
app.config['MAX_FORM_MEMORY_SIZE'] = None

# Define the route for the default homepage
@app.route('/')
def home():
    return "Hello, World! Your Flask app is running successfully."

@app.route("/analyse", methods=["POST"])
def analyze_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    uploaded_file = request.files["image"]

    if uploaded_file.filename == "":
        return jsonify({"error": "No image selected"}), 400

    temp_path = None

    try:
        # Create a secure temporary file.
        # delete=False because we need to pass its path to the handler.
        with tempfile.NamedTemporaryFile(
            suffix=".img",
            delete=False
        ) as temp_file:
            temp_path = temp_file.name
            uploaded_file.save(temp_path)

        print("Temporary file saved at:", temp_path)
        print("Request form data:", request.form)

        # Pass the path to your image-analysis handler
        intensity, intensity_r, intensity_g, intensity_b = extraction_intensite(temp_path, int(request.form.get("yh") or 0), int(request.form.get("yb") or 0), int(request.form.get("xMin") or 0), int(request.form.get("xMin") or 0) + int(request.form.get("xWidth") or 0), showplots=False, debug=False)

        return jsonify(intensity.tolist()), 200

    except Exception as e:
        app.logger.exception("Image processing failed")
        return jsonify({"error": "Image processing failed"}), 500

    finally:
        # Always delete the temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.route("/calibration", methods=["POST"])
def calib():
    data = request.get_json()
    slope, intercept = calibration(data.get("longueurs"), data.get("intensities"))
    return jsonify({"slope":slope.item(), "intercept":intercept.item()}), 200 #type:ignore

# Start the local development server
if __name__ == '__main__':
    app.run(debug=True)
