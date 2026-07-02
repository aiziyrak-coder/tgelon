# Taxi E'lon Bot — Professional Edition

Shaharlararo taxi e'lonlarini Telegram guruh va kanallarga avtomatik yuborish.

## Imkoniyatlar

- Ko'p foydalanuvchili tizim
- Taxi shablon (yo'nalish, vaqt, narx, telefon + Qo'ng'iroq tugmasi)
- Erkin matn e'lonlari
- Guruh/kanal boshqaruvi + admin holatini yangilash
- Jamlanmalar (chatlarni guruhlash)
- Avtomatik yuborish rejasi (preset + maxsus interval)
- Yuborish tarixi (loglar)
- Admin panel (statistika, bloklash, broadcast, loglar)
- Toshkent vaqti, flood control, xavfsizlik tekshiruvlari

## O'rnatish

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env da BOT_TOKEN va ADMIN_IDS ni to'ldiring
python run.py
```

## Docker

```bash
docker compose up -d --build
```

## Zaxira

```bash
python scripts/backup_db.py
```

## Tekshiruv

```bash
python scripts/health_check.py
```

## Muhim

- Bot tokenini hech kimga bermang
- Guruh/kanalda bot **admin** bo'lishi kerak
- Vaqt: Asia/Tashkent (UTC+5)
