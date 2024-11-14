import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [description, setDescription] = useState('');
  const [storyData, setStoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState('');
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setDescription('');
      setStoryData(null);
      setError(null);
    }
  };

  const generateDescription = async () => {
    if (!selectedImage) {
      setError('Please select an image first');
      return;
    }

    setLoading(true);
    setLoadingProgress('Generating description...');
    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post('http://localhost:8080/generate_description', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setDescription(response.data.description);
    } catch (err) {
      setError('Error generating description: ' + err.message);
    } finally {
      setLoading(false);
      setLoadingProgress('');
    }
  };

  const generateVisualStory = async () => {
    if (!description) {
      setError('Please generate a description first');
      return;
    }

    setLoading(true);
    setLoadingProgress('Generating visual story...');

    try {
      const response = await axios.post('http://localhost:8080/generate_visual_story', {
        prompt: description
      });

      console.log('Story Response:', response.data);

      if (response.data.success && response.data.story_data) {
        setStoryData(response.data.story_data);
      } else {
        throw new Error('Failed to generate story');
      }
    } catch (err) {
      console.error('Story generation error:', err);
      setError('Error generating story: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
      setLoadingProgress('');
    }
  };

  const playStory = async () => {
    if (!storyData || isPlaying) return;

    setIsPlaying(true);
    setLoadingProgress('Playing audio...');

    try {
      // Construct the story text from all paragraphs
      const story_text = storyData.map(segment => segment.paragraph).join(' ');
      
      const response = await axios.post('http://localhost:8080/hear_story', {
        story_text: story_text
      });

      if (!response.data.success) {
        throw new Error('Failed to play audio');
      }
    } catch (err) {
      setError('Error playing audio: ' + err.message);
    } finally {
      setIsPlaying(false);
      setLoadingProgress('');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>ImageTales</h1>
        <div className="tagline">Uncover the Magic Hidden in Every Moment</div>
      </header>

      <main className="App-main">
        <section className="control-panel">
          <div className="upload-section">
            <input
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              id="image-upload"
              className="file-input"
            />
            <label htmlFor="image-upload" className="upload-button">
              {selectedImage ? 'Change Image' : 'Upload Image'}
            </label>

            {previewUrl && (
              <div className="preview-container">
                <img src={previewUrl} alt="Preview" className="preview-image" />
              </div>
            )}
          </div>

          <div className="button-container">
            <button
              onClick={generateDescription}
              disabled={!selectedImage || loading}
              className="action-button"
            >
              {loading && !description ? 'Generating...' : 'Generate Scenario'}
            </button>
            <button
              onClick={generateVisualStory}
              disabled={!description || loading}
              className="action-button"
            >
              {loading && description ? 'Generating...' : 'Generate Story'}
            </button>
            <button
              onClick={playStory}
              disabled={!storyData || loading || isPlaying}
              className="action-button audio-button"
              aria-label="Play story audio"
            >
              <span className="audio-icon">🔊</span>
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}
          {loading && (
            <div className="loading">
              <div className="loading-spinner"></div>
              <p>{loadingProgress}</p>
            </div>
          )}
        </section>

        {description && (
          <section className="description-section">
            <h2>STORY SCENARIO</h2>
            <div className="content-box">
              <p>{description}</p>
            </div>
          </section>
        )}

        {storyData && (
          <section className="story-section">
            <h2>GENERATED VISUAL STORY</h2>
            <div className="story-container">
              {storyData.map((segment, index) => (
                <div key={index} className={`story-segment ${index % 2 === 1 ? 'reverse' : ''}`}>
                  <div className="story-image">
                    {segment.data && (
                      <img 
                        src={`data:image/jpeg;base64,${segment.data}`}
                        alt={`Story scene ${index + 1}`}
                        onError={(e) => {
                          console.error('Image loading error for segment:', index, e);
                          e.target.src = 'placeholder.png';
                        }}
                      />
                    )}
                  </div>
                  <div className="story-text">
                    <div className="paragraph">
                      <p>{segment.paragraph}</p>
                    </div>
                    <div className="image-description">
                      <h4>Scene Description:</h4>
                      <p>{segment.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;