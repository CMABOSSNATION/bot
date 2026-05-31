"""
Lead and booking storage
Saves all captured leads and bookings to a JSON file
"""

import json
import os
from datetime import datetime


LEADS_FILE = "leads.json"


def save_lead(data):
    """Save a lead or booking to the JSON file"""
    try:
        # Load existing leads
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r") as f:
                leads = json.load(f)
        else:
            leads = []

        # Add timestamp
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["status"] = "new"

        leads.append(data)

        # Save back to file
        with open(LEADS_FILE, "w") as f:
            json.dump(leads, f, indent=2)

        print(f"Lead saved: {data.get('name')} - {data.get('type')}")

        # Also send notification to your WhatsApp
        notify_owner(data)

    except Exception as e:
        print(f"Error saving lead: {e}")


def notify_owner(data):
    """Send notification to business owner WhatsApp"""
    import requests
    from dotenv import load_dotenv
    load_dotenv()

    owner_phone = os.getenv("OWNER_PHONE")
    whatsapp_token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("PHONE_NUMBER_ID")

    if not all([owner_phone, whatsapp_token, phone_number_id]):
        return

    lead_type = data.get("type", "inquiry")

    if lead_type == "quote":
        message = (
            f"🔔 *New Quote Request!*\n\n"
            f"👤 Name: {data.get('name')}\n"
            f"📱 Phone: {data.get('phone')}\n"
            f"📧 Email: {data.get('email')}\n"
            f"💼 Project: {data.get('project')}\n"
            f"💰 Budget: {data.get('budget')}\n"
            f"🕐 Time: {data.get('timestamp')}"
        )
    elif lead_type == "booking":
        message = (
            f"📅 *New Consultation Booking!*\n\n"
            f"👤 Name: {data.get('name')}\n"
            f"📱 Phone: {data.get('phone')}\n"
            f"📆 Date: {data.get('date')}\n"
            f"💬 Topic: {data.get('topic')}\n"
            f"🕐 Time: {data.get('timestamp')}"
        )
    else:
        message = f"🔔 New inquiry from {data.get('phone')}"

    try:
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {whatsapp_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": owner_phone,
            "type": "text",
            "text": {"body": message}
        }
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"Owner notification error: {e}")


def get_all_leads():
    """Return all saved leads"""
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    return []


def get_leads_today():
    """Return leads captured today"""
    today = datetime.now().strftime("%Y-%m-%d")
    all_leads = get_all_leads()
    return [l for l in all_leads if l.get("timestamp", "").startswith(today)]
