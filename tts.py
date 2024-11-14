import requests
import pygame
import io

paragraphs= ["This is the first paragraph of the document. It provides an introduction to the topic at hand, offering some background information and setting the stage for the rest of the content.",
    "The second paragraph delves deeper into the details of the subject. It expands on key points raised earlier, providing more specific information and examples to support the argument.",
    "In the third paragraph, the discussion shifts focus slightly to address a related but different aspect of the topic. It introduces new perspectives and offers insights into potential challenges or solutions.",]
story_text = '\n\n'.join(paragraphs)
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

