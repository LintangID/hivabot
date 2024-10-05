from flask import Blueprint
from .webhooks import dp
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
import logging
from . import db, app
from .diagnosa import *
from .models import UserTelegram, Stadium, Gejala, Term, RiwayatDiagnosa, ProsesDiagnosa

message_handler = Blueprint('message_handler', __name__)


logging.basicConfig(level=logging.INFO)

# States untuk stateful conversation
ENTER_NEW_NAME, START_DIAGNOSA, FORWARD_CHAINING, END, CONFIRMATION = range(5)

# Fungsi untuk menangani perintah /start
def start(update, context):
    if context.user_data.get('conversation_active') is None:
        try:
            id_user = update.message.from_user.id 
            name = update.message.from_user.first_name
            with app.app_context():
                user_exist = UserTelegram.query.filter_by(id_user_telegram=id_user).first()
                if user_exist:
                    text = "Selamat datang kembali "+ user_exist.name +"!. Ketik /info untuk melihat daftar perintah."
                    update.message.reply_text(text)
                else:
                    new_user_telegram = UserTelegram(id_user_telegram = id_user, name = name)
                    db.session.add(new_user_telegram)
                    db.session.commit()
                    text = "Halo "+ name +"! Saya adalah hivabot. Ketik /info untuk melihat daftar perintah dan lebih mengenal hivabot."
                    update.message.reply_text(text)
        except Exception as e:
            logging.error("Error: %s", str(e))

# Fungsi untuk menangani perintah /info
def info(update, context):
    if context.user_data.get('conversation_active') is None:
        text = 'HIVABot (HIV Aware Bot) adalah bot yang menggunakan basis pengetahuan dari pakar/ahli untuk membantu anda melakukan diagnosa penyakit HIV berdasarkan keyakinan anda terhadap gejala - gejala yang anda alami.\n\n\nBerikut adalah daftar perintah hivabot:\n/info - Menampilkan informasi\n/ubah_nama - Menghubah nama\n/diagnosa - Memulai diagnosa'
        update.message.reply_text(text)

# Fungsi untuk menangani pesan yang diterima
def text_handler(update, context):
    if context.user_data.get('conversation_active') is None:
        # text = update.message.text
        text = "Silahkan ketik /diagnosa untuk melakukan diagnosa dan /info untuk melihat informasi bot"
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    
# Callback function untuk perintah /update
def update_name(update: Update, context: CallbackContext) -> int:
    if context.user_data.get('conversation_active') is None:
        update.message.reply_text(f"Silakan kirimkan nama baru:")
        context.user_data['conversation_active'] = True
        return ENTER_NEW_NAME

# Callback function untuk menerima nama baru
def get_name(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    new_name = update.message.text
    with app.app_context():
            user = UserTelegram.query.filter_by(id_user_telegram=user_id).first()
            if user:
                user.name = new_name
                db.session.commit()
                update.message.reply_text(f"Halo {new_name}! Nama kamu berhasil diubah")
            else: 
                update.message.reply_text("Nama kamu belum terdaftar")
    del context.user_data['conversation_active']
    return ConversationHandler.END

# Callback function untuk mengakhiri percakapan
def cancel_diagnosa(update: Update, context: CallbackContext):
    riwayat_id = context.user_data.get('riwayat_id')
    with app.app_context():
        riwayat = RiwayatDiagnosa.query.filter_by(id=riwayat_id).first()
        proses_diagnosa = ProsesDiagnosa.query.filter_by(riwayat_id=riwayat_id).all()
        db.session.delete(riwayat)
        if proses_diagnosa:
            for item in proses_diagnosa:
                db.session.delete(item)
        db.session.commit()
    text = "proses diagnosa dibatalkan."
    update.message.reply_text(text,reply_markup=ReplyKeyboardRemove())
    del context.user_data['conversation_active']
    return ConversationHandler.END

def diagnosa_start(update: Update, context: CallbackContext) -> int:
    if context.user_data.get('conversation_active') is None:
        context.user_data['conversation_active'] = True
        with app.app_context():
            user_telegram_id = update.message.from_user.id
            new_riwayat_diagnosa = RiwayatDiagnosa(user_telegram_id = user_telegram_id)
            db.session.add(new_riwayat_diagnosa)
            db.session.commit()
        riwayat = RiwayatDiagnosa.query.filter_by(user_telegram_id = user_telegram_id).order_by(RiwayatDiagnosa.tanggal.desc()).first()
        riwayat_id = riwayat.id
        context.user_data['riwayat_id'] = riwayat_id
        keyboard = [
            [KeyboardButton("Mulai")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        text = "Untuk proses diagnosa, tanggapi pertanyaan yang muncul sesuai tingkat keyakinan anda dengan menekan tombol TIDAK / KURANG YAKIN / SEDIKIT YAKIN / CUKUP YAKIN / YAKIN / SANGAT YAKIN. Tekan /cancel untuk membatalkan proses diagnosa."
        update.message.reply_text(text, reply_markup=reply_markup)
        return START_DIAGNOSA

def proses_diagnosa(update: Update, context: CallbackContext) -> int:
    if update.message.text == "Mulai":
        terms = Term.query.all()
        keyboard = [[KeyboardButton(term.term)] for term in terms]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        result = pertanyaan()
        text = result['pertanyaan']
        data = {'daftar_stadium':result['daftar_rule'],
                'daftar_gejala':result['daftar_gejala'],
                'gejala_terbanyak':result['gejala_terbanyak'],
                'kemunculan':result['kemunculan']   
        }
        context.user_data['data'] = data
        update.message.reply_text(text, reply_markup=reply_markup)
        return FORWARD_CHAINING

def forward_chaining(update: Update, context: CallbackContext) -> int:
    terms = Term.query.all()
    keyboard = [[KeyboardButton(term.term)] for term in terms]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    data = context.user_data.get('data')
    answer = update.message.text
    term = Term.query.filter_by(term=answer).first()
    nilai = term.nilai_cf
    if nilai is not None:
        riwayat_id = context.user_data.get('riwayat_id')
        gejala_id = data['gejala_terbanyak']
        with app.app_context():
            new_proses_diagnosa = ProsesDiagnosa(riwayat_id = riwayat_id, gejala_id=gejala_id, cf = nilai)
            db.session.add(new_proses_diagnosa)
            db.session.commit()
        result = forwardChaining(nilai,data)
        data_baru = {'daftar_stadium':result['daftar_stadium'],
                'daftar_gejala':result['daftar_gejala'],
                'gejala_terbanyak':result['gejala_terbanyak']
                }
        context.user_data['data'] = data_baru
        if result['gejala_terbanyak'] != 0:
            data_baru = {'daftar_stadium':result['daftar_stadium'],
                'daftar_gejala':result['daftar_gejala'],
                'gejala_terbanyak':result['gejala_terbanyak'],
                'kemunculan':result['kemunculan'],
                }
            context.user_data['data'] = data_baru
            text = result['pertanyaan']
            update.message.reply_text(text, reply_markup=reply_markup)
            return FORWARD_CHAINING
        else:
            if len(result['daftar_stadium']) == 0:
                riwayat = RiwayatDiagnosa.query.filter_by(id=riwayat_id).first()
                proses_diagnosa = ProsesDiagnosa.query.filter_by(riwayat_id=riwayat_id).all()
                db.session.delete(riwayat)
                if proses_diagnosa:
                    for item in proses_diagnosa:
                        db.session.delete(item)
                db.session.commit()
                text="Anda tidak memiliki kemungkinan terinfeksi HIV"
                update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
                del context.user_data['conversation_active']
                return ConversationHandler.END
            else:
                text = "Diagnosa selesai, tekan tombol SELESAI untuk melihat hasil atau /cancel untuk membatalkan diagnosa"
                keyboard = [
                    [InlineKeyboardButton("Selesai",callback_data="button_end")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(text, reply_markup=reply_markup)
                return END

def diagnosa_end(update: Update, context: CallbackContext) -> int:
    update.effective_message.edit_reply_markup(None)
    query = update.callback_query
    query.answer()
    data = context.user_data.get('data')
    riwayat_id = context.user_data.get('riwayat_id')
    diagnosa = certaintyFactor(data['daftar_stadium'],riwayat_id)
    text = diagnosa
    query.edit_message_text(text)
    keyboard = [
            [KeyboardButton("Ya",request_contact=True)],
            [KeyboardButton("Tidak")],
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    text = "Apakah anda berkenan membagikan nomor telepon untuk dihubungi dan penangan lebih lanjut?"
    query.message.reply_text(text,reply_markup=reply_markup)
    with app.app_context():
        proses_diagnosa = ProsesDiagnosa.query.filter_by(riwayat_id=riwayat_id).all()
        if proses_diagnosa:
            for item in proses_diagnosa:
                db.session.delete(item)
        db.session.commit()
    return CONFIRMATION

def confirmation(update: Update, context: CallbackContext) -> int:
    contact = update.message.contact
    responses = update.message.text
    if contact:
        phone_number = contact.phone_number
        user_id = update.message.from_user.id
        user = UserTelegram.query.filter_by(id_user_telegram=user_id).first()
        if user:
            user.phone_number = phone_number
            db.session.commit()
        update.message.reply_text(f"Terima kasih, kami akan menghubungi Anda di nomor {phone_number}.",reply_markup=ReplyKeyboardRemove())
    elif responses.lower() == "tidak":
        update.message.reply_text("Terima kasih, nomor anda tidak akan disimpan dalam bot.",reply_markup=ReplyKeyboardRemove())
        
    del context.user_data['conversation_active']
    return ConversationHandler.END

# Stateful conversation handler
conv_handler_nama = ConversationHandler(

    entry_points=[CommandHandler('ubah_nama', update_name)],
    states={
        ENTER_NEW_NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)]
    },
    fallbacks=[],
    allow_reentry=False
)

conv_handler_diagnosa = ConversationHandler(
    entry_points=[CommandHandler('diagnosa', diagnosa_start)],
    states={
        START_DIAGNOSA: [MessageHandler(Filters.text & ~Filters.command, proses_diagnosa)],
        FORWARD_CHAINING: [MessageHandler(Filters.text & ~Filters.command, forward_chaining)],
        END: [CallbackQueryHandler(diagnosa_end)],
        CONFIRMATION: [
            MessageHandler(Filters.contact, confirmation),
            MessageHandler(Filters.text & ~Filters.command, confirmation),
            ]
    },
    fallbacks=[CommandHandler('cancel', cancel_diagnosa)],
    allow_reentry=False
)

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("info", info))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
dp.add_handler(conv_handler_nama,group=1)
dp.add_handler(conv_handler_diagnosa,group=1)

