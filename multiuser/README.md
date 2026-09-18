# Bale Multi-User Login Bot

ربات بله برای **لاگین چندکاربره** بدون ترمینال.

## قابلیت‌ها

- `/start` برای کاربر جدید → گرفتن شماره → کد ورود → (در صورت نیاز) رمز دو مرحله‌ای
- اگر قبلاً وارد شده باشد → نمایش وضعیت سشن
- `/status` وضعیت حساب
- `/logout` حذف سشن
- `/cancel` لغو فلو لاگین
- پشتیبانی از ده‌ها کاربر (پیش‌فرض تا ۱۰۰ نفر در `config`)

## نقش‌ها

| بخش | کار |
|-----|-----|
| ربات (Bot Token) | ثبت‌نام، لاگین، راهنما |
| سشن (`aiobale`) | ذخیره لاگین اکانت شخصی هر کاربر |

## نصب (Windows PowerShell)

```powershell
cd bale-multiuser
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

توکن را در `core/config.py` بگذارید، سپس:

```powershell
python main.py
```

## وابستگی‌ها

- `requests` — Bot API بله (`https://tapi.bale.ai/bot`)
- `aiobale-py` — لاگین اکانت شخصی (شماره/کد/رمز) و فایل سشن
- `aiohttp` — وابستگی aiobale

## امنیت

- توکن ربات و سشن‌ها را public نکنید
- پوشه `sessions/` و `data/` در `.gitignore` هستند
- اگر توکن لو رفته، از BotFather بله توکن جدید بگیرید

## مرحله بعد (اختیاری)

Worker جدا برای آنلاین نگه داشتن سشن‌ها و اجرای دستورات (`/afk` و ...) روی اکانت هر کاربر.
