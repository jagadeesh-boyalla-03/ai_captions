"""
PROJECT: AI-Powered Multi-Platform Social Media Caption Generator & Studio
MAIN SCRIPT: app.py (Interactive Streamlit Web Dashboard)

PURPOSE:
An interactive web application built with Streamlit that uses Google Gemini Multimodal AI
to analyze uploaded images and voice notes, then automatically generates tailored, ready-to-post
social media captions across 7 major platforms (Instagram, Twitter/X, Facebook, LinkedIn,
Pinterest, YouTube, Kick) in 8 creative tones.

HOW TO RUN:
    streamlit run app.py
"""

# 1. Python Libraries & Module Imports

# os provides tools to work with file paths, directories, and system environment variables
import os

# json allows reading and writing data in JSON format (used for history.json and users.json)
import json

# time is used to add short pauses during automatic API retries
import time

# random generates random numbers (used to add random delay/jitter during API retries)
import random

# hashlib provides cryptographic hashing algorithms (used for PBKDF2 secure password hashing)
import hashlib

# secrets generates cryptographically secure random salts and tokens, and safe hash comparisons
import secrets

# datetime and timedelta are used to record exact date and time stamps for accounts and captions
from datetime import datetime, timedelta

# PIL.Image (Pillow) is used to open, inspect, and convert uploaded images into RGB format
from PIL import Image

# io converts raw binary bytes into in-memory file streams
import io

# importlib.util allows dynamic execution of prototype modules from origin/
import importlib.util

# urllib.request allows checking the health of the local FastAPI backend service
import urllib.request
import urllib.error

# requests library for sending multipart requests to the FastAPI backend
try:
    import requests
except ImportError:
    requests = None

# streamlit (st) is the core web framework that creates our entire user interface, buttons, and cards
import streamlit as st

# google.genai is the official Google GenAI SDK used to communicate with Google Gemini AI models
from google import genai

# types provides helper data types for Gemini (like Part for handling raw audio bytes)
from google.genai import types

# load_dotenv reads secret variables (like GEMINI_API_KEY) from our local .env configuration file
from dotenv import load_dotenv


# 2. Environment & Page Setup

# Load all environment variables from the local .env file into Python's os.environ
load_dotenv()

# Configure the Streamlit web browser tab and layout:
# - page_title: Sets the text shown on the browser tab
# - layout="centered": Centers the main content area for a clean, focused reading experience
# - initial_sidebar_state="expanded": Keeps the left settings sidebar open when the user visits
st.set_page_config(
    page_title="Social Media Caption Generator",
    layout="centered",
    initial_sidebar_state="expanded"
)


# 3. Platform Copywriting Rules & Constants

# Dictionary holding the copywriting guidelines, maximum character limits, and styles for each platform.
# Gemini uses these exact rules when writing captions so that every caption fits the network perfectly.
PLATFORM_RULES = {
    "Instagram": {
        "key": "instagram",          # Short internal identifier
        "max_chars": 2200,            # Maximum character ceiling allowed on Instagram
        "style": "warm, visual, engaging; 5-8 relevant hashtags; 1-2 emojis; engaging call to action",
    },
    "X (Twitter)": {
        "key": "x",                  # Short internal identifier
        "max_chars": 280,             # Twitter enforces a strict 280 character limit
        "style": "punchy, witty, high-impact concise text; 2-3 targeted hashtags; strictly under 280 characters",
    },
    "Facebook": {
        "key": "facebook",           # Short internal identifier
        "max_chars": 600,             # Recommended length for maximum Facebook feed engagement
        "style": "conversational, community-focused, engaging question; 4-5 relevant hashtags",
    },
    "LinkedIn": {
        "key": "linkedin",           # Short internal identifier
        "max_chars": 750,             # Optimal length for professional business posts
        "style": "professional, insight-driven, practical career/business takeaways; 5+ industry hashtags",
    },
    "Pinterest": {
        "key": "pinterest",          # Short internal identifier
        "max_chars": 500,             # Best length for Pinterest pin descriptions
        "style": "keyword-rich, aesthetic and inspirational; 5-7 search hashtags",
    },
    "YouTube": {
        "key": "youtube",            # Short internal identifier
        "max_chars": 5000,            # YouTube descriptions allow long-form explanations
        "style": "video description format with key takeaways, subscribe CTA, and 5-10 tags/hashtags",
    },
    "Kick": {
        "key": "kick",               # Short internal identifier
        "max_chars": 150,             # Stream titles on Kick must be short and punchy
        "style": "high energy stream title, hype hook, 2-3 hashtags; strictly under 150 characters",
    },
}

# The 8 creative writing tones available for the user to pick in the sidebar dropdown
TONE_OPTIONS = [
    "Friendly & Upbeat",       # Positive, warm, welcoming voice
    "Professional",            # Formal, corporate, business-focused tone
    "Playful & Witty",         # Clever, funny, entertaining style
    "Inspirational",           # Motivational, uplifting, visionary messaging
    "Humorous",                # Lighthearted, comedy-driven, meme-friendly style
    "Minimalist & Aesthetic",  # Short, clean, poetic, aesthetic style
    "Urgent & Promotional",    # Sales-focused, limited-time offer, call-to-action
    "Storyteller",             # Narrative, storytelling, engaging background journey
]

# The list of Gemini models used for automatic fallback:
# If the first model is busy or hits a rate limit, the app automatically switches to the next one
DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",   # Primary model: Fastest and most cost-effective
    "gemini-3.5-flash",        # First backup: Highly reliable and versatile
    "gemini-3.6-flash"         # Second backup: Latest generation flagship model
]


# 4. Lightweight JSON Storage Architecture (No SQL Database Needed)

# Define the absolute path to the local 'data' directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Path to the JSON file where registered user profiles are stored
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Path to the JSON file where generated caption records are stored
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


def load_json(filepath: str, default=None):
    """
    Safely reads and parses a JSON file from disk.
    - If the file does not exist or has corrupted data, it returns 'default' (empty list).
    - This ensures the application never crashes due to missing files.
    """
    if default is None:
        default = []
    # Check if file exists on disk
    if not os.path.exists(filepath):
        return default
    try:
        # Open the file with UTF-8 encoding to support emojis and symbols
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If any read or JSON decoding error occurs, safely return the default value
        return default


def save_json(filepath: str, data):
    """
    Safely writes Python data (list or dict) to a JSON file on disk.
    - Creates the parent directory if it does not exist yet.
    - Formats the file with 2-space indentation for easy human readability.
    """
    # Ensure the directory exists before writing
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # Write formatted JSON data
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Path to origin directory containing evolutionary prototypes
ORIGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "origin")


# 4b. Origin Prototype & FastAPI REST Backend Bridge Helpers

def check_fastapi_backend(url="http://127.0.0.1:8000"):
    """
    Pings the local FastAPI backend service at /api/health or /health to check if uvicorn is running.
    Returns (is_online: bool, data: dict | None)
    """
    for path in ["/api/health", "/health"]:
        try:
            req = urllib.request.Request(f"{url}{path}", headers={"User-Agent": "StreamlitClient"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True, json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass
    return False, None


def call_fastapi_generate(api_base_url, image_bytes, filename, platforms_list, tone, context, api_key, token=None):
    """
    Sends a multipart POST request to the FastAPI REST backend (/api/generate)
    to generate captions through the headless backend rather than direct Gemini client.
    """
    if requests is None:
        return False, "Python 'requests' library is not installed."
    try:
        files = {"file": (filename, image_bytes, "image/jpeg")}
        data = {
            "platforms": ",".join(platforms_list),
            "tone": tone,
            "context": context or "",
            "api_key": api_key or "",
            "user_token": token or ""
        }
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.post(f"{api_base_url}/api/generate", files=files, data=data, headers=headers, timeout=60)
        if resp.status_code == 200:
            return True, resp.json()
        return False, f"Backend returned status {resp.status_code}: {resp.text}"
    except Exception as err:
        return False, str(err)


def load_origin_module(module_name: str, filename: str):
    """
    Dynamically loads and returns a Python script module from the origin/ directory.
    This enables app.py to directly execute prototypes like origin/1_caption_image.py.
    """
    file_path = os.path.join(ORIGIN_DIR, filename)
    if not os.path.exists(file_path):
        return None, f"File {filename} not found in origin/ directory."
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, None
    except Exception as e:
        return None, str(e)
    return None, "Failed to load origin module."


@st.cache_resource(show_spinner=False)
def load_blip_from_origin():
    """
    Loads and caches Salesforce BLIP weights into memory using origin/1_caption_image.py.
    """
    mod, err = load_origin_module("origin_blip", "1_caption_image.py")
    if err or mod is None:
        return None, None, err
    try:
        if hasattr(mod, "load_model"):
            processor, model = mod.load_model()
            return processor, model, None
        return None, None, "load_model() function not found in origin/1_caption_image.py"
    except Exception as exc:
        return None, None, str(exc)


# 5. User Authentication & Password Security (PBKDF2 with Random Salts)

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using the industry-standard PBKDF2-HMAC-SHA256 algorithm.
    - Generates a unique 16-byte cryptographically secure random salt.
    - Runs 100,000 iterations to make brute-force cracking mathematically infeasible.
    - Returns a string in format: 'salt:hex_hash'
    """
    # Generate 16 bytes of random salt in hex string format
    salt = secrets.token_hex(16)
    # Compute the PBKDF2 key using sha256 with 100,000 iterations
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
    # Combine the salt and the key hash separated by a colon
    return f"{salt}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies if a candidate password matches the stored 'salt:hash' string.
    - Extracts the salt originally used to hash this user's password.
    - Re-hashes the candidate password with that exact salt.
    - Uses secrets.compare_digest() to prevent timing attacks.
    """
    try:
        # Split the stored string into salt and the key hex
        salt, key_hex = stored_hash.split(":", 1)
        # Hash the candidate password with the extracted salt
        test_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
        # Constant-time comparison between the newly computed hash and the stored hash
        return secrets.compare_digest(test_key.hex(), key_hex)
    except Exception:
        # If any parsing error occurs (e.g. malformed hash), reject the login safely
        return False


def register_user(name: str, email: str, password: str):
    """
    Registers a new user account and saves it into data/users.json.
    - Performs input validation (checks non-empty name, valid email structure, password length >= 6).
    - Checks whether an account with this email already exists.
    - Hashes password and assigns a new unique user ID.
    """
    name = name.strip()
    email = email.strip().lower()

    # Validation: Ensure name is not blank
    if not name:
        return False, "Please enter your full name.", None

    # Validation: Check basic email structure
    if not email or "@" not in email or "." not in email:
        return False, "Please enter a valid email address.", None

    # Validation: Enforce minimum password length of 6 characters
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    # Load existing registered users from users.json
    users = load_json(USERS_FILE, default=[])

    # Check if email is already taken
    for u in users:
        if u.get("email", "").lower() == email:
            return False, "An account with this email already exists. Please log in.", None

    # Calculate next incremental unique user ID
    new_id = max([u.get("id", 0) for u in users], default=0) + 1

    # Build the user dictionary record
    new_user = {
        "id": new_id,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),  # Store only the salted PBKDF2 hash
        "created_at": datetime.utcnow().isoformat()
    }

    # Append to the users list and save to data/users.json
    users.append(new_user)
    save_json(USERS_FILE, users)

    # Return success flag, message, and safe user profile (without password hash)
    return True, "Account created successfully!", {"id": new_id, "name": name, "email": email}


def login_user(email: str, password: str):
    """
    Authenticates an existing user against data/users.json.
    - Searches for matching email.
    - Verifies candidate password against stored PBKDF2 salt and hash.
    - Returns success flag, welcome message, and user session profile.
    """
    email = email.strip().lower()

    # Validation: Ensure both fields are provided
    if not email or not password:
        return False, "Please enter both email and password.", None

    # Load users from JSON storage
    users = load_json(USERS_FILE, default=[])

    # Search for user by email
    for u in users:
        if u.get("email", "").lower() == email:
            # Verify the entered password against the stored salted hash
            if verify_password(password, u.get("password_hash", "")):
                return True, f"Welcome back, {u['name']}!", {"id": u["id"], "name": u["name"], "email": u["email"]}
            else:
                return False, "Incorrect password. Please try again.", None

    # Email was not found in users.json
    return False, "No account found with this email. Please sign up first.", None


# 6. Caption History & Favorites Management

def fetch_saved_history(user_id=None, limit=30):
    """
    Retrieves previous caption generation records from data/history.json.
    - If user_id is provided, filters history so users only see their own captions.
    - Sorts records newest first (highest ID first).
    - Returns up to 'limit' records (default 30).
    """
    history = load_json(HISTORY_FILE, default=[])
    # If user is logged in, filter only their records
    if user_id is not None:
        filtered = [h for h in history if h.get("user_id") == user_id]
    else:
        filtered = history
    # Sort newest to oldest
    filtered.sort(key=lambda x: x.get("id", 0), reverse=True)
    return filtered[:limit]


def save_captions_to_db(description: str, media_type: str, tone: str, captions_map: dict, liked_platforms: list = None, user_id: int = 1):
    """
    Saves a newly generated set of captions into data/history.json.
    - Builds a structured record with unique ID, user ID, image description, tone, captions, and timestamp.
    """
    try:
        history = load_json(HISTORY_FILE, default=[])
        # Generate new sequential record ID
        new_id = max([h.get("id", 0) for h in history], default=0) + 1

        # Package platform captions and their character limit rules into a dictionary
        payload = {}
        for p_name, caption_text in captions_map.items():
            rule = PLATFORM_RULES.get(p_name, {})
            key = rule.get("key", p_name.lower())
            payload[key] = {
                "label": p_name,
                "caption": caption_text,
                "max_chars": rule.get("max_chars", 1000)
            }

        # Build complete history record
        new_record = {
            "id": new_id,
            "user_id": user_id or 1,
            "description": description,
            "media_type": media_type,
            "tone": tone,
            "captions_json": json.dumps(payload),
            "liked_platforms": list(liked_platforms or []),  # List of platforms favorited by user
            "created_at": datetime.utcnow().isoformat()       # ISO timestamp
        }

        # Append and save to history.json
        history.append(new_record)
        save_json(HISTORY_FILE, history)
        return new_id
    except Exception:
        return None


def update_history_likes(record_id: int, liked_platforms: list):
    """
    Updates the list of liked platforms (heart icon) for a specific history record in data/history.json.
    """
    try:
        history = load_json(HISTORY_FILE, default=[])
        updated = False
        # Find matching record by ID
        for h in history:
            if h.get("id") == record_id:
                h["liked_platforms"] = list(liked_platforms)
                updated = True
                break
        # Save back to file if updated
        if updated:
            save_json(HISTORY_FILE, history)
            return True
        return False
    except Exception:
        return False


def delete_history_record(record_id: int):
    """
    Deletes a specific history record from data/history.json by ID.
    """
    try:
        history = load_json(HISTORY_FILE, default=[])
        # Filter out the record with matching ID
        history = [h for h in history if h.get("id") != record_id]
        save_json(HISTORY_FILE, history)
        return True
    except Exception:
        return False


# 7. Session State Initialization (Keeps app state persistent across clicks)

# Streamlit re-runs the entire python script on every user click.
# st.session_state is a dictionary that remembers variables across re-runs.

# Stores currently logged in user info (or None if not logged in)
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# Tracks if the user chose 1-click Guest Mode (skipping login)
if "guest_mode" not in st.session_state:
    st.session_state["guest_mode"] = False

# Default social platforms selected when app loads
if "platform_selection" not in st.session_state:
    st.session_state["platform_selection"] = ["Instagram", "LinkedIn", "X (Twitter)"]

# Holds the current active generated captions dictionary: {Platform: CaptionText}
if "current_captions" not in st.session_state:
    st.session_state["current_captions"] = {}

# Holds Gemini's one-sentence visual description of the uploaded image
if "current_description" not in st.session_state:
    st.session_state["current_description"] = ""

# Dictionary tracking which platforms are liked: {Platform: True/False}
if "liked_captions" not in st.session_state:
    st.session_state["liked_captions"] = {}

# ID of the currently active history record (if viewing or loaded from history)
if "active_record_id" not in st.session_state:
    st.session_state["active_record_id"] = None


# Callback functions for Select All / Clear platform buttons
def select_all_platforms():
    """Selects all 7 available social media platforms in one click."""
    st.session_state["platform_selection"] = list(PLATFORM_RULES.keys())


def clear_all_platforms():
    """Clears all platform selections in one click."""
    st.session_state["platform_selection"] = []


def toggle_like(platform_name: str):
    """
    Toggles the like status for a specific platform caption and persists to JSON.
    """
    # Flip the boolean value for this platform
    curr = st.session_state["liked_captions"].get(platform_name, False)
    st.session_state["liked_captions"][platform_name] = not curr

    # If this caption set has an ID in history, update the liked list in data/history.json
    rec_id = st.session_state.get("active_record_id")
    if rec_id:
        liked_list = [p for p, is_l in st.session_state["liked_captions"].items() if is_l]
        update_history_likes(rec_id, liked_list)


# 8. Sidebar Controls (User Profile, API Key, Tone, Platforms, History)

with st.sidebar:
    # User Profile / Guest Mode Status
    if st.session_state.get("current_user"):
        # User is logged in: show their name, email, and Log Out button
        user = st.session_state["current_user"]
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"📧 `{user['email']}`")
        if st.button("🚪 Log Out", key="sidebar_logout_btn", use_container_width=True):
            # Clear user session and reset
            st.session_state["current_user"] = None
            st.session_state["guest_mode"] = False
            st.session_state["current_captions"] = {}
            st.session_state["active_record_id"] = None
            st.toast("Logged out successfully.")
            st.rerun()
        st.divider()
    elif st.session_state.get("guest_mode"):
        # User is in Guest Mode: show guest label and button to switch to Sign In
        st.caption("👤 **Guest Mode**")
        if st.button("🔑 Sign In / Sign Up", key="sidebar_signin_btn", use_container_width=True):
            st.session_state["guest_mode"] = False
            st.rerun()
        st.divider()

    # API Key Resolution
    # First check if GEMINI_API_KEY is available in environment (.env)
    api_key = os.environ.get("GEMINI_API_KEY", "")

    # If not in .env, check if running on Streamlit Cloud Secrets
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = str(st.secrets["GEMINI_API_KEY"])
        except Exception:
            pass

    # If still not found, show a password-masked input box in sidebar so user can type it
    if not api_key:
        api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")
        if not api_key:
            st.sidebar.warning("GEMINI_API_KEY not found in .env or secrets.")
            st.info("Please add GEMINI_API_KEY to your .env file or enter it above to proceed.")
            st.stop()

    # Select the primary Gemini model
    selected_model = DEFAULT_MODELS[0]

    # Caption Tone Selection Dropdown
    st.subheader("Caption Tone")
    selected_tone = st.selectbox(
        "Select Tone",
        TONE_OPTIONS,
        index=0,
        help="Choose the personality and style of your generated captions"
    )

    st.divider()

    # Target Platforms Selection
    st.subheader("Target Platforms")
    # Quick buttons: Select All & Clear
    col_sel_all, col_clear = st.columns(2)
    col_sel_all.button("Select All", on_click=select_all_platforms, use_container_width=True)
    col_clear.button("Clear", on_click=clear_all_platforms, use_container_width=True)

    # Multi-select widget for choosing social networks
    selected_platforms = st.multiselect(
        "Choose Platforms",
        options=list(PLATFORM_RULES.keys()),
        key="platform_selection",
        help="Pick the social platforms you want to generate captions for"
    )

    # Show count of selected platforms
    st.caption(f"{len(selected_platforms)} of {len(PLATFORM_RULES)} platforms selected")

    st.divider()

    # Saved Caption History Section
    st.subheader("History")

    def load_history_record(row):
        """
        Parses a saved history record and restores it into the active studio screen.
        """
        try:
            parsed = json.loads(row["captions_json"])
            restored = {}
            for k, v in parsed.items():
                p_name = k.capitalize()
                for full_name, rule_data in PLATFORM_RULES.items():
                    if rule_data["key"] == k or full_name.lower() == k.lower():
                        p_name = full_name
                        break
                if isinstance(v, dict) and "caption" in v:
                    restored[p_name] = v["caption"]
                elif isinstance(v, str):
                    restored[p_name] = v
            # Restore state variables
            st.session_state["current_captions"] = restored
            st.session_state["current_description"] = row["description"]
            st.session_state["active_record_id"] = row["id"]
            if restored:
                st.session_state["platform_selection"] = list(restored.keys())
            # Restore liked badges
            likes_data = row.get("liked_platforms", [])
            if isinstance(likes_data, str):
                try:
                    likes_data = json.loads(likes_data)
                except Exception:
                    likes_data = []
            st.session_state["liked_captions"] = {p: True for p in (likes_data or [])}
            return True
        except Exception as err:
            st.error(f"Error loading record: {err}")
            return False

    # Filter history by current user ID (or all if in guest mode)
    cur_u = st.session_state.get("current_user")
    filter_uid = cur_u["id"] if cur_u else None
    saved_records = fetch_saved_history(user_id=filter_uid, limit=30)

    if saved_records:
        options_map = {}
        for row in saved_records:
            time_str = row.get("created_at", "")[:10] if row.get("created_at") else "Recent"
            desc_text = row.get("description", "")
            short_desc = (desc_text[:24] + "...") if len(desc_text) > 24 else desc_text
            likes_data = row.get("liked_platforms", [])
            if isinstance(likes_data, str):
                try:
                    likes_data = json.loads(likes_data)
                except Exception:
                    likes_data = []
            liked_count = len(likes_data) if isinstance(likes_data, list) else 0
            like_badge = f" [❤️ {liked_count}]" if liked_count > 0 else ""
            opt_key = f"#{row['id']} - {time_str} - {row.get('tone', 'Standard')}{like_badge} - {short_desc}"
            options_map[opt_key] = row

        st.session_state["_history_options_map"] = options_map

        options_list = ["-- Select saved caption --"] + list(options_map.keys())
        active_id = st.session_state.get("active_record_id")
        current_idx = 0
        if active_id:
            for idx, opt in enumerate(options_list[1:], start=1):
                if opt.startswith(f"#{active_id} "):
                    current_idx = idx
                    break

        def on_history_change():
            chosen = st.session_state.get("history_select_key")
            omap = st.session_state.get("_history_options_map", {})
            if chosen and chosen in omap:
                load_history_record(omap[chosen])
                st.toast(f"Loaded record #{omap[chosen]['id']}! 📂")

        chosen_label = st.selectbox(
            "Saved Captions",
            options=options_list,
            index=current_idx,
            key="history_select_key",
            on_change=on_history_change
        )

        selected_row = options_map.get(chosen_label)

        # Buttons to Load or Delete selected record
        col_load, col_del = st.columns(2)
        if col_load.button("Load to View", use_container_width=True):
            if selected_row:
                load_history_record(selected_row)
                st.toast(f"Loaded saved record #{selected_row['id']} 📂")
                st.rerun()
            else:
                st.info("Please choose a saved caption from the dropdown above.")

        if col_del.button("Delete", use_container_width=True):
            if selected_row:
                delete_history_record(selected_row["id"])
                if st.session_state.get("active_record_id") == selected_row["id"]:
                    st.session_state["current_captions"] = {}
                    st.session_state["current_description"] = ""
                    st.session_state["active_record_id"] = None
                    st.session_state["liked_captions"] = {}
                st.toast(f"Deleted record #{selected_row['id']}")
                st.rerun()
            else:
                st.info("Please choose a saved caption from the dropdown above.")
    else:
        st.info("No saved history yet.")

    # System Architecture & Component Status
    st.divider()
    st.subheader("System Architecture")
    backend_live, _ = check_fastapi_backend()
    if backend_live:
        st.success("🟢 **FastAPI Backend**: Online (`:8000`)")
        st.session_state["use_api_route"] = st.toggle(
            "Route via FastAPI Backend",
            value=st.session_state.get("use_api_route", False),
            help="Sends generation requests through http://127.0.0.1:8000/api/generate instead of direct Gemini client"
        )
    else:
        st.info("⚡ **Inference**: Direct Gemini Vision Mode")
        st.caption("*(Run `uvicorn api.index:app` for REST server)*")
        st.session_state["use_api_route"] = False

    st.caption("🔬 **Origin Prototypes**: Linked to Tab 2")
    st.caption("💾 **Database**: Shared `data/` JSON storage")


# 9. Initialize Gemini Client & Resilient Retry / Fallback Helper

# Create the Google GenAI Client instance using our verified API key
client = genai.Client(api_key=api_key.strip())


def generate_content_with_retry(client, contents, preferred_model=None, max_retries=3):
    """
    Calls Google Gemini API with automatic 3-tier model fallback and exponential backoff.
    - If the preferred model encounters a transient error (e.g. 429 rate limit or 503 unavailable),
      it waits with exponential delay and retries.
    - If errors persist, it cascades to the backup models:
      gemini-3.5-flash-lite -> gemini-3.5-flash -> gemini-3.6-flash
    """
    # Build list of models to try in order
    models_to_try = [preferred_model] if preferred_model else []
    for m in DEFAULT_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_err = None
    # Loop through each model in the fallback cascade
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                # Send inference request to Gemini
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                # If valid text response received, return it immediately
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_err = e
                err_str = str(e).upper()
                # Check if error is temporary (rate limit or temporary server outage)
                is_transient = "503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str or "RESOURCE_EXHAUSTED" in err_str
                if is_transient and attempt < max_retries - 1:
                    # Exponential backoff with random jitter: (1.5^attempt) + random(0.5..1.0)
                    sleep_time = (1.5 ** attempt) + random.uniform(0.5, 1.0)
                    time.sleep(sleep_time)
                else:
                    # Break out and try the next model in the cascade
                    break

    # If all models failed, raise the last recorded error
    if last_err:
        raise last_err
    raise Exception("Gemini service temporarily unavailable.")


# 10. Authentication Gate (Sign In, Sign Up, or Guest Mode)

# If the user has neither logged in nor clicked "Continue as Guest", show the Auth Gate
if not st.session_state.get("current_user") and not st.session_state.get("guest_mode"):
    st.title("Social Media Caption Studio")
    st.write("Generate tailored, platform-optimized captions across 7 social platforms using Google Gemini Multimodal AI.")

    # Two tabs: Sign In and Sign Up
    tab_signin, tab_signup = st.tabs(["🔑 Sign In", "✨ Sign Up (First-Time User)"])

    # Tab 1: Sign In
    with tab_signin:
        st.subheader("Welcome Back")
        with st.form("signin_form"):
            in_email = st.text_input("Email Address", placeholder="name@example.com")
            in_pass = st.text_input("Password", type="password")
            btn_signin = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            if btn_signin:
                ok, msg, u_obj = login_user(in_email, in_pass)
                if ok:
                    st.session_state["current_user"] = u_obj
                    st.toast(f"Welcome back, {u_obj['name']}! 🎉")
                    st.rerun()
                else:
                    st.error(msg)

        st.divider()
        # 1-Click Guest Mode Button
        if st.button("🚀 Continue as Guest (Skip Sign In)", key="guest_signin_btn", use_container_width=True):
            st.session_state["guest_mode"] = True
            st.rerun()

    # Tab 2: Sign Up
    with tab_signup:
        st.subheader("Create a New Account")
        st.caption("Store your generated multi-platform captions and favorites securely.")
        with st.form("signup_form"):
            new_name = st.text_input("Full Name", placeholder="e.g. Jagadeesh")
            new_email = st.text_input("Email Address", placeholder="e.g. user@example.com")
            new_pass = st.text_input("Create Password", type="password", help="At least 6 characters")
            new_confirm = st.text_input("Confirm Password", type="password")
            btn_signup = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
            if btn_signup:
                if new_pass != new_confirm:
                    st.error("Passwords do not match. Please re-enter your password.")
                else:
                    ok, msg, u_obj = register_user(new_name, new_email, new_pass)
                    if ok:
                        st.session_state["current_user"] = u_obj
                        st.toast(f"Account created! Welcome, {u_obj['name']}! 🎉")
                        st.rerun()
                    else:
                        st.error(msg)

        st.divider()
        # 1-Click Guest Mode Button
        if st.button("🚀 Continue as Guest", key="guest_signup_btn", use_container_width=True):
            st.session_state["guest_mode"] = True
            st.rerun()

    # Stop rendering the rest of the page until user authenticates or chooses guest mode
    st.stop()


# 11. Main Studio Dashboard & Multi-Component Architecture

tab_studio, tab_origin, tab_api = st.tabs([
    "✨ Social Media Studio",
    "🔬 Origin Prototype Lab (BLIP Offline)",
    "🌐 FastAPI REST Backend Bridge"
])

with tab_studio:
    # Header title and instructions
    st.title("Social Media Caption Generator")
    st.write("Upload an image -> get ready-to-post captions for every platform.")

    # Banner displayed when viewing a loaded history record
    active_rec = st.session_state.get("active_record_id")
    current_caps = st.session_state.get("current_captions", {})
    if active_rec and current_caps:
        col_hist_info, col_hist_reset = st.columns([4, 1])
        with col_hist_info:
            st.info(f"📂 **Viewing Saved Record #{active_rec}**: *{st.session_state.get('current_description', '')}*")
        with col_hist_reset:
            if st.button("➕ New Upload", use_container_width=True, help="Clear loaded history to upload a new image"):
                st.session_state["current_captions"] = {}
                st.session_state["current_description"] = ""
                st.session_state["active_record_id"] = None
                st.session_state["liked_captions"] = {}
                st.rerun()

    # Image file uploader widget supporting JPG, JPEG, PNG, and WEBP formats
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])

    # Optional Context Section: text input + compact Voice Input popover
    col_context_label, col_voice_btn = st.columns([3, 1])
    with col_context_label:
        st.write("**OPTIONAL CONTEXT / CAMPAIGN DETAILS**")
    with col_voice_btn:
        with st.popover("Voice Input", use_container_width=True):
            st.caption("Speak your campaign notes or context:")
            # Native Streamlit audio recorder using browser microphone
            voice_recording = st.audio_input("Record voice", label_visibility="collapsed")

    # Text input for optional notes
    extra_context = st.text_input(
        "Optional context",
        value="",
        placeholder="e.g. new product launch, weekend getaway, course completed",
        label_visibility="collapsed"
    )

    # Show confirmation indicator if voice recording is attached
    if voice_recording is not None:
        st.caption("Voice recording attached and ready.")

    # Open and validate image with Pillow (without rendering preview)
    image_obj = None
    if uploaded_file is not None:
        try:
            # Convert image to RGB format to standardize color channels
            image_obj = Image.open(uploaded_file).convert("RGB")
            st.success(f"Image successfully uploaded: {uploaded_file.name}")
        except Exception as err:
            st.error(f"Error opening image: {err}")


    # 12. Caption Generation Pipeline (FastAPI Routing or Direct Gemini Fallback)

    # The "Generate Captions" button is disabled if no image is uploaded or no platforms are selected
    generate_btn_disabled = (image_obj is None) or (len(selected_platforms) == 0)

    if st.button("Generate Captions", type="primary", disabled=generate_btn_disabled):
        try:
            routed_via_api = False

            # Check if user toggled to route through the FastAPI REST backend
            if st.session_state.get("use_api_route", False):
                backend_up, _ = check_fastapi_backend()
                if backend_up and uploaded_file is not None:
                    with st.spinner("Routing request through FastAPI REST backend (/api/generate)..."):
                        img_byte_io = io.BytesIO()
                        image_obj.save(img_byte_io, format="JPEG")
                        call_ok, call_res = call_fastapi_generate(
                            api_base_url="http://127.0.0.1:8000",
                            image_bytes=img_byte_io.getvalue(),
                            filename=uploaded_file.name,
                            platforms_list=selected_platforms,
                            tone=selected_tone,
                            context=extra_context,
                            api_key=api_key
                        )
                        if call_ok and isinstance(call_res, dict) and "captions" in call_res:
                            routed_via_api = True
                            image_description = call_res.get("description", "")
                            st.session_state["current_description"] = image_description
                            parsed_caps = {}
                            for p_key, c_info in call_res["captions"].items():
                                p_label = c_info.get("label", p_key.capitalize())
                                parsed_caps[p_label] = c_info.get("caption", "")
                            st.session_state["current_captions"] = parsed_caps
                            st.session_state["liked_captions"] = {}
                            st.success("✅ Captions generated via FastAPI Backend (`POST /api/generate`)!")
                        else:
                            st.warning(f"FastAPI request notice ({call_res}). Falling back to direct Gemini client...")

            if not routed_via_api:
                # Direct Gemini Pipeline Execution
                # Phase 1: Gemini Vision Scene Understanding
                with st.spinner("Analyzing image using Gemini Vision..."):
                    # Pass image tensor directly to Gemini to get a factual description
                    image_description = generate_content_with_retry(
                        client=client,
                        contents=[image_obj, "Provide a plain, factual, one-sentence description of this image."],
                        preferred_model=selected_model
                    )

                # Store description in session state
                st.session_state["current_description"] = image_description
                st.caption(f"Image understood as: *{image_description}*")

                # Phase 1b: Transcribe Voice Audio if Provided
                voice_text = ""
                if voice_recording is not None:
                    try:
                        with st.spinner("Transcribing microphone voice recording..."):
                            # Get raw audio bytes from the voice recording
                            audio_bytes = voice_recording.getvalue()
                            mime_type = voice_recording.type or "audio/wav"
                            # Create a Gemini audio Part
                            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                            # Feed audio part to Gemini for speech-to-text transcription
                            audio_response = client.models.generate_content(
                                model=selected_model,
                                contents=[
                                    audio_part,
                                    "Transcribe the spoken speech in this audio clearly into text. Output only the transcription, nothing else."
                                ]
                            )
                            if audio_response and audio_response.text:
                                voice_text = audio_response.text.strip()
                                st.info(f"Voice context recognized: {voice_text}")
                    except Exception as audio_err:
                        st.warning(f"Audio transcription notice: {str(audio_err)}")

                # Merge typed context and transcribed voice context
                combined_context = extra_context.strip()
                if voice_text:
                    combined_context = f"{combined_context} {voice_text}".strip() if combined_context else voice_text

                new_captions = {}
                progress_bar = st.progress(0)
                total_p = len(selected_platforms)

                # Phase 2: Platform-by-Platform Caption Generation
                for idx, platform_name in enumerate(selected_platforms):
                    rules = PLATFORM_RULES[platform_name]
                    context_line = f"\nAdditional context: {combined_context}\n" if combined_context else ""

                    # Construct structured copywriting prompt enforcing platform rules and character limits
                    prompt = f"""You are an elite social media copywriter.
Media Description: "{image_description}"
{context_line}
Platform: {platform_name}
Platform Requirements: {rules['style']}
Character Limit: strictly under {rules['max_chars']} characters

Requirements:
- Tone: {selected_tone}
- Hashtags: Include 5+ relevant, high-traffic hashtags on the final line(s).
- Structure: Punchy hook, concise body/takeaway, quick call to action, followed by hashtags.
- Output ONLY the ready-to-post caption text without preambles or markdown code fences.
"""
                    with st.spinner(f"Writing {platform_name} caption..."):
                        caption = generate_content_with_retry(
                            client=client,
                            contents=prompt,
                            preferred_model=selected_model
                        )
                        new_captions[platform_name] = caption

                    # Update progress bar
                    progress_bar.progress((idx + 1) / total_p)

                # Save generated captions to session state
                st.session_state["current_captions"] = new_captions
                st.session_state["liked_captions"] = {}

                # Phase 3: Automatically Save to JSON History
                active_u_id = st.session_state["current_user"]["id"] if st.session_state.get("current_user") else 1
                saved_id = save_captions_to_db(
                    description=image_description,
                    media_type="image",
                    tone=selected_tone,
                    captions_map=new_captions,
                    liked_platforms=[],
                    user_id=active_u_id
                )
                st.session_state["active_record_id"] = saved_id
                if saved_id:
                    st.toast(f"Saved to history (Record #{saved_id})")

                st.success("Captions generated successfully.")

        except Exception as e:
            st.error(f"Error generating captions: {str(e)}")


    # 13. Results Cards, Character Limit Meters, Likes & Downloads

    current_captions = st.session_state.get("current_captions", {})
    active_desc = st.session_state.get("current_description", "")
    liked_map = st.session_state.get("liked_captions", {})

    # If captions exist, render the results grid
    if current_captions:
        st.divider()

        # Header section: Title, Like All button, and Clear Likes button
        col_head_title, col_like_all, col_clear_likes = st.columns([3, 1, 1])
        num_liked = sum(1 for p in current_captions if liked_map.get(p, False))

        with col_head_title:
            st.subheader(f"Generated Captions ({len(current_captions)} platforms)")
            liked_summary = f" • ❤️ **{num_liked} of {len(current_captions)} liked**" if num_liked > 0 else ""
            if active_desc:
                st.caption(f"Visual Context: *{active_desc}*{liked_summary}")
            elif liked_summary:
                st.caption(liked_summary)

        with col_like_all:
            if st.button("❤️ Like All", use_container_width=True, help="Like all platform captions"):
                for p in current_captions:
                    st.session_state["liked_captions"][p] = True
                rec_id = st.session_state.get("active_record_id")
                if rec_id:
                    update_history_likes(rec_id, list(current_captions.keys()))
                st.toast("Liked all captions! ❤️")
                st.rerun()

        with col_clear_likes:
            if st.button("🤍 Clear Likes", use_container_width=True, help="Clear all likes"):
                st.session_state["liked_captions"] = {}
                rec_id = st.session_state.get("active_record_id")
                if rec_id:
                    update_history_likes(rec_id, [])
                st.toast("Cleared all likes.")
                st.rerun()

        # Loop through each platform caption and render its card
        for platform_name, caption in current_captions.items():
            rules = PLATFORM_RULES.get(platform_name, {"max_chars": 1000})
            char_count = len(caption)
            max_chars = rules["max_chars"]
            is_liked = liked_map.get(platform_name, False)
            rec_k = str(st.session_state.get("active_record_id", "gen"))

            # Platform Header with Liked badge
            col_p_title, col_p_badge = st.columns([4, 1])
            with col_p_title:
                st.markdown(f"### {platform_name}")
            with col_p_badge:
                if is_liked:
                    st.markdown("❤️ **Liked**")

            # Caption text area (read/copy enabled)
            st.text_area(
                f"{platform_name} caption",
                value=caption,
                height=140,
                key=f"text_area_{platform_name}_{rec_k}",
                label_visibility="collapsed"
            )
            # Character count meter proving compliance with limits
            st.caption(f"Length: {char_count} / {max_chars} characters")

            # Action Buttons: Download .txt file & Toggle Like
            col_dl, col_like = st.columns([3, 1])
            with col_dl:
                st.download_button(
                    label=f"📥 Download {platform_name} Caption",
                    data=caption,
                    file_name=f"{platform_name.lower().replace(' ', '_')}_caption.txt",
                    mime="text/plain",
                    key=f"dl_{platform_name}_{rec_k}",
                    use_container_width=True
                )
            with col_like:
                if is_liked:
                    if st.button("❤️ Liked", key=f"like_{platform_name}_{rec_k}", type="primary", use_container_width=True):
                        toggle_like(platform_name)
                        st.toast(f"Unliked {platform_name} caption.")
                        st.rerun()
                else:
                    if st.button("🤍 Like", key=f"like_{platform_name}_{rec_k}", type="secondary", use_container_width=True):
                        toggle_like(platform_name)
                        st.toast(f"Liked {platform_name} caption! ❤️")
                        st.rerun()

            st.divider()


# 14. Origin Prototype Lab (BLIP Offline Captioning & Vector Search)

with tab_origin:
    st.header("🔬 Origin Prototype Lab")
    st.markdown("""
    This tab provides a direct interactive bridge to the experimental prototypes located in the `origin/` directory.
    Before building this production studio, we benchmarked local offline vision models to understand their strengths and limitations.
    """)

    st.divider()
    st.subheader("1. Offline BLIP Image Captioning (`origin/1_caption_image.py`)")
    st.caption("Salesforce BLIP runs locally on your machine (CPU or GPU) using PyTorch and Hugging Face Transformers.")

    col_blip_left, col_blip_right = st.columns([1, 1])
    sample_files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))] if os.path.exists(DATA_DIR) else []

    with col_blip_left:
        blip_img_choice = st.selectbox(
            "Select a Sample Image from data/",
            options=["-- Select an image --"] + sample_files,
            key="origin_sample_choice"
        )
        blip_custom_file = st.file_uploader("Or upload your own image for BLIP", type=["jpg", "jpeg", "png"], key="origin_custom_file")

        active_blip_img = None
        if blip_custom_file:
            active_blip_img = Image.open(blip_custom_file).convert("RGB")
            st.image(active_blip_img, caption="Custom Image", use_container_width=True)
        elif blip_img_choice and blip_img_choice != "-- Select an image --":
            sample_path = os.path.join(DATA_DIR, blip_img_choice)
            if os.path.exists(sample_path):
                active_blip_img = Image.open(sample_path).convert("RGB")
                st.image(active_blip_img, caption=f"Sample: {blip_img_choice}", use_container_width=True)

    with col_blip_right:
        st.markdown("#### Run BLIP Inference")
        st.write("Calls `load_model()` and `generate_caption()` directly from `origin/1_caption_image.py`.")

        btn_blip_disabled = (active_blip_img is None)
        if st.button("🚀 Run Offline BLIP Model", type="primary", disabled=btn_blip_disabled, key="run_blip_btn"):
            with st.spinner("Executing origin/1_caption_image.py (Salesforce BLIP)..."):
                processor, model, err = load_blip_from_origin()
                if err or processor is None or model is None:
                    st.warning(f"⚠️ Offline model notice: {err}")
                    st.info("Salesforce BLIP requires `torch` and `transformers` installed. In cloud environments, the studio uses Google Gemini Vision to conserve RAM.")
                else:
                    try:
                        inputs = processor(active_blip_img, return_tensors="pt")
                        out = model.generate(**inputs, max_new_tokens=30)
                        blip_result = processor.decode(out[0], skip_special_tokens=True)
                        st.success(f"**BLIP Generated Caption**:\n\n*\"{blip_result}\"*")
                        st.info("💡 **Architectural Difference**: Notice BLIP outputs a single objective fact. In Tab 1, Google Gemini uses this visual understanding to produce tailored copywriting for 7 platforms with custom tones, character limits, and hashtags!")
                    except Exception as b_err:
                        st.error(f"BLIP Inference Error: {b_err}")

    st.divider()
    st.subheader("2. Semantic Vector Search Architecture (`origin/2_build_search_index.py`)")
    st.markdown("""
    In `origin/2_build_search_index.py`, we implemented semantic image search using **OpenAI CLIP** and **FAISS (Facebook AI Similarity Search)**:
    - **Visual Embeddings**: Images are transformed via `CLIPModel.get_image_features()` into 512-dimensional vector coordinates.
    - **Unit Normalization**: Normalizing vector lengths ensures that inner product equals **Cosine Similarity**.
    - **FAISS Flat Index**: `faiss.IndexFlatIP(512)` stores the vectors in `data/image_index.faiss` for sub-millisecond retrieval.
    """)

    idx_path = os.path.join(DATA_DIR, "image_index.faiss")
    p_path = os.path.join(DATA_DIR, "image_paths.npy")
    if os.path.exists(idx_path) and os.path.exists(p_path):
        st.success("✅ **Vector Index Found**: `data/image_index.faiss` is built and indexed on disk.")
    else:
        st.info("💡 Build the vector index on your local machine anytime with: `python origin/2_build_search_index.py ./data`")


# 15. FastAPI REST Backend Bridge & System Architecture

with tab_api:
    st.header("🌐 FastAPI REST Backend Bridge")
    st.markdown("""
    This tab bridges the Streamlit application with the headless **FastAPI REST server** (`api/index.py`).
    Both share the exact same user accounts and caption history in `data/`.
    """)

    col_api_ctrl, col_api_status = st.columns([1, 2])
    with col_api_ctrl:
        test_url = st.text_input("FastAPI Server URL", value="http://127.0.0.1:8000", key="test_api_url_input")
        btn_check = st.button("📡 Ping FastAPI Server", use_container_width=True)

    backend_ok, health_info = check_fastapi_backend(test_url)
    with col_api_status:
        if backend_ok:
            st.success(f"🟢 **FastAPI Server Online**: {health_info.get('service', 'Operational')}")
            st.json(health_info)
        else:
            st.warning("⚪ **FastAPI Server Offline** (Direct Gemini mode active)")
            st.caption("Start the backend server in a separate terminal: `uvicorn api.index:app --reload --port 8000`")

    st.divider()
    st.subheader("Live REST API Endpoints (`api/index.py`)")
    st.markdown("""
    | Method | Endpoint | Description | Auth Required |
    | :--- | :--- | :--- | :---: |
    | `GET` | `/health` | Server probe and liveness check | No |
    | `POST` | `/api/auth/register` | User signup with PBKDF2 salt & hash | No |
    | `POST` | `/api/auth/login` | Authenticate credentials & issue 30-day bearer token | No |
    | `GET` | `/api/auth/me` | Fetch active user profile & caption count | Yes (Bearer Token) |
    | `POST` | `/api/auth/logout` | Invalidate and purge session token | Yes (Bearer Token) |
    | `POST` | `/api/generate` | Multimodal caption generation pipeline | Optional (Guest/User) |
    | `GET` | `/api/history` | Retrieve saved user captions | Yes (Bearer Token) |
    | `PUT` | `/api/history/{id}/like` | Update per-platform likes/favorites | Yes (Bearer Token) |
    | `DELETE` | `/api/history/{id}` | Delete a specific saved caption item | Yes (Bearer Token) |
    """)

    st.divider()
    st.subheader("Shared Database Bridge Architecture")
    st.info("🔒 **Data Interoperability**: `app.py` and `api/index.py` share the exact same storage in `data/users.json` and `data/history.json`. A user registered via Streamlit can authenticate through FastAPI `POST /api/auth/login`, and captions generated via REST API appear immediately in the Streamlit history explorer!")
