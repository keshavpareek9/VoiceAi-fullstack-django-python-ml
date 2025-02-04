import asyncio
import datetime
import json
import logging
import os
import platform
import glob
import soundfile as sf
import speech_recognition as sr
import librosa
from gtts import gTTS
import openai
import pygame
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from voice_command.responses import greeting_responses
from voice_command.utils import stopAudioPlayback

# Configure OpenAI API key
openai.api_key = "sk-proj-c6SnJ39v2VPLWvK7cvP1T3BlbkFJRtscOIb1sQm8mIl55Cp6"

# Configure logging
logging.basicConfig(filename='files/app.log', level=logging.ERROR, format='%(asctime)s %(message)s')

# Global variable to store the last response
last_response = ""

# File to store interaction logs
interaction_log_file = 'files/interaction_logs.txt'

def index(request):
    return render(request, 'voice_command/index.html')

@csrf_exempt
def listen(request):
    if request.method == 'GET':
        result = asyncio.run(main())  # Assuming `main()` returns `response_data` including `audio_url`
        return JsonResponse(result)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only GET requests are allowed'}, status=405)

@csrf_exempt
def stop_audio(request):
    if request.method == 'POST':
        stopAudioPlayback()  # Call your existing stop audio function
        return JsonResponse({'status': 'success', 'message': 'Audio playback stopped.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

def say(text):
    print(text)  # Print the text for debugging
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
            logging.error(f"Unsupported OS for playback: {os_name}")

    except Exception as e:
        logging.error(f"Error during text-to-speech: {e}")
        print("An error occurred while generating speech. Please check the log file for more details.")
    finally:
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass

# Function to check if the query is related to repair
def is_query_related(query, domain_keywords):
    return any(keyword in query.lower() for keyword in domain_keywords)

# Asynchronous function to take voice command from the user
async def take_command(domain_keywords, retries=3):
    global last_response
    recognizer = sr.Recognizer()
    response_data = {"command": "", "message": ""}

    with sr.Microphone() as source:
        say("Listening for user command...")
        try:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            say("Recognizing user command...")

            # Save audio for preprocessing
            with open("audio.wav", "wb") as f:
                f.write(audio.get_wav_data())

            # Preprocess audio asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, preprocess_audio, "audio.wav")

            with sr.AudioFile("processed.wav") as source:
                audio = recognizer.record(source)

            try:
                query = recognizer.recognize_google(audio, language="en-in")
                print(f"User said: {query}")
                response_data["command"] = query
            except sr.UnknownValueError:
                query = ""
                print("Google could not understand the audio")

            if not query:
                try:
                    query = recognizer.recognize_sphinx(audio)  # CMU Sphinx as fallback
                    print(f"User said (Sphinx): {query}")
                    response_data["command"] = query
                except sr.UnknownValueError:
                    query = ""
                    print("Sphinx could not understand the audio")

            if not query:
                response_data["message"] = "Sorry, I didn't understand that. Please try again."
                say(response_data["message"])
                return response_data

            # Check if the query is a common greeting or time-related query
            if handle_common_greetings(query.lower()):
                response_data["message"] = last_response
                return response_data

            if not is_query_related(query, domain_keywords):
                if query.lower() == "can you repeat":
                    repeat_last_response()
                else:
                    response_data["message"] = "Sorry, I can only assist with the selected domain-related queries."
                    say(response_data["message"])
                return response_data

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": query}
                ]
            )

            answer = response['choices'][0]['message']['content'].strip()
            answer = ' '.join(answer.split()[:150])  # Limit the response to 150 words
            last_response = answer
            response_data["message"] = answer
            say(answer)
            say("How can I assist you further?")

        except sr.WaitTimeoutError:
            print("Timeout occurred. Retrying...")
            if retries > 0:
                return await take_command(domain_keywords, retries - 1)
            else:
                response_data["message"] = "Timeout occurred. Please try again."
                say(response_data["message"])
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said.")
        except Exception as e:
            logging.error(f"Error in take_command: {e}")
            print("An error occurred. Please check the log file for more details.")
        finally:
            if os.path.exists("audio.wav"):
                os.remove("audio.wav")
            if os.path.exists("processed.wav"):
                os.remove("processed.wav")
            return response_data

def handle_common_greetings(query):
    global last_response
    response = greeting_responses.get(query)
    if response:
        last_response = response
        say(response)
        say("How can I assist you further?")
        return True
    return False

def repeat_last_response():
    global last_response
    if last_response:
        say(last_response)
    else:
        say("There is no previous response to repeat.")

def preprocess_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)  # Load the audio file
    y_resampled = librosa.resample(y, orig_sr=sr, target_sr=16000)  # Resample to 16kHz
    sf.write("processed.wav", y_resampled, 16000)  # Save the processed file

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

def log_interaction(query, response):
    try:
        with open(interaction_log_file, 'a') as log_file:
            log_file.write(f"User Query: {query}\nAssistant Response: {response}\n\n")
    except Exception as e:
        logging.error(f"Error logging interaction: {e}")

def cleanup_temp_files():
    try:
        files = glob.glob("output_*.mp3")
        for file in files:
            os.remove(file)
    except Exception as e:
        logging.error(f"Error cleaning up temporary files: {e}")

async def main():
    say("Hey! I am your assistant.")
    
    domain_keyword_files = choose_domain()
    domain_keywords = []
    for file in domain_keyword_files:
        keywords = load_keywords(file)
        if keywords:
            domain_keywords.extend(keywords)
        else:
            print("No keywords loaded. Exiting.")
            return
    
    try:
        while True:
            result = await take_command(domain_keywords)
            if result:
                log_interaction(result["command"], result["message"])
                return result
    finally:
        cleanup_temp_files()

def choose_domain():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        say("Please choose a domain by saying the domain name, for example, 'Repair' or 'Health'")
        say("Listening for domain choice...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Adjust noise for a shorter duration
            audio = recognizer.listen(source, timeout=5)  # Reduce the timeout if needed
            domain_choice = recognizer.recognize_google(audio, language="en-in").lower()
            print(f"User chose: {domain_choice}")

            if "repair" in domain_choice:
                return ["files/repair.txt"]
            elif "health" in domain_choice:
                return ["files/health.txt"]
            else:
                say("Invalid choice. Please say 'Repair' or 'Health'.")
                return choose_domain()
        except sr.WaitTimeoutError:
            say("Timeout occurred. Please try again.")
            return choose_domain()
        except sr.UnknownValueError:
            say("Sorry, I could not understand what you said. Please try again.")
            return choose_domain()
        except Exception as e:
            logging.error(f"Error in choose_domain: {e}")
            print("An error occurred. Please check the log file for more details.")
            return choose_domain()

if __name__ == '__main__':
    asyncio.run(main())
