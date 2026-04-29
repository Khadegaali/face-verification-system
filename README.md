<div align="center">

# 🪪 FaceVerify

**Real-time face verification system using AI — built with Flask & DeepFace**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask)
![DeepFace](https://img.shields.io/badge/DeepFace-Facenet-orange?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-Camera-green?style=flat-square&logo=opencv)


> Register with your ID photo, then verify your identity live through your webcam in seconds.

</div>

---

##  Features

- **User Registration** — Upload your name, email, and an ID photo
-  **Live Camera Verification** — Real-time face matching via webcam
-  **AI-Powered Matching** — Uses FaceNet embeddings via DeepFace
-  **Confidence Score** — Returns similarity distance for every verification
-  **SQLite Storage** — Lightweight database, zero configuration
-  **Privacy First** — All uploaded photos are excluded from version control

---

##  Demo Flow

```
Register (name + email + ID photo)
        ↓
Verification Page (shows your ID photo)
        ↓
Start Camera → live frames captured → face compared to ID
        ↓
Result: REAL ✅  or  FAKE ❌  with distance score
```

---

##  Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Khadegaali/face-verification-system.git
cd face-verification-system
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python system.py
```

Open your browser at **http://127.0.0.1:5000**

---

##  Requirements

Create a `requirements.txt` with:

```
flask
deepface
opencv-python
pillow
numpy
werkzeug
tf-keras
```

Or install manually:

```bash
pip install flask deepface opencv-python pillow numpy werkzeug tf-keras
```

> **Note:** DeepFace will automatically download the FaceNet model weights (~90 MB) on first run.

---

##  Project Structure

```
face-verification-system/
│
├── system.py               # Main Flask application
├── requirements.txt        # Python dependencies
├── .gitignore              # Excludes uploads, DB, and secrets
│
├── templates/
│   ├── register.html       # Registration page
│   └── verify.html         # Verification page
│
└── uploads/                #  Gitignored — stores user photos
    └── (not tracked)
```

---

## ⚙️ How It Works

### Face Matching Algorithm

1. **Registration**: The uploaded ID photo is pre-processed (converted to RGB, contrast enhanced) and stored.
2. **Embedding**: DeepFace extracts a 128-dimensional FaceNet embedding from the ID photo.
3. **Live Capture**: The webcam captures frames every N frames.
4. **Comparison**: Each live frame embedding is compared to the ID embedding using **cosine distance**.
5. **Decision**: If distance < threshold → **REAL**, otherwise → **FAKE**.

### Distance Threshold

| Distance | Result |
|----------|--------|
| 0.00 – 0.35 | ✅ Strong match |
| 0.35 – 0.50 | ✅ Good match (REAL) |
| 0.50 – 0.65 | ❌ Weak match (FAKE) |
| 0.65+ | ❌ Different person |

Default threshold: **0.50** — adjustable in `system.py`:

```python
THRESHOLD = 0.50  # Lower = stricter
```

---

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Registration page |
| `POST` | `/register` | Submit registration form |
| `GET` | `/verify/<user_id>` | Verification page for a user |
| `POST` | `/start_camera_verify` | Trigger webcam verification |
| `GET` | `/results` | JSON list of all verifications |
| `GET` | `/uploads/<filename>` | Serve uploaded images |

### `/start_camera_verify` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | int | required | User to verify |
| `timeout` | int | `10` | Max seconds to wait |
| `frame_interval` | int | `5` | Check every N frames |

### Response Example

```json
{
  "status": "REAL",
  "distance": 0.387
}
```

---

## Privacy & Security

- The `uploads/` folder is **gitignored** — no user photos are ever committed
- The `face_verification.db` database is **gitignored** — no personal data is tracked
- For production use, consider:
  - Encrypting the database
  - Using environment variables for config
  - Adding authentication before the `/results` endpoint
  - Setting `debug=False` in `system.py`

---

## 🛠️ Configuration

| Variable | Location | Description |
|----------|----------|-------------|
| `THRESHOLD` | `system.py` | Match sensitivity (default: 0.50) |
| `timeout` | POST param | Camera session duration |
| `frame_interval` | POST param | How often to sample frames |
| `UPLOAD_FOLDER` | `system.py` | Where photos are stored |

---

##  Troubleshooting

**Image not showing on verify page?**
Make sure you're running the latest `system.py` — earlier versions stored the full filesystem path instead of just the filename.

**Camera won't open?**
- Check that no other app is using the webcam
- On Linux, try `cv2.VideoCapture(1)` if `0` doesn't work

**DeepFace can't detect face?**
- Ensure good lighting
- Face must be clearly visible and front-facing
- Try increasing `timeout` in the POST request

**First run is slow?**
DeepFace downloads FaceNet model weights (~90 MB) on first use. Subsequent runs are fast.

---


---

