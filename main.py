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
        amount = float(data["amount"])
        wallet = data["wallet"]

        balance_ref = db.reference(f"/users/{user_id}/balance")
        current_balance = balance_ref.get() or 500.0

        if current_balance < amount:
            await update.message.reply_text("❌ Insufficient balance.")
            return

        new_balance = current_balance - amount
        balance_ref.set(new_balance)

        tx_hash = f"0xSIMULATED{random.randint(1000000,9999999)}"
        db.reference(f"/logs/{tx_hash}").set({
            "user_id": user_id,
            "wallet": wallet,
            "amount": amount,
            "balance_after": new_balance
        })

        await context.bot.send_message(chat_id=int(user_id),
            text=f"✅ Approved!\n\n💰 Amount: {amount}\n🏦 Wallet: {wallet}\n\n🔁 TX HASH: `{tx_hash}`\n\n🪙 New Balance: {new_balance}",
            parse_mode='Markdown')

        await context.bot.send_message(chat_id=update.effective_chat.id,
            text=f"✅ Sent to {wallet} with hash {tx_hash}\nNew balance: {new_balance}")

        ref.delete()
    else:
        await update.message.reply_text("❌ Invalid passcode or request")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance_ref = db.reference(f"/users/{user_id}/balance")
    balance = balance_ref.get() or 500.0
    balance_ref.set(balance)
    await update.message.reply_text(f"💰 Your current Pi balance is: {balance}")

async def set_webhook():
    from telegram import Bot
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    url = os.getenv("WEBHOOK_URL")  # You must set this in Railway
    await bot.set_webhook(url=url)

def main():
    import asyncio
    asyncio.run(set_webhook())

    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=os.getenv("WEBHOOK_URL")
    )

if __name__ == "__main__":
    main()
