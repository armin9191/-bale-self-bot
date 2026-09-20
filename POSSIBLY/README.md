# POSSIBLY

**Group Management + Fun + Games Bot** برای پیام‌رسان بله (Bale).

فقط در گروه `@possibly` (ID: `4739068741`) فعال است.

## ویژگی‌ها

- محدودیت سخت گروهی
- مدیریت: `/ban` `/kick` `/unban` (با User ID یا Reply)
- سیستم یادگیری (یاد بگیر / فراموش کن / لیست یادگیری)
- اکو
- نجوا (Whisper) با دکمه مشاهده فقط برای گیرنده
- آمار روزانه واقعی از PostgreSQL
- بازی دوز (Tic-Tac-Toe) با اینلاین کیبورد
- موتور مافیا و جرأت‌حقیقت (قابل گسترش)
- منوی خصوصی با نقش‌ها
- بکاپ PostgreSQL فقط برای Owner
- Rate limit و لاگ امن

## تکنولوژی

- Python 3.12+
- `python-bale-bot==2.5.0`
- PostgreSQL + `asyncpg`
- Pillow / arabic-reshaper / python-bidi (برای قابلیت GIF آینده)
- Railway Worker

## نصب محلی

```bash
cd POSSIBLY
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Secrets را **هرگز** در Git commit نکنید.

```bash
export BOT_TOKEN="your_token_from_BotFather"
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export OWNER_ID=1967315238
export POSSIBLY_ADMIN_ID=1967315238
export ALLOWED_GROUP_ID=4739068741
```

یا مقادیر را موقتاً در `config.py` برای تست محلی بگذارید (قبل از push پاک کنید).

### اجرا

```bash
python main.py
```

لاگ مورد انتظار:

```
[INFO] POSSIBLY starting
[INFO] Connected to PostgreSQL
[INFO] Handler registry loaded
[INFO] POSSIBLY initialized
[INFO] Bot is running
```

## Railway

1. پروژه را به Railway وصل کنید.
2. PostgreSQL plugin اضافه کنید.
3. Variables:
   - `BOT_TOKEN`
   - `DATABASE_URL` (از پلاگین PostgreSQL)
   - `OWNER_ID` / `POSSIBLY_ADMIN_ID` / `ALLOWED_GROUP_ID` (اختیاری)
4. `Procfile`:
   ```
   worker: python main.py
   ```
5. `runtime.txt`: `python-3.12`

## ساختار

```
POSSIBLY/
├── main.py
├── config.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── bot/
│   ├── handlers/          # dispatcher مرکزی + ماژول‌ها
│   ├── games/             # موتورهای بازی بدون وابستگی به Bale
│   ├── keyboards.py
│   ├── messages.py
│   └── permissions.py
└── database/
    ├── postgres.py
    └── repositories.py
```

## محدودیت‌های واقعی API بله

- لیست کامل اعضای گروه وجود ندارد → فقط کاربران مشاهده‌شده توسط ربات ذخیره می‌شوند.
- Kick خالص وجود ندارد → ban سپس unban استفاده می‌شود.
- دسترسی‌های پیشرفته promote/restrict محدودتر از تلگرام است.
- نجوا در گروه محتوا را نشان نمی‌دهد؛ فقط گیرنده از طریق دکمه می‌بیند (یا پیام خصوصی در صورت امکان).

## امنیت

- Token و DATABASE_URL فقط از Environment Variables خوانده می‌شوند.
- User ID معیار اصلی permission است (نه username).
- Owner/Admin محافظت‌شده در برابر ban/kick.
- بکاپ فقط برای `POSSIBLY_ADMIN_ID` ارسال می‌شود.
- هیچ secret در لاگ چاپ نمی‌شود.

## دستورات گروه

| دستور | توضیح |
|-------|--------|
| `امار` / `آمار` | آمار امروز |
| `اکو متن` | اکو + حذف پیام اصلی در صورت داشتن permission |
| `یاد بگیر trigger response` | یادگیری (Admin) |
| `فراموش کن trigger` | حذف یادگیری |
| `لیست یادگیری` | لیست triggerها |
| Reply + `نجوا متن` | نجوا خصوصی |
| `دوز` | شروع بازی دوز |
| `/ban USER_ID` یا Reply+/ban | بن |
| `/kick ...` | کیک |
| `/unban ...` | آنبن |

Private: `/start` یا `منو` → منوی اینلاین

Owner private: `بکاپ`

## Production Checklist

- [ ] BOT_TOKEN از BotFather جدید گرفته شده (توکن قبلی revoke)
- [ ] DATABASE_URL فقط در Railway Variables
- [ ] ربات در گروه Admin است و can_delete_messages / can_restrict_members دارد
- [ ] Group ID درست است
- [ ] Worker روی Railway در حال اجراست
- [ ] لاگ‌ها بدون secret هستند

## License

Private project for @possibly group.
