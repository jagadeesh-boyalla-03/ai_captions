# AI-Powered Multi-Platform Social Media Caption Generator & Studio

[![FastAPI](https://img.shields.io/badge/FastAPI-0.139+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Multimodal%20Vision-4285F4.svg?style=flat&logo=google)](https://ai.google.dev)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-26%20Passed-brightgreen.svg?style=flat&logo=pytest)](file:///c:/Users/boyal/OneDrive/Desktop/ai-projects/1/tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, full-stack social media studio that transforms visual images and videos into platform-optimized, high-engagement captions and hashtags with multimodal AI powered by **Google Gemini**.

---

## 🌟 Key Features

* **Multimodal Vision AI**: Analyzes uploaded photos and visual assets using Google Gemini to capture visual context, vibe, mood, and subject details.
* **Multi-Platform Tailoring**: Automatically generates distinct, formatted captions adhering to platform rules, character limits, tone, and hashtag strategies for:
  * 📸 **Instagram** (up to 2,200 chars, storytelling, trending & niche tags)
  * 🐦 **X / Twitter** (strictly ≤ 280 chars, punchy hooks, targeted tags)
  * 👥 **Facebook** (conversational, community questions, discussion hooks)
  * 💼 **LinkedIn** (professional, thought leadership, business insights)
  * 📌 **Pinterest** (search-optimized, aesthetic descriptions)
  * ▶️ **YouTube** (description formatting, timestamps, subscribe CTAs)
  * 🟢 **Kick** (high-energy stream titles, hype hooks)
* **User Authentication**: Secure user registration, sign-in, session tokens, and PBKDF2 password hashing with unique salts.
* **Caption History & Management**: Registered users automatically save generation history to JSON storage (`data/history.json`) with options to inspect, like/unlike, or delete items.
* **Guest Mode**: 1-click generation without mandatory login for rapid previews.
* **Interactive Web App**: Sleek, modern single-page dashboard with real-time copy-to-clipboard, tone customization, and platform toggles.
* **Tested & Reliable**: Full automated test suite covering authentication, API endpoints, and caption generation with 100% passing tests.

---

## 📁 Project Structure

```text
ai-powered-social-caption-generator/
│
├── api/
│   └── index.py            # FastAPI backend, Gemini vision engine, Auth & JSON routes
│
├── static/
│   └── auth_robot.jpg      # Static illustration assets
│
├── data/
│   ├── users.json          # JSON store (Registered users & PBKDF2 hashes)
│   ├── history.json        # JSON store (Caption generations & platform likes)
│   └── sessions.json       # JSON store (Active auth session tokens)
│
├── tests/
│   ├── conftest.py         # Pytest configuration, fixtures & test setup
│   ├── test_api.py         # Health, SPA routing & history endpoint tests
│   ├── test_auth.py        # PBKDF2 password hashing & session token tests
│   └── test_captions.py    # Gemini retry, fallback & platform clamping tests
│
├── origin/                 # Standalone prototypes and research scripts
│   ├── 1_caption_image.py
│   └── 6_social_media_captions.py     # Standalone terminal caption generator
│
├── app.py                  # Streamlit application with JSON auth & history
├── requirements.txt        # Python dependency manifest
└── README.md               # Project documentation
```

---

## 🧠 Step-by-Step Project Explanation & Workflow Pipeline

This project is built as a complete, modern full-stack web application designed to take an image or video, analyze it with multimodal AI, and produce platform-tailored social captions. Here is how the entire system functions step-by-step:

### 🔄 End-to-End Execution Flow (6-Stage Pipeline)

```
[ User Action ]
  1. Uploads media file (Drag-and-Drop or File Picker)
  2. Selects target networks (Instagram, X, LinkedIn, etc.)
  3. Dictates campaign context using Hands-Free Voice Mic (Web Speech API)
        │
        ▼
[ Client Processing ]
  • Client-side FileReader renders instant image preview thumbnail
  • Reactive input validator enables "Generate Social Captions" action button
  • Packages data into multipart/form-data with optional user auth bearer token
        │
        ▼
[ Backend Ingestion & Auth (FastAPI / Streamlit) ]
  • POST /api/generate receives multipart payload
  • Authenticates bearer token or session state against JSON user store (if logged in)
  • Validates media mime-type (PNG/JPEG/WEBP or MP4 video)
        │
        ▼
[ Stage 1: Multimodal Vision Ingestion (Google Gemini) ]
  • Image: Converted to RGB buffer and fed to Gemini Multimodal Vision API
  • Video: Uploaded via Gemini File API, polled until ready, and analyzed
  • Output: Factual, objective scene & subject description (e.g., "A sunset over mountain lake")
        │
        ▼
[ Stage 2: Prompt Engineering & Structured Inference ]
  • Injects visual description, tone rules, user voice context, and platform limits
  • Enforces structured JSON schema response (SocialCaptions Pydantic model)
  • Platform-specific constraints:
      - X/Twitter: Strictly ≤ 280 chars, punchy hooks
      - Instagram: Up to 2,200 chars with 5-8 niche hashtags
      - LinkedIn: Insight-driven with professional business takeaway
      - YouTube: Long-form video description format with subscribe CTA
  • Model fallback cascade: gemini-3.5-flash-lite ➔ gemini-3.5-flash ➔ gemini-3.6-flash
        │
        ▼
[ Stage 3: Post-Processing & Persistence ]
  • String clamping guarantees strict compliance with platform character limits
  • If user is authenticated, caption record is saved to JSON history store (`data/history.json`)
  • Returns structured JSON payload to client
        │
        ▼
[ Stage 4: UI Rendering & Interaction ]
  • Glassmorphism results grid renders platform cards with character meters
  • Single-caption and "Copy All Captions" 1-click clipboard utilities
  • Live session stats (total generated captions badge) updated in top navbar
```

---

### 📂 Codebase Section-by-Section Step Guide

#### Frontend Architecture (`frontend/index.html` & `index.html`)
* **STEP 1: Document Head & Fonts**: Loads Tailwind CDN, modern Google Fonts (`Outfit` & `Plus Jakarta Sans`), and cache-control meta tags.
* **STEP 2: Custom Glassmorphism Theme**: Custom CSS for dark glass panels (`.glass-card`), glowing amber buttons, custom scrollbars, and active platform pills.
* **STEP 3: Top Navigation Bar**: Dynamic state switching between guest actions (Sign in / Sign up) and authenticated user profile (initials avatar, dropdown menu, caption count badge).
* **STEP 4: Authentication View (`#authScreen`)**: Split card featuring a 3D robot mascot illustration, Google/Outlook OAuth demo buttons, and responsive Sign Up / Log In form.
* **STEP 5: Studio Workspace (`#appWorkspace`)**: The main creator dashboard with hero header and grid layout.
* **STEP 6: Caption Settings Panel**: Tone dropdown selector, developer API key drawer, and interactive platform matrix multi-select.
* **STEP 7: Hands-Free Voice Input**: Microphone dictation powered by browser Web Speech API with live transcript streaming and pulse animations.
* **STEP 8: Media Upload Dropzone**: Drag-and-drop zone with instant base64 thumbnail rendering via `FileReader` API.
* **STEP 9: Primary Action Button**: Dynamic reactive submit button with inline error alert card.
* **STEP 10: Results Cards Grid**: Responsive grid rendering platform cards, character limits, and single-click copy buttons.
* **STEP 11: Inference Spinner Overlay**: Fullscreen backdrop blur with animated spinner during Gemini AI processing.
* **STEP 12: Caption History Modal**: Modal dialog allowing logged-in creators to view past generations, copy captions, and delete records.
* **STEP 13: JavaScript Application Controller**:
  - `13.1`: Centralized reactive state store (`apiKey`, `platforms`, `tone`, `file`, `context`, `token`, `user`).
  - `13.2`: Cached DOM element queries.
  - `13.3`: Local browser developer API key storage.
  - `13.4`: Platform matrix multi-select toggles.
  - `13.5`: Voice recognition engine (Web Speech API event handlers).
  - `13.6`: Drag-and-drop file upload & thumbnail generator.
  - `13.7`: Form validation and dynamic button state controller.
  - `13.8`: Inline error banner manager.
  - `13.9`: SPA view coordinator (toggles auth card vs workspace).
  - `13.10`: Session persistence & `/api/auth/me` profile hydration.
  - `13.11`: Auth mode switcher (Sign Up vs Log In) & OAuth toasts.
  - `13.12`: Unified auth form submit handler (`/api/auth/register` & `/api/auth/login`).
  - `13.13`: User account dropdown & logout controller (`/api/auth/logout`).
  - `13.14`: Caption history manager & JSON synchronizer (`/api/history`).
  - `13.15`: Multimodal inference pipeline caller (`/api/generate`).
  - `13.16`: Results card renderer with XSS sanitizers (`escapeHtml`, `escapeJsString`).
  - `13.17`: One-click clipboard utilities (`copyCaption`, `copyAllBtn`).
  - `13.18`: Application bootstrap & initialization sequence.

---

#### Backend Architecture (`api/index.py` & `app.py`)
* **STEP 1: Logging & App Setup**: Structured logging, `.env` loading, FastAPI/Streamlit initialization, and CORS middleware configuration.
* **STEP 2: JSON Storage Initialization**: Auto-initializes `users.json`, `sessions.json`, and `history.json` under `data/`. Pure JSON file storage eliminates external database overhead and SQLite locking.
* **STEP 3: Cryptographic Security**: PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and unique 16-byte random salts. 32-byte URL-safe session token generation with 30-day expiration.
* **STEP 4: Platform Rules & Data Models**: Pydantic request models (`RegisterRequest`, `LoginRequest`, `SocialCaptions`), character limit clamping, and retry backoff handlers.
* **STEP 5: Authentication Endpoints & Flow**:
  - `POST /api/auth/register` (or Streamlit Sign Up): Creates new user in `data/users.json`, hashes password, returns bearer token / hydrates session.
  - `POST /api/auth/login` (or Streamlit Sign In): Verifies salt/hash from `data/users.json`, authenticates session.
  - `GET /api/auth/me`: Verifies active session token, returns profile and generation counts.
  - `POST /api/auth/logout`: Invalidates session token.
* **STEP 6: History Management**:
  - `GET /api/history`: Fetches previous generations for the authenticated user from `data/history.json`.
  - `PUT /api/history/{id}/like`: Persists per-platform likes/favorites into `data/history.json`.
  - `DELETE /api/history/{id}`: Deletes a specific history record belonging to the user from `data/history.json`.
* **STEP 7: Multimodal Vision & Generation Pipeline**:
  - `POST /api/generate`: Multipart file upload handler, Gemini Vision analysis, structured prompt construction, schema generation, fallback templates, and automatic history recording.
* **STEP 8: SPA & Static File Routing**: Serves single-page application `index.html` across candidate paths, static illustrations (`/static/...`), and `/health` monitoring probe.

---

## 🚀 Quickstart & Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Jagadeesh-31/ai-powered-social-caption-generator.git
cd ai-powered-social-caption-generator
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

Create a `.env` file in the project root directory:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

*(You can get a free API key at [Google AI Studio](https://aistudio.google.com/)).*

---

## 💻 Running the Application

### Option A: Modern Web Application (FastAPI + Web UI)

Start the Uvicorn development server:

```powershell
uvicorn api.index:app --reload --port 8000
```

Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

* Interactive Swagger API docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**
* Redoc documentation: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**

---

### Option B: Streamlit Demo

To run the interactive Streamlit UI prototype:

```powershell
streamlit run app.py
```

---

### Option C: Standalone CLI Script

Generate captions directly for any image file via the command line:

```powershell
python origin/6_social_media_captions.py path/to/image.jpg --platforms instagram,x,linkedin --tone playful
```

---

## 🧪 Running Automated Tests

Run the full Pytest test suite with:

```powershell
pytest -v
```

All 26 tests cover:
- Authentication & Password Security (PBKDF2 salt uniqueness & validation)
- Token-based Session Management & Expiration
- Caption Length Clamping & Platform Formatting Rules
- Fallback Generators & Gemini Error Handling
- REST API Endpoints, Healthchecks & SPA Delivery

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `GET` | `/health` | Healthcheck and server status | No |
| `POST` | `/api/auth/register` | Register new user account | No |
| `POST` | `/api/auth/login` | Authenticate user and issue session token | No |
| `GET` | `/api/auth/me` | Fetch active user profile | Yes (Bearer Token) |
| `POST` | `/api/auth/logout` | Invalidate current session | Yes (Bearer Token) |
| `POST` | `/api/generate` | Generate captions from uploaded image/video | Optional (Guest/User) |
| `GET` | `/api/history` | Retrieve user's previous generated captions | Yes (Bearer Token) |
| `DELETE` | `/api/history/{id}` | Delete a specific saved caption item | Yes (Bearer Token) |

---

## 🚢 Deployment on Streamlit Community Cloud

Deploying this app to **Streamlit Community Cloud** is completely free and takes less than 2 minutes:

1. **Push your code to GitHub**:
   Ensure your latest code is committed and pushed to your GitHub repository:
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Open Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
   - Click **"Create app"** ➔ **"Deploy a public app from GitHub"**.

3. **Configure App Settings**:
   - **Repository**: Select your repository (e.g., `your-username/ai-social-caption-generator`).
   - **Branch**: `main`
   - **Main file path**: `app.py`

4. **Add Secrets (API Key)**:
   - Click **"Advanced settings"** ➔ **"Secrets"**.
   - Add your Gemini API key in TOML format:
     ```toml
     GEMINI_API_KEY = "your_actual_gemini_api_key_here"
     ```
   *(Note: The app will read `GEMINI_API_KEY` either from Streamlit secrets or `.env` automatically).*

5. **Click "Deploy!"**:
   Streamlit Cloud installs dependencies from `requirements.txt` and launches your live URL!

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
