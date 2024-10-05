from flask import Blueprint, request
from telegram.ext import Updater
from telegram import Update

webhook_bp = Blueprint("webhook", __name__)

TOKEN = '7075699303:AAF-qX4Vgn1xto2NRc9aR6suJ3OwUAOE9-M'
updater = Updater(token = TOKEN, use_context=True)
dp = updater.dispatcher

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, updater.bot)
        dp.process_update(update)
        return 'ok'
    except Exception as e:
        print("Error in webhook:", e)
        return 'error'
