import json
from pathlib import Path
import asyncio, random, os
from collections import defaultdict
from typing import Dict, Any
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# Carica token dal file .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Carica question bank da file JSON
import json
from pathlib import Path

DATA_PATH = Path(__file__).with_name("questions.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    QUESTION_BANK = json.load(f)

ALL_TOPICS = list(QUESTION_BANK.keys())

# Stato utenti
user_state: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
    "topic": None, "score": 0, "asked": 0, "current_q": None
})

def make_keyboard(options):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"A️ {options[0]}", callback_data="0")],
        [InlineKeyboardButton(f"B️ {options[1]}", callback_data="1")],
        [InlineKeyboardButton(f"C️ {options[2]}", callback_data="2")],
        [InlineKeyboardButton(f"D️ {options[3]}", callback_data="3")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono AeliusDonatus_bot👨‍🏫​📜\n"
        "Scrivi un argomento (es. 'ablativo assoluto') oppure usa /topics per la lista.\n"
        "Poi invia /quiz per iniziare. Comandi: /help /score /stop"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi:\n"
        "/topics – mostra gli argomenti disponibili\n"
        "/quiz – avvia un quiz sull’argomento scelto\n"
        "/score – mostra il punteggio\n"
        "/stop – termina la sessione"
    )

async def topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "Argomenti disponibili:\n- " + "\n- ".join(ALL_TOPICS)
    await update.message.reply_text(txt)

def best_match_topic(user_text: str) -> str | None:
    s = user_text.lower()
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
    return {"q": q["q"], "opts": opts, "ans": ans_new_index, "spiega": q["spiega"]}

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    topic = user_state[uid]["topic"]
    if not topic:
        await update.message.reply_text("Prima scegli un argomento con /topics.")
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
        msg = (
            f"❌ Errato.\nSoluzione: {letters[q['ans']]} – {q['opts'][q['ans']]}\n"
            f"{q['spiega']}\n\nPunteggio: {st['score']}/{st['asked']}"
        )
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
    if not TOKEN or ":" not in TOKEN:
        raise RuntimeError("Il token non è stato caricato correttamente. Controlla il file .env.")

    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("topics", topics))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(answer_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_topic_from_text))

    # Avvio: run_polling gestisce da sé l’event loop
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
