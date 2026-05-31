"""
WhatsApp Bot - Software/Web/App Development Business
Supports English and Luganda
Runs on Hetzner VPS with Meta Cloud API + Claude AI
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from claude_ai import get_ai_response
from responses import get_menu, detect_language
from leads import save_lead

load_dotenv()

app = Flask(__name__)

# Meta API credentials from .env
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Track conversation state per user
conversation_states = {}


def send_message(to, message):
    """Send WhatsApp text message to a number"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def send_interactive_menu(to, title, body, options):
    """Send interactive button menu"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    rows = [{"id": str(i+1), "title": opt} for i, opt in enumerate(options)]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": title},
            "body": {"text": body},
            "action": {
                "button": "Choose Option",
                "sections": [{"title": "Menu", "rows": rows}]
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def handle_message(phone, message_text):
    """Main logic to handle incoming messages"""

    msg = message_text.strip().lower()
    state = conversation_states.get(phone, {"step": "start", "lang": "en", "data": {}})
    lang = detect_language(message_text) or state.get("lang", "en")
    state["lang"] = lang

    # ── GREETING / START ──────────────────────────────────────────
    if state["step"] == "start" or msg in ["hi", "hello", "hey", "helo", "muli otya", "osibye", "start", "menu"]:
        state["step"] = "main_menu"
        conversation_states[phone] = state
        welcome = get_menu("welcome", lang)
        send_message(phone, welcome)
        return

    # ── MAIN MENU SELECTION ───────────────────────────────────────
    if state["step"] == "main_menu":

        if msg in ["1", "services", "obuweereza"]:
            state["step"] = "services"
            send_message(phone, get_menu("services", lang))

        elif msg in ["2", "quote", "price", "omuwendo", "get quote"]:
            state["step"] = "quote_name"
            send_message(phone, get_menu("ask_name", lang))

        elif msg in ["3", "portfolio", "work", "ebikolebwa"]:
            send_message(phone, get_menu("portfolio", lang))
            state["step"] = "main_menu"
            send_message(phone, get_menu("return_menu", lang))

        elif msg in ["4", "contact", "talk", "yunga"]:
            send_message(phone, get_menu("contact", lang))
            state["step"] = "main_menu"
            send_message(phone, get_menu("return_menu", lang))

        elif msg in ["5", "book", "appointment", "entebbe"]:
            state["step"] = "book_name"
            send_message(phone, get_menu("ask_name", lang))

        else:
            # Use Claude AI for any free-text question
            ai_reply = get_ai_response(message_text, lang)
            send_message(phone, ai_reply)
            send_message(phone, get_menu("return_menu", lang))

        conversation_states[phone] = state
        return

    # ── QUOTE FLOW ────────────────────────────────────────────────
    if state["step"] == "quote_name":
        state["data"]["name"] = message_text
        state["step"] = "quote_project"
        send_message(phone, get_menu("ask_project", lang))
        conversation_states[phone] = state
        return

    if state["step"] == "quote_project":
        state["data"]["project"] = message_text
        state["step"] = "quote_budget"
        send_message(phone, get_menu("ask_budget", lang))
        conversation_states[phone] = state
        return

    if state["step"] == "quote_budget":
        state["data"]["budget"] = message_text
        state["step"] = "quote_email"
        send_message(phone, get_menu("ask_email", lang))
        conversation_states[phone] = state
        return

    if state["step"] == "quote_email":
        state["data"]["email"] = message_text
        state["data"]["phone"] = phone
        state["data"]["type"] = "quote"

        # Save lead to file
        save_lead(state["data"])

        # Send confirmation
        name = state["data"].get("name", "")
        send_message(phone, get_menu("quote_confirm", lang).replace("{name}", name))

        # Reset state
        state["step"] = "main_menu"
        state["data"] = {}
        conversation_states[phone] = state
        return

    # ── BOOKING FLOW ──────────────────────────────────────────────
    if state["step"] == "book_name":
        state["data"]["name"] = message_text
        state["step"] = "book_date"
        send_message(phone, get_menu("ask_date", lang))
        conversation_states[phone] = state
        return

    if state["step"] == "book_date":
        state["data"]["date"] = message_text
        state["step"] = "book_topic"
        send_message(phone, get_menu("ask_topic", lang))
        conversation_states[phone] = state
        return

    if state["step"] == "book_topic":
        state["data"]["topic"] = message_text
        state["data"]["phone"] = phone
        state["data"]["type"] = "booking"

        # Save booking
        save_lead(state["data"])

        name = state["data"].get("name", "")
        date = state["data"].get("date", "")
        send_message(phone, get_menu("book_confirm", lang).replace("{name}", name).replace("{date}", date))

        # Reset
        state["step"] = "main_menu"
        state["data"] = {}
        conversation_states[phone] = state
        return

    # ── FALLBACK — Claude AI handles anything else ────────────────
    ai_reply = get_ai_response(message_text, lang)
    send_message(phone, ai_reply)
    send_message(phone, get_menu("return_menu", lang))


# ── WEBHOOK ENDPOINTS ─────────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Receive and process incoming WhatsApp messages"""
    data = request.get_json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message = value["messages"][0]
            phone = message["from"]

            # Handle text messages
            if message["type"] == "text":
                text = message["text"]["body"]
                handle_message(phone, text)

            # Handle interactive list replies
            elif message["type"] == "interactive":
                reply = message["interactive"]
                if reply["type"] == "list_reply":
                    text = reply["list_reply"]["title"]
                    handle_message(phone, text)
                elif reply["type"] == "button_reply":
                    text = reply["button_reply"]["title"]
                    handle_message(phone, text)

    except (KeyError, IndexError) as e:
        print(f"Error processing message: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/leads", methods=["GET"])
def view_leads():
    """Simple endpoint to view all captured leads"""
    try:
        with open("leads.json", "r") as f:
            leads = json.load(f)
        return jsonify(leads), 200
    except FileNotFoundError:
        return jsonify([]), 200


@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is Running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
