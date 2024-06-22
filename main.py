import os
import requests
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import pytz

# Load environment variables from .env file
load_dotenv()

# Access environment variables from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Timezone for scheduling (change as per your requirement)
TIMEZONE = 'Asia/Kolkata'

# Dictionary to store user settings (time and city)
user_settings = {}

# Scheduler object
scheduler = BackgroundScheduler()

# Function to get weather data
def get_weather(city):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": {"message": "Failed to retrieve weather data. Please try again later."}}

# Function to format the weather message
def format_weather_message(data):
    city = data["location"]["name"]
    current_temp_c = data["current"]["temp_c"]
    weather_description = data["current"]["condition"]["text"].lower()
    
    if "sunny" in weather_description:
        return (f"☀ Current Weather in {city}:\n\n"
                f"It's a bright and sunny day with a temperature of {current_temp_c}°C. Perfect weather to soak up some sunshine and enjoy the outdoors! 🌞")
    elif "cloudy" in weather_description:
        return (f"☁ Current Weather in {city}:\n\n"
                f"The temperature is {current_temp_c}°C, with a blanket of clouds overhead. A great day for a cozy indoor activity or a leisurely walk! ☁")
    elif any(keyword in weather_description for keyword in ["rain", "showers"]):
        return (f"🌧 Current Weather in {city}:\n\n"
                f"It's {current_temp_c}°C with rain showers. Don’t forget your umbrella if you're heading out, and maybe enjoy the soothing sound of the rain! 🌧")
    elif "snow" in weather_description:
        return (f"❄ Current Weather in {city}:\n\n"
                f"Brrr, it’s {current_temp_c}°C with a snowy wonderland outside. Bundle up if you're going out, or stay warm and watch the snowflakes dance! ❄")
    elif "windy" in weather_description:
        return (f"🌬 Current Weather in {city}:\n\n"
                f"The temperature is {current_temp_c}°C, and it's quite windy out there. Hold onto your hat and enjoy the brisk breeze! 🌬")
    elif any(keyword in weather_description for keyword in ["storm", "thunderstorm"]):
        return (f"⛈ Current Weather in {city}:\n\n"
                f"It's {current_temp_c}°C with a storm brewing. Stay safe indoors, and perhaps enjoy a good book or movie while the storm passes! ⛈")
    elif "fog" in weather_description:
        return (f"🌫 Current Weather in {city}:\n\n"
                f"With a temperature of {current_temp_c}°C, it's quite foggy. Drive safely and take it slow in the low visibility! 🌫")
    elif "partly cloudy" in weather_description:
        return (f"🌤 Current Weather in {city}:\n\n"
                f"The temperature is {current_temp_c}°C with some clouds in the sky. It's a mix of sun and clouds, perfect weather for a day outdoors! 🌤")
    elif "overcast" in weather_description:
        return (f"🌥 Current Weather in {city}:\n\n"
                f"It's {current_temp_c}°C with overcast skies. The sky is completely covered with clouds, making it a bit gloomy outside. 🌥")
    elif "mist" in weather_description:
        return (f"🌫 Current Weather in {city}:\n\n"
                f"The temperature is {current_temp_c}°C with mist in the air. The visibility is reduced, so take care if you're driving or walking outdoors! 🌫")
    else:
        return (f"Current Weather in {city}:\n\n"
                f"The temperature is {current_temp_c}°C with {weather_description}.")

# Function to send weather update message
def send_weather_update(context):
    for user_id, settings in user_settings.items():
        city = settings['city']
        weather_data = get_weather(city)
        if "error" in weather_data:
            message = f"Error: {weather_data['error']['message']}"
        else:
            message = format_weather_message(weather_data)
        context.bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN)

# Function to send daytime alerts every 4 hours
def send_daytime_alert(context):
    current_time = datetime.now(pytz.timezone(TIMEZONE)).time()
    if current_time >= time(8, 0) and current_time <= time(20, 0):  # Check if current time is between 8 AM and 8 PM
        for user_id in user_settings:
            context.bot.send_message(chat_id=user_id, text="Hello! Just a friendly alert from your weather bot. Have a great day!")
    else:
        print("Skipping daytime alert as it is outside of specified hours.")

# Function to handle /setweather command
def set_weather(update, context):
    if len(context.args) < 2:
        update.message.reply_text("Please provide both time and city in the format: /setweather HH:MM CityName")
        return
    
    try:
        time_str = context.args[0]
        city = " ".join(context.args[1:])
        
        # Validate time format
        datetime.strptime(time_str, "%H:%M")
        
        # Store user settings
        user_id = update.message.from_user.id
        user_settings[user_id] = {'time': time_str, 'city': city}
        
        update.message.reply_text(f"Got it! I will send you daily weather updates for {city} at {time_str} (local time).")
        
        # Schedule the weather update
        schedule_weather_update(context)
        
    except ValueError:
        update.message.reply_text("Invalid time format. Please use HH:MM format for time.")

# Function to handle /stopweather command
def stop_weather(update, context):
    user_id = update.message.from_user.id
    if user_id in user_settings:
        del user_settings[user_id]
        update.message.reply_text("You will no longer receive daily weather updates.")
    else:
        update.message.reply_text("You haven't set any daily weather updates yet.")

# Function to schedule weather updates
def schedule_weather_update(context):
    global scheduler
    if scheduler.running:
        scheduler.shutdown(wait=False)
        scheduler = BackgroundScheduler()
    
    scheduler.configure(timezone=pytz.timezone(TIMEZONE))
    
    for user_id, settings in user_settings.items():
        time_str = settings['time']
        city = settings['city']
        
        hour, minute = map(int, time_str.split(':'))
        
        trigger = CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone(TIMEZONE))
        scheduler.add_job(send_weather_update, trigger=trigger, args=[context])
    
    scheduler.start()

# Function to handle the /start command
def start(update, context):
    update.message.reply_text(f"Hello {update.message.from_user.first_name}! 🌞\n\n"
                              "Welcome to our weather bot, created by a team of passionate engineering students from DSCE. Whether you're planning a picnic, checking on your travel destinations, or simply curious about the weather, I'm here to help!\n\n"
                              "To set your daily weather update time and city, use the command:\n"
                              "/setweather HH:MM CityName\n\n"
                              "To stop receiving daily weather updates, use:\n"
                              "/stopweather\n\n"
                              "Let's dive into the world of weather! 🌍☀🌧❄")

# Function to handle messages
def message_handler(update, context):
    text = update.message.text.strip().lower()
    if text.startswith("/setweather"):
        set_weather(update, context)
    elif text == "/stopweather":
        stop_weather(update, context)