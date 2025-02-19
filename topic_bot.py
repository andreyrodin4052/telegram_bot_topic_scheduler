import logging
import json
from datetime import time, datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from calendar_manager import CalendarManager  # Your custom library

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# JSON file to store configurations
CONFIG_FILE = "config.json"

# Global scheduler
scheduler = AsyncIOScheduler()

# Global variables for /add command
topic = None
exponent_base = None

# Initialize CalendarManager
calendar_db = CalendarManager()

def load_config():
    """Load configurations from the JSON file."""
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            return (
                config["BOT_TOKEN"],
                config["CHAT_ID"],
                time(hour=config["DEFAULT_TIME"]["hour"], minute=config["DEFAULT_TIME"]["minute"]),
            )
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error loading config file: {e}")
        raise RuntimeError("Failed to load configuration. Please check the config file.")

def save_config(bot_token: str, chat_id: int, default_time: time):
    """Save configurations to the JSON file."""
    config = {
        "BOT_TOKEN": bot_token,
        "CHAT_ID": chat_id,
        "DEFAULT_TIME": {"hour": default_time.hour, "minute": default_time.minute},
    }
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

async def remind_topic(app: Application, date: str = None):
    """Remind me of a topic every day at a given time."""
    # Use the provided date or the current date if none is provided
    if date:
        try:
            # Validate the date format (yyyy-mm-dd)
            datetime.strptime(date, "%Y-%m-%d")
            current_date = date
        except ValueError:
            # If the date is invalid, use the current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            logger.warning(f"Invalid date format '{date}'. Using current date instead.")
    else:
        current_date = datetime.now().strftime("%Y-%m-%d")

    # Get the text and is_event flag from the calendar manager
    text_event , is_event = calendar_db.show_events(current_date)

    # Send the message only if there is an event
    if is_event:
        await app.bot.send_message(chat_id=CHAT_ID, text=text_event )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to initialize the bot and list available commands."""
    commands = [
        ("/start", "Start the bot and list all available commands."),
        ("/settime HH:MM", "Set the time for the daily reminder (in UTC)."),
        ("/add <topic> <exponent_base>", "Add a topic and an exponent base. If the last argument is not a number between 1 and 5, it is treated as part of the topic, and the exponent base defaults to 2."),
        ("/remind [yyyy-mm-dd]", "Manually trigger the reminder for the specified or current date."),
    ]

    # Create a formatted message with all commands and descriptions
    message = "Welcome! Here are the available commands:\n\n"
    for command, description in commands:
        message += f"{command}: {description}\n"

    await update.message.reply_text(message)

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the time for the daily reminder."""
    try:
        # Check if more than one argument is provided
        if len(context.args) != 1:
            raise ValueError("Please provide exactly one argument (time in HH:MM format).")

        # Get the time from the user's message (format: HH:MM)
        new_time = context.args[0]
        hour, minute = map(int, new_time.split(':'))
        new_time_obj = time(hour=hour, minute=minute)
        
        # Stop the existing job
        scheduler.remove_job("daily_reminder")

        # Add a new job with the updated time
        scheduler.add_job(
            remind_topic,
            trigger=CronTrigger(hour=new_time_obj.hour, minute=new_time_obj.minute, timezone="UTC"),
            id="daily_reminder",
            args=[context.application],  # Pass the application object
        )

        # Save the new default time to the config file
        save_config(BOT_TOKEN, CHAT_ID, new_time_obj)

        await update.message.reply_text(f"Time updated successfully! New time: {new_time_obj.strftime('%H:%M')} UTC")
    except ValueError as e:
        await update.message.reply_text(f"Error: {e}\nUsage: /settime HH:MM")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a topic and an exponent base."""
    global topic, exponent_base

    try:
        # Check if at least one argument is provided
        if len(context.args) < 1:
            raise ValueError("Please provide at least one argument: a topic.")

        # Check if the last argument is a number between 1 and 5
        try:
            exponent_base = float(context.args[-1])
            if not (1 <= exponent_base <= 5):  # If not between 1 and 5, treat it as part of the topic
                raise ValueError
        except (ValueError, IndexError):
            # If the last argument is not a valid number between 1 and 5, treat it as part of the topic
            exponent_base = 2.0  # Default value
            topic = " ".join(context.args)  # All arguments are part of the topic
        else:
            # If the last argument is a valid number, separate it from the topic
            topic = " ".join(context.args[:-1])  # All arguments except the last are part of the topic

        # Add the topic and exponent base to the calendar manager
        result = calendar_db.add_multiple(topic, exponent_base)

        # Send the result to the user
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def trigger_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger the reminder for the specified or current date."""
    try:
        # Get the optional date argument (if provided)
        date = context.args[0] if context.args else None

        # Call the remind_topic function with the optional date
        await remind_topic(context.application, date)
        await update.message.reply_text("Manual reminder sent successfully!")
    except Exception as e:
        await update.message.reply_text(f"Failed to send manual reminder: {e}")

async def post_init(application: Application):
    """Start the scheduler after the bot is running."""
    # Schedule the job with the loaded default time
    scheduler.add_job(
        remind_topic,
        trigger=CronTrigger(hour=DEFAULT_TIME.hour, minute=DEFAULT_TIME.minute, timezone="UTC"),
        id="daily_reminder",
        args=[application],  # Pass the application object
    )
    scheduler.start()

def main():
    """Start the bot."""
    global BOT_TOKEN, CHAT_ID, DEFAULT_TIME

    # Load configurations from the JSON file
    try:
        BOT_TOKEN, CHAT_ID, DEFAULT_TIME = load_config()
    except RuntimeError as e:
        logger.error(e)
        return

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settime", set_time))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("remind", trigger_reminder))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()