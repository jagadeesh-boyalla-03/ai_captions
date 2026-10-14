"""
PROJECT: AI-Powered Multi-Platform Social Media Caption Generator & Studio
SCRIPT: origin/1_caption_image.py (Baseline Offline BLIP Image Captioning)

PURPOSE:
An offline prototype script that uses the open-source Salesforce BLIP deep learning
model from Hugging Face to generate descriptive text captions for images without
requiring any external API key.

HOW TO RUN:
    python origin/1_caption_image.py data/astronaut.jpg
"""

# sys is used to read command-line arguments and exit on errors
import sys

# PIL.Image (Pillow) opens and converts images into RGB format
from PIL import Image

# transformers provides pre-trained AI models and processors from Hugging Face
from transformers import BlipProcessor, BlipForConditionalGeneration


# 1. Load BLIP Processor and Vision Model

def load_model():
    """
    Downloads and caches the BLIP captioning model from Hugging Face.
    - BlipProcessor: Prepares the image (resizes, normalizes, turns into numbers/tensors).
    - BlipForConditionalGeneration: The neural network that creates words from image features.
    """
    print("Loading BLIP model (first run will download ~1GB, be patient)...")
    
    # BlipProcessor prepares the raw image pixels for the AI model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    
    # BlipForConditionalGeneration generates natural language captions from image features
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    
    # Return both objects so they can be reused
    return processor, model


# 2. Generate Caption from an Image File

def generate_caption(image_path, processor, model):
    """
    Takes an image path, runs it through the BLIP model, and returns a caption string.
    """
    # Open the image file from disk and convert to RGB channels
    raw_image = Image.open(image_path).convert("RGB")
    
    # Preprocess the image into PyTorch tensors that the model can understand
    inputs = processor(raw_image, return_tensors="pt")
    
    # Model generates token IDs for the caption (up to 30 new words)
    out = model.generate(**inputs, max_new_tokens=30)
    
    # Decode the numerical token IDs back into human-readable English text
    caption = processor.decode(out[0], skip_special_tokens=True)
    
    return caption


# 3. Main Execution Block

if __name__ == "__main__":
    # Check if the user passed an image file path as an argument
    if len(sys.argv) < 2:
        print("Usage: python origin/1_caption_image.py <image_path>")
        sys.exit(1)

    # Read the image path from the first command-line argument
    image_path = sys.argv[1]
    
    # Load the processor and the BLIP model into memory
    processor, model = load_model()
    
    # Generate the caption using the loaded model
    caption = generate_caption(image_path, processor, model)
    
    # Print the image path and generated caption to the terminal
    print(f"\nImage: {image_path}")
    print(f"Generated Caption: {caption}")
