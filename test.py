from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import base64
import os
import re
import requests
from dotenv import load_dotenv
from groq import Groq
# import openai
import logging
from openai import OpenAI
import argparse
import pygame
import io

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
load_dotenv()

# client = OpenAI()
# API Keys and Configuration
grok_api_key = os.getenv("GROQ_API_KEY")
# openai_api_key = os.getenv("OPENAI_API_KEY")
client1 = Groq(api_key=grok_api_key)
llava_model = 'llava-v1.5-7b-4096-preview'
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
# client = OpenAI(
#     # This is the default and can be omitted
#     api_key=os.environ.get("OPENAI_API_KEY"),
# )




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
        latest_image_description = image_to_text(client1, llava_model, base64_image, default_prompt)
        
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
            'content': 
                f'''Give a short story with a description of an image that would suit each paragraph. The following is the prompt. 
                Format = 
                Image Description:
                Paragraph:
                {latest_image_description}'''
            }
        )
        conversation = ChatGPT_conversation(conversation)
        ans = ('{0}: {1}\n'.format(conversation[-1]['role'].strip(), conversation[-1]['content'].strip()))
        raw_contents = conversation[1]["content"]
        print("RAW: ",conversation)
        print()

        split_contents = re.split('\n|\n\n', raw_contents)
        print("Contents: ", split_contents)
        print()
        # Create empty lists for image descriptions, paragraphs, and images
        image_descriptions = []
        paragraphs = []
        images = []

        # Split the answer into lines
        lines = ans.strip().split('\n')

        for i, line in enumerate(split_contents):
            if line==(""):
                pass
            # Check if the line is an image description
            if "Image Description:" in line:
                # Append the image description to the list
                image_descriptions.append(line[len('Image Description:'):].strip())
            # Check if the line is a paragraph
            elif "Paragraph:" in line:
                # Append the paragraph to the list
                paragraphs.append(line[len('Paragraph:'):].strip())

        # Generate images 
        count = 1
        for index, description in enumerate(image_descriptions):
            # Parse the command line arguments
            parser = argparse.ArgumentParser()
            parser.add_argument("-p", "--prompt", help="Text to image prompt:", default=description)
            parser.add_argument("-n", "--number", help="Number of images generated", default=1)
            parser.add_argument("-s", "--size", help="Image size: 256, 512 or 1024", default=1024)

            # Finalize arguments
            args = parser.parse_args()

            # Get the results of the image
            res = openai_client.images.generate(
            prompt=args.prompt,
            n=int(args.number),
            size=f'{args.size}x{args.size}',
            response_format="b64_json"
            )

            # Access the data attribute of the ImagesResponse object
            for i in range(len(res.data)):
                # Get the B64 JSON data of the image
                b64 = res.data[i].b64_json

                # Add the file name, description, and paragraph to the images list
                images.append({'paragraph': paragraphs[index], 'description': description, 'data': b64})
                
                # Increment count
                count += 1
                
        print("RAW: ", raw_contents)
        print()
        print("IMAGES: ", images)
        print()
        
        story_text = '\n\n'.join(paragraphs)
        
        return jsonify({
           'success': True,
            'original_description': latest_image_description,
           'story_data': images,
           'story_text': story_text
        })

    except Exception as e:
        logger.error(f"Error in story generation: {str(e)}")
        return jsonify({
           'success': False,
            'error': str(e)
        }), 500


@app.route('/hear_story', methods=['POST'])
def hear_story():
    try:
        # Get the story data from the request
        # story_data = request.json['story_data']
        story_text = request.json['story_text']

        # Set up the text-to-speech request
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        payload = {
            "text": story_text,
            "model_id": "eleven_monolingual_v1",
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