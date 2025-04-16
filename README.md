**SuperApp**

SuperApp is a multi-functional desktop application that combines several powerful tools into one convenient interface. It features:

- Media Converter: Convert audio and video files between various formats using FFmpeg.
- Offline Translator: Translate text offline between multiple languages with Argos Translate.
- PDF Translator: Extract text (with OCR fallback) from PDF files, translate it, and create a new PDF.
- Video Translator: Transcribe and translate video/audio files using OpenAI's Whisper to create subtitle file in English.
- Video Downloader: Download videos from popular sites (e.g., YouTube, Vimeo) using yt-dlp with multiple options (audio extraction, subtitles, metadata embedding, etc.).

 Features

- User-Friendly Interface: Built with Tkinter and organized using Notebook tabs.
- Multi-Tool Integration: All functionalities accessible from one unified application.
- Cross-Platform: Works on Windows, Linux, and macOS.
- Offline Translation: No Internet connection required for text and PDF translation once language packages are installed.

## Requirements

The project relies on the following Python libraries:

- Pillow
- pytesseract
- PyPDF2
- argostranslate
- reportlab
- pdf2image
- openai-whisper
- yt-dlp
- torch

Other requirements:
- **Tkinter**: Included with Python.
- **FFmpeg**: Must be installed and added to your system PATH.
- **Poppler**: Required for pdf2image to work correctly (install via Homebrew on macOS: `brew install poppler`).

See the provided [`requirements.txt`](requirements.txt) for the full list of Python packages.

## Installation

1. **Clone the Repository:**

   git clone https://github.com/yourusername/superapp.git
   cd superapp

Install Python Dependencies:
Ensure you are using Python 3. Then run:

pip install -r requirements.txt

Install External Dependencies:
FFmpeg: Download and install FFmpeg.
Poppler (macOS): Install via Homebrew:

brew install poppler

Running the Application
To start SuperApp, simply run:

python3 superapp.py

This will launch the SuperApp window with all the tabs for the integrated functionalities.



Screenshots

<img width="451" alt="image" src="https://github.com/user-attachments/assets/de17b6de-dead-423f-8d00-dd18e0d4011d" />

<img width="451" alt="image" src="https://github.com/user-attachments/assets/bf46ac31-8afb-450a-bf90-5407d9adf86d" />

<img width="451" alt="image" src="https://github.com/user-attachments/assets/ee47ee83-46b3-479d-98a8-03cc6b19b557" />

<img width="451" alt="image" src="https://github.com/user-attachments/assets/57f67d5c-2028-4d11-9ff3-b366cee54e01" />




