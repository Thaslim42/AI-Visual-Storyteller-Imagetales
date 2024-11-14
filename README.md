# AI-Visual-Storyteller-Imagetales
generate story from image frames
## Demo Video
[link]([https://www.linkedin.com/posts/thaslim-vs_ai-machinelearning-python-activity-7262339032800460800](https://www.linkedin.com/posts/thaslim-vs_ai-machinelearning-python-activity-7262339032800460800-i8vR))

![assets/screenshot.png](https://github.com/Thaslim42/AI-Visual-Storyteller-Imagetales/blob/7baf1c75586291f9591457d0be601ad18250a137/Screenshot%202024-11-12%20150903.png)
![screenshot2.png](https://github.com/Thaslim42/AI-Visual-Storyteller-Imagetales/blob/main/Screenshot%202024-11-14%20220040.png)
![screenshot3.png](https://github.com/Thaslim42/AI-Visual-Storyteller-Imagetales/blob/main/Screenshot%202024-11-12%20162222.png)


This Flask-based web application integrates multiple AI services to generate image descriptions, stories, and voice outputs. The application performs the following:

Image Description Generation: Users can upload an image, and the app generates a cartoon-like description using the LLAVA model.

Story Generation: Based on the image description, a visual story is created, where each paragraph is paired with an image description. The story is generated using OpenAI's GPT-3.5 model.
Text-to-Speech Conversion: After generating the story, users can listen to it through the Eleven Labs text-to-speech API, converting the story into audio format.

Technologies Used:
Flask: Web framework for building the app.
OpenAI API: For text and image generation.
Eleven Labs API: Converts generated text into speech.
LLAVA: AI model used for image description generation.
Groq API: Utilized for handling specific AI tasks.

Features:
Upload an image to generate a description.
Generate a visual story based on the image description.
Convert the story into audio and listen to it.

This project brings together AI models in computer vision, natural language processing, and text-to-speech to create a multimedia experience, making it both interactive and immersive.

