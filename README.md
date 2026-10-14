# 📸 AI-Powered Multi-Platform Social Media Caption Generator & Studio

[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=flat&logo=streamlit)](https://share.streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Multimodal%20Vision-4285F4.svg?style=flat&logo=google)](https://ai.google.dev)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, full-stack social media studio that transforms visual assets (images and voice notes) into platform-optimized, high-engagement captions and hashtags using **Google Gemini Multimodal AI**.

---

## 🌟 Key Features

* **Multimodal Vision AI**: Understands visual content using Google Gemini (`gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`) with automatic retry and model fallback cascade.
* **Hands-Free Voice Context**: Record voice notes directly from your microphone via Streamlit's native audio input. The Gemini audio pipeline automatically transcribes campaign notes into caption context.
* **Multi-Platform Copywriting**: Generates ready-to-post, tailored captions adhering to platform-specific character limits, styles, and hashtag strategies for:
  * 📸 **Instagram** (up to 2,200 chars, storytelling, 5–8 niche hashtags, emojis, CTA)
  * 🐦 **X / Twitter** (strictly ≤ 280 chars, punchy hooks, 2–3 targeted tags)
  * 👥 **Facebook** (conversational, community questions, discussion hooks, 4–5 tags)
  * 💼 **LinkedIn** (professional insights, business takeaways, 5+ industry tags)
  * 📌 **Pinterest** (search-optimized, aesthetic descriptions, 5–7 tags)
  * ▶️ **YouTube** (video description format, key takeaways, subscribe CTA, 5–10 tags)
  * 🟢 **Kick** (high-energy stream titles, hype hooks, 2–3 tags)
* **8 Creative Tones**: Friendly & Upbeat, Professional, Playful & Witty, Inspirational, Humorous, Minimalist & Aesthetic, Urgent & Promotional, Storyteller.
* **Authentication & Security**: Built-in user registration, login, and guest mode using industry-standard **PBKDF2-HMAC-SHA256** password hashing with unique random salts and constant-time verification.
* **Caption History & Favorites**: Inspect past generations, toggle ❤️ / 🤍 platform favorites, download individual `.txt` captions, or clear records directly from lightweight JSON storage.
* **Dual Architecture**: Includes both a primary interactive **Streamlit web dashboard** (`app.py`) and a headless **FastAPI REST server** (`api/index.py`).

---

## 📁 Project Structure

```text
ai_captions/
├── app.py                      # ⭐ MAIN APP: Streamlit interactive web dashboard
├── api/
│   └── index.py                # 🌐 BACKEND: FastAPI REST server & Gemini API routes
├── origin/                     # 🔬 LAB & PROTOTYPES: Evolutionary history of the project
│   ├── 1_caption_image.py      # Prototype 1: Offline BLIP image captioning CLI
│   └── 2_build_search_index.py # Prototype 2: CLIP + FAISS vector search index builder
├── data/                       # Sample images & JSON runtime storage
│   ├── astronaut.jpg           # Sample test images
│   ├── cabin.jpg
│   ├── cake.jpg
│   ├── car.jpg
│   ├── cyberpunk.jpg
│   └── friends.jpg
├── requirements.txt            # Python dependencies manifest
├── .env.example                # Safe environment variable configuration template
├── .gitignore                  # Git ignore rules (protects API keys & user data)
└── README.md                   # Project documentation
```

---

## 🔄 End-to-End Workflow Pipeline

```text
[ 1. User Ingestion ]
  • Uploads image (JPG, PNG, WEBP)
  • (Optional) Dictates voice notes via microphone or types campaign context
  • Selects target social platforms and creative tone
        │
        ▼
[ 2. Gemini Multimodal Analysis ]
  • Vision: Gemini extracts factual, one-sentence scene understanding
  • Audio: Gemini transcribes microphone speech into contextual text notes
        │
        ▼
[ 3. Platform Copywriting & Structuring ]
  • Formulates specialized copywriting prompts per platform
  • Enforces character limits, hashtag density, hooks, and call-to-actions
  • 3-tier model fallback: gemini-3.5-flash-lite ➔ gemini-3.5-flash ➔ gemini-3.6-flash
        │
        ▼
[ 4. Post-Processing & Persistence ]
  • Validates and clamps character lengths strictly within platform ceilings
  • Auto-saves generated captions to data/history.json
        │
        ▼
[ 5. Interactive Studio Display ]
  • Platform cards with live character count meters
  • 1-click text download (.txt) per platform
  • Interactive ❤️ Like / 🤍 Unlike favorites system
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jagadeesh-boyalla-03/ai_captions.git
cd ai_captions
```

### 2. Set Up a Virtual Environment

* **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```

* **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key

Create a `.env` file in the root directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

Add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

*(You can get a free API key at [Google AI Studio](https://aistudio.google.com/)).*

---

## 💻 Running the Application

### Option A: Interactive Streamlit Web Studio (Recommended)

Run the main application dashboard:

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

### Option B: FastAPI REST Backend Service

Run the headless asynchronous API server:

```bash
uvicorn api.index:app --reload --port 8000
```

* **API Base URL**: `http://localhost:8000`
* **Interactive Swagger UI**: `http://localhost:8000/docs`
* **Redoc Documentation**: `http://localhost:8000/redoc`

---

### Option C: Evolutionary Prototypes (`origin/`)

* **Local Offline BLIP Captioning**:
  ```bash
  python origin/1_caption_image.py data/astronaut.jpg
  ```
* **Build CLIP Vector Search Index**:
  ```bash
  python origin/2_build_search_index.py ./data
  ```

---

## 🔌 API Endpoints Summary (`api/index.py`)

| Method | Endpoint | Description | Auth Required |
|:---|:---|:---|:---:|
| `GET` | `/health` | Healthcheck and service status probe | No |
| `POST` | `/api/auth/register` | Register new user account with PBKDF2 hash | No |
| `POST` | `/api/auth/login` | Authenticate credentials and issue 30-day token | No |
| `GET` | `/api/auth/me` | Retrieve profile and lifetime caption stats | Yes (`Bearer <token>`) |
| `POST` | `/api/auth/logout` | Invalidate active session token | Yes (`Bearer <token>`) |
| `POST` | `/api/generate` | Multimodal caption generation from image/video | Optional (Guest/User) |
| `GET` | `/api/history` | Retrieve saved caption generation history | Yes (`Bearer <token>`) |
| `PUT` | `/api/history/{id}/like` | Update liked platforms for a history record | Yes (`Bearer <token>`) |
| `DELETE` | `/api/history/{id}` | Delete a specific saved caption item | Yes (`Bearer <token>`) |

---

## 🚢 Deployment on Streamlit Community Cloud

Deploying this app live to **Streamlit Community Cloud** takes under 2 minutes:

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **Open Streamlit Community Cloud**:
   * Navigate to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
   * Click **"Create app"** (or **"New app"**).

3. **Configure App Settings**:
   * **Repository**: `jagadeesh-boyalla-03/ai_captions`
   * **Branch**: `main`
   * **Main file path**: `app.py`

4. **Configure Advanced Settings**:
   * Click **"Advanced settings..."** before deploying.
   * **Python version**: Select **`3.11`** or **`3.12`** *(avoid experimental 3.14)*.
   * **Secrets**: In the secrets box, enter your Gemini API key:
     ```toml
     GEMINI_API_KEY = "your_actual_gemini_api_key_here"
     ```
   * Click **Save**.

5. **Deploy**:
   * Click **"Deploy"**! Streamlit Cloud will install dependencies from `requirements.txt` and launch your live studio URL.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
