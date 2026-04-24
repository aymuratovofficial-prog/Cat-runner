import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

TOKEN = "8530524207:AAH24HlJHuAFE9j_Xhew34wDkFcc5_EryME"

CHANNELS = ["@nukus_jumis_bar", "@vipmusic_2026"]
ADMIN_IDS = [100272577916, 1002880001827]

MIN_WITHDRAW = 10000

# DATABASE
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# TABLE CREATE + FIX
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer INTEGER,
    balance INTEGER DEFAULT 0,
    invited INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    card TEXT,
    status TEXT
)
""")

# 🔥 AGAR eski DB bo‘lsa ustun qo‘shadi
try:
    cursor.execute("ALTER TABLE users ADD COLUMN invited INTEGER DEFAULT 0")
except:
    pass

conn.commit()

# USER ADD
def add_user(user_id, referrer=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:

        if referrer == user_id:
            referrer = None

        cursor.execute(
            "INSERT INTO users (user_id, referrer, balance, invited) VALUES (?, ?, 0, 0)",
            (user_id, referrer)
        )
        conn.commit()

        if referrer:
            cursor.execute("SELECT invited FROM users WHERE user_id=?", (referrer,))
            row = cursor.fetchone()
            invited = row[0] if row else 0

            cursor.execute(
                "UPDATE users SET balance = balance + 1000, invited = invited + 1 WHERE user_id=?",
                (referrer,)
            )
            conn.commit()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    referrer = int(args[0]) if args else None
    add_user(user.id, referrer)

    keyboard = [
        [InlineKeyboardButton("🔔 Kanal 1", url="https://t.me/nukus_jumis_bar")],
        [InlineKeyboardButton("🔔 Kanal 2", url="https://t.me/vipmusic_2026")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
    ]

    await update.message.reply_text(
        "📢 Barcha kanallarga obuna bo‘ling!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# CHECK
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    for ch in CHANNELS:
        member = await context.bot.get_chat_member(ch, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await query.answer("❌ Barcha kanallarga obuna bo‘ling!", show_alert=True)
            return

    menu = [
        ["👥 Referallar"],
        ["💰 Balans", "💳 Pul chiqarish"],
    ]

    await query.message.reply_text(
        "✅ Tasdiqlandi",
        reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True)
    )

# BALANS
async def balans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    bal = row[0] if row else 0

    await update.message.reply_text(f"💰 Balans: {bal} so'm")

# REFERAL
async def referal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT invited FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    count = row[0] if row else 0

    link = f"https://t.me/{context.bot.username}?start={user_id}"

    await update.message.reply_text(f"👥 Referallar: {count}\n🔗 Link:\n{link}")

# WITHDRAW
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    bal = row[0] if row else 0

    if bal < MIN_WITHDRAW:
        await update.message.reply_text(f"❌ Minimum {MIN_WITHDRAW} so'm kerak")
        return

    await update.message.reply_text("💳 Karta raqamingizni yuboring:")
    context.user_data["withdraw"] = True

# TEXT HANDLER
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # withdraw step
    if context.user_data.get("withdraw"):
        context.user_data["withdraw"] = False

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        bal = row[0] if row else 0

        cursor.execute(
            "INSERT INTO withdraws (user_id, amount, card, status) VALUES (?, ?, ?, ?)",
            (user_id, bal, text, "pending")
        )
        conn.commit()

        cursor.execute("UPDATE users SET balance=0 WHERE user_id=?", (user_id,))
        conn.commit()

        for admin in ADMIN_IDS:
            await context.bot.send_message(
                admin,
                f"💸 So‘rov\nUser: {user_id}\nSumma: {bal}\nKarta: {text}"
            )

        await update.message.reply_text("✅ So‘rov yuborildi")
        return

    # menu
    if text == "💰 Balans":
        await balans(update, context)
    elif text == "👥 Referallar":
        await referal(update, context)
    elif text == "💳 Pul chiqarish":
        await withdraw(update, context)

# ADMIN
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in ADMIN_IDS:
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM withdraws WHERE status='pending'")
        req = cursor.fetchone()[0]

        await update.message.reply_text(f"👨‍💻 Users: {users}\n💸 So‘rovlar: {req}")

# RUN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(check, pattern="check"))
app.add_handler(MessageHandler(filters.TEXT, handle_text))

app.run_polling()
