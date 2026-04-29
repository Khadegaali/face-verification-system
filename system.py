# from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
# import sqlite3, os
# from datetime import datetime
# from werkzeug.utils import secure_filename
# from deepface import DeepFace
# import cv2
# from PIL import Image, ImageEnhance
# import numpy as np
# import time

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# DB_PATH = os.path.join(BASE_DIR, "face_verification.db")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# app = Flask(__name__)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# #  Database Setup 
# def init_db():
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     try:
#         c = conn.cursor()
#         c.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT,
#                 email TEXT UNIQUE,
#                 id_image TEXT,
#                 result TEXT,
#                 distance REAL,
#                 timestamp TEXT
#             )
#         ''')
#         conn.commit()
#     finally:
#         conn.close()

# init_db()

# def ensure_rgb_and_enhance(path):
#     try:
#         img = Image.open(path)
#         if img.mode != "RGB":
#             img = img.convert("RGB")
#         enhancer = ImageEnhance.Contrast(img)
#         img = enhancer.enhance(1.4)
#         img.save(path)
#     except Exception as e:
#         print("Preprocess warning:", e)

# def save_user(name, email, image_filename):
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     try:
#         c = conn.cursor()
#         c.execute("INSERT INTO users (name, email, id_image, timestamp) VALUES (?, ?, ?, ?)",
#                   (name, email, image_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#         conn.commit()
#         return c.lastrowid
#     finally:
#         conn.close()

# def get_user(user_id):
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     try:
#         c = conn.cursor()
#         c.execute("SELECT id, name, email, id_image FROM users WHERE id = ?", (user_id,))
#         return c.fetchone()
#     finally:
#         conn.close()

# def update_verification(user_id, result, distance):
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     try:
#         c = conn.cursor()
#         c.execute("UPDATE users SET result=?, distance=?, timestamp=? WHERE id=?",
#                   (result, float(distance), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
#         conn.commit()
#     finally:
#         conn.close()

# # Routes 
# @app.route('/')
# def home():
#     return render_template("register.html")

# @app.route('/register', methods=['POST'])
# def register():
#     name = request.form.get("name")
#     email = request.form.get("email")
#     id_file = request.files.get("id_image")

#     if not name or not email or not id_file:
#         return "Missing fields", 400

#     filename = secure_filename(email + "_" + id_file.filename)
#     save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#     id_file.save(save_path)
#     ensure_rgb_and_enhance(save_path)

#     try:
#         user_id = save_user(name, email, save_path)
#     except Exception as e:
#         return f"DB error: {e}", 400

#     return redirect(url_for("verify_page", user_id=user_id))

# @app.route('/verify/<int:user_id>')
# def verify_page(user_id):
#     user = get_user(user_id)
#     if not user:
#         return "User not found", 404
#     return render_template("verify.html", user_id=user[0], name=user[1], email=user[2], id_image=user[3])

# @app.route('/start_camera_verify', methods=['POST'])
# def start_camera_verify():
#     try:
#         user_id = int(request.form.get("user_id"))
#         timeout_seconds = int(request.form.get("timeout", 10))
#         frame_interval = int(request.form.get("frame_interval", 5))
#     except:
#         return jsonify({"error": "Invalid parameters"}), 400

#     user = get_user(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     id_image_path = user[3]
#     ensure_rgb_and_enhance(id_image_path)

#     try:
#         rep = DeepFace.represent(
#             img_path=id_image_path,
#             model_name="Facenet",
#             enforce_detection=True,
#             detector_backend="opencv"
#         )
#         id_emb = np.array(rep[0]["embedding"], dtype=np.float32)
#         id_emb = id_emb / np.linalg.norm(id_emb)
#     except Exception as e:
#         return jsonify({"error": f"Cannot compute embedding for ID image: {e}"}), 500

#     THRESHOLD = 0.50
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         return jsonify({"error": "Cannot open camera"}), 500

#     start_ts = time.time()
#     frame_count = 0
#     last_status = None

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame_count += 1
#         if frame_count % frame_interval == 0:
#             tmp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"live_{user_id}.jpg")
#             cv2.imwrite(tmp_path, frame)
#             ensure_rgb_and_enhance(tmp_path)

#             try:
#                 rep2 = DeepFace.represent(
#                     img_path=tmp_path,
#                     model_name="Facenet",
#                     enforce_detection=True,
#                     detector_backend="opencv"
#                 )
#                 live_emb = np.array(rep2[0]["embedding"], dtype=np.float32)
#                 live_emb = live_emb / np.linalg.norm(live_emb)

#                 dist = 1.0 - float(np.dot(id_emb, live_emb))
#                 is_match = dist < THRESHOLD
#                 status = "REAL" if is_match else "FAKE"
#                 update_verification(user_id, status, dist)
#                 last_status = {"status": status, "distance": dist}

#                 if is_match:
#                     cap.release()
#                     cv2.destroyAllWindows()
#                     return jsonify(last_status)
#             except Exception as e:
#                 print("Frame processing warning:", e)

#         if time.time() - start_ts > timeout_seconds:
#             break

#     cap.release()
#     cv2.destroyAllWindows()
#     if last_status:
#         return jsonify(last_status)
#     else:
#         update_verification(user_id, "NO_FACE_DETECTED", 1.0)
#         return jsonify({"status": "NO_FACE_DETECTED", "message": "No face detected during session"}), 200

# @app.route('/results')
# def results():
#     conn = sqlite3.connect(DB_PATH, timeout=10)
#     try:
#         c = conn.cursor()
#         c.execute("SELECT id, name, email, result, distance, timestamp FROM users ORDER BY id DESC")
#         rows = c.fetchall()
#     finally:
#         conn.close()

#     data = []
#     for r in rows:
#         data.append({
#             "id": r[0],
#             "name": r[1],
#             "email": r[2],
#             "result": r[3],
#             "distance": r[4],
#             "timestamp": r[5]
#         })
#     return jsonify(data)

# @app.route('/uploads/<path:filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# if __name__ == "__main__":
#     app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3, os
from datetime import datetime
from werkzeug.utils import secure_filename
from deepface import DeepFace
import cv2
from PIL import Image, ImageEnhance
import numpy as np
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "face_verification.db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ─── Database Setup ───────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                id_image TEXT,
                result TEXT,
                distance REAL,
                timestamp TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

init_db()

def ensure_rgb_and_enhance(path):
    try:
        img = Image.open(path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)
        img.save(path)
    except Exception as e:
        print("Preprocess warning:", e)

def save_user(name, email, image_filename):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c = conn.cursor()
        # Store only the filename (not the full path)
        c.execute("INSERT INTO users (name, email, id_image, timestamp) VALUES (?, ?, ?, ?)",
                  (name, email, image_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, email, id_image FROM users WHERE id = ?", (user_id,))
        return c.fetchone()
    finally:
        conn.close()

def update_verification(user_id, result, distance):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET result=?, distance=?, timestamp=? WHERE id=?",
                  (result, float(distance), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
    finally:
        conn.close()

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    id_file = request.files.get("id_image")

    if not name or not email or not id_file:
        return "Missing fields", 400

    # ✅ FIX: store only the filename, not the full path
    filename = secure_filename(email + "_" + id_file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    id_file.save(save_path)
    ensure_rgb_and_enhance(save_path)

    try:
        user_id = save_user(name, email, filename)   # ✅ pass filename, not save_path
    except Exception as e:
        return f"DB error: {e}", 400

    return redirect(url_for("verify_page", user_id=user_id))

@app.route('/verify/<int:user_id>')
def verify_page(user_id):
    user = get_user(user_id)
    if not user:
        return "User not found", 404

    # ✅ FIX: build a proper URL for the image using url_for
    image_url = url_for('uploaded_file', filename=user[3])

    return render_template(
        "verify.html",
        user_id=user[0],
        name=user[1],
        email=user[2],
        id_image=image_url   # ✅ pass URL, not filesystem path
    )

@app.route('/start_camera_verify', methods=['POST'])
def start_camera_verify():
    try:
        user_id = int(request.form.get("user_id"))
        timeout_seconds = int(request.form.get("timeout", 10))
        frame_interval = int(request.form.get("frame_interval", 5))
    except Exception:
        return jsonify({"error": "Invalid parameters"}), 400

    user = get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ✅ FIX: reconstruct the full filesystem path from the stored filename
    id_image_path = os.path.join(app.config["UPLOAD_FOLDER"], user[3])
    ensure_rgb_and_enhance(id_image_path)

    try:
        rep = DeepFace.represent(
            img_path=id_image_path,
            model_name="Facenet",
            enforce_detection=True,
            detector_backend="opencv"
        )
        id_emb = np.array(rep[0]["embedding"], dtype=np.float32)
        id_emb = id_emb / np.linalg.norm(id_emb)
    except Exception as e:
        return jsonify({"error": f"Cannot compute embedding for ID image: {e}"}), 500

    THRESHOLD = 0.50
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({"error": "Cannot open camera"}), 500

    start_ts = time.time()
    frame_count = 0
    last_status = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_interval == 0:
            tmp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"live_{user_id}.jpg")
            cv2.imwrite(tmp_path, frame)
            ensure_rgb_and_enhance(tmp_path)

            try:
                rep2 = DeepFace.represent(
                    img_path=tmp_path,
                    model_name="Facenet",
                    enforce_detection=True,
                    detector_backend="opencv"
                )
                live_emb = np.array(rep2[0]["embedding"], dtype=np.float32)
                live_emb = live_emb / np.linalg.norm(live_emb)

                dist = 1.0 - float(np.dot(id_emb, live_emb))
                is_match = dist < THRESHOLD
                status = "REAL" if is_match else "FAKE"
                update_verification(user_id, status, dist)
                last_status = {"status": status, "distance": dist}

                if is_match:
                    cap.release()
                    cv2.destroyAllWindows()
                    return jsonify(last_status)
            except Exception as e:
                print("Frame processing warning:", e)

        if time.time() - start_ts > timeout_seconds:
            break

    cap.release()
    cv2.destroyAllWindows()

    if last_status:
        return jsonify(last_status)
    else:
        update_verification(user_id, "NO_FACE_DETECTED", 1.0)
        return jsonify({"status": "NO_FACE_DETECTED", "message": "No face detected during session"}), 200

@app.route('/results')
def results():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, email, result, distance, timestamp FROM users ORDER BY id DESC")
        rows = c.fetchall()
    finally:
        conn.close()

    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "result": r[3],
            "distance": r[4],
            "timestamp": r[5]
        })
    return jsonify(data)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)