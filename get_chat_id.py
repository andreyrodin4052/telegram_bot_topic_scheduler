from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

# Main function to run the bot
def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Add the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
