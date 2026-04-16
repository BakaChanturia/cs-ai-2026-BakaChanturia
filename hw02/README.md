# HW2 Audio Pipeline

## Overview

This project implements an end-to-end audio pipeline using the Gemini API.

The pipeline performs the following steps:

Text → Text-to-Speech (TTS) → MP3 → Speech-to-Text (STT) → Comparison

The goal is to demonstrate how AI systems can generate, process, and evaluate audio data.

---

## Project Structure

```
hw2/
├── hw2-audio-pipeline.py
├── reflection.md
├── requirements.txt
├── .env.example
├── audio-output/
│   ├── voice_kore_sample.mp3
│   └── voice_puck_sample.mp3
└── README.md
```

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Create a `.env` file in the project directory:

```
GEMINI_API_KEY=your_api_key_here
```

Note: Do not commit your real API key. Use `.env.example` as a template.

---

## Running the Pipeline

Run the script from the `hw2` directory:

```bash
python hw2-audio-pipeline.py
```

---

## Pipeline Steps

### Step 1 – Text-to-Speech (Voice 1)

- Converts input text into speech using the first voice (Kore)
- Saves output as an MP3 file
- Reports generation time and file size

---

### Step 2 – Text-to-Speech (Voice 2)

- Generates the same text using a second voice (Puck)
- Allows comparison between voice styles

---

### Step 3 – Speech-to-Text

- Transcribes one of the generated audio files
- Reports transcription time and audio duration

---

### Step 4 – Comparison

- Compares original and transcribed text
- Calculates word overlap accuracy

---

## Example Output

```
=== HW2 Audio Pipeline ===

[1/4] Generating speech with voice: Kore
  Text: "Welcome to the museum audio guide..."
  Generated in 17.97s
  File: audio-output/voice_kore_sample.mp3 (114.3 KB)
  Cost: $0.0000

[2/4] Generating speech with voice: Puck
  Text: "Welcome to the museum audio guide..."
  Generated in 19.37s
  File: audio-output/voice_puck_sample.mp3 (120.0 KB)
  Cost: $0.0000

[3/4] Transcribing audio-output/voice_kore_sample.mp3
  Transcript: "Welcome to the museum audio guide..."
  Transcribed in 5.82s
  Audio duration: 29.2s
  Cost: $0.0000

[4/4] Comparing original vs transcribed text
  Original:    "Welcome to the museum audio guide..."
  Transcribed: "Welcome to the museum audio guide..."
  Word overlap accuracy: 100.0%

=== Cost and Latency Summary ===
  TTS calls:  2 | Total cost: $0.0000 | Avg latency: 18.67s
  STT calls:  1 | Total cost: $0.0000 | Avg latency: 5.82s
  Pipeline total: $0.0000

=== Pipeline complete ===
```

---

## Output Files

Generated audio files are stored in:

```
audio-output/
```

Example:

- voice_kore_sample.mp3  
- voice_puck_sample.mp3  

---

## Notes

- Gemini Free Tier is used, so cost is displayed as $0.0000
- ffmpeg is required for MP3 conversion
- The script includes retry logic for API calls
- Both MP3 and WAV formats are supported for transcription

---

## Summary

This project demonstrates a complete audio processing pipeline including speech generation, transcription, and evaluation.