import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini model globally
model = None

def configure_ai():
    """Initializes the AI engine with API keys."""
    global model
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        api_key = api_key.strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    else:
        print("Warning: GEMINI_API_KEY not found in environment!")

# For direct use if imported
configure_ai()


def analyze_product(image_path):
    """Analyze the product image using Gemini Vision."""
    sample_file = genai.upload_file(path=image_path, display_name="Product")
    
    prompt = """
    Analyze this product image. Provide a detailed description including:
    1. What the product is.
    2. Key features and visual elements.
    3. Target audience.
    4. Overall vibe (luxury, practical, fun, etc.).
    Keep it concise but detailed enough for marketing purposes.
    """
    
    response = model.generate_content([sample_file, prompt])
    return response.text

def generate_marketing_content(product_description):
    """Generate 5 marketing angles using Gemini."""
    prompt = f"""
    Based on this product description:
    {product_description}
    
    Create 5 distinct marketing advertisements in SPANISH. 
    Each ad must follow one of these specific angles:
    1. Deseo/Aspiración: Focus on how it improves the user's life/status.
    2. Conexión emocional: Focus on feelings, family, or personal growth.
    3. Urgencia/Escasez: Focus on limited time or stock.
    4. Prueba social: Focus on popularity and reviews.
    5. Beneficio Racional: Focus on specs, price, and utility.
    
    Format the response EXACTLY as follows for each angle:
    ---
    ANGLE_NAME: [Name of the angle]
    COPY: [The marketing text]
    IMAGE_PROMPT: [A very detailed English prompt for an HD professional advertisement image using Flux model. Include details about lighting, high-end photography, and professional typography/layout.]
    ---
    """
    
    response = model.generate_content(prompt)
    return response.text

def generate_marketing_image(prompt, index):
    """Generate an image using Pollinations.ai with the Flux model."""
    # Encode prompt for URL
    encoded_prompt = requests.utils.quote(prompt)
    # Flux model is usually better for text and quality
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
    
    response = requests.get(url)
    if response.status_code == 200:
        image_filename = f"ad_image_{index}.jpg"
        with open(image_filename, 'wb') as f:
            f.write(response.content)
        return image_filename
    return None

def parse_angles(content):
    """Simple parser for the generated angles."""
    angles = []
    blocks = content.split("---")
    for block in blocks:
        if "ANGLE_NAME:" in block and "COPY:" in block:
            angle_data = {}
            lines = block.strip().split("\n")
            for line in lines:
                if line.startswith("ANGLE_NAME:"):
                    angle_data['name'] = line.replace("ANGLE_NAME:", "").strip()
                elif line.startswith("COPY:"):
                    angle_data['copy'] = line.replace("COPY:", "").strip()
                elif line.startswith("IMAGE_PROMPT:"):
                    angle_data['image_prompt'] = line.replace("IMAGE_PROMPT:", "").strip()
            if angle_data:
                angles.append(angle_data)
    return angles
