from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import base64
import os
import re
import requests
from dotenv import load_dotenv
from groq import Groq
import logging
from openai import OpenAI
import argparse
import pygame
import io
import time

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
load_dotenv()

# Client setup
grok_api_key = os.getenv("GROQ_API_KEY")
llava_model = 'llava-v1.5-7b-4096-preview'
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

# Global variable to store the latest image description
latest_image_description = None

def encode_image(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def image_to_text(client1, model, base64_image, prompt):
    """Generate description using LLAVA model"""
    chat_completion = client1.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        model=model
    )
    return chat_completion.choices[0].message.content

@app.route('/generate_description', methods=['POST'])
def generate_description():
    """Generate description from uploaded image using LLAVA"""
    global latest_image_description
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400
    
    try:
        image = request.files['image']
        default_prompt = 'Describe this image like a cartoon image.'

        # Save and encode the image
        image_path = secure_filename(image.filename)
        image.save(image_path)
        base64_image = encode_image(image_path)

        # Get image description
        latest_image_description = image_to_text(Groq(api_key=grok_api_key), llava_model, base64_image, default_prompt)
        
        # Clean up the saved image
        if os.path.exists(image_path):
            os.remove(image_path)
        
        return jsonify({
            'success': True,
            'description': latest_image_description
        })
        
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def ChatGPT_conversation(conversation):
    """Handle the conversation with GPT model"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation,
            temperature=0.7,
            max_tokens=2000
        )
        
        conversation.append({
            'role': response.choices[0].message.role,
            'content': response.choices[0].message.content
        })
        return conversation
    except Exception as e:
        logger.error(f"Error in ChatGPT conversation: {str(e)}")
        raise

def generate_image(prompt, max_retries=3, retry_delay=5):
    """Generate an image using the OpenAI API"""
    retries = 0
    while retries < max_retries:
        try:
            res = openai_client.images.generate(
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
            return res.data[0].b64_json
        except Exception as e:
            if "429" in str(e):
                retries += 1
                logger.warning(f"Rate limit reached, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Error generating image: {str(e)}")
                raise
    logger.error("Maximum retries reached, unable to generate image.")
    return None

@app.route('/generate_visual_story', methods=['POST'])
def generate_visual_story():
    """Generate story based on the latest image description"""
    global latest_image_description

    try:
        if not latest_image_description:
            return jsonify({
              'success': False,
                'error': 'No image description available. Please generate a description first.'
            }), 400

        # Initialize conversation with the image description
        conversation = []
        conversation.append(
            {
                'role':'system', 
                'content': f'''Give a short story with a description of an image that would suit each paragraph. The following is the prompt:
                
                Image Description:
                {latest_image_description}
                
                Paragraph:'''
            }
        )
        conversation = ChatGPT_conversation(conversation)
        
        # Extract the paragraphs and image descriptions from the conversation
        image_descriptions = []
        paragraphs = []
        for message in conversation:
            if message['role'] == 'assistant':
                content = message['content']
                if 'Image Description:' in content:
                    image_description = content.split('Image Description:')[1].strip()
                    if image_description:
                        image_descriptions.append(image_description)
                    else:
                        logger.warning("Empty image description in the response.")
                elif 'Paragraph:' in content:
                    paragraph = content.split('Paragraph:')[1].strip()
                    if paragraph:
                        paragraphs.append(paragraph)
                    else:
                        logger.warning("Empty paragraph in the response.")
                else:
                    logger.warning(f"Unexpected response format: {content}")
            else:
                logger.warning(f"Unexpected message role: {message['role']}")

        if len(image_descriptions) != len(paragraphs):
            logger.error("Mismatch between the number of image descriptions and paragraphs.")
            return jsonify({
                'success': False,
                'error': "Unexpected response format from the GPT-3 API."
            }), 500

        # Generate images
        images = []
        for index, description in enumerate(image_descriptions):
            image_data = generate_image(description)
            images.append({
                'paragraph': paragraphs[index],
                'description': description,
                'data': image_data
            })

        story_text = '\n\n'.join(paragraphs)
        
        return jsonify({
           'success': True,
           'original_description': latest_image_description,
           'story_data': images,
           'story_text': story_text
        })

    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        return jsonify({
           'success': False,
            'error': str(e)
        }), 500

@app.route('/hear_story', methods=['POST'])
def hear_story():
    try:
        # Get the story text from the request
        story_text = request.json['story_text']

        # Set up the text-to-speech request
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        payload = {
            "text": story_text,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 1,
                "use_speaker_boost": False
            }
        }
        headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }

        # Send the text-to-speech request
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Use BytesIO to handle the audio data in memory
            audio_data = io.BytesIO(response.content)

            # Initialize pygame mixer
            pygame.mixer.init()

            # Load and play the audio from memory
            pygame.mixer.music.load(audio_data)
            print("Playing audio...")
            pygame.mixer.music.play()

            # Wait for the audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Return a success response
            return jsonify({'success': True})
        else:
            # Return an error response
            return jsonify({'success': False, 'error': response.text}), 500

    except Exception as e:
        logger.error(f"Error in hearing story: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 
    
if __name__ == '__main__':
    app.run(port=8080, debug=True)