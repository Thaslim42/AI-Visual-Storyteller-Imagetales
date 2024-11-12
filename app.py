from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import base64
import os
import re
import io
import pygame
import requests
from dotenv import load_dotenv
from groq import Groq
import openai
import argparse

# Initialize Flask app
app = Flask(__name__)
CORS(app)
load_dotenv()

# API Keys and Configuration
api_key = os.getenv("GROQ_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
client = Groq(api_key=api_key)
llava_model = 'llava-v1.5-7b-4096-preview'
MODEL_ID = 'gpt-3.5-turbo'

# ElevenLabs Configuration
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 1,
    "use_speaker_boost": False
}

# [Previous helper functions remain the same: encode_image, image_to_text, generate_description, ChatGPT_conversation]
# Helper function to encode image as base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Generate image description using LLAVA model
def image_to_text(client, model, base64_image, prompt):
    chat_completion = client.chat.completions.create(
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

# Endpoint to generate description from image using LLAVA model
@app.route('/generate_description', methods=['POST'])
def generate_description():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'})
    
    image = request.files['image']
    default_prompt = 'Describe this image in detail like a story.'

    # Save and encode the image
    image_path = secure_filename(image.filename)
    image.save(image_path)
    base64_image = encode_image(image_path)

    # Get image description
    image_description = image_to_text(client, llava_model, base64_image, default_prompt)
    
    return jsonify({'description': image_description})

# ChatGPT conversation handler that takes the image description as the prompt
def ChatGPT_conversation(conversation):
    response = client.chat.completions.create(
        model= MODEL_ID,
        messages=conversation
    )
    conversation.append({
        'role': response['choices'][0]['message']['role'],
        'content': response['choices'][0]['message']['content']
    })
    return conversation
@app.route('/generate_visual_story', methods=['POST'])
def generate():
    print("Initializing Call")
    
    # if 'image' not in request.files:
    #     return jsonify({'error': 'No image file uploaded'})
    
    # image = request.files['image']
    # default_prompt = 'Describe this image in detail like a story.'

    # Save and encode the image
    # image_path = secure_filename(image.filename)
    # image.save(image_path)
    # base64_image = encode_image(image_path)

    try:
        # Get image description directly
        # image_description = image_to_text(client, llava_model, base64_image, default_prompt)
        
        # Initialize conversation with generated description
        conversation = [
            {
                'role': 'system', 
                'content': f'Give a short story with a description of an image that would suit each paragraph. '
                          f'Format = Image Description: Paragraph: {image_description}'
            }
        ]
        conversation = ChatGPT_conversation(conversation)
        raw_contents = conversation[1]["content"]

        # Rest of the function remains the same
        split_contents = re.split('\n|\n\n', raw_contents)
        image_descriptions, paragraphs, images = [], [], []

        for line in split_contents:
            if line == "":
                continue
            if "Image Description:" in line:
                image_descriptions.append(line[len('Image Description:'):].strip())
            elif "Paragraph:" in line:
                paragraphs.append(line[len('Paragraph:'):].strip())

        # Generate images
        for index, description in enumerate(image_descriptions):
            if index >= len(paragraphs):
                break
                
            res = openai.Image.create(
                prompt=description,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
            
            b64 = res['data'][0]['b64_json']
            images.append({
                'paragraph': paragraphs[index], 
                'description': description, 
                'data': b64
            })

        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)
            
        return jsonify(images)
        
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({'error': str(e)}), 500

def text_to_speech(text):
    """Convert text to speech using ElevenLabs API"""
    headers = {
        "xi-api-key": elevenlabs_api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": VOICE_SETTINGS
    }
    
    response = requests.post(ELEVENLABS_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"ElevenLabs API Error: {response.text}")

@app.route('/Hear_story', methods=['POST'])
def generate_story_with_audio():
    try:
        # Generate the story and images
        story_data = generate()
        
        # Convert story to speech
        full_story = ""
        for image_data in story_data:
            full_story += f"{image_data['paragraph']}\n\n"
        
        audio_data = text_to_speech(full_story)
        
        # Convert audio data to base64 for frontend
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Add audio data to response
        response_data = {
            'story': story_data,  # Contains paragraphs, descriptions, and generated images
            'audio': audio_base64
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080, debug=True)