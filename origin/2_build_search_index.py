"""
PROJECT: AI-Powered Multi-Platform Social Media Caption Generator & Studio
SCRIPT: origin/2_build_search_index.py (Vector Search Index Builder)

PURPOSE:
Scans an image directory, converts all images into mathematical vector numbers
(embeddings) using OpenAI CLIP, and saves a fast searchable vector index using FAISS.

HOW TO RUN:
    python origin/2_build_search_index.py ./data
"""

# sys handles command-line arguments and system exit
import sys

# os works with directories and file path resolution
import os

# glob finds all files matching a pattern (like *.jpg or *.png)
import glob

# numpy handles numerical arrays and vector matrices
import numpy as np

# faiss (Facebook AI Similarity Search) provides fast vector similarity indexing
import faiss

# PIL.Image opens and converts image files to RGB
from PIL import Image

# transformers provides the OpenAI CLIP model and processor
from transformers import CLIPProcessor, CLIPModel

# Resolve file paths for saving the FAISS index and image paths list
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_FILE = os.path.join(DATA_DIR, "image_index.faiss") if os.path.exists(DATA_DIR) else "image_index.faiss"
PATHS_FILE = os.path.join(DATA_DIR, "image_paths.npy") if os.path.exists(DATA_DIR) else "image_paths.npy"


# 1. Load CLIP Model and Processor from Hugging Face

def load_clip():
    """
    Loads OpenAI's CLIP model. CLIP can understand both text and images in the same
    mathematical space, allowing users to search images using natural language.
    """
    print("Loading CLIP model...")
    # Load the CLIP neural network weights
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    # Load the image and text preprocessor
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor


# 2. Build FAISS Vector Index from Images

def build_index(image_folder, model, processor):
    """
    Reads all photos in 'image_folder', computes their CLIP vector embeddings,
    and saves a FAISS index to disk for instant searching.
    """
    # Collect all image file paths in the folder
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_paths.extend(glob.glob(os.path.join(image_folder, ext)))

    # If no images found, show a message and stop
    if not image_paths:
        print(f"No images found in {image_folder}")
        sys.exit(1)

    print(f"Found {len(image_paths)} images. Generating embeddings...")

    # Compute a 512-dimensional vector for each image
    embeddings = []
    for path in image_paths:
        # Open image and convert to standard RGB format
        image = Image.open(path).convert("RGB")
        # Preprocess image into tensor format
        inputs = processor(images=image, return_tensors="pt")
        # Extract visual vector features from the model
        features = model.get_image_features(**inputs)
        image_features = features.pooler_output if hasattr(features, "pooler_output") else features
        # Normalize the vector so its length is 1 (allows using Cosine Similarity)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        # Store as numpy array
        embeddings.append(image_features.detach().numpy()[0])

    # Convert the list into a 2D float32 numpy matrix
    embeddings = np.array(embeddings).astype("float32")

    # Initialize a FAISS Inner Product index (IndexFlatIP matches Cosine Similarity for normalized vectors)
    embedding_dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(embedding_dimension)
    # Add all image vectors into the FAISS index
    index.add(embeddings)

    # Ensure the destination folder exists
    os.makedirs(os.path.dirname(os.path.abspath(INDEX_FILE)), exist_ok=True)
    # Save the FAISS vector index file
    faiss.write_index(index, INDEX_FILE)
    # Save the matching image file paths as a numpy file
    np.save(PATHS_FILE, np.array(image_paths))

    print(f"Index built and saved successfully: {INDEX_FILE}, {PATHS_FILE}")
    print(f"Total images indexed: {len(image_paths)}")


# 3. Main Execution Block

if __name__ == "__main__":
    # Ensure user passed an image folder argument
    if len(sys.argv) < 2:
        print("Usage: python origin/2_build_search_index.py <image_folder>")
        sys.exit(1)

    # Load CLIP model and build index for the target folder
    model, processor = load_clip()
    build_index(sys.argv[1], model, processor)
