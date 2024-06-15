#!/usr/bin/env python
import os
import sqlite3
import requests
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('HADITH_API_KEY')

# Set up the database
conn = sqlite3.connect('subscribers.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS subscribers (chat_id INTEGER UNIQUE)''')
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily Hadith notifications."""
    user_id = update.effective_user.id
    try:
        c.execute("INSERT INTO subscribers (chat_id) VALUES (?)", (user_id,))
        conn.commit()
        await update.message.reply_text(
            "You have been subscribed to daily Hadith notifications by Hadith Inc.! 🕌\n"
            "Use /help to learn more about the commands available.\n\n"
            "Stay tuned and receive a daily Hadith automatically, InshaAllah! 🕋\n\n"
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text("You are already subscribed to Hadith Inc., MashaAllah 📚")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Here's how you can use this bot:\n"
        "/start - Subscribe to daily Hadith notifications\n"
        "/help - Get help and command usage\n"
        "/about - Learn more about this service and its creator\n"
        "/stop - Unsubscribe from daily Hadith notifications\n\n"
        "Just stay tuned and receive a daily Hadith automatically, InshaAllah! 🕋"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide information about the bot and its creator."""
    await update.message.reply_text(
        "<b>About This Service:</b>\n"
        "This bot provides daily Hadiths from renowned sources: Sahih Bukhari, Sahih Muslim"
        "and Al-Tirmidhi. These texts are essential in understanding the sayings and practices of the "
        "Prophet Muhammad (PBUH).\n\n"
        "<b>Creator:</b>\n"
        "Muhammad Sajawal Khan from Pakistan 🇵🇰 (Contact Me: sajawalkhan111@gmail.com)\n"
        "Please remember me in your prayers. 🤲\n\n"
        "The Hadiths are carefully selected and provided from respected collections, ensuring authenticity "
        "and relevance.\n\n"
        "Thank you for using this service, and may it benefit you greatly. Aameen!",
        parse_mode='HTML'
    )
    
# stop the bot
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily Hadith notifications."""
    user_id = update.effective_user.id
    try:
        c.execute("DELETE FROM subscribers WHERE chat_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text("You have been unsubscribed from daily Hadith notifications. 😢")
    except sqlite3.IntegrityError:
        await update.message.reply_text("You are not subscribed to Hadith Inc. yet. 😇")
        

async def send_hadith(context: CallbackContext) -> None:
    """Send a random Hadith to all subscribers."""
    # Define the books and their ranges
    books = {
        'sahih-bukhari': 7563,
        'sahih-muslim': 7500,
        'al-tirmidhi': 3950
    }

    # Randomly select a book
    selected_book, max_hadith_number = random.choice(list(books.items()))

    # Generate a random Hadith number within the valid range for the selected book
    hadith_number = random.randint(1, max_hadith_number)

    # Construct the API endpoint
    url = f"https://www.hadithapi.com/public/api/hadiths?apiKey={API_KEY}&hadithNumber={hadith_number}&book={selected_book}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()['hadiths']['data'][0]
        message = (
            f"<b>🕌 Salaam, from Hadith Inc.</b>\n\n"
            f"<b>📜 Hadith of the Day:</b>\n\n"
            f"<i>{data['hadithEnglish']}</i>\n\n"
            f"<b>📖 Urdu Translation:</b>\n\n {data['hadithUrdu']}\n\n"
            f"<b>🗣 Narrated by:</b> {data['englishNarrator']}\n"
            f"<b>🔍 Reference:</b> {data['book']['bookName']}, Hadith No. {data['hadithNumber']}\n"
            f"<b>📚 Chapter:</b> {data['chapter']['chapterEnglish']} (Vol. {data['volume']})\n\n"
            f"<b>If you love this bot, remember me in your prayers. JazakAllah Khair!</b>\n\n"
            f"📷 <a href='https://instagram.com/hadith.inc'>Follow us on Instagram</a>\n"

        )
        c.execute("SELECT chat_id FROM subscribers")
        chat_ids = c.fetchall()
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(chat_id=chat_id[0], text=message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to send message to {chat_id[0]}: {e}")
    else:
        logger.error("Failed to fetch Hadith.")


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("stop", stop))

    # Schedule the daily Hadith to be sent every day at 7:30 AM Pakistan Standard Time
    application.job_queue.run_daily(send_hadith, time=datetime.time(hour=2, minute=30)) # 7:00 AM PST


    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
