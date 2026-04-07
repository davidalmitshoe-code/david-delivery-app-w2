import logging
import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# ---------------- FLASK HEARTBEAT (Render fix) ----------------
server = Flask(__name__)

@server.route('/')
def home():
    return "UMC Blessed Bot is Online 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ---------------- CONFIGURATION ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("BOT_TOKEN")   # <-- use Render env variable
ADMIN_ID = 998942116
ADMIN_USERNAME = "@Haffa_advert"
DEVELOPER_USERNAME = "@pselms"

NAME, PHONE, EMAIL, PHOTO, CHOIR_PART, PAY_TYPE, SCREENSHOT = range(7)

# ---------------- BOT LOGIC ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 Grace and Peace to you!\n\n"
        "Welcome to the UMC Choir Registration.\n"
        "Please enter your Full Name:"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Enter your Phone Number:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Enter your Email Address:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text(
        "Send profile photo or type /skip"
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['profile_pic'] = update.message.photo[-1].file_id
    else:
        context.user_data['profile_pic'] = None

    keyboard = [['Member', 'Participant', 'Other']]
    await update.message.reply_text(
        "Which member are you?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CHOIR_PART


async def get_choir_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type'] = update.message.text

    pay_keyboard = [
        ['Student (25)', 'Uni Student (50)'],
        ['Worker (100)', 'Yearly (300)'],
        ['Membership (300)', 'Studio/Album Donation']
    ]

    await update.message.reply_text(
        "Select your Payment Type:",
        reply_markup=ReplyKeyboardMarkup(pay_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return PAY_TYPE


async def get_pay_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pay_choice'] = update.message.text

    bank_details = (
        "Payment Details:\n\n"
        "CBE: 1000021359778\n"
        "Hossana Hawariyawit B/K Maranata Mez\n\n"
        "Send payment screenshot"
    )

    await update.message.reply_text(
        bank_details,
        reply_markup=ReplyKeyboardRemove()
    )

    return SCREENSHOT


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Send receipt photo.")
        return SCREENSHOT

    receipt = update.message.photo[-1].file_id
    data = context.user_data

    report = (
        "NEW UMC REGISTRATION\n\n"
        f"Name: {data.get('name')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Email: {data.get('email')}\n"
        f"Type: {data.get('type')}\n"
        f"Payment: {data.get('pay_choice')}\n"
        f"User ID: {update.effective_user.id}"
    )

    try:
        await context.bot.send_message(ADMIN_ID, report)

        if data.get('profile_pic'):
            await context.bot.send_photo(
                ADMIN_ID,
                data['profile_pic'],
                caption="Profile Photo"
            )

        await context.bot.send_photo(
            ADMIN_ID,
            receipt,
            caption="Payment Receipt"
        )

        await update.message.reply_text(
            "Registration Successful!\n\n"
            f"Support: {ADMIN_USERNAME}\n"
            f"SupportDeveloper: {DEVELOPER_USERNAME}"
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Error sending to admin.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Registration cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ---------------- MAIN ----------------
def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                CommandHandler("skip", get_photo)
            ],
            CHOIR_PART: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_choir_part)],
            PAY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_type)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("Bot running...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
