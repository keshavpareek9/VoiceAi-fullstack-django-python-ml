import datetime

# Function to get the current time
def get_current_time_response():
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")  # Example: 07:30 AM
    return f"It's currently {current_time}."

# Common greeting questions and responses
greeting_responses = {
    "how are you": "I'm an AI, so I don't have feelings, but I'm here and ready to help you!",
    "what's your name": "I'm Rishbh, your AI assistant.",
    "where are you from": "I was created by Keshav, based in India.",
    "how's it going": "I'm functioning smoothly and ready to assist you. How can I help you today?",
    "what do you do": "I assist with answering questions, providing information, and helping with various tasks.",
    "have we met before": "I'm not able to remember past interactions, but I'm here to assist you with whatever you need right now.",
    "how was your day": "I don't experience days, but I'm here to make your day better!",
    "what brings you here": "I'm here to help you with any questions or tasks you have.",
    "how have you been": "I'm always operational and ready to assist you.",
    "what's new with you": "I don't have personal updates, but I'm always learning and improving to assist you better.",
    "did you have a good weekend": "I don't experience weekends, but I'm always here to help you, no matter the day.",
    "how's everything": "Everything is running smoothly. How can I assist you today?",
    "nice to meet you. how do you do": "Nice to meet you too! I'm here to assist with anything you need.",
    "long time no see. how have you been": "I've been right here, always ready to help. How can I assist you today?",
    "how is your family": "I don't have a family, but I'm here to help you with any information or assistance you need.",
    "how's your work going": "My work is to assist you, and it's going great! How can I help you today?",
    "how's your health": "I don't have health, but I'm fully operational and ready to assist you.",
    "what have you been up to": "I've been here, ready to assist you with any queries or tasks you have.",
    "do you come here often": "I'm always here, available whenever you need assistance.",
    "how is the weather today": "I can't check the current weather directly, but you can use weather websites or apps for the most accurate information.",
    "good morning": "Good morning! How can I assist you today?",
    "good afternoon": "Good afternoon! How can I assist you right now?",
    "good evening": "Good evening! How can I help you at this hour?",
    "what time is it": get_current_time_response(),
    "what's the time": get_current_time_response(),
    "do you have the time": get_current_time_response()
}
