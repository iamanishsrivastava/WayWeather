import os
import telebot
from telebot import types
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_weather(city):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    response = requests.get(url)
    return response.json()  # Assuming successful request

def format_weather_message(data):
    city = data["location"]["name"]
    current_temp_c = data["current"]["temp_c"]
    weather_description = data["current"]["condition"]["text"]
    return (f"**{city}'s Weather :**\n\n"
            f"* Today's Weather : {weather_description}\n"
            f"* Current Temperature : {current_temp_c}°C\n")

def handle_weather_request(message, city):
    weather_data = get_weather(city)
    if "error" in weather_data:
        bot.send_message(message.chat.id, f"Error: {weather_data['error']['message']}")
    else:
        response_message = format_weather_message(weather_data)
        bot.send_message(message.chat.id, response_message)

# Create a Telegram Bot instance
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Handle start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_message = (f"Hi {message.from_user.first_name}! \n\n"
                       f"I'm a personal Weather Bot developed by group of engineers to get the weather for any city by just typing it's name or 'weather' followed by the city name .\n\n"
                       f"For example, try:\n* 'weather Bangalore'\n* ',Delhi'")
    bot.send_message(message.chat.id, welcome_message)

# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower().strip()
    if text.startswith("weather "):
        city = text[len("weather "):].strip()
        handle_weather_request(message, city)
    elif text:  # If any text is provided, assume it's a city name
        handle_weather_request(message, text)
    else:
        bot.send_message(message.chat.id, "Please provide a city name.")

# Start the bot
bot.polling()