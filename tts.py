import requests
import pygame
import io

url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"

payload = {
    "text": """GitHub Models: A New Era of AI-Powered Development

GitHub Models is a platform that allows developers to interact with a variety of AI models directly within the GitHub ecosystem. It's designed to streamline development processes and enhance productivity.""",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.8,
        "style": 1,
        "use_speaker_boost": False
    }
}

headers = {
    "xi-api-key": "sk_97cceca5ebf83045d5ca0339512cc0ff1ec01f739c009c52",
    "Content-Type": "application/json"
}

# Send the POST request
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
else:
    print(f"Error: {response.text}")






def ChatGPT_conversation(conversation):
    # Receive response from ChatGPT
    response = openai.ChatCompletion.create(  # Correct method
        model=MODEL_ID,
        messages=conversation
    )
    
    # Append information to the conversation
    conversation.append({
        'role': response['choices'][0]['message']['role'],  # Extract the role from the response
        'content': response['choices'][0]['message']['content']  # Extract the content
    })
    
    # Return updated conversation
    return conversation

# GET - Image and Story generator
@app.route('/generate', methods=['POST'])
def generate():
    # Print information
    print("Initializing Call")
    
    # Get the prompt
    prompt = request.json['prompt']
    
    print("USER PROMPT: ", prompt)
    
    # Variable prepping
    conversation = []
    conversation.append(
        {
            'role': 'system', 
            'content': 
                f'''Give a short story with a description of an image that would suit each paragraph. The following is the prompt. 
                Format = 
                Image Description:
                Paragraph:
                {prompt}'''
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
        if line == "":
            continue
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
