# Asosiy menyu tugmalari
BTN_NEW_ANN = "🚀 E'lon yaratish"
BTN_DISTRIBUTE = "📡 E'lon tarqatish"
BTN_MY_ANNS = "📋 Mening e'lonlarim"
BTN_GROUPS = "👥 Guruhlarim"
BTN_COLLECTIONS = "📁 Jamlanmalar"
BTN_AUTO = "📡 E'lon tarqatish"  # eski tugma mosligi
BTN_SEND = "📡 E'lon tarqatish"  # eski tugma mosligi
BTN_LOGS = "📜 Yuborish tarixi"
BTN_HELP = "ℹ️ Yordam va ko'rsatma"
BTN_ADMIN = "🛡 Admin panel"
BTN_HOME = "🏠 Bosh menyu"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP = "⏭ Keyingisi"
BTN_SHARE_PHONE = "📱 Telefon raqamni yuborish"

DEFAULT_COLLECTION = "Asosiy guruhlar"

# --- Ro'yxatdan o'tish ---

REG_WELCOME = """
🌟 <b>Xush kelibsiz!</b>

Men <b>TGTaxi</b> — shaharlararo taxi e'lonlaringizni Telegram guruh va kanallarga <b>avtomatik yuboradigan</b> yordamchingizman.

<b>Ro'yxatdan o'tish 2 qadam:</b>
1️⃣ Telefon raqamingizni <b>tugma orqali</b> yuborasiz
2️⃣ Ism va familiyangizni yozasiz

<i>Ma'lumotlaringiz faqat bot ichida saqlanadi va hech kimga berilmaydi.</i>
"""

REG_STEP_PHONE = """
📱 <b>1-qadam / 2</b>

Quyidagi <b>ko'k tugmani</b> bosing — telefon raqamingiz avtomatik yuboriladi.

<i>⚠️ Faqat o'z raqamingizni yuboring. Boshqa raqam qabul qilinmaydi.</i>
"""

REG_STEP_NAME = """
✍️ <b>2-qadam / 2</b>

Endi <b>ism va familiyangizni</b> yozing.

<i>Masalan: Aliyev Vali</i>
"""

REG_DONE = """
🎉 <b>Tabriklaymiz, {name}!</b>

Ro'yxatdan muvaffaqiyatli o'tdingiz.
Telefon: <b>{phone}</b>

Endi taxi e'lonlaringizni yaratishingiz va guruhlarga yuborishingiz mumkin! 🚀
"""

REG_REQUIRED = """
🔐 <b>Avval ro'yxatdan o'ting</b>

Botdan foydalanish uchun telefon raqamingiz va ismingiz kerak.
Bu bir martalik va 1 daqiqadan kam vaqt oladi.

/start bosing va ro'yxatdan o'ting 👇
"""

REG_WRONG_PHONE = "❌ Faqat <b>o'z telefon raqamingizni</b> tugma orqali yuboring.\n\nMatn yozmang — pastdagi ko'k tugmani bosing."
REG_WRONG_NAME = "❌ Ism-familiya kamida 2 ta so'z bo'lishi kerak.\n\n<i>Masalan: Karimov Sardor</i>"

# --- Asosiy ekranlar ---

WELCOME = """
👋 Salom, <b>{name}</b>!

🚖 Men sizning taxi e'lonlaringizni guruh va kanallarga <b>avtomatik yuboraman</b>.

{status}

<b>Tez boshlash:</b>
1️⃣ «🚀 E'lon yaratish» — post yarating (rasm+matn)
2️⃣ Guruhga botni <b>admin</b> qiling — <b>siz ham admin</b> bo'ling
3️⃣ «📡 E'lon tarqatish» — e'lon, jamlanma, vaqt tanlang

💡 <i>Batafsil: «ℹ️ Yordam va ko'rsatma»</i>
"""

HELP = """
<b>📖 To'liq qo'llanma</b>

<b>1. E'lon yaratish</b> 🚀
«E'lon yaratish» tugmasini bosing.
• <b>Taxi shablon</b> — yo'nalish, vaqt, narx, telefon
• <b>Erkin matn</b> — o'zingiz yozasiz
• <b>Rasm + matn</b> — rasm bilan e'lon

<b>2. Guruhga qo'shish</b> 👥
• Guruhga qo'shing: t.me/taxitgbot?startgroup=true
• Botni <b>ADMIN</b> qiling
• «Xabar yuborish» huquqini bering
✅ Guruh avtomatik ro'yxatga tushadi!

<b>3. Jamlanmalar</b> 📁
Guruhlarni to'plamlarga ajrating.
«Asosiy guruhlar» avtomatik to'ldiriladi.

<b>4. E'lon tarqatish</b> 📡
• Faol e'lonni tanlang
• Jamlanmani tanlang (guruhlar to'plami)
• Vaqt: 1, 2, 5, 10 yoki 15 daqiqa — «Boshlash»
• <b>Muhim:</b> har guruhda siz ham bot ham admin bo'lishingiz kerak

<b>5. E'lon egasi</b>
Har bir postda e'lon egasining ismi va telefoni ko'rinadi.

<b>❓ Muammo bo'lsa:</b>
• Bot admin emasmi? → Admin qiling
• E'lon ketmayaptimi? → Guruhlarim dan tekshiring
• /start — boshidan boshlash
"""

# Bo'lim tushuntirishlari
HINT_NEW_ANN = (
    "🚀 <b>E'lon yaratish</b>\n\n"
    "Qanday e'lon kerak? Tanlang:\n"
    "• <b>Taxi</b> — bot savollar beradi, tayyor shablon yasaydi\n"
    "• <b>Erkin matn</b> — o'zingiz yozasiz\n"
    "• <b>Rasm + matn</b> — rasm bilan chiroyli e'lon"
)

HINT_SEND = (
    "📤 <b>Hozir yuborish</b>\n\n"
    "E'lonni <b>darhol</b> barcha tayyor guruhlarga yuboradi.\n"
    "Avval e'lon va kamida 1 ta admin guruh bo'lishi kerak."
)

HINT_MY_ANNS = (
    "📋 <b>Mening e'lonlarim</b>\n\n"
    "Barcha e'lonlaringiz shu yerda.\n"
    "Tanlab tahrirlash, yoqish/o'chirish yoki o'chirish mumkin."
)

HINT_DISTRIBUTE = (
    "📡 <b>E'lon tarqatish</b>\n\n"
    "<b>3 qadam:</b>\n"
    "1️⃣ Faol e'lonni tanlang\n"
    "2️⃣ Jamlanmani tanlang (guruhlar to'plami)\n"
    "3️⃣ Vaqt: 1, 2, 5, 10 yoki 15 daqiqa — «Boshlash»\n\n"
    "⚠️ <b>Muhim:</b> har bir guruhda <b>siz ham bot ham admin</b> bo'lishingiz kerak.\n"
    "Boshqa foydalanuvchilarning guruhlariga e'lon ketmaydi."
)

HINT_GROUPS = (
    "👥 <b>Guruhlarim</b>\n\n"
    "✅ — siz va bot admin (tarqatish mumkin)\n"
    "⚠️ — bot admin, siz emas\n"
    "❌ — bot admin emas"
)

HINT_AUTO = (
    "⏰ <b>Avtomatik yuborish</b>\n\n"
    "E'lonni belgilangan vaqtda avtomatik yuboradi.\n"
    "Masalan: har 30 daqiqada yoki har 1 soatda."
)

HINT_LOGS = (
    "📜 <b>Yuborish tarixi</b>\n\n"
    "Qaysi guruhga qachon yuborilganini ko'rasiz.\n"
    "✅ muvaffaqiyatli | ❌ xato"
)

HINT_COLLECTIONS = (
    "📁 <b>Jamlanmalar</b>\n\n"
    "Guruhlarni to'plamlarga ajrating.\n"
    "Masalan: «Toshkent guruhlari», «Samarqand guruhlari»."
)

STEP = "📍 <b>{n}-qadam / {total}</b>\n\n{text}"

FSM_HINT = (
    "✏️ <b>Jarayon davom etmoqda</b>\n\n"
    "Savolga javob yozing yoki «❌ Bekor qilish» bosing."
)

SEND_CONFIRM = "📤 <b>{name}</b> e'lonini <b>{count}</b> ta guruhga yuborilsinmi?"
