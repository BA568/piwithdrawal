import os
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import random

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://piwalletwithdrawel.firebaseio.com/'
})

user_requests = {}
ADMIN_USERNAME = "@RITAHERNANDEZ001"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Welcome to the Pi Withdrawal Bot. Type /withdraw to begin.")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_requests[user_id] = {"step": 1}
    await update.message.reply_text("Enter your Pi wallet address 🧾:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_requests:
        return

    step = user_requests[user_id]["step"]

    if step == 1:
        user_requests[user_id]["wallet"] = text
        user_requests[user_id]["step"] = 2
        await update.message.reply_text("Enter amount to withdraw 💰:")
    elif step == 2:
        user_requests[user_id]["amount"] = text
        passcode = str(random.randint(100000, 999999))
        user_requests[user_id]["passcode"] = passcode

        ref = db.reference(f"/requests/{user_id}")
        ref.set(user_requests[user_id])

        admin_chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=admin_chat_id,
            text=f"🛡️ New Withdrawal Request:\n\n👤 User: @{update.effective_user.username}\n💰 Amount: {text}\n🏦 Wallet: {user_requests[user_id]['wallet']}\n\nReply with:\n/approve {user_id} {passcode}")

        await update.message.reply_text("📨 Request submitted. Awaiting admin approval...")
        user_requests.pop(user_id)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /approve <user_id> <passcode>")
        return

    user_id, code = args
    ref = db.reference(f"/requests/{user_id}")
    data = ref.get()

    if data and data.get("passcode") == code:
        tx_hash = f"0xSIMULATED{random.randint(1000000,9999999)}"
        await context.bot.send_message(chat_id=int(user_id),
            text=f"✅ Approved!\n\n💰 Amount: {data['amount']}\n🏦 Wallet: {data['wallet']}\n\n🔁 TX HASH: `{tx_hash}`",
            parse_mode='Markdown')

        await context.bot.send_message(chat_id=update.effective_chat.id,
            text=f"✅ Sent to {data['wallet']} with hash {tx_hash}")
        ref.delete()
    else:
        await update.message.reply_text("❌ Invalid passcode or request")

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
