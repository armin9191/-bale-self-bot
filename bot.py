from client import bot

import handlers.start
import handlers.home
import handlers.menu_patch
import handlers.shop
import handlers.stats
import handlers.comments
import handlers.profile
import handlers.navigation
import handlers.channel
import handlers.add_channel
import handlers.channel_settings
import handlers.footer_text
import handlers.admin_panel
import handlers.admin_complete
import handlers.admin_users
import handlers.admin_channels
import handlers.admin_system
import handlers.admin
import handlers.support
import handlers.help

@bot.event
async def on_ready():
    print("✅ Connected!")
    print(bot.user)

@bot.event
async def on_update(update):
    print("Update:", update)

if __name__ == "__main__":
    print("🤖 User Bot Started...")
    bot.run()
