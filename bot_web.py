# bot_web.py
import os, random, json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# === Config ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # impostalo su Render
PUBLIC_URL = os.getenv("PUBLIC_URL")     # es. https://aeolusdonatus-bot.onrender.com
PORT = int(os.getenv("PORT", "10000"))   # Render imposta PORT, default OK

if not TOKEN or ":" not in TOKEN:
    raise RuntimeError("Manca TELEGRAM_BOT_TOKEN (token BotFather).")

if not PUBLIC_URL or not PUBLIC_URL.startswith("http"):
    raise RuntimeError(
        "Manca PUBLIC_URL. Imposta PUBLIC_URL nelle env di Render con l'URL del servizio, "
        "es. https://aeolusdonatus-bot.onrender.com"
    )

# === Carica questions.json ===
DATA_PATH = Path(__file__).with_name("questions.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    QUESTION_BANK = json.load(f)

ALL_TOPICS = list(QUESTION_BANK.keys())

# === Stato utenti in RAM ===
user_state: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
    "topic": None, "score": 0, "asked": 0, "current_q": None
})

def make_keyboard(options):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🅰 {options[0]}", callback_data="0")],
        [InlineKeyboardButton(f"🅱 {options[1]}", callback_data="1")],
        [InlineKeyboardButton(f"🅲️ {options[2]}", callback_data="2")],
        [InlineKeyboardButton(f"🅳️ {options[3]}", callback_data="3")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono AeliusDonatus_bot👨‍🏫​📜\n"
        "Scrivi un argomento (es. 'ablativo assoluto') oppure usa /topics.\n"
        "Poi invia /quiz. Comandi: /help /score /stop"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi:\n"
        "/topics – argomenti\n"
        "/quiz – nuova domanda\n"
        "/score – punteggio\n"
        "/stop – termina sessione"
    )

async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Argomenti:\n- " + "\n- ".join(ALL_TOPICS))

def best_match_topic(text: str) -> str | None:
    s = text.lower()
    for t in ALL_TOPICS:
        if t in s:
            return t
    return None

async def set_topic_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    topic = best_match_topic(update.message.text)
    if topic is None:
        await update.message.reply_text("Argomento non riconosciuto. Usa /topics.")
        return
    user_state[uid]["topic"] = topic
    await update.message.reply_text(f"Argomento impostato: *{topic}*.\nUsa /quiz per iniziare.", parse_mode="Markdown")

def pick_question(topic: str):
    q = random.choice(QUESTION_BANK[topic])
    idxs = list(range(4))
    random.shuffle(idxs)
    opts = [q["opts"][i] for i in idxs]
    ans_new_index = idxs.index(q["ans"])
    return {"q": q["q"], "opts": opts, "ans": ans_new_index, "spiega": q.get("spiega", "")}

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    topic = user_state[uid]["topic"]
    if not topic:
        await update.message.reply_text("Prima scegli un argomento (/topics o scrivi il nome).")
        return
    q = pick_question(topic)
    user_state[uid]["current_q"] = q
    user_state[uid]["asked"] += 1
    await update.message.reply_text(q["q"], reply_markup=make_keyboard(q["opts"]))

async def answer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    st = user_state[uid]
    if not st["current_q"]:
        await query.edit_message_text("Nessuna domanda attiva. Usa /quiz per iniziare.")
        return
    chosen = int(query.data)
    q = st["current_q"]
    correct = (chosen == q["ans"])
    if correct:
        st["score"] += 1
        msg = f"✅ Corretto!\n{q['spiega']}\n\nPunteggio: {st['score']}/{st['asked']}"
    else:
        letters = ["A","B","C","D"]
        msg = f"❌ Errato.\nSoluzione: {letters[q['ans']]} – {q['opts'][q['ans']]}\n{q['spiega']}\n\nPunteggio: {st['score']}/{st['asked']}"
    st["current_q"] = None
    await query.edit_message_text(msg)
    await query.message.reply_text("Vuoi un’altra domanda? /quiz • Cambia argomento: /topics")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    st = user_state[uid]
    await update.message.reply_text(f"Punteggio: {st['score']}/{st['asked']}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_state.pop(uid, None)
    await update.message.reply_text("Sessione terminata. A presto!")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(answer_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_topic_from_text))

    # Config webhook
    # Path "segreto" per sicurezza (non deve essere guessabile)
    secret_path = f"/{TOKEN.split(':')[0]}-{TOKEN.split(':')[1][:8]}"
    webhook_url = f"{PUBLIC_URL}{secret_path}"

    # Avvia server webhook (libreria apre un server aiohttp interno)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=secret_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
