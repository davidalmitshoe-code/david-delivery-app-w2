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

# --- 1. THE WEB HEARTBEAT (Fixes Render Port Errors) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "UMC Blessed Bot is Online 24/7"

def run_flask():
    # Render requires port 10000 by default or via environment variable
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False is critical when running in a thread
    server.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- 2. CONFIGURATION ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8651749292:AAE669h-KhqRLqVuHaoWiRo2zRRmza0W95c" 
ADMIN_ID = 998942116 
ADMIN_USERNAME = "@Haffa_advert" # <--- Added for display
DEVELOPER_USERNAME = "@pselms" 

NAME, PHONE, EMAIL, PHOTO, CHOIR_PART, PAY_TYPE, SCREENSHOT = range(7)

# --- 3. BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 **Grace and Peace to you in the name of our Lord!**\n\n"
        "Welcome to the UMC Choir Registration. We are blessed to have you.\n"
        "To begin, what is your **Full Name**?",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"Thank you, {update.message.text}. Now, what is your **Phone Number**?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Great! Please enter your **Email Address**:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    await update.message.reply_text(
        "📸 **Profile Picture:**\n"
        "Please send a photo for your choir profile, or type /skip to continue without one."
    )
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['profile_pic'] = update.message.photo[-1].file_id
    else:
        context.user_data['profile_pic'] = None

    reply_keyboard = [['Member', 'Participant', 'other']]
    await update.message.reply_text(
        "Which Member are you in NOW?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
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
        "💳 **Select your Contribution/Payment Type:**",
        reply_markup=ReplyKeyboardMarkup(pay_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PAY_TYPE

async def get_pay_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pay_choice'] = update.message.text
    bank_details = (
        "✅ **Payment Details:**\n\n"
        "🏦 **CBE:** `1000021359778` (Hossana Hawariyawit B/K Maranata Mez)\n"
        "Please complete your payment and **send the Screenshot** of the receipt below."
    )
    await update.message.reply_text(bank_details, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send the payment receipt as a photo.")
        return SCREENSHOT

    receipt_photo = update.message.photo[-1].file_id
    user_info = context.user_data
    admin_report = (
        "🚨 **NEW UMC REGISTRATION** 🚨\n\n"
        f"👤 **Name:** {user_info.get('name')}\n"
        f"📞 **Phone:** {user_info.get('phone')}\n"
        f"📧 **Email:** {user_info.get('email')}\n"
        f"🎶 **Type:** {user_info.get('type')}\n"
        f"💰 **Payment Choice:** {user_info.get('pay_choice')}\n"
        f"🆔 **User ID:** {update.effective_user.id}"
    )

    try:
        # Notify Admin
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_report, parse_mode="Markdown")
        if user_info.get('profile_pic'):
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=user_info['profile_pic'], caption="Member Profile Photo")
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=receipt_photo, caption="Payment Receipt attached.")
        
        # Confirmation to User
        await update.message.reply_text(
            "✅ **Registration Successful!**\n\n"
            "Your information has been submitted. May the Lord bless your service.\n\n"
            "📖 *'Serve the Lord with gladness; come before him with joyful songs.' - Psalm 100:2*\n\n"
            f"🆘 **Support Admin:** {ADMIN_USERNAME}\n"
            f"💻 **Support Developer:** {DEVELOPER_USERNAME}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error notifying admin. Please contact {DEVELOPER_USERNAME}")
        logging.error(f"Error in registration: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration stopped. God bless you.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- 4. MAIN EXECUTION ---
def main():
    # Start Flask first to satisfy Render's port check immediately
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Build the application
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo), CommandHandler('skip', get_photo), MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo)],
            CHOIR_PART: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_choir_part)],
            PAY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pay_type)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    
    print("Bot is LIVE! Keep the terminal/server running.")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
