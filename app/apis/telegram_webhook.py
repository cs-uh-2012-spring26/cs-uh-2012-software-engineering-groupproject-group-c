import os
import requests
from flask import request
from flask_restx import Namespace, Resource

import app.db.users as users_db

api = Namespace('telegram', description='Telegram webhook for chat_id capture')

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


def send_telegram_message(chat_id: str, text: str):
    """Send a message to a Telegram user."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    url = TELEGRAM_API_URL.format(token=token, method="sendMessage")
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception:
        pass


def send_contact_request(chat_id: str):
    """Ask user to share their contact."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    url = TELEGRAM_API_URL.format(token=token, method="sendMessage")
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": "Welcome to FitnessApp! 👋\n\nPlease share your contact so we can link your account and send you class reminders.",
            "reply_markup": {
                "keyboard": [[{
                    "text": "📱 Share Contact",
                    "request_contact": True
                }]],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
        }, timeout=5)
    except Exception:
        pass


@api.route('/webhook')
class TelegramWebhook(Resource):

    def post(self):
        """
        Telegram webhook endpoint.
        Telegram calls this when a user messages the bot.
        Automatically captures chat_id by matching phone number to user account.
        """
        data = request.json
        if not data:
            return {'status': 'no data'}, 200

        message = data.get('message', {})
        chat_id = str(message.get('chat', {}).get('id', ''))

        if not chat_id:
            return {'status': 'no chat_id'}, 200

        # Handle contact sharing
        contact = message.get('contact')
        if contact:
            phone_number = contact.get('phone_number', '').strip()
            # Normalize — remove + and spaces, keep last 10 digits
            phone_number = phone_number.replace('+', '').replace(' ', '')
            phone_number = phone_number[-10:]

            user = users_db.get_user_by_phone(phone_number)
            if user:
                users_db.update_chat_id(user['email'], chat_id)
                send_telegram_message(
                    chat_id,
                    "✅ *Account linked successfully!*\n\nYou will now receive Telegram notifications for your fitness classes."
                )
            else:
                send_telegram_message(
                    chat_id,
                    "❌ No account found with this phone number.\n\nPlease make sure you registered with this number."
                )
            return {'status': 'ok'}, 200

        # Any other message — ask for contact
        send_contact_request(chat_id)
        return {'status': 'ok'}, 200