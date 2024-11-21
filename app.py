import streamlit as st
import openai
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime
import hashlib

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(page_title="DALL-E Image Generator", layout="wide")

# Initialize OpenAI client
def initialize_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        openai.api_key = api_key
        return True
    st.error("OPENAI_API_KEY not found in environment variables!")
    return False

def generate_image(prompt, size="1024x1024"):
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        
        # Download the image
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

def verify_password():
    """Simple password protection for the app"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Enter application password:", type="password")
        app_password = os.getenv('APP_PASSWORD')
        
        if password:
            if app_password and hashlib.sha256(password.encode()).hexdigest() == app_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password!")
        return st.session_state.authenticated
    return True

def rate_limit():
    """Simple rate limiting"""
    if 'last_generation' not in st.session_state:
        st.session_state.last_generation = None
    
    if st.session_state.last_generation:
        time_diff = (datetime.now() - st.session_state.last_generation).total_seconds()
        if time_diff < 10:  # 10 seconds cooldown
            st.warning(f"Please wait {10 - int(time_diff)} seconds before generating another image")
            return False
    return True

def main():
    st.title("DALL-E Image Generator")
    
    # Add password protection
    if not verify_password():
        return
        
    # Initialize OpenAI
    if not initialize_openai():
        return
    
    # Image generation section
    prompt = st.text_area("Enter your image prompt:", height=100)
    size = st.selectbox("Select image size:", ["1024x1024", "1792x1024", "1024x1792"])
    
    if st.button("Generate Image"):
        if prompt:
            # Add rate limiting
            if not rate_limit():
                return
                
            with st.spinner("Generating image..."):
                # Sanitize prompt
                prompt = prompt.strip()[:1000]  # Limit prompt length
                
                image = generate_image(prompt, size)
                if image:
                    st.session_state.last_generation = datetime.now()
                    st.image(image, caption="Generated Image", use_column_width=True)
                    
                    # Add download button
                    buf = BytesIO()
                    image.save(buf, format="PNG")
                    st.download_button(
                        label="Download Image",
                        data=buf.getvalue(),
                        file_name="generated_image.png",
                        mime="image/png"
                    )
        else:
            st.warning("Please enter a prompt first!")

if __name__ == "__main__":
    main()