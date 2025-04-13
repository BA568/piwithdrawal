
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import random

# Load Firebase
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://piwalletwithdrawel.firebaseio.com/'
})

# Telegram Setup
BOT_TOKEN = '7557926144:AAH3bBKcAoLgO5KTHWjXWmHY9Q3Rm5FM6u0'
AUTHORIZED_USERS = ["@Banky664", "@RITAHERNANDEZ001"]
ADMIN = "@RITAHERNANDEZ001"

# In-Memory Store
user_requests = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👑 Welcome to the Pi Withdrawal Bot. Type /withdraw to begin.")

def withdraw(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_requests[user_id] = {"step": 1}
    update.message.reply_text("Enter your Pi wallet address 🧾:")

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_requests:
        return

    step = user_requests[user_id]["step"]

    if step == 1:
        user_requests[user_id]["wallet"] = text
        user_requests[user_id]["step"] = 2
        update.message.reply_text("Enter amount to withdraw 💰:")
    elif step == 2:
        user_requests[user_id]["amount"] = text
        passcode = str(random.randint(100000, 999999))
        user_requests[user_id]["passcode"] = passcode

        # Save to Firebase
        ref = db.reference(f"/requests/{user_id}")
        ref.set(user_requests[user_id])

        # Notify admin
        context.bot.send_message(chat_id=ADMIN,
            text=f"🛡️ New Withdrawal Request:\n\n👤 User: @{update.effective_user.username}\n💰 Amount: {text}\n🏦 Wallet: {user_requests[user_id]['wallet']}\n\nReply with:\n/approve {user_id} {passcode}")

        update.message.reply_text("📨 Request submitted. Awaiting admin approval...")

        # Reset
        user_requests.pop(user_id)

def approve(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 2:
        update.message.reply_text("Usage: /approve <user_id> <passcode>")
        return

    user_id, code = args
    ref = db.reference(f"/requests/{user_id}")
    data = ref.get()

    if data and data.get("passcode") == code:
        tx_hash = f"0xSIMULATED{random.randint(1000000,9999999)}"
        context.bot.send_message(chat_id=int(user_id),
            text=f"✅ Approved!\n\n💰 Amount: {data['amount']}\n🏦 Wallet: {data['wallet']}\n\n🔁 TX HASH: `{tx_hash}`",
            parse_mode='Markdown')

        context.bot.send_message(chat_id=ADMIN, text=f"✅ Sent to {data['wallet']} with hash {tx_hash}")
        ref.delete()
    else:
        update.message.reply_text("❌ Invalid passcode or request")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("withdraw", withdraw))
    dp.add_handler(CommandHandler("approve", approve))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
