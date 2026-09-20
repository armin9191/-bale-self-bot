from bale import InlineKeyboardMarkup, InlineKeyboardButton

def private_menu(admin: bool = False, owner: bool = False):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👤 پروفایل من", callback_data="profile"), row=1)
    kb.add(InlineKeyboardButton("📊 آمار من", callback_data="my_stats"), row=1)
    kb.add(InlineKeyboardButton("🎮 بازی‌ها", callback_data="games"), row=2)
    kb.add(InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about"), row=2)
    if admin:
        kb.add(InlineKeyboardButton("👥 اعضای گروه", callback_data="members"), row=3)
        kb.add(InlineKeyboardButton("🛡 مدیریت", callback_data="management"), row=3)
        kb.add(InlineKeyboardButton("📊 آمار گروه", callback_data="group_stats"), row=4)
        kb.add(InlineKeyboardButton("🧠 یادگیری", callback_data="learning"), row=4)
        kb.add(InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"), row=5)
        kb.add(InlineKeyboardButton("📜 لاگ مدیریت", callback_data="logs"), row=5)
    if owner:
        kb.add(InlineKeyboardButton("👑 Owner", callback_data="owner"), row=6)
    return kb

def ttt_keyboard(board):
    kb = InlineKeyboardMarkup()
    for r in range(3):
        for c in range(3):
            i = r * 3 + c
            label = board[i] or str(i + 1)
            kb.add(InlineKeyboardButton(label, callback_data=f"ttt:{i}"), row=r + 1)
    return kb
