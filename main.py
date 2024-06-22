import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load environment variables from .env file
load_dotenv()

# Access environment variables from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Function to get weather data
def get_weather(city):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    response = requests.get(url)
    return response.json()
     # Assuming successful request

# Function to format the weather message
def format_weather_message(data):
    city = data["location"]["name"]
    current_temp_c = data["current"]["temp_c"]
    weather_description = data["current"]["condition"]["text"]
    return (f"**{city} ka Mausam:**\n\n"
            f"* Aaj ka mausam: {weather_description}\n"
            f"* Taapmaan: {current_temp_c}°C\n")

# Function to handle the /start command
def start(update, context):
    update.message.reply_text(f"Hello {update.message.from_user.first_name}! 🌞\n\n"
                              "Welcome to our weather bot, created by a team of passionate engineering students from DSCE. Whether you're planning a picnic, checking on your travel destinations, or simply curious about the weather, I'm here to help!\n\n"
                              "Just type the name of any city or 'weather' followed by the city name to get started. For example:\n"
                              "• 'weather Bangalore'\n"
                              "• 'weather Delhi'\n\n"
                              "Let's dive into the world of weather! 🌍☀️🌧️❄️")

# Function to handle weather requests
def handle_weather_request(update, city):
    weather_data = get_weather(city)
    if "error" in weather_data:
        update.message.reply_text(f"Error: {weather_data['error']['message']}")
    else:
        response_message = format_weather_message(weather_data)
        update.message.reply_text(response_message)

# Function to handle messages
def message_handler(update, context):
    text = update.message.text.strip().lower()
    if text.startswith("weather "):
        city = text[len("weather "):].strip()
        handle_weather_request(update, city)
    else:
        handle_weather_request(update, text)

# Define the main function to start the bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler('start', start))

    # Message handler
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    # Start the bot
    updater.start_polling()
    print("Telegram bot is now running.")

    # Keep the program running
    updater.idle()

if __name__ == '__main__':
    main()