# ⚔️ POSSIBLY

**POSSIBLY** یک ربات حرفه‌ای برای پیام‌رسان بله است که با تمرکز روی **مدیریت گروه، سرگرمی، بازی و ابزارهای مدیریتی** ساخته شده است.

این پروژه با Python 3.12+ و `python-bale-bot` طراحی شده و برای اجرای دائمی روی **Railway** و استفاده از **PostgreSQL** آماده است.

---

## ✨ قابلیت‌ها

### 🛡 مدیریت گروه

* `/ban`
* `/kick`
* `/unban`
* پشتیبانی از User ID
* پشتیبانی از Reply در دستورات مدیریت
* سیستم Permission
* Owner / Admin / Member
* ثبت عملیات مدیریتی
* جلوگیری از اجرای دستورات حساس توسط کاربران عادی

> عملیات مدیریتی فقط زمانی اجرا می‌شود که متد مربوطه توسط نسخه نصب‌شده‌ی کتابخانه Bale پشتیبانی شود.

---

## 🧠 سیستم یادگیری

مدیران گروه می‌توانند پاسخ‌های اختصاصی برای کلمات تعریف کنند.

### یادگیری

```text
یاد بگیر تست سلام
```

بعد از آن:

```text
تست
```

ربات:

```text
╭━━━━━━━━━━━━━━━╮
│ ⚔️ POSSIBLY
╰━━━━━━━━━━━━━━━╯

سلام
```

### حذف

```text
فراموش کن تست
```

### لیست

```text
لیست یادگیری
```

حداکثر تعداد Learning برای هر گروه:

```text
300
```

اطلاعات در PostgreSQL ذخیره می‌شوند.

---

# 📊 آمار

دستورات:

```text
امار
```

یا:

```text
آمار
```

آمار روزانه شامل:

* تعداد پیام‌ها
* GIF
* Voice
* عکس
* ویدیو
* سایر پیام‌ها
* فعال‌ترین کاربران

است.

آمار بر اساس تاریخ ذخیره می‌شود و Reset فیزیکی در نیمه‌شب انجام نمی‌شود.

به این ترتیب اطلاعات روزهای قبلی نیز قابل نگهداری هستند.

---

# 🎮 بازی‌ها

POSSIBLY دارای معماری جدا برای Game Engineها است.

## 🎭 Mafia

فازهای بازی:

```text
Lobby
↓
Players Join
↓
Game Start
↓
Night
↓
Role Actions
↓
Day
↓
Discussion
↓
Voting
↓
Execution
↓
Next Night
↓
Victory
```

نقش‌های پایه:

* Mafia
* Citizen
* Doctor
* Detective

State بازی قابلیت ذخیره در PostgreSQL را دارد تا Restart شدن سرویس باعث از بین رفتن State نشود.

---

# ❌⭕ Tic Tac Toe

دوز دو نفره با Board نه‌خانه‌ای:

```text
[ 1 ][ 2 ][ 3 ]

[ 4 ][ 5 ][ 6 ]

[ 7 ][ 8 ][ 9 ]
```

ویژگی‌ها:

* دو بازیکن
* مدیریت نوبت
* تشخیص برنده
* تشخیص Draw
* Game State جداگانه
* امکان اتصال به Inline/Callback Keyboard در لایه Bale

---

# 🎲 Truth or Dare

سیستم جرأت یا حقیقت شامل:

* ایجاد بازی
* Join
* Leave
* Start توسط Creator
* Remove Player
* End Game
* انتخاب جرأت
* انتخاب حقیقت
* Ready
* نوبت بازیکنان
* جلوگیری از تکرار مورد انتخاب‌شده

Question/Dare Pool از Game Logic جدا نگه داشته شده است.

---

# 💬 Whisper

سیستم نجوا برای ارسال محتوای خصوصی بین کاربران طراحی شده است.

فرمت:

```text
نجوا سلام
```

با Reply به پیام کاربر مقصد.

ساختار اطلاعات Whisper در PostgreSQL:

* sender
* receiver
* group
* content
* created_at
* expires_at
* viewed

### امنیت

برای Whisper باید موارد زیر رعایت شوند:

* Rate Limit
* Expiration
* جلوگیری از Spam
* ثبت Sender
* ثبت Receiver
* جلوگیری از نمایش عمومی محتوای خصوصی

نمایش خصوصی فقط در صورتی فعال می‌شود که نوع Interaction مورد نیاز توسط API واقعی Bale پشتیبانی شود.

POSSIBLY هیچ سیستم خصوصی جعلی یا ناامن را به عنوان قابلیت واقعی معرفی نمی‌کند.

---

# 🎞 GIF Caption

فرمت:

```text
گیف سلام
```

با Reply به GIF.

سیستم پردازش GIF برای:

* متن فارسی
* متن انگلیسی
* Unicode
* تغییر اندازه فونت
* شکستن خط
* قرارگیری متن نزدیک مرکز تصویر
* پردازش GIF متحرک

طراحی شده است.

کتابخانه‌های مورد استفاده:

```text
Pillow
arabic-reshaper
python-bidi
```

برای جلوگیری از مصرف بیش از حد RAM/CPU روی Railway باید محدودیت‌هایی برای:

* حجم فایل
* تعداد Frame
* ابعاد تصویر
* طول متن

اعمال شود.

---

# 👤 Private Panel

در Private Chat با ربات، پنل اختصاصی قابل استفاده است.

### Member

```text
👤 پروفایل من
📊 آمار من
🎮 بازی‌ها
ℹ️ درباره ربات
```

### Admin

```text
👥 اعضای گروه
🛡 مدیریت
📊 آمار گروه
🧠 یادگیری
⚙️ تنظیمات
🎮 بازی‌ها
📜 لاگ مدیریت
```

### Owner

Owner به امکانات مدیریتی بیشتری دسترسی دارد.

---

# 💾 PostgreSQL

POSSIBLY از PostgreSQL به عنوان Database اصلی استفاده می‌کند.

Database به صورت Connection Pool مدیریت می‌شود.

برای هر Query یک Connection جدید ساخته نمی‌شود.

---

## Database Tables

### users

اطلاعات کاربران:

```text
user_id
username
display_name
first_seen
last_seen
```

---

### group_members

اعضای شناخته‌شده گروه:

```text
group_id
user_id
role
joined_at
```

Roleها:

```text
owner
admin
member
```

---

### learned_words

سیستم Learning:

```text
id
group_id
trigger
response
created_by
created_at
```

---

### daily_stats

آمار روزانه:

```text
group_id
user_id
date
messages
gifs
voice
photos
videos
other
```

---

### games

اطلاعات Game:

```text
game_id
group_id
type
creator_id
status
state
created_at
updated_at
```

---

### game_players

بازیکنان:

```text
game_id
user_id
state
joined_at
```

---

### whispers

نجواها:

```text
id
group_id
sender_id
receiver_id
encrypted_or_private_content
created_at
expires_at
viewed
```

---

### moderation_logs

لاگ مدیریت:

```text
id
group_id
actor_id
target_id
action
details
created_at
```

---

# 🔐 Security

اطلاعات حساس نباید داخل GitHub قرار بگیرند.

موارد حساس:

```text
BOT_TOKEN
DATABASE_PASSWORD
DATABASE_URL
GitHub Token
API Keys
```

### توصیه

برای Repository عمومی هرگز Token واقعی قرار ندهید.

اگر Token به صورت عمومی منتشر شد:

1. Token را فوراً Revoke کنید.
2. Token جدید بسازید.
3. Password دیتابیس را تغییر دهید.
4. History مربوط به Secret را بررسی کنید.

---

# ⚙️ Configuration

در نسخه Local پروژه می‌توان Configuration را در:

```text
config.py
```

قرار داد.

نمونه:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    DATABASE_URL: str
    ALLOWED_GROUP_ID: int
    ALLOWED_GROUP_USERNAME: str
    OWNER_ID: int
    POSSIBLY_ADMIN_ID: int


settings = Settings(
    BOT_TOKEN="YOUR_BALE_BOT_TOKEN",

    DATABASE_URL="YOUR_POSTGRES_CONNECTION_STRING",

    ALLOWED_GROUP_ID=4739068741,

    ALLOWED_GROUP_USERNAME="@possibly",

    OWNER_ID=1967315238,

    POSSIBLY_ADMIN_ID=1967315238,
)
```

### نکته امنیتی مهم

اگر Repository عمومی است، این روش توصیه نمی‌شود.

برای Deployment عمومی بهتر است Secretها در Environment Variables یا Secret Manager قرار بگیرند.

---

# 🏠 گروه اصلی

گروه اصلی POSSIBLY:

```text
@possibly
```

Numeric Group ID نیز باید در Configuration مشخص شود.

نمونه:

```text
4739068741
```

Username به تنهایی مرز امنیتی محسوب نمی‌شود.

بنابراین Bot باید Numeric ID را بررسی کند.

اگر پیام از گروه دیگری دریافت شود، قابلیت‌های اصلی اجرا نمی‌شوند.

---

# 👑 Owner

Owner اصلی پروژه:

```text
1967315238
```

این ID برای Permissionهای سطح Owner استفاده می‌شود.

---

# 🛡 POSSIBLY Admin

Admin اختصاصی:

```text
1967315238
```

این کاربر می‌تواند قابلیت‌های مدیریتی اختصاصی مانند Backup را دریافت کند.

---

# 💾 PostgreSQL Backup

Admin اختصاصی می‌تواند در Private Chat با ربات بنویسد:

```text
بکاپ
```

سیستم Backup باید:

1. Permission کاربر را بررسی کند.
2. PostgreSQL را Backup بگیرد.
3. فایل Backup را تولید کند.
4. فایل را فقط برای Admin ارسال کند.

اطلاعات اتصال PostgreSQL نباید برای کاربر ارسال شوند.

Database Password و `DATABASE_URL` نیز نباید در پیام یا Log نمایش داده شوند.

---

# 🏗 Project Structure

ساختار پروژه:

```text
possibly/
│
├── main.py
├── config.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── README.md
├── .gitignore
│
├── bot/
│   ├── __init__.py
│   ├── permissions.py
│   ├── messages.py
│   ├── keyboards.py
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── backup.py
│   │   ├── learning.py
│   │   ├── stats.py
│   │   ├── echo.py
│   │   ├── whisper.py
│   │   ├── gif.py
│   │   └── games.py
│   │
│   └── games/
│       ├── __init__.py
│       ├── mafia.py
│       ├── tic_tac_toe.py
│       └── truth_dare.py
│
└── database/
    ├── __init__.py
    ├── postgres.py
    ├── models.py
    └── repositories.py
```

---

# 🐍 Requirements

نسخه Python:

```text
Python 3.12+
```

کتابخانه اصلی:

```text
python-bale-bot==2.5.0
```

Database:

```text
asyncpg
```

پردازش تصویر:

```text
Pillow
arabic-reshaper
python-bidi
```

---

# 💻 نصب Local

ابتدا Repository را Clone کنید:

```powershell
git clone YOUR_REPOSITORY_URL
cd possibly
```

ساخت Virtual Environment:

```powershell
py -3.12 -m venv .venv
```

فعال‌سازی:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

نصب Dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

# 🗄️ اتصال PostgreSQL

POSSIBLY به PostgreSQL نیاز دارد.

نمونه Connection String:

```text
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

برای Railway بهتر است Connection String از PostgreSQL Service خود Railway گرفته شود.

---

# 🚂 Railway Deployment

POSSIBLY برای Railway Worker طراحی شده است.

فایل:

```text
Procfile
```

نمونه:

```text
worker: python main.py
```

---

## Railway PostgreSQL

در Railway:

1. یک Project بسازید.
2. PostgreSQL Service اضافه کنید.
3. سرویس Bot را اضافه کنید.
4. Repository GitHub را متصل کنید.
5. PostgreSQL و Bot را در همان Project قرار دهید.
6. Connection String صحیح PostgreSQL را به Bot بدهید.
7. Deploy کنید.

---

# 🔑 Railway Variables

در Deployment واقعی بهتر است Secretها به صورت Variables/Secrets تنظیم شوند.

نمونه:

```text
BOT_TOKEN
DATABASE_URL
ALLOWED_GROUP_ID
OWNER_ID
```

مقادیر واقعی Secret نباید در README یا GitHub قرار گیرند.

---

# 🔄 Database Initialization

هنگام Start شدن Bot، Connection Pool ایجاد می‌شود.

Schemaهای مورد نیاز نیز در صورت نبودن ساخته می‌شوند.

اجرای Bot:

```powershell
python main.py
```

---

# ▶️ اجرای Bot

Local:

```powershell
python main.py
```

اگر همه چیز صحیح باشد، Logهایی مشابه زیر مشاهده می‌شود:

```text
[INFO] POSSIBLY starting
[INFO] Connected to PostgreSQL
[INFO] Handler registry loaded
[INFO] POSSIBLY initialized
```

---

# 📋 Logging

Logging استاندارد استفاده می‌شود.

سطح‌های اصلی:

```text
INFO
WARNING
ERROR
```

نمونه:

```text
[INFO] POSSIBLY starting
[INFO] Connected to PostgreSQL
[INFO] Handler registry loaded
[INFO] User joined game
[WARNING] Unsupported operation
[ERROR] Bale API request failed
```

### اطلاعات ممنوع در Log

هرگز این موارد Log نشوند:

```text
BOT_TOKEN
DATABASE_URL
DATABASE_PASSWORD
GitHub Token
API Keys
```

---

# 🧩 Permission System

سه Role اصلی:

```text
Owner
Admin
Member
```

### Member

دسترسی به قابلیت‌های عمومی.

### Admin

دسترسی به:

* مدیریت
* Learning
* آمار مدیریتی
* تنظیمات
* لاگ‌ها

### Owner

دسترسی کامل مدیریتی.

برای عملیات حساس، Permission باید در همان لحظه دوباره بررسی شود.

نباید صرفاً به اطلاعات قدیمی ذخیره‌شده در Database اعتماد شود.

---

# 🛡 Anti-Spam

سیستم باید برای دستورات حساس Rate Limit داشته باشد.

موارد دارای Rate Limit:

* Commands
* Whisper
* GIF Processing
* Game Actions
* Callback Actions

همچنین باید از:

* Loop بی‌نهایت
* Callbackهای قدیمی
* درخواست‌های غیرضروری API
* پردازش GIFهای بسیار بزرگ

جلوگیری شود.

---

# 🧠 State Management

Game State در PostgreSQL نگهداری می‌شود.

بنابراین Restart شدن Railway نباید به صورت خودکار باعث حذف بازی فعال شود.

State بازی‌ها باید شامل:

```text
game status
players
current phase
turn
actions
votes
roles
```

باشد.

---

# 🔄 Restart Safety

POSSIBLY باید بتواند بعد از Restart دوباره اجرا شود.

اطلاعات دائمی نباید در حافظه Python نگهداری شوند.

موارد مهم در PostgreSQL ذخیره می‌شوند:

```text
Users
Members
Statistics
Learning
Games
Game Players
Whispers
Moderation Logs
```

---

# 🌐 Bale API Compatibility

POSSIBLY از:

```text
python-bale-bot
```

استفاده می‌کند.

نسخه مورد استفاده پروژه:

```text
2.5.0
```

یک اصل مهم پروژه:

> هیچ متد Bale نباید صرفاً بر اساس حدس نام‌گذاری شود.

قبل از اضافه کردن قابلیت جدید باید:

1. نسخه نصب‌شده بررسی شود.
2. Documentation بررسی شود.
3. Source Code کتابخانه در صورت نیاز بررسی شود.
4. Signature متد بررسی شود.
5. API واقعی Bale بررسی شود.
6. Permission مورد نیاز بررسی شود.
7. قابلیت روی Bot تست شود.

اگر API بله قابلیتی را پشتیبانی نکند، آن قابلیت نباید Fake شود.

---

# ⚠️ محدودیت‌های API

برخی قابلیت‌ها ممکن است به دلیل محدودیت API بله یا Permissionهای Bot قابل پیاده‌سازی نباشند.

به‌خصوص:

* تعاملات خصوصی خاص
* بعضی اطلاعات اعضا
* برخی عملیات مدیریتی
* بعضی انواع Callback
* پردازش مستقیم برخی Mediaها

در چنین مواردی پروژه باید رفتار واقعی API را رعایت کند.

نباید برای کاربر وانمود شود که قابلیتی انجام شده است، در حالی که API آن را اجرا نکرده است.

---

# 👥 دریافت اعضای گروه

در صورت پشتیبانی API و Permission لازم، Bot می‌تواند اطلاعات اعضای گروه را دریافت کند.

اطلاعات قابل نمایش:

```text
Display Name
Username
User ID
Role
```

اگر API امکان دریافت کامل Member List را ندهد، سیستم فقط از اطلاعاتی که Bot واقعاً دریافت کرده استفاده می‌کند.

---

# 🧹 Error Handling

خطاهای موقت نباید باعث Crash دائمی Bot شوند.

برای سرویس‌های خارجی:

```text
Bale API
PostgreSQL
File Processing
```

باید Error Handling وجود داشته باشد.

برای خطاهای موقت Database یا API می‌توان Retry محدود با Exponential Backoff استفاده کرد.

---

# 📁 GitHub

قبل از Push کردن:

```powershell
git status
```

بررسی کنید که Secretها داخل Repository نباشند.

سپس:

```powershell
git add .
git commit -m "Update POSSIBLY"
git push
```

---

# 🚫 .gitignore

حداقل موارد زیر باید Ignore شوند:

```gitignore
.venv/
__pycache__/
*.pyc
.env
*.log
backup/
temp/
media/
.vscode/
```

همچنین فایل‌های Backup دیتابیس نباید به صورت تصادفی Commit شوند.

---

# 🔐 GitHub Personal Access Token

اگر برای Git از GitHub Token استفاده می‌کنید:

* Token را داخل Source Code نگذارید.
* Token را داخل README قرار ندهید.
* Token را داخل `config.py` قرار ندهید.
* Token را داخل Commit قرار ندهید.

برای Repository مشخص، حداقل Permission لازم را انتخاب کنید.

---

# 🧪 تست Local

قبل از Deploy:

```powershell
python main.py
```

سپس موارد زیر را تست کنید:

```text
ربات آنلاین است؟
PostgreSQL وصل است؟
گروه مجاز شناسایی می‌شود؟
Member پیام می‌دهد؟
Admin دستورات را اجرا می‌کند؟
Learning کار می‌کند؟
آمار ثبت می‌شود؟
Game ایجاد می‌شود؟
```

---

# 🧪 تست Database

پس از اتصال Database، بررسی کنید که Tableها ساخته شده باشند:

```text
users
group_members
learned_words
daily_stats
games
game_players
whispers
moderation_logs
```

---

# 🚨 Troubleshooting

## 401 Unauthorized

اگر Log:

```text
401: Unauthorized
```

نشان داد، Token ربات معتبر نیست.

Token جدید را از پنل مربوط به Bot دریافت کنید.

---

## PostgreSQL Connection Error

اگر خطایی مانند:

```text
socket.gaierror
```

یا:

```text
getaddrinfo failed
```

دیدید، Host دیتابیس از محیط فعلی قابل Resolve نیست.

برای Railway از آدرس داخلی PostgreSQL فقط داخل محیط مناسب Railway استفاده کنید.

برای اجرای Local باید Connection String قابل دسترسی از سیستم Local داشته باشید.

---

## asyncio.run Error

اگر خطایی مشابه:

```text
asyncio.run() cannot be called from a running event loop
```

دیدید، احتمالاً `bot.run()` داخل یک Event Loop دیگر اجرا شده است.

در `python-bale-bot` نسخه مورد استفاده، `Bot.run()` خودش Event Loop را مدیریت می‌کند.

بنابراین معماری اجرای Bot باید مطابق API همان نسخه باشد.

---

## Bot Online است ولی پیام نمی‌گیرد

موارد زیر را بررسی کنید:

1. Token صحیح است.
2. Bot واقعاً Online شده.
3. Bot در گروه وجود دارد.
4. Permissionهای لازم را دارد.
5. `ALLOWED_GROUP_ID` صحیح است.
6. Handlerها Register شده‌اند.
7. Group ID پیام با Group ID تنظیم‌شده برابر است.

---

# 🏗 Development Rules

قوانین توسعه POSSIBLY:

### 1. API حدس زده نشود

قبل از استفاده از هر متد Bale آن را بررسی کنید.

### 2. Database از Handler جدا باشد

Handler نباید محل اصلی SQL Logic باشد.

### 3. Game Logic مستقل باشد

Game Engine نباید مستقیماً به Bale API وابسته باشد.

### 4. Global State حداقلی باشد

اطلاعات مهم باید در PostgreSQL قرار بگیرند.

### 5. قابلیت Fake ساخته نشود

اگر API قابلیتی را پشتیبانی نمی‌کند، باید محدودیت اعلام شود.

### 6. Secret داخل GitHub قرار نگیرد

Token و Password باید Secret باقی بمانند.

---

# 📌 Roadmap

## Core

* [x] Python project
* [x] PostgreSQL
* [x] Connection Pool
* [x] Railway structure
* [x] Permission architecture
* [x] Group restriction
* [x] Logging

## Management

* [ ] Ban
* [ ] Kick
* [ ] Unban
* [ ] Temporary Kick
* [ ] Member Management
* [ ] Moderation Logs

## Learning

* [x] Add Learning
* [x] Remove Learning
* [x] List Learning
* [x] 300-item limit

## Statistics

* [x] Daily statistics
* [x] Message counter
* [x] GIF counter
* [x] Voice counter
* [x] Photo counter
* [x] Video counter
* [x] Top users

## Games

* [ ] Complete Mafia
* [x] Tic Tac Toe Engine
* [ ] Complete Tic Tac Toe UI
* [ ] Complete Truth or Dare

## Media

* [ ] GIF Caption
* [ ] Resource Limits
* [ ] Persian Typography

## Private Features

* [ ] Private Panel
* [ ] Whisper
* [ ] Backup Delivery
* [ ] Admin Dashboard

---

# 📜 License

این پروژه برای استفاده و توسعه شخصی/تیمی POSSIBLY ساخته شده است.

قبل از انتشار عمومی، License مناسب پروژه را مشخص کنید.

---

# ⚔️ POSSIBLY

**Group Management • Fun • Games**

```text
@possibly
```

ساخته شده با:

```text
Python
python-bale-bot
PostgreSQL
Railway
```

> هدف POSSIBLY ساخت یک Bot پایدار، قابل توسعه و مبتنی بر API واقعی Bale است؛ نه شبیه‌سازی قابلیت‌هایی که سرویس Bale واقعاً ارائه نمی‌کند.
