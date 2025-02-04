import os
import glob
import logging
import datetime
import platform
import asyncio
import librosa
import soundfile as sf
import speech_recognition as sr
from gtts import gTTS
import openai

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(filename='files/app.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

# Global variable to store the last response
last_response = ""

# Function to convert text to speech using gTTS
def say(text):
    try:
        tts = gTTS(text=text, lang='en-in')
        file_name = f"output_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        tts.save(file_name)

        # Determine the OS and use the appropriate command to play the file
        os_name = platform.system().lower()
        if 'darwin' in os_name:
            os.system(f"afplay {file_name}")  # For macOS
        elif 'win' in os_name:
            os.system(f"start {file_name}")  # For Windows
        elif 'linux' in os_name:
            os.system(f"xdg-open {file_name}")  # For Linux
        else:
            print(f"Unsupported OS for playback: {os_name}")

        # Clean up the temporary file
        os.remove(file_name)

    except Exception as e:
        logging.error(f"Error during text-to-speech: {e}")
        print("An error occurred while generating speech. Please check the log file for more details.")

# Function to check if the query is related to the chosen domain
def is_query_related(query, domain_keywords):
    return any(keyword in query.lower() for keyword in domain_keywords)

# Function to load keywords from a file
def load_keywords(file_path):
    try:
        with open(file_path, "r") as file:
            keywords = [line.strip() for line in file]
        print(f"Loaded keywords from {file_path}: {keywords}")
        return keywords
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        print(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Error while loading keywords from {file_path}: {e}")
        print("An error occurred while loading keywords. Please check the log file for more details.")
        return []

# Function to preprocess audio using librosa
def preprocess_audio(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)  # Load the audio file
        y_resampled = librosa.resample(y, orig_sr=sr, target_sr=16000)  # Resample to 16kHz
        sf.write("processed.wav", y_resampled, 16000)  # Save the processed file
    except Exception as e:
        logging.error(f"Error during audio preprocessing: {e}")
        print("An error occurred during audio preprocessing. Please check the log file for more details.")

# Asynchronous function to take voice command from the user
async def take_command(domain_keywords):
    global last_response
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        say("Listening for user command...")
        try:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            print("Recognizing user command...")

            # Save audio for preprocessing
            with open("audio.wav", "wb") as f:
                f.write(audio.get_wav_data())

            # Preprocess audio asynchronously
            await asyncio.to_thread(preprocess_audio, "audio.wav")

            with sr.AudioFile("processed.wav") as source:
                audio = recognizer.record(source)

            try:
                query = recognizer.recognize_google(audio, language="en-in")
                print(f"User said: {query}")
            except sr.UnknownValueError:
                query = ""
                print("Google could not understand the audio")

            if not query:
                try:
                    query = recognizer.recognize_sphinx(audio)
                    print(f"User said: {query}")
                except sr.UnknownValueError:
                    print("Sphinx could not understand the audio")
                    say("Could not understand the audio")
                    return None

            # Check if the query is related to the chosen domain
            if not is_query_related(query, domain_keywords):
                say("Query not related to the chosen domain")
                return None

            response = await process_query(query)
            say(response)
            return response

        except sr.WaitTimeoutError:
            say("Listening timed out. Please try again.")
            return None

# Asynchronous function to process user query using OpenAI API
async def process_query(query):
    global last_response
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=query,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7
        )
        last_response = response.choices[0].text.strip()
        return last_response
    except Exception as e:
        logging.error(f"Error during query processing: {e}")
        print("An error occurred during query processing. Please check the log file for more details.")
        return "An error occurred during query processing."
