from datetime import date
from database.postgres import get_pool

async def upsert_user(user_id, username, display_name):
    await get_pool().execute("""INSERT INTO users(user_id,username,display_name) VALUES($1,$2,$3)
    ON CONFLICT(user_id) DO UPDATE SET username=EXCLUDED.username,display_name=EXCLUDED.display_name,last_seen=NOW()""", user_id, username, display_name)

async def upsert_member(group_id, user_id, role="member"):
    await get_pool().execute("""INSERT INTO group_members(group_id,user_id,role) VALUES($1,$2,$3)
    ON CONFLICT(group_id,user_id) DO UPDATE SET role=EXCLUDED.role""", group_id,user_id,role)

async def increment_stat(group_id,user_id,stat,day: date):
    if stat not in {"messages","gifs","voice","photos","videos","other"}: raise ValueError("invalid stat")
    await get_pool().execute(f"""INSERT INTO daily_stats(group_id,user_id,date,{stat}) VALUES($1,$2,$3,1)
    ON CONFLICT(group_id,user_id,date) DO UPDATE SET {stat}=daily_stats.{stat}+1""",group_id,user_id,day)
