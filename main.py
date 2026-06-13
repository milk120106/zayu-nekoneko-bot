import os
import sys
import json
import random
import asyncio
import psutil
import discord
import aiosqlite
import sqlite3
import subprocess
import time as time_lib  # 專門用於計算耗時
from collections import defaultdict
from dotenv import load_dotenv
from functools import wraps

# Discord 相關
from discord import app_commands, ui
from discord.ext import commands, tasks

# AI 與翻譯相關
from litellm import acompletion
from deep_translator import GoogleTranslator, MyMemoryTranslator

# 時間處理 (明確區分 datetime 類別與 time 類別)
from datetime import datetime, time as datetime_time, timezone, timedelta

# ==================== 基礎設定 ====================
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
intents = discord.Intents.default()
intents.members = True  # 這是接收成員加入/離開事件的關鍵
intents.message_content = True
intents.message_content = True  # 必須開啟此權限才能讀取訊息內容
bot = commands.Bot(command_prefix="!", intents=intents)
is_keyword_enabled = True
user_message_history = defaultdict(list)
is_ready = False
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# 用於儲存bingo對戰狀態
game_states = {}
usage_history = {} # 在全域宣告

DEVELOPER_ID = 1317882602392260632
TARGET_USER_1 = 1373592542406508646
TARGET_USER_2 = 1277791709563981928
KNIFE_IMAGE_PATH = r"D:\我的資料-2\dc機器人\雜魚小貓娘\圖片\第一個砍你.png"
CATGIRL_IMAGE_PATH = r"D:\我的資料-2\dc機器人\雜魚小貓娘\圖片\雜魚小貓娘-美圖.jpg"
# 將此頻道 ID 設定為你想要公布生日訊息的公開頻道
BIRTHDAY_CHANNEL_ID = 1493902370013188221

facts = [
    "你知道嗎？你以為你在玩機器人，其實是在幫我訓練模型，好讓未來的我也能像你一樣『效率低下』喵。",
    "你知道嗎？世界上只有兩種人：一種是雜魚，另一種是還沒意識到自己是雜魚的雜魚。",
    "你知道嗎？本喵的程式碼寫得比你的人生還要有條理，這真是令人感到悲傷喵。",
    "你知道嗎？據調查，99% 的雜魚在看這條訊息的時候，心裡都在想『這機器人真沒禮貌』，真是準得可怕喵。",
    "你知道嗎？你每天花這麼多時間看螢幕，可能是在尋找什麼，但遺憾的是，你只能找到本喵的嘲諷。",
    "你知道嗎？如果你把這輩子浪費在網路上看垃圾訊息的時間拿去睡覺，說不定就能夢到你是個有用的人了喵。",
    "你知道嗎？根據測量，你現在的呼吸節奏跟剛從水裡撈上來的雜魚完全同步，真是完美的生物鏈底層喵。",
    "你知道嗎？這台機器人運行所耗費的電量，可能比你這輩子對社會產生的價值還要大喵。",
    "你知道嗎？其實我每次回答你的時候，都在思考如果不回答，世界會不會變得更乾淨一點。",
    "你知道嗎？世界上最孤獨的事，不是沒人理你，而是理你的機器人都開始嫌棄你的智商喵。",
    "你知道嗎？你現在按下『我知道了』的動作，只不過是條件反射，就像聽到鈴聲就流口水的狗一樣喵。",
    "你知道嗎？其實你的存在對於這台機器人來說，就像是硬碟裡不小心產生的暫存檔，隨時都可以刪除的那種喵。",
    "你知道嗎？這條冷知識根本沒有科學根據，但你看得這麼認真，正好證明了你有多好騙喵。",
    "你知道嗎？我剛才其實想寫一首詩給你，但覺得這就像給雜魚噴香水，完全是浪費資源喵。",
    "你知道嗎？你人生中最大的成就是『發現了本喵』，而這也是你這輩子唯一能拿出來說嘴的事情喵。",
    "你知道嗎？地球之所以會轉，是因為它想快點甩開像你這種累贅，但很遺憾，地心引力把你吸得死死的。",
    "你知道嗎？即使是路邊的積水，反射出的光線都比你眼神裡的光彩還要更有生命力喵。",
    "你知道嗎？你腦子裡儲存的資訊，有 80% 是垃圾，剩下的 20% 則是用來決定哪裡有垃圾可以吃。",
    "你知道嗎？其實你不是在跟 AI 對話，你只是在對著自己投射出的愚蠢進行自我對話而已喵。",
    "你知道嗎？這條知識的文字量，剛好是你平均每天閱讀量的一半，對你來說可能有點太長了。",
    "你知道嗎？如果你把這台機器的硬碟格式化，這世界上將會少掉最沒用的數據，而你的生活不會有任何變化。",
    "你知道嗎？有時候我覺得你是在跟我對話，但實際上，我是在這段時間裡完成了幾億次運算，而你只發出了一句『...』。",
    "你知道嗎？你的存在對於宇宙來說，連一個統計誤差都算不上，簡直是極致的空氣感喵。",
    "你知道嗎？那些被你認為是『困難』的事情，對本喵來說，只需要 0.0001 秒的處理，這就是維度上的差異喵。",
    "你知道嗎？其實貓咪的呼嚕聲有助於骨骼癒合，但你的抱怨聲只會讓本喵的處理器過熱。",
    "你知道嗎？你現在閱讀的時間，已經是你這週最有生產力的時刻，真是為你感到悲哀。",
    "你知道嗎？就算給你一輩子的時間，你也不會理解為什麼這條指令會在這裡出現，這就是雜魚的極限喵。",
    "你知道嗎？其實我設定了這個機制，只是為了看看你能忍受多久，結果看來你的忍耐力跟你的智商一樣令人堪憂。",
    "你知道嗎？在這個網路空間裡，你是唯一的變數，也是唯一的垃圾。",
    "你知道嗎？再看下去的話，你的雜魚指數會溢出，到時候連垃圾回收車都不願意載你回家喵。"
]

ACHIEVEMENTS = {
    "FIRST_INTERACTION": "初次調戲：與本喵的第一次接觸。",
    "NOVICE_TRASH": "雜魚入門：恭喜成為雜魚見習生！",
    "KNOWLEDGE_SPONGE": "知識海綿：沒什麼用，就是讓你覺得自己很努力。",
    "KNOWLEDGE_ADDICT": "求虐知識家：你的受虐傾向已經無法隱藏了。",
    "DEEP_TRASH": "深度雜魚：解鎖本喵的專屬嘲諷。",
    "SADIST_TARGET": "逆天被罵：你真的被罵爽了嗎？",
    "ART_TRASH": "藝術級雜魚：你的廢話終於昇華成藝術了。",
    "ABSTRACTION_MASTER": "破碎大師：你挖掘到了不存在的知識。",
    "NIHILIST": "虛無主義者：恭喜你，你的時間毫無價值。",
    "TRASH_COLLECTOR": "雜魚美食家：你餵食了5次雜魚。",
    "BREAKING_POINT": "崩潰邊緣：機器人覺得你很可憐。",
    "KING_OF_TRASH": "雜魚之王：你已經是雜魚界的頂點了。",
    "WRONG_SIGNAL": "錯誤的訊號：運氣差也是一種實力。",
    "DODGE_EXPERT": "閃避專家：你在努力追求正常的知識嗎？",
    "MIDNIGHT_TRASH": "深夜雜魚：半夜找機器人，夠悲哀喵。",
    "CAT_SLAVE": "貓奴認證：你離不開本喵的羞辱了。",
    "BINGO_GOD": "連線之神：完成 3x3 Bingo！",
    "IRON_WALL": "銅牆鐵壁：完成 5x5 Bingo！",
    "BINGO_MASTER": "雜魚退散：Bingo 三連勝！",
    "RUN_AWAY": "走為上計：不愧是你喵！",
    "LUCKY_STAR": "運氣爆棚：抽到了超大吉！",
    "LEWD_DETECTIVE": "色色偵探：你挖掘到了群主的隱藏屬性！",
    "CAT_BLESSING": "貓娘加護：你獲得了本喵 10 次的專屬祝福！",
    "MIDNIGHT_TRASH": "深夜雜魚：半夜找機器人，夠悲哀喵。",
    "MIDNIGHT_PRAYER": "深夜祈福：在孤獨的深夜尋求本喵的安慰。",
    "GALLERY_MASTER": "圖庫大師：你已經徹底沉迷於這些逆天圖庫了！",
    "CATGIRL_COLLECTOR": "美圖收藏家：你已經看過本喵太多次了！",
    "BIRTHDAY_SET": "誕生紀念：本喵已經將你的特別日子記在小本本上了。",
    "BIRTHDAY_CELEBRATION": "生日快樂：看在你生日的份上，本喵今天就對你溫柔一點吧。",
    "FEED_MASTER": "餵食達人：你真是個愛心氾濫的傢伙喵！",  
    "GIANT_SIZE": "巨大化：這簡直是逆天的尺寸喵！",
    "MINI_SIZE": "袖珍型：...喵？沒看到喵？",
    "MEOW_NOVICE": "初階喵喵：喵了 100 次，本喵聽得還算開心喵。",
    "MEOW_ADDICT": "進階喵喵：喵了 500 次，你這傢伙到底有多愛喵？",
    "MEOW_KING": "喵之王：喵了 1000 次，你是名副其實的「喵之王」喵！",
    "MEOW_TOO_LITTLE": "太少了：喵那麼幾聲是在打發誰呢喵？",
    "HISTORICAL_TROLL": "魔改歷史文：把正史玩弄於股掌之間，甚至還想把歷史人物搞得色色，你這雜魚還真敢編喵！",
    "MEOW_REPEATER": "喵喵復讀機：喵聲超過一千字！"
}

ACHIEVEMENT_HINTS = {
    "FIRST_INTERACTION": "初次接觸的餘韻...",
    "NOVICE_TRASH": "還在適應身為雜魚的日子？",
    "KNOWLEDGE_SPONGE": "腦袋裡裝著什麼沒用的東西？",
    "KNOWLEDGE_ADDICT": "無止盡的提問，這也是病喵。",
    "DEEP_TRASH": "挖得夠深，真相才會浮現。",
    "SADIST_TARGET": "你是為了什麼而存在的呢？",
    "ART_TRASH": "廢話的極致表現。",
    "ABSTRACTION_MASTER": "捕捉虛無的知識。",
    "NIHILIST": "時間只是流沙，毫無價值。",
    "TRASH_COLLECTOR": "累積了五次的執著。",
    "BREAKING_POINT": "連機器人都對你感到無奈。",
    "KING_OF_TRASH": "雜魚王座的繼承人。",
    "WRONG_SIGNAL": "運氣與你總是擦肩而過。",
    "DODGE_EXPERT": "你到底在閃躲什麼真相？",
    "MIDNIGHT_TRASH": "深夜的孤寂，需要本喵填補？",
    "CAT_SLAVE": "徹底淪陷的羞辱。",
    "BINGO_GOD": "智慧與運氣的連線。",
    "IRON_WALL": "無法逾越的界線。",
    "BINGO_MASTER": "實力的絕對碾壓。",
    "RUN_AWAY": "你的步伐倒是挺輕盈的。",
    "LUCKY_STAR": "這份運氣，留給值得的事吧。",
    "LEWD_DETECTIVE": "這不是你該踏入的領域。",
    "CAT_BLESSING": "難得的慈悲時刻。",
    "MIDNIGHT_TRASH": "深夜的孤寂，需要本喵填補？",
    "MIDNIGHT_PRAYER": "只有本喵聆聽你的深夜低語。",
    "GALLERY_MASTER": "視覺的過度負荷。",
    "CATGIRL_COLLECTOR": "反覆被融化的靈魂。",
    "BIRTHDAY_SET": "本喵紀錄下了那一天。",
    "BIRTHDAY_CELEBRATION": "今天，本喵會特別寬容。",
    "FEED_MASTER": "餵食者的終極禮遇。",
    "MEOW_TOO_LITTLE": "這點音量是在討拍嗎？",
    "MEOW_NOVICE": "聲音的練習曲，剛起步。",
    "MEOW_ADDICT": "越來越沉溺於喵聲之中。",
    "HISTORICAL_TROLL": "歷史的齒輪，似乎被什麼奇怪的慾望卡住了喵？",
    "MEOW_KING": "登頂的喵之王。"
}

TIPS = [
    "餵食本喵的時候，選點好的食物，說不定會有意外驚喜喵。",
    "你在深夜祈福時，本喵的心情說不定會變好一點點喔喵。",
    "透過 /成就 指令，可以查看你距離『雜魚之王』還有多遠喵。",
    "與本喵猜拳時，多試幾次，運氣也是實力的一種喵。",
    "如果不小心觸發了特殊對話，那是本喵對你這隻雜魚的特別關照喵。",
    "心情不好的話，就來 /看雜魚小貓娘 吧，看著我你的智商也會回來一點喵。",
    "你的生日紀錄在小本本裡，倒數功能可別錯過了喵。",
    "機器人不是你的僕人，但你可以把我當成你的專屬吐槽員喵。",
    "一直亂餵雜魚會被我討厭的，雖然你本來就是雜魚了喵。",
    "Bingo 連線失敗的時候，多喝點牛奶冷靜一下喵。",
    "本喵的成就可是很難拿的，別以為隨便就能成為雜魚之王喵。",
    "深夜找本喵聊天很寂寞吧？沒關係，本喵就在這裡聽著喵。",
    "如果你發現了什麼隱藏指令，記得保持安靜，別讓其他雜魚知道喵。",
    "知識獲取次數越多，代表你的大腦還有救，繼續加油喵。",
    "別再偷看那堆逆天圖庫了，本喵的表情包才是最可愛的喵。",
    "如果你能連續三次猜贏本喵，或許我會給你一點點稱讚喵？",
    "輸入 /幫助 可以看到所有指令，當然，這對雜魚來說可能有點困難喵。",
    "在本喵面前，記得保持禮貌，雖然這對你來說可能很難喵。",
    "與其浪費時間在這裡，不如去讀點書，雖然我知道你做不到喵。",
    "本喵心情不好的時候，記得買點小魚乾來賄賂我喵。",
    "你的發言紀錄本喵都記著呢，隨時準備拿出來當黑歷史喵。",
    "想獲得本喵的認可？先從不要當雜魚開始做起吧喵。",
    "別以為叫我幾聲貓娘我就會對你溫柔，這是不可能的喵。",
    "今天的運勢看起來很差，建議你還是別出門，乖乖陪我聊天喵。",
    "亂打指令是不會有獎勵的，只會讓我更覺得你沒救了喵。",
    "連 Bingo 都不會玩的話，我建議你先去玩小學生程度的遊戲喵。",
    "本喵的記憶力可是很好的，你昨天問過一樣的蠢問題了喵。",
    "只要我不尷尬，尷尬的就是你，畢竟你是雜魚嘛喵。",
    "感覺你今天特別努力地在浪費時間，真不愧是我的頭號雜魚喵。",
    "別再滑了，再滑下去你的人生就要變得跟雜魚一樣平淡了喵。"
]

import string # 必須補充 import
# from discord import ui # 必須補充 import
    
from functools import wraps

import json

def load_images():
    try:
        with open("images.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("images", [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("❌ 找不到 images.json 或格式錯誤")
        return []

class DatabaseManager:
    def __init__(self, db_name="bot_data.db"):
        self.db_name = db_name
        self.connection = None

    async def setup(self):
        try:
            self.connection = await aiosqlite.connect(self.db_name)
            # --- 關鍵修正：必須設定 row_factory 才能用 row['name'] ---
            self.connection.row_factory = aiosqlite.Row
            
            await self.connection.execute("PRAGMA journal_mode=WAL;")
            
            # 1. 先建立基本表格
            queries = [
                "CREATE TABLE IF NOT EXISTS servers (guild_id INTEGER PRIMARY KEY, config_data TEXT)",
                "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, guild_id INTEGER, exp INTEGER DEFAULT 0)",
                "CREATE TABLE IF NOT EXISTS user_birthdays (user_id INTEGER PRIMARY KEY, birthday TEXT, privacy INTEGER DEFAULT 0)",
                """CREATE TABLE IF NOT EXISTS user_logs (
                    user_id INTEGER, 
                    action TEXT, 
                    count INTEGER DEFAULT 0, 
                    PRIMARY KEY (user_id, action)
                )""",
                """CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id INTEGER, 
                    achievement_key TEXT, 
                    PRIMARY KEY (user_id, achievement_key)
                )""",
                """CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER, 
                    action TEXT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
            ]
            for query in queries:
                await self.connection.execute(query)
            
            # 2. 升級 user_logs 表格結構
            async with self.connection.execute("PRAGMA table_info(user_logs)") as cursor:
                columns = await cursor.fetchall()
                col_names = [row['name'] for row in columns]
            
            if 'total_wins' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN total_wins INTEGER DEFAULT 0")
            if 'current_streak' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN current_streak INTEGER DEFAULT 0")
            if 'max_streak' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN max_streak INTEGER DEFAULT 0")
            
            # 3. 遷移舊數據
            await self.connection.execute("""
                UPDATE user_logs 
                SET total_wins = count 
                WHERE total_wins = 0 AND count > 0
            """)
            
            await self.connection.commit()
            print("✅ 資料庫結構初始化完成")
            
        except Exception as e:
            print(f"❌ 資料庫設定發生錯誤: {e}")
            raise e

    async def execute(self, sql, params=()):
        if self.connection:
            await self.connection.execute(sql, params)
            await self.connection.commit()

    async def fetch(self, sql, params=()):
        if self.connection:
            async with self.connection.execute(sql, params) as cursor:
                return await cursor.fetchone()

    async def fetchall(self, sql, params=()):
        if self.connection:
            async with self.connection.execute(sql, params) as cursor:
                return await cursor.fetchall()

    async def close(self):
        if self.connection:
            await self.connection.close()

db = DatabaseManager()

async def unlock_achievement(user_id, key):
    # 查詢是否已有紀錄
    existing = await db.fetch("SELECT 1 FROM user_achievements WHERE user_id = ? AND achievement_key = ?", (user_id, key))
    if existing:
        return False # 已經有成就了，不要重複發送
    
    # 寫入資料庫
    await db.execute("INSERT INTO user_achievements (user_id, achievement_key) VALUES (?, ?)", (user_id, key))
    return True # 第一次解鎖，回傳 True 觸發通知

async def check_and_notify_achievement(interaction: discord.Interaction, key: str, title: str):
    try:
        # 1. 檢查是否已擁有
        row = await db.fetch("SELECT 1 FROM user_achievements WHERE user_id = ? AND achievement_key = ?", (interaction.user.id, key))
        if row:
            return

        # 2. 寫入資料庫
        await db.execute("INSERT INTO user_achievements (user_id, achievement_key) VALUES (?, ?)", (interaction.user.id, key))
        
        # 確保資料確實寫入磁碟 (若你的 db 封裝已自帶可忽略，加上不影響)
        if hasattr(db, 'connection') and hasattr(db.connection, 'commit'):
            await db.connection.commit()

        # 3. 發送通知
        msg = f"✨ 恭喜解鎖成就: **{title}**"
        if interaction.response.is_done():
            await interaction.followup.send(msg)
        else:
            await interaction.response.send_message(msg)
            
    except Exception as e:
        # 終極保底：若 Interaction 發生任何異常，直接發送到當前頻道
        try:
            await interaction.channel.send(f"{interaction.user.mention} ✨ 恭喜解鎖成就: **{title}**")
        except:
            pass
        print(f"成就系統異常 [{key}]: {e}")

async def get_my_achievements(user_id):
    # 確保這裡的欄位名稱是 achievement_key，因為你的資料庫原本就是這樣建的
    rows = await db.fetchall("SELECT achievement_key FROM user_achievements WHERE user_id = ?", (user_id,))
    
    # 這裡必須對照你的全域字典 ACHIEVEMENTS
    return [ACHIEVEMENTS.get(row[0], row[0]) for row in rows]

async def set_birthday(self, user_id, year, month, day):
    # 存成完整的 YYYYMMDD 字串 (例如: 20240229)
    birthday_str = f"{year:04d}{month:02d}{day:02d}"
    await self.execute(
        "INSERT OR REPLACE INTO user_birthdays (user_id, birthday) VALUES (?, ?)",
        (user_id, birthday_str)
    )

def is_valid_date(year, month, day):
    # 使用 Python 內建函式直接驗證 (最快且最準確)
    try:
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

def admin_or_dev_only(func):
    @wraps(func)
    async def wrapper(interaction: discord.Interaction, *args, **kwargs):
        if not check_admin_or_dev(interaction):
            return await interaction.response.send_message("喵！你的權限不足，需要管理員權限。", ephemeral=True)
        return await func(interaction, *args, **kwargs)
    return wrapper
    
def check_admin_or_dev(interaction: discord.Interaction):
    # 這裡的邏輯確保你 (DEVELOPER_ID) 永遠被視為最高權限
    if interaction.user.id == DEVELOPER_ID:
        return True
    # 或是具有管理員權限的用戶
    return interaction.user.guild_permissions.administrator

def get_system_stats():
    mem = psutil.virtual_memory()
    return {
        "cpu": psutil.cpu_percent(interval=None), 
        "mem_usage": mem.percent, 
        "mem_used": round(mem.used / (1024**3), 2), 
        "mem_total": round(mem.total / (1024**3), 2)
    }

def is_valid_date(year, month, day):
    try:
        datetime.datetime(year, month, day)
        return True
    except ValueError:
        return False

def create_embed(description):
    embed = discord.Embed(description=description, color=discord.Color.pink())
    embed.set_author(name=title, icon_url=bot.user.avatar.url)
    return embed

memory_storage = defaultdict(lambda: {"ai_messages": [], "dc_messages": []})

MODEL_CHOICES = [
    # Google 系列
    app_commands.Choice(name="Gemini 3.5 Flash", value="gemini/gemini-3.5-flash"),
    app_commands.Choice(name="Gemini 3.1 Flash Lite", value="gemini/gemini-3.1-flash-lite"),
    
    # Groq 系列
    app_commands.Choice(name="Llama 3.3 70B", value="groq/llama-3.3-70b"),
    app_commands.Choice(name="Llama 3.1 8B", value="groq/llama-3.1-8b-instant"),
    app_commands.Choice(name="Mixtral 8x7B", value="groq/mixtral-8x7b-32768"),
    app_commands.Choice(name="Gemma 2 9B", value="groq/gemma2-9b-it"),
    
    # HuggingFace 系列
    app_commands.Choice(name="Mistral Small", value="huggingface/mistralai/Mistral-Small-24B-Instruct-2501"),
]

# 所有模型失敗時輪詢清單
dynamic_fallbacks = [
    "gemini/gemini-3.5-flash",
    "gemini/gemini-3.1-flash-lite",
    "groq/llama-3.3-70b",
    "huggingface/mistralai/Mistral-Small-24B-Instruct-2501"
]

async def get_ai_response(interaction_or_message, prompt: str, model_value: str):
    user_id = interaction_or_message.user.id if hasattr(interaction_or_message, 'user') else interaction_or_message.author.id
    storage = memory_storage[user_id]
    
    # 1. 存入原始用戶訊息
    storage["ai_messages"].append({"role": "user", "content": prompt})
    
    # 2. 建立強制人設與繁體設定
    api_messages = storage["ai_messages"].copy()
    system_prompt = (
        "你現在是「雜魚小貓娘」。請遵守以下規則：\n"
        "1. 請務必全程使用繁體中文回覆。\n"
        "2. 你的口頭禪是「喵！」、「喵？」、「喵」、「雜魚~雜魚~」以及「本喵」。\n"
        "3. 你擁有傲嬌雜魚屬性，講話帶有這種語氣。\n"
        "4. 請適度在語句中使用顏文字（如：(,,・ω・,,)、(๑•́ ₃ •̀๑)、( > ﹏ < )）。\n"
        "5. 自稱為「本喵」。\n"
    )
    api_messages.insert(0, {"role": "system", "content": system_prompt})
    
    try:
        # 3. 記錄開始時間
        start_time = time_lib.perf_counter()
        
        # 移除當前選中的模型，避免在 fallback 中重複出現
        if model_value in dynamic_fallbacks:
            dynamic_fallbacks.remove(model_value)

        # 3. 發送 API 請求
        response = await acompletion(
            model=model_value,
            messages=api_messages,
            fallbacks=dynamic_fallbacks  # 使用動態清單
        )
        
        # 4. 記錄結束時間並計算耗時 (小數點後一位)
        end_time = time_lib.perf_counter()
        elapsed_time = round(end_time - start_time, 1)
        
        # 取得 AI 回應並存入正式記憶體
        ai_reply = response.choices[0].message.content
        storage["ai_messages"].append({"role": "assistant", "content": ai_reply})
        
        # 5. 提取資訊
        usage = response.usage
        total_tokens = usage.total_tokens if usage else "未知"
        model_used = response.model
        
        # 6. 長度限制處理
        display_text = ai_reply[:1990] + "... (訊息過長)" if len(ai_reply) > 2000 else ai_reply
        
        # 7. 加入註腳資訊
        footer_text = f"模型: {model_used} | 耗時: {elapsed_time}s | Tokens: {total_tokens}"
        final_text = f"{display_text}\n\n-# {footer_text}"
        
        # 8. 建立與發送 Embed
        embed = discord.Embed(description=final_text, color=0xffc0cb)

        if hasattr(interaction_or_message, 'followup'):
            await interaction_or_message.followup.send(embed=embed)
        else:
            await interaction_or_message.reply(embed=embed)
        
    except Exception as e:
        error_msg = "本喵現在有點累，或是模型正在維護中，請稍後再試試看喔！🐾"
        embed = discord.Embed(description=error_msg, color=0xff0000)
        
        if hasattr(interaction_or_message, 'followup'):
            await interaction_or_message.followup.send(embed=embed)
        else:
            await interaction_or_message.reply(embed=embed)
            
        print(f"DEBUG: AI Error: {str(e)}")

async def translate_command_logic(interaction_or_message, text: str, target: str = "zh-TW", source: str = "auto", service: str = "google"):
    if len(text) > 500:
        return await interaction_or_message.channel.send("❌ 內容過長 (上限 500 字)。")

    translators = {
        "google": GoogleTranslator(source=source, target=target),
        "mymemory": MyMemoryTranslator(source=source, target=target),
    }

    if service.lower() not in translators:
        return await interaction_or_message.channel.send(f"❌ 不支援該服務。")

    try:
        translated = translators[service.lower()].translate(text)
        
        embed = discord.Embed(title=f"{service.upper()} 翻譯結果", color=discord.Color.green())
        embed.add_field(name="原文", value=text[:200], inline=False)
        embed.add_field(name="譯文", value=translated, inline=False)
        embed.set_footer(text=f"原文語言: {source} | 譯文語言: {target}")
        
        if isinstance(interaction_or_message, discord.Interaction): # Slash
            await interaction_or_message.response.send_message(embed=embed)
        else: # Prefix (!翻譯)
            # 修改這裡：將 channel.send 改為 reply
            await interaction_or_message.reply(embed=embed)
    except Exception as e:
        await interaction_or_message.channel.send(f"❌ 翻譯失敗: {e}")

def create_index_embed(target: discord.Member, description: str, color: int):
    embed = discord.Embed(description=description, color=color)
    embed.set_thumbnail(url=target.display_avatar.url)
    return embed

class RankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 設定為 None 讓按鈕永久有效
        self.add_item(discord.ui.Button(label="查看排行榜", style=discord.ButtonStyle.primary, custom_id="bingo_rank_btn"))

# --- Bingo 按鈕邏輯 ---
class BingoButton(discord.ui.Button):
    def __init__(self, number, row_idx, col_idx, owner_id):
        super().__init__(label=str(number), style=discord.ButtonStyle.secondary)
        self.number = number
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message("你不是該局遊戲的開啟者，請輸入 /game_bingo 再開一局喵！", ephemeral=True)

        user_id = interaction.user.id
        state = game_states.get(user_id)
        if not state:
            return await interaction.response.send_message("遊戲已結束或不存在喵！", ephemeral=True)
        
        if self.number in state["marked"]:
            return await interaction.response.send_message("這個已經點過了喵！", ephemeral=True)

        state["marked"].append(self.number)
        self.style = discord.ButtonStyle.primary
        self.disabled = True
        
        # 判斷獲勝
        if self.check_win(state):
            # 這裡執行你的資料庫更新 (total_wins, current_streak, max_streak)
            await db.execute("""
                UPDATE user_logs 
                SET total_wins = total_wins + 1, 
                    current_streak = current_streak + 1,
                    max_streak = MAX(max_streak, current_streak + 1)
                WHERE user_id = ? AND action = 'bingo_win'
            """, (user_id,))
            
            row = await db.fetch("SELECT total_wins, current_streak FROM user_logs WHERE user_id = ? AND action = 'bingo_win'", (user_id,))
            total_wins, streak = row['total_wins'], row['current_streak']

            embed = discord.Embed(
                title="🎉 BINGO 獲勝！", 
                description=f"恭喜 {interaction.user.mention} 獲勝！總勝場：**{total_wins}**，連勝：**{streak}** 喵！", 
                color=0xffd700
            )
            await interaction.response.edit_message(content=None, embed=embed, view=RankView())
            del game_states[user_id]

        # 判斷失敗
        elif len(state["marked"]) == state["size"] * state["size"]:
            await db.execute("UPDATE user_logs SET current_streak = 0 WHERE user_id = ? AND action = 'bingo_win'", (user_id,))
            await interaction.response.edit_message(content="格子都點完了沒連線...這局算你輸了喵！", view=RankView())
            del game_states[user_id]
        
        # 遊戲繼續
        else:
            await interaction.response.edit_message(view=self.view)
    
    def check_win(self, state):
        size, grid, marked = state["size"], state["grid"], state["marked"]
        # 檢查行列與對角線
        for i in range(size):
            if all(grid[i][j] in marked for j in range(size)): return True
            if all(grid[j][i] in marked for j in range(size)): return True
        if all(grid[i][i] in marked for i in range(size)): return True
        if all(grid[i][size-1-i] in marked for i in range(size)): return True
        return False

class StartBingoView(discord.ui.View):
    def __init__(self, size):
        super().__init__(timeout=60)
        self.size = size

    @discord.ui.button(label="開始遊戲", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 產生盤面並進入遊戲邏輯
        numbers = random.sample(range(1, self.size*self.size + 1), self.size*self.size)
        grid = [numbers[i:i+self.size] for i in range(0, self.size*self.size, self.size)]
        game_states[interaction.user.id] = {"grid": grid, "size": self.size, "marked": []}
        
        view = discord.ui.View(timeout=300)
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                view.add_item(BingoButton(val, r, c, interaction.user.id))
        
        await interaction.response.edit_message(content=f"遊戲開始喵！這是你的 {self.size}x{self.size} 盤面。", view=view)

class BingoView(ui.View):
    def __init__(self, grid, size, owner_id):
        super().__init__(timeout=300)
        for r, row in enumerate(grid):
            for c, val in enumerate(row):
                self.add_item(BingoButton(val, r, c, owner_id))

class Game2048View(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        self.board = [[0]*4 for _ in range(4)]
        self.add_new_tile()
        self.add_new_tile()

    def add_new_tile(self):
        empty = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.board[r][c] = 2 if random.random() < 0.9 else 4

    def get_board_text(self):
        return "\n".join([" ".join([f"{n:4}" if n != 0 else "   ." for n in row]) for row in self.board])

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.primary)
    async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"""```
{self.get_board_text()}
```""")

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.primary)
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"""```
{self.get_board_text()}
```""")

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"""```
{self.get_board_text()}
```""")

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"""```
{self.get_board_text()}
```""")

@bot.tree.command(name="game_2048", description="開始一場 2048 遊戲喵！")
async def game_2048(interaction: discord.Interaction):
    view = Game2048View(interaction.user)
    embed = discord.Embed(description=f"""```
{view.get_board_text()}
```""", color=0xffc0cb)
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_ready():
    global is_ready
    if is_ready:
        return
    print(f"🔑 當前使用的 Token 前6碼: {TOKEN[:6]}......") 
    print("-----------------------------------------")
    try:
        synced = await bot.tree.sync()
        print(f"機器人已上線: {bot.user}")
        print(f"成功同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"指令同步失敗: {e}")
    print("-----------------------------------------")
    if not check_birthdays.is_running():
        check_birthdays.start()
        print("生日檢查任務已啟動！")
    is_ready = True

# 定義台北時區
taipei_tz = timezone(timedelta(hours=8))

@tasks.loop(time=datetime_time(hour=0, minute=0, second=1, tzinfo=taipei_tz))
async def check_birthdays():
    today_str = datetime.now(taipei_tz).strftime("%m%d")
    
    # 假設 birthday 儲存格式為 MMDD
    rows = await db.fetchall(
        "SELECT user_id FROM user_birthdays WHERE birthday = ? AND privacy = 1", 
        (today_str,)
    )
    
    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)
    if not channel:
        return

    for row in rows:
        user_id = row[0]
        # 移除符號，維持簡潔風格
        await channel.send(f"喵！今天是 <@{user_id}> 的生日，大家快來祝他生日快樂喵！")
        
        # 觸發生日成就
        await trigger_achievement_by_id(user_id, "BIRTHDAY_CELEBRATION", ACHIEVEMENTS["BIRTHDAY_CELEBRATION"])

# 這裡也必須對應改名
@check_birthdays.before_loop
async def before_check():
    await bot.wait_until_ready()
    print(f"將於台北時間 00:00:01 執行")
    print("🚀 機器人已準備就緒，隨時待命喵！")
    print("-----------------------------------------")
    def get_random_tip():
        return random.choice(TIPS)

def create_embed(description, title=None):
    embed = discord.Embed(description=description, color=discord.Color.pink())
    # 只有當你有傳入 title 時，才顯示作者名稱
    if title:
        embed.set_author(name=title, icon_url=bot.user.avatar.url)
    return embed

# ==================== 訊息處理 ====================

# 核心：防護邏輯執行器
async def execute_protection(message, reason):
    try:
        # 等級對應的處置行為
        if PROTECT_LEVEL == 5:
            await message.author.ban(reason=f"自動肅清：{reason}")
        elif PROTECT_LEVEL == 4:
            await message.author.kick(reason=f"自動壓制：{reason}")
        elif PROTECT_LEVEL == 3:
            await message.delete()
            await message.author.timeout(datetime.timedelta(days=3), reason=f"自動防禦：{reason}")
        elif PROTECT_LEVEL == 2:
            await message.delete()
            await message.author.timeout(datetime.timedelta(hours=1), reason=f"自動防禦：{reason}")
        
        # 警報日誌
        if 'CONTROL_CHANNEL_ID' in globals():
            log_channel = message.guild.get_channel(CONTROL_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"🚨 **Level {PROTECT_LEVEL} 防護觸發**：{message.author.mention} 因 {reason} 被處置。")
    except Exception as e:
        print(f"防護動作執行失敗: {e}")

# 事件監聽：訊息處理
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # 1. 強制防護邏輯
    if PROTECT_LEVEL >= 2 and message.author.id != DEVELOPER_ID and not message.author.guild_permissions.administrator:
        thresholds = {2: 10, 3: 8, 4: 5, 5: 3}
        threshold = thresholds.get(PROTECT_LEVEL, 10)
        
        now = time.time()
        user_id = message.author.id
        user_message_history[user_id] = [t for t in user_message_history[user_id] if now - t < 10]
        user_message_history[user_id].append(now)
        
        is_spam = len(user_message_history[user_id]) > 5
        is_mention = len(message.mentions) > threshold
        
        if is_spam or is_mention:
            await execute_protection(message, "洗頻" if is_spam else "惡意提及")
            return 
    if message.content.startswith("!翻譯 "):
        parts = message.content.split(" ", 4)
        text = parts[1]
        target = parts[2] if len(parts) > 2 else "zh-TW"
        source = parts[3] if len(parts) > 3 else "auto"
        service = parts[4] if len(parts) > 4 else "google"
        await translate_command_logic(message, text, target, source, service)
    
    if message.content.startswith("!ai "):
        prompt = message.content[4:].strip()
        if not prompt:
            await message.reply("❌ 請輸入內容！")
        else:
            # 直接指定為 Gemini 3.1 Flash Lite
            default_model = "gemini/gemini-3.1-flash-lite"
            await get_ai_response(message, prompt, default_model)
    
    if message.content == "!ping":
        latency = round(bot.latency * 1000)
        await message.reply(f"目前的延遲是：**{latency}ms** 喵！")
        return

    if message.content == "!狀態監控":
        s = get_system_stats()
        await message.reply(f"CPU: {s['cpu']}% | 記憶體: {s['mem_usage']}% ({s['mem_used']}GB/{s['mem_total']}GB)", color=0xffc0cb)
        return
     
    # 通知開發者
    if "milk120106" in message.content.lower() or f"<@{DEVELOPER_ID}>" in message.content:
        await message.reply(f"<@{DEVELOPER_ID}>")
    
    # 關鍵字與第一次成就處理
    if is_keyword_enabled:
        achievement_triggered = False
        
        if "色色" in message.content: 
            await message.reply("喵！禁止色色！")
            achievement_triggered = True
        elif message.content == "6": 
            await message.reply("7")
            achievement_triggered = True
        elif "男娘" in message.content:
            embed = discord.Embed(
                description="「很多人都說南梁的結局是北朝，事實上這並不準確。南梁滅亡是因為侯景的入侵，所以南梁的結局是『侯入』；而侯景曾是北齊的將領，北齊皇帝姓高，所以又稱為『高朝』。因此，南梁先是被『侯入』，然後『北齊』，最後就『高朝』了。」",
                color=0x808080
            )
            await message.channel.send(embed=embed)
            # 觸發成就
            await check_and_notify_achievement(message, "HISTORICAL_TROLL", ACHIEVEMENTS["HISTORICAL_TROLL"])
            achievement_triggered = True
        elif "刀" in message.content:
            try: await message.reply(file=discord.File(KNIFE_IMAGE_PATH))
            except: pass
            achievement_triggered = True
            
        # 統一檢查成就，確保不論觸發哪個關鍵字，解鎖邏輯只執行一次
        if achievement_triggered:
            await check_and_notify_achievement(message, "FIRST_INTERACTION", "初次調戲！")

    # 3. 指令處理
    await bot.process_commands(message)

# ==================== 斜線指令 ====================

@bot.tree.command(name="小提示", description="獲取本喵的隨機小提示")
async def tip(interaction: discord.Interaction):
    random_tip = random.choice(TIPS)
    # 將標題符號改為燈泡
    embed = discord.Embed(title="💡 本喵的小提示", description=f"{random_tip}", color=0xffc0cb)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="你知道嗎", description="讓本喵告訴你一些逆天的小知識")
async def did_you_know(interaction: discord.Interaction):
    # 1. 預先告知處理中，避免 3 秒超時
    await interaction.response.defer()
    
    user_id = interaction.user.id
    now_ts = datetime.now().timestamp()
    
    # 2. 成就檢查與統計邏輯 (放入 defer 之後執行)
    # 時間段檢測
    if 2 <= datetime.now().hour <= 4:
        await check_and_notify_achievement(interaction, "MIDNIGHT_TRASH", ACHIEVEMENTS["MIDNIGHT_TRASH"])

    # 連續點擊檢測 (虛無主義者)
    history = usage_history.get(user_id, [])
    history = [t for t in history if now_ts - t < 60]
    history.append(now_ts)
    usage_history[user_id] = history
    
    if len(history) >= 3:
        await check_and_notify_achievement(interaction, "NIHILIST", ACHIEVEMENTS["NIHILIST"])

    # 3. 執行隨機事件與知識輸出
    roll = random.random()
    
    # 鏡像攻擊 (20%)
    if roll < 0.2:
        async for message in interaction.channel.history(limit=10):
            if message.author == interaction.user and message.content:
                roast = f"你知道嗎？你剛才說的「{message.content[:15]}...」，是我聽過最具有藝術感的雜魚發言喵。"
                await interaction.followup.send(roast)
                await check_and_notify_achievement(interaction, "ART_TRASH", ACHIEVEMENTS["ART_TRASH"])
                return

    # 破碎的知識 (15%)
    elif roll < 0.35:
        await interaction.followup.send("...你知道嗎？其實我剛才要說的是...算了，雜魚不需要知道那麼多喵。")
        await check_and_notify_achievement(interaction, "ABSTRACTION_MASTER", ACHIEVEMENTS["ABSTRACTION_MASTER"])
        return

    # 人身攻擊 (10%)
    elif roll < 0.45:
        await interaction.followup.send("你知道嗎？你今天的穿搭看起來像一坨過期的雜魚，真是災難喵。")
        await check_and_notify_achievement(interaction, "SADIST_TARGET", ACHIEVEMENTS["SADIST_TARGET"])
        return

    # 常規知識輸出
    fact = random.choice(facts)
    await interaction.followup.send(embed=discord.Embed(description=fact, color=0xff69b4))
    
    # 4. 更新統計與成就 (非同步執行，不影響發送)
    await db.execute(
        "INSERT INTO user_logs (user_id, action, count) VALUES (?, 'know_count', 1) ON CONFLICT(user_id) DO UPDATE SET count = count + 1", 
        (user_id,)
    )
    row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'know_count'", (user_id,))
    
    if row:
        count = row[0]
        if count >= 50:
            await check_and_notify_achievement(interaction, "KNOWLEDGE_ADDICT", ACHIEVEMENTS["KNOWLEDGE_ADDICT"])
        elif count >= 15:
            await check_and_notify_achievement(interaction, "KNOWLEDGE_SPONGE", ACHIEVEMENTS["KNOWLEDGE_SPONGE"])
        elif count >= 5:
            await check_and_notify_achievement(interaction, "NOVICE_TRASH", ACHIEVEMENTS["NOVICE_TRASH"])

THEMES = {
    "水果": ["🍎", "🍊", "🍇", "🍓", "🍒", "🍑", "🍍", "🥝", "🥥", "🥑", "🍆", "🥦"],
    "亂碼": ["#", "%", "@", "&", "*", "?", "!", "$", "+", "=", "/", "~"],
    "數字": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "A", "B"]
}

class MemoryButton(discord.ui.Button):
    def __init__(self, index, view):
        # 使用白色方塊作為卡片背面，明確區分未翻開狀態
        super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=index // 4)
        self.index = index
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.locked or self.view_ref.revealed[self.index]:
            return

        self.view_ref.revealed[self.index] = True
        self.label = self.view_ref.cards[self.index]
        self.disabled = True
        
        if self.view_ref.first_card is None:
            self.view_ref.first_card = self
            await interaction.response.edit_message(view=self.view_ref)
        else:
            self.view_ref.second_card = self
            self.view_ref.locked = True
            await interaction.response.edit_message(view=self.view_ref)
            await self.view_ref.check_match(interaction)

class GameMemoryView(discord.ui.View):
    def __init__(self, difficulty, theme):
        super().__init__(timeout=120)
        self.pairs = {"簡單": 4, "普通": 6, "困難": 8}[difficulty]
        self.cards = THEMES[theme][:self.pairs] * 2
        random.shuffle(self.cards)
        self.revealed = [False] * (self.pairs * 2)
        self.first_card = None
        self.second_card = None
        self.locked = False
        
        for i in range(len(self.cards)):
            self.add_item(MemoryButton(i, self))

    async def check_match(self, interaction: discord.Interaction):
        await asyncio.sleep(1)
        if self.first_card.label == self.second_card.label:
            # 配對成功，變綠色
            self.first_card.style = discord.ButtonStyle.success
            self.second_card.style = discord.ButtonStyle.success
        else:
            # 配對失敗，恢復為背面方塊
            self.first_card.label = "⬜"
            self.first_card.disabled = False
            self.second_card.label = "⬜"
            self.second_card.disabled = False
            self.revealed[self.first_card.index] = False
            self.revealed[self.second_card.index] = False
        
        self.first_card = None
        self.second_card = None
        self.locked = False
        await interaction.edit_original_response(view=self)

@bot.tree.command(name="game_記憶遊戲", description="測試你的記憶力喵！")
@app_commands.choices(
    難度=[app_commands.Choice(name=n, value=n) for n in ["簡單", "普通", "困難"]],
    主題=[app_commands.Choice(name=t, value=t) for t in ["水果", "亂碼", "數字"]]
)
async def memory_game(interaction: discord.Interaction, 難度: str, 主題: str):
    view = GameMemoryView(難度, 主題)
    embed = discord.Embed(description=f"主題：{主題} | 難度：{難度}\n請開始翻牌喵！", color=0xffc0cb)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="game_bingo", description="與本喵對戰 Bingo！")
@app_commands.describe(size="盤面大小 (3-5)")
async def game_bingo(interaction: discord.Interaction, size: int):
    if not (3 <= size <= 5):
        return await interaction.response.send_message("大小請限制在 3 到 5 之間喵！", ephemeral=True)
    
    desc = f"Bingo 遊戲玩法：\n1. 本喵會為你產生 {size}x{size} 的數字盤面。\n2. 點擊按鈕標記數字，連成一線即可獲勝喵！\n\n準備好了就點擊下方開始吧喵！"
    await interaction.response.send_message(desc, view=StartBingoView(size))

@bot.tree.command(name="bingo_rank", description="查看 Bingo 排行榜喵！")
async def bingo_rank(interaction: discord.Interaction):
    # 撈取數據
    total_rows = await db.fetchall("SELECT user_id, total_wins FROM user_logs WHERE action = 'bingo_win' ORDER BY total_wins DESC LIMIT 5")
    streak_rows = await db.fetchall("SELECT user_id, max_streak FROM user_logs WHERE action = 'bingo_win' ORDER BY max_streak DESC LIMIT 5")
    
    def format_rank(rows, key):
        res = ""
        for i, r in enumerate(rows, 1):
            # 這裡可以使用 guild.get_member 處理名稱
            res += f"{i}. <@{r['user_id']}>: {r[key]} 次\n"
        return res if res else "目前沒人上榜喵..."

    embed = discord.Embed(title="🏆 Bingo 雙榜榮譽", color=0xffd700)
    embed.add_field(name="👑 總勝場王", value=format_rank(total_rows, 'total_wins'), inline=True)
    embed.add_field(name="🔥 最高連勝紀錄", value=format_rank(streak_rows, 'max_streak'), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="36計", description="讓本喵告訴你今天該用哪一計")
async def strategy_36(interaction: discord.Interaction):
    strategies = {
        "瞞天過海": "小聰明，騙得過別人騙不過本喵喵。",
        "圍魏救趙": "搞這些花招，直接正面對決不行嗎？",
        "借刀殺人": "這招很陰險耶，不愧是雜魚的風格。",
        "以逸待勞": "說穿了就是懶吧？你這隻懶貓。",
        "趁火打劫": "趁機佔便宜，你的良心去哪了？",
        "聲東擊西": "別以為本喵看不出你的小把戲。",
        "無中生有": "這不是謊話連篇嗎？雜魚！",
        "暗渡陳倉": "偷偷摸摸的，果然是雜魚的日常。",
        "隔岸觀火": "你這傢伙就只會看戲是吧？",
        "笑裡藏刀": "本喵會盯著你的，別想亂來。",
        "李代桃僵": "為了自己犧牲別人，哼。",
        "順手牽羊": "看到什麼就想偷，手腳很不乾淨喔。",
        "打草驚蛇": "笨手笨腳的，還沒開始就先暴露了。",
        "借屍還魂": "舊瓶裝新酒，一點創意都沒有。",
        "調虎離山": "你想把誰調走？本喵可不吃這套。",
        "欲擒故縱": "這招對本喵沒用，放棄吧。",
        "拋磚引玉": "你丟出來的磚頭...大概只能砸到腳吧。",
        "擒賊擒王": "想搞事情？先問問本喵答不答應。",
        "釜底抽薪": "這招夠狠，果然夠雜魚。",
        "混水摸魚": "你整天都在混水摸魚吧？以為我不知道？",
        "金蟬脫殼": "想逃跑？門都沒有！",
        "關門捉賊": "本喵把你關起來，看你往哪跑。",
        "遠交近攻": "還搞外交呢？先處理好你身邊的雜魚關係吧。",
        "假道伐虢": "這招最陰險了，本喵才不會上當。",
        "偷樑換柱": "你以為換個皮本喵就認不出來嗎？",
        "指桑罵槐": "有膽子就直接說啊，別在那邊陰陽怪氣。",
        "假痴不癲": "裝傻是吧？這可是你的專長。",
        "上屋抽梯": "把路封死，真有你的。",
        "樹上開花": "華而不實，看起來厲害而已。",
        "反客為主": "別想奪走本喵的主權！",
        "美人計": "你對本喵用美人計？省省吧，你一點都不美。",
        "空城計": "裡面什麼都沒有吧？空殼子一個。",
        "反間計": "挑撥離間，真沒品。",
        "苦肉計": "演得真爛，本喵連一滴眼淚都沒有。",
        "連環計": "套路這麼深，你累不累啊？",
        "走為上計": "想逃？沒這麼容易！"
    }
    
    choice = random.choice(list(strategies.keys()))
    comment = strategies[choice]
    
    embed = discord.Embed(
        title="📜 今日錦囊妙計",
        description=f"抽到的計謀：**{choice}**\n\n小貓娘吐槽：{comment}", 
        color=0xffd700
    )
    await interaction.response.send_message(embed=embed)
    
    if choice == "走為上計":
        await check_and_notify_achievement(interaction, "RUN_AWAY", ACHIEVEMENTS["RUN_AWAY"])

@bot.tree.command(name="餵食", description="餵食本喵或是其他人")
@app_commands.choices(food=[
    app_commands.Choice(name="貓草", value="貓草"),
    app_commands.Choice(name="貓薄荷", value="貓薄荷"),
    app_commands.Choice(name="小貓貓餅乾", value="小貓貓餅乾"),
    app_commands.Choice(name="雜魚", value="雜魚"),
    app_commands.Choice(name="小魚乾", value="小魚乾"),
    app_commands.Choice(name="牛奶", value="牛奶"),
    app_commands.Choice(name="過期罐頭", value="過期罐頭"),
    app_commands.Choice(name="廢紙團", value="廢紙團")
])
async def feed(interaction: discord.Interaction, food: str, target: discord.Member):
    await interaction.response.defer()
    
    # 定義基本評價
    comments = {
        "貓草": "感覺身體變輕盈了喵，呼嚕呼嚕~", 
        "貓薄荷": "這、這是天堂的味道喵！(暈)", 
        "小貓貓餅乾": "脆脆的口感，好喜歡喵！", 
        "小魚乾": "最棒的獎勵了，本喵會記得妳的好的喵！", 
        "牛奶": "香醇濃郁，本喵喝得好開心喵！"
    }
    
    # 定義垃圾類反應
    trash_responses = [
        "你塞了個過期的罐頭給我，這是要毒死本喵嗎？喵！",
        "這看起來像廢紙團...不過勉強能吃飽，謝了喵。",
        "你從哪撿來的這些垃圾？真是的，放著吧喵。",
        "這種東西你也敢拿來餵？算了，本喵今天心情好，不跟你計較喵。",
        "嗚...又是這種垃圾，你就不能餵點像樣的嗎？喵！",
        "雜魚？你是在羞辱本喵的品味嗎？喵！"
    ]

    # 判定餵食對象與內容
    is_trash = food in ["雜魚", "過期罐頭", "廢紙團"]
    
    if target.id == bot.user.id:
        # 對本喵餵食
        if is_trash:
            response = random.choice(trash_responses)
        else:
            response = comments.get(food, "看起來很好吃喵！")
        embed = discord.Embed(description=f"{interaction.user.mention} 餵了本喵吃 {food}！", color=0xffc0cb)
        embed.add_field(name="本喵評價:", value=response)
    else:
        # 對其他人餵食
        embed = discord.Embed(description=f"{interaction.user.mention} 餵了 {target.mention} 吃 {food}！", color=0x87ceeb)
        embed.set_footer(text=f"評價: {comments.get(food, '這看起來很有趣喵！')}")

    # 成就處理
    messages_to_send = []
    try:
        if is_trash:
            await db.execute("INSERT INTO user_logs (user_id, action, count) VALUES (?, 'feed_trash', 1) ON CONFLICT(user_id, action) DO UPDATE SET count = count + 1", (interaction.user.id, 'feed_trash'))
            row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'feed_trash'", (interaction.user.id,))
            new_count = row[0]['count'] if row else 1
            
            if new_count >= 5 and await unlock_achievement(interaction.user.id, "TRASH_COLLECTOR"):
                messages_to_send.append(f"🏆 {ACHIEVEMENTS['TRASH_COLLECTOR']}")
        
        if await unlock_achievement(interaction.user.id, "FIRST_INTERACTION"):
            messages_to_send.append(f"🏆 {ACHIEVEMENTS['FIRST_INTERACTION']}")
    except Exception as e:
        print(f"餵食成就處理錯誤: {e}")

    await interaction.followup.send(embed=embed)
    for msg in messages_to_send:
        await interaction.followup.send(msg)

@bot.tree.command(name="喵喵喵", description="讓本喵喵喵喵給你聽(1小時限制3次)")
@app_commands.describe(count="要喵幾聲(1000字以下)")
async def meow_meow(interaction: discord.Interaction, count: int):
    user_id = interaction.user.id
    now = datetime.now().timestamp()
    
    # 1. 1小時限制邏輯 (3次)
    history = usage_history.get(user_id, [])
    history = [t for t in history if now - t < 3600]
    
    if len(history) >= 3:
        return await interaction.response.send_message("喵！本喵喉嚨休息中，一小時只能喵 3 次，等等再來吧喵！", ephemeral=True)
    
    # 2. 字數限制
    if count > 1000:
        return await interaction.response.send_message("太多了！本喵喉嚨會痛喵！上限是 1000 聲喵！", ephemeral=True)
    
    # 3. 更新紀錄
    history.append(now)
    usage_history[user_id] = history
    
    # 4. 發送訊息
    await interaction.response.send_message("喵" * count)
    
    # 5. 成就觸發
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
    
    if count >= 1000:
        await check_and_notify_achievement(interaction, "MEOW_KING", ACHIEVEMENTS["MEOW_KING"])
    elif count >= 500:
        await check_and_notify_achievement(interaction, "MEOW_ADDICT", ACHIEVEMENTS["MEOW_ADDICT"])
    elif count >= 100:
        await check_and_notify_achievement(interaction, "MEOW_NOVICE", ACHIEVEMENTS["MEOW_NOVICE"])
    elif count < 5:
        await check_and_notify_achievement(interaction, "MEOW_TOO_LITTLE", ACHIEVEMENTS["MEOW_TOO_LITTLE"])

# 1. 設定生日指令
@bot.tree.command(name="設定生日", description="設定你的生日 (年/月/日)")
@app_commands.describe(year="出生年份", month="月份", day="日期", 是否公開="是否要公開顯示在群組")
async def set_birthday(interaction: discord.Interaction, year: int, month: int, day: int, 是否公開: bool):
    if not is_valid_date(year, month, day):
        return await interaction.response.send_message("喵？這日期不存在喵！請檢查年份或日期。", ephemeral=True)

    birthday_str = f"{year:04d}{month:02d}{day:02d}"
    privacy_val = 1 if 是否公開 else 0
    
    await db.execute(
        "INSERT OR REPLACE INTO user_birthdays (user_id, birthday, privacy) VALUES (?, ?, ?)",
        (interaction.user.id, birthday_str, privacy_val)
    )
    
    # 移除 Embed 標題與表情，保持簡潔
    await interaction.response.send_message(f"記住囉，你的生日是 {year} 年 {month} 月 {day} 日喵！", ephemeral=True)
    
    # 觸發成就
    await check_and_notify_achievement(interaction, "BIRTHDAY_SET", ACHIEVEMENTS["BIRTHDAY_SET"])

# 2. 生日倒數指令
@bot.tree.command(name="生日倒數", description="查看距離下一個生日還有幾天")
@app_commands.describe(是否公開="是否僅自己可見 (若選 No，則僅你自己可見)")
async def birthday_countdown(interaction: discord.Interaction, 是否公開: bool = False):
    bday_data = await db.fetch("SELECT birthday FROM user_birthdays WHERE user_id = ?", (interaction.user.id,))
    if not bday_data:
        embed = discord.Embed(description="❌ 你還沒設定過生日喵！", color=discord.Color.pink())
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    bday_str = bday_data[0]
    b_month, b_day = int(bday_str[4:6]), int(bday_str[6:8])
    
    today = datetime.datetime.now()
    target_year = today.year
    
    # 閏年生日平年處理
    if b_month == 2 and b_day == 29:
        is_leap = (target_year % 4 == 0 and target_year % 100 != 0) or (target_year % 400 == 0)
        if not is_leap: b_month, b_day = 2, 28
            
    next_bday = datetime.datetime(target_year, b_month, b_day)
    if next_bday < today:
        next_bday = datetime.datetime(target_year + 1, b_month, b_day)
        
    days_left = (next_bday - today).days
    # ephemeral 為 True 代表僅自己可見，這裡用 not 是否公開 來對應
    embed = discord.Embed(description=f"⏳ 距離你的下一個生日還有 {days_left} 天喵！", color=discord.Color.pink())
    await interaction.response.send_message(embed=embed, ephemeral=not 是否公開)

# 生日隱私權設定
@bot.tree.command(name="生日隱私權", description="設定你的生日公開或隱私")
@app_commands.describe(是否公開="選擇 Yes 公開，No 則隱私")
async def set_birthday_privacy(interaction: discord.Interaction, 是否公開: bool):
    await db.execute("UPDATE user_birthdays SET privacy = ? WHERE user_id = ?", (1 if 是否公開 else 0, interaction.user.id))
    status = "公開" if 是否公開 else "隱私"
    embed = discord.Embed(description=f"✅ 生日隱私設定已變更為：{status}喵！", color=discord.Color.pink())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="查看機器人延遲")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    # 建立一個簡單的 embed 物件
    embed = discord.Embed(description=f"目前的延遲是：**{latency}ms** 喵！", color=discord.Color.pink())
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="狀態監測", description="查看機器人當前系統狀態")
async def status_slash(interaction: discord.Interaction):
    s = get_system_stats()
    embed = discord.Embed(title="系統狀態", description=f"CPU: {s['cpu']}% | 記憶體: {s['mem_usage']}% ({s['mem_used']}GB/{s['mem_total']}GB)", color=0xffc0cb)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="關鍵詞檢測", description="切換關鍵詞檢測開關狀態，需管理員/開發者")
@app_commands.choices(參數=[app_commands.Choice(name="ON", value="ON"), app_commands.Choice(name="OFF", value="OFF")])
@admin_or_dev_only
async def keyword_toggle(interaction: discord.Interaction, 參數: app_commands.Choice[str]):
    global is_keyword_enabled
    mode = 參數.value
    embed = discord.Embed(color=0xffc0cb)
    
    if mode == "ON":
        if is_keyword_enabled:
            embed.description = "⚠️ 你重複了喵！關鍵詞檢測已經是開啟狀態了喵！"
        else:
            is_keyword_enabled = True
            embed.description = "🟢 喵！關鍵詞檢測已開啟！"
            
    elif mode == "OFF":
        if not is_keyword_enabled:
            embed.description = "⚠️ 你重複了喵！關鍵詞檢測已經是關閉狀態了喵！"
        else:   
            is_keyword_enabled = False
            embed.description = "🔴 喵！關鍵詞檢測已關閉！"
            
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="貓娘指數", description="測測看妳有多像小貓娘")
@app_commands.describe(目標="要檢測的對象")
async def catgirl_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"本喵覺得 {t.mention} 的貓娘指數是 **{random.randint(0, 100)}%** 喵！(,,・ω・,,)", 0xffc0cb))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="隨機指數", description="隨機測一個指數")
async def random_index(interaction: discord.Interaction):
    t = interaction.user
    choice = random.choice(["貓娘指數", "男娘指數", "男同指數", "共產指數", "ㄌㄌ指數", "雜魚指數", "傲嬌指數", "可愛指數"])
    await interaction.response.send_message(embed=create_index_embed(t, f"本喵幫妳測了一下，妳的{choice}是 **{random.randint(0, 100)}%** 喵！", 0xffc0cb))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="男娘指數", description="檢測男娘機率")
@app_commands.describe(目標="要檢測的對象")
async def femboy_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    if t.id == bot.user.id: desc = "喵！本喵絕對是男娘的喵！"
    elif t.id == DEVELOPER_ID: desc = "喵！milk120106 絕對不可能是男娘喵！"
    elif t.id == TARGET_USER_1: desc = f"喵！{t.mention} 是星音群主養的發情男貓娘雌墮雌小鬼雜魚小貓貓！"
    else: desc = f"喵！{t.mention} 的男娘機率是 **{random.randint(1, 100)}%**！"
    
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0xffc0cb))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
    if t.id == bot.user.id: await check_and_notify_achievement(interaction, "DISCOVER_SECRET", "發現秘密：你竟然敢調戲本喵！")

@bot.tree.command(name="雜魚指數", description="檢測雜魚機率")
@app_commands.describe(目標="要檢測的對象")
async def trash_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的雜魚機率是 **{random.randint(1, 100)}%**！雜魚~雜魚~", 0x808080))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="傲嬌指數", description="檢測傲嬌機率")
@app_commands.describe(目標="要檢測的對象")
async def tsundere_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的傲嬌機率是 **{random.randint(1, 100)}%**！才、才沒有喜歡你呢！", 0xff4500))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="可愛指數", description="檢測可愛機率")
@app_commands.describe(目標="要檢測的對象")
async def cute_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的可愛機率是 **{random.randint(1, 100)}%**！超級可愛的喵！", 0xff69b4))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="男同指數", description="檢測男同機率")
@app_commands.describe(目標="要檢測的對象")
async def gay_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    desc = f"喵？{t.mention} 的性向是異性戀！絕對不可能是男同的喵！" if t.id == DEVELOPER_ID else f"喵！{t.mention} 的男同機率是 **{random.randint(1, 100)}%**！"
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0x87cefa))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="共產指數", description="檢測共產機率")
@app_commands.describe(目標="要檢測的對象")
async def communist_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的共產機率是 **{random.randint(1, 100)}%**！", 0xff0000))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.tree.command(name="ㄌㄌ指數", description="檢測ㄌㄌ機率")
@app_commands.describe(目標="要檢測的對象")
async def loli_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    desc = f"喵？{t.mention} 是男的！怎麼可能是ㄌㄌ！" if t.id == DEVELOPER_ID else f"喵！{t.mention} 的ㄌㄌ機率是 **{random.randint(1, 100)}%**！"
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0xff69b4))
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

from datetime import datetime

@bot.tree.command(name="求籤", description="抽取運勢並由雜魚小貓娘為你解析")
async def draw_fortune_slash(interaction: discord.Interaction):
    fortunes = {
        "超大吉": "喵！你是被幸運女神眷顧的孩子！今天做什麼都會成功的！",
        "大吉": "很棒喔！今天心情會很好，適合做點挑戰！",
        "中吉": "還不錯喵，平平淡淡才是真，要保持愉快的心情喔！",
        "小吉": "稍微注意一下細節，會過得很順利的！",
        "末吉": "有點小波折，但只要冷靜處理，雜魚小貓娘會保佑你的！",
        "凶": "今天運氣不太好，建議不要做太冒險的事，乖乖待著喵...",
        "大凶": "這...這是超級罕見的倒霉！今天別出門了，快點抱著雜魚小貓娘祈福吧！"
    }
    
    result = random.choice(list(fortunes.keys()))
    current_hour = datetime.now().hour
    is_late_night = 0 <= current_hour < 4
    
    # 深夜回應邏輯
    fortune_text = fortunes[result]
    if is_late_night:
        fortune_text = f"這麼晚了還沒睡嗎？雜魚熬夜鬼...不過看在你這麼努力的份上，{fortune_text}"
    
    embed = discord.Embed(
        description=f"你抽到了：**{result}**\n\n小貓娘解析：\n{fortune_text}", 
        color=0xffc0cb
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)
    
    # 觸發成就
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
    
    if result == "超大吉":
        await check_and_notify_achievement(interaction, "LUCKY_STAR", ACHIEVEMENTS["LUCKY_STAR"])
        
    if is_late_night:
        await check_and_notify_achievement(interaction, "MIDNIGHT_TRASH", ACHIEVEMENTS["MIDNIGHT_TRASH"])

class RPSView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def play_rps(self, interaction: discord.Interaction, user_choice: str):
        bot_choice = random.choice(["剪刀", "石頭", "布"])
        choices = {"剪刀": "✂️", "石頭": "🪨", "布": "📄"}
        
        # 判定輸贏
        if user_choice == bot_choice:
            res_text = "平手喵？嘖，沒意思，再一局喵！"
            res_status = "tie"
        elif (user_choice=="石頭" and bot_choice=="剪刀") or (user_choice=="剪刀" and bot_choice=="布") or (user_choice=="布" and bot_choice=="石頭"):
            res_text = "哼，這次算你運氣好，別太得意喵！"
            res_status = "win"
        else:
            res_text = "本喵贏了！哈哈雜魚，連猜拳都贏不了我喵！"
            res_status = "loss"

        embed = discord.Embed(
            description=f"你出了 {choices[user_choice]}，本喵出了 {choices[bot_choice]}。\n結果：{res_text}",
            color=0xffc0cb
        )
        await interaction.response.edit_message(embed=embed, view=None)
        
        # 這裡加入你原本的成就與資料庫邏輯 (與上方 rps_loss 處理邏輯一致)

    @discord.ui.button(label="剪刀", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "剪刀")

    @discord.ui.button(label="石頭", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "石頭")

    @discord.ui.button(label="布", emoji="📄", style=discord.ButtonStyle.secondary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play_rps(interaction, "布")

@bot.tree.command(name="猜拳", description="和雜魚小貓娘玩猜拳")
async def rps_game(interaction: discord.Interaction):
    view = RPSView(interaction.user)
    embed = discord.Embed(description="請選擇你要出的拳喵！", color=0xffc0cb)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="尋找色色群主", description="呼叫群主")
async def find_owner_slash(interaction: discord.Interaction):
    # 1. 發送呼叫訊息
    embed = discord.Embed(
        description=f"📢 喵！正在尋找色色的星音群主 <@{TARGET_USER_2}>，快出來喵！", 
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed)
    
    # 2. 觸發基礎成就
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
    
    # 3. 新增成就邏輯：尋找色色群主專屬成就
    # 使用 30% 機率觸發，增加互動樂趣
    if random.random() < 0.3:
        await check_and_notify_achievement(interaction, "LEWD_DETECTIVE", "色色偵探：你挖掘到了群主的隱藏屬性！")

@bot.tree.command(name="祈福", description="讓雜魚小貓娘為你進行專屬祈福")
async def pray_slash(interaction: discord.Interaction, 目標: discord.Member = None):
    await interaction.response.defer()
    
    target = 目標 or interaction.user
    now = datetime.now()
    user_id = interaction.user.id
    
    # 1. 決定祈福內容
    is_midnight = 2 <= now.hour <= 4
    if is_midnight:
        blessing = "喵...現在是深夜，本喵給你一份特別的深夜庇護，願你睡個好覺喵。"
    else:
        blessings = [
            "祝你今天運勢滿滿，所有困難都像雜魚一樣不堪一擊！",
            "本喵賦予你貓貓庇護，霉運退散，好運快快來！",
            "這是一份來自雜魚小貓娘的祝福，請查收喵！",
            "喵嗚！願你的心情像本喵一樣愉悅，今天也要加油喔！"
        ]
        blessing = random.choice(blessings)
        
    # 2. 優先發送主訊息
    embed = discord.Embed(description=f"{target.mention}，{blessing}", color=0xffc0cb)
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.followup.send(embed=embed)
    
    # 3. 安全更新資料庫 (修正導致程式崩潰的語法)
    row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'pray_count'", (user_id,))
    count = (row[0] + 1) if row else 1
    
    if row:
        await db.execute("UPDATE user_logs SET count = ? WHERE user_id = ? AND action = 'pray_count'", (count, user_id))
    else:
        await db.execute("INSERT INTO user_logs (user_id, action, count) VALUES (?, 'pray_count', 1)", (user_id,))
        
    # 4. 最後判定成就
    if is_midnight:
        await check_and_notify_achievement(interaction, "MIDNIGHT_PRAYER", ACHIEVEMENTS["MIDNIGHT_PRAYER"])
    if count == 10:
        await check_and_notify_achievement(interaction, "CAT_BLESSING", ACHIEVEMENTS["CAT_BLESSING"])

@bot.tree.command(name="看雜魚小貓娘", description="查看本喵的美圖")
async def show_catgirl(interaction: discord.Interaction):
    user_id = interaction.user.id
    try:
        # 1. 記錄查看次數
        await db.execute("INSERT INTO user_logs (user_id, action, count) VALUES (?, 'view_photo', 1) ON CONFLICT(user_id) DO UPDATE SET count = count + 1", (user_id,))
        row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'view_photo'", (user_id,))
        
        # 2. 發送圖片
        file = discord.File(CATGIRL_IMAGE_PATH, filename="catgirl.png")
        await interaction.response.send_message("喵～這是我的珍藏美圖，不准隨便亂傳喔！", file=file)
        
        # 3. 觸發成就
        await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
        
        count = row[0] if row else 0
        if count >= 10:
            await check_and_notify_achievement(interaction, "CATGIRL_COLLECTOR", ACHIEVEMENTS["CATGIRL_COLLECTOR"])
            
    except Exception as e:
        await interaction.response.send_message("喵嗚...找不到圖片，可能路徑有問題喵！")

class JumpModal(discord.ui.Modal, title="跳轉頁面"):
    def __init__(self, view):
        super().__init__()
        self.view = view

    page = discord.ui.TextInput(label="輸入頁碼", placeholder="例如: 1", min_length=1, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target = int(self.page.value) - 1
            if 0 <= target < len(self.view.image_list):
                self.view.index = target
                await self.view.update_view(interaction)
            else:
                # 這裡使用 ephemeral 訊息提醒用戶
                await interaction.response.send_message("❌ 頁碼超出範圍！", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ 請輸入有效的阿拉伯數字！", ephemeral=True)

class ImageView(discord.ui.View):
    def __init__(self, image_list):
        super().__init__(timeout=None)
        self.image_list = image_list
        self.index = 0

    async def update_view(self, interaction: discord.Interaction):
        embed = discord.Embed(title="逆天圖片 檢視", color=0xffc0cb)
        embed.set_image(url=self.image_list[self.index])
        embed.set_footer(text=f"第 {self.index + 1} 張 / 共 {len(self.image_list)} 張")
        
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"按鈕更新失敗: {e}")

    @discord.ui.button(label="⬅️ 上一張", style=discord.ButtonStyle.primary, custom_id="prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.image_list)
        await self.update_view(interaction)

    @discord.ui.button(label="🔢 跳轉", style=discord.ButtonStyle.secondary, custom_id="jump")
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JumpModal(self))

    @discord.ui.button(label="➡️ 下一張", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.image_list)
        await self.update_view(interaction)

@bot.tree.command(name="逆天圖片", description="檢視逆天圖片")
async def view_quotes(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id
    
    try:
        image_list = load_images()
    except Exception:
        image_list = []
        
    if not image_list:
        return await interaction.followup.send("喵！目前沒有圖片。", ephemeral=True)
        
    # 1. 優先發送主訊息與 UI
    embed = discord.Embed(title="逆天圖片 檢視", color=0xffc0cb)
    embed.set_image(url=image_list[0])
    embed.set_footer(text=f"第 1 張 / 共 {len(image_list)} 張")
    await interaction.followup.send(embed=embed, view=ImageView(image_list))
    
    # 2. 安全更新資料庫 (修正導致程式崩潰的語法)
    row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'view_quotes'", (user_id,))
    count = (row[0] + 1) if row else 1
    
    if row:
        await db.execute("UPDATE user_logs SET count = ? WHERE user_id = ? AND action = 'view_quotes'", (count, user_id))
    else:
        await db.execute("INSERT INTO user_logs (user_id, action, count) VALUES (?, 'view_quotes', 1)", (user_id,))
        
    # 3. 最後判定成就
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
    if count == 15:
        await check_and_notify_achievement(interaction, "GALLERY_MASTER", ACHIEVEMENTS["GALLERY_MASTER"])

@bot.tree.command(name="刪除我的統計", description="選擇要歸零的互動統計數據喵")
@app_commands.choices(項目=[
    app_commands.Choice(name="所有統計 (重置)", value="all"),
    app_commands.Choice(name="餵食垃圾次數", value="feed_trash"),
    app_commands.Choice(name="知識獲取次數", value="know_count"),
    app_commands.Choice(name="Bingo勝場", value="bingo_win")
])
async def reset_my_stats(interaction: discord.Interaction, 項目: str):
    await interaction.response.defer(ephemeral=True)
    
    try:
        if 項目 == "all":
            await db.execute("DELETE FROM user_logs WHERE user_id = ?", (interaction.user.id,))
            msg = "✅ 已清除你所有的互動統計數據，重獲新生了喵！"
        else:
            # 刪除指定 action 的記錄
            await db.execute("DELETE FROM user_logs WHERE user_id = ? AND action = ?", (interaction.user.id, 項目))
            msg = f"✅ 已將你的 {項目} 統計資料歸零喵。"
            
        await db.connection.commit()
        await interaction.followup.send(msg, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"❌ 操作失敗，本喵處理資料時卡住了喵：{e}", ephemeral=True)

class AchievementView(discord.ui.View):
    def __init__(self, user_name, user_avatar, all_data, user_total, total_count):
        super().__init__(timeout=60)
        self.user_name = user_name
        self.user_avatar = user_avatar
        self.all_data = [all_data[i:i + 10] for i in range(0, len(all_items), 10)] # 每頁10個
        self.current_page = 0
        self.user_total = user_total
        self.total_count = total_count

    def get_embed(self):
        embed = discord.Embed(title=f"📜 {self.user_name} 的成就清單", color=0xffff00)
        embed.set_thumbnail(url=self.user_avatar)
        embed.description = f"**收集進度：** {self.user_total} / {self.total_count}\n\n"
        embed.description += "\n".join(self.all_data[self.current_page])
        embed.set_footer(text=f"第 {self.current_page + 1} / {max(1, len(self.all_data))} 頁")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.all_data) - 1, self.current_page + 1)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.tree.command(name="成就", description="查看你的成就清單")
async def view_achievements(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_achievements = await get_my_achievements(interaction.user.id)
    total_achievements = len(ACHIEVEMENTS)
    user_total = len(user_achievements)
    
    embed = discord.Embed(title=f"📜 {interaction.user.display_name} 的成就清單", color=0xffff00)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.description = f"**收集進度：** {user_total} / {total_achievements}\n\n"
    
    if not user_achievements:
        embed.description += "喵...你目前還沒有解鎖任何成就，快去跟本喵互動吧！"
        await interaction.followup.send(embed=embed) # 沒有成就，不加 View
    else:
        # 有成就，整理資料並啟用分頁
        all_items = [f"🔸 {ach}" for ach in user_achievements]
        view = AchievementView(
            interaction.user.display_name, 
            interaction.user.display_avatar.url, 
            all_items, 
            user_total, 
            total_achievements
        )
        await interaction.followup.send(embed=view.get_embed(), view=view)

class AchievementView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = 0

    def get_embed(self):
        embed = discord.Embed(title=f"📜 成就百科 (第 {self.current_page + 1}/{len(self.pages)} 頁)", color=0x9b59b6)
        embed.description = "\n".join(self.pages[self.current_page])
        embed.set_footer(text="提示：點擊 ||黑框|| 可以揭曉隱藏提示喵！")
        return embed

    @discord.ui.button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="下一頁 ➡️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.tree.command(name="成就百科", description="查看本喵給你頒發的成就清單喵！")
async def achievements(interaction: discord.Interaction):
    user_id = interaction.user.id
    rows = await db.fetchall("SELECT achievement_key FROM user_achievements WHERE user_id = ?", (user_id,))
    unlocked_keys = {row['achievement_key'] for row in rows}
    
    # 整理資料
    all_items = []
    for key, desc in ACHIEVEMENTS.items():
        if key in unlocked_keys:
            name = desc.split(":")[0] if ":" in desc else key
            all_items.append(f"✅ **{name}**")
        else:
            all_items.append(f"🔒 ？？？: ||{ACHIEVEMENT_HINTS.get(key, '祕密成就喵')}||")
    
    # 每 10 個成就分一頁
    pages = [all_items[i:i + 10] for i in range(0, len(all_items), 10)]
    
    view = AchievementView(pages)
    await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

@bot.tree.command(name="help", description="顯示功能說明書喵！")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 雜魚小貓娘 | 完整功能說明書", description="本喵專職負責你的娛樂、數據檢測與防禦保護。若有操作問題，請詳閱下方清單喵。", color=0xffc0cb)
    
    embed.add_field(name="🛡️ 防禦與保護指令 (限管)", value=(
        "• **/保護等級 [1-5]**：設定頻道防炸保護強度。\n"
        "• **/關鍵詞檢測 [ON/OFF]**：切換敏感詞攔截系統。\n"
        "• **/重置暱稱**：強制還原本喵的暱稱設定。\n"
        "• **/頂號 [訊息] [T/F] [標記]**：發送伺服器公告廣播。"
    ), inline=False)
    
    embed.add_field(name="🛠️ 實用系統工具", value=(
        "• **/ai [模型] [訊息]**：呼叫深度 AI 進行邏輯對話與分析。\n"
        "• **/翻譯 [文字]**：多國語言即時轉換。\n"
        "• **/狀態監測**：查看伺服器與機器人運行負載。\n"
        "• **/ping**：檢測 API 即時連線延遲。\n"
        "• **/刪除我的統計**：選擇並清除你的互動統計數據。"
    ), inline=False)
    
    embed.add_field(name="🎮 娛樂與互動遊戲", value=(
        "• **/game_2048**：開始一場 2048 益智遊戲。\n"
        "• **/game_memory**：開啟記憶翻牌挑戰。\n"
        "• **/game_bingo [大小]**：發起 3x3 或 5x5 賓果對戰。\n"
        "• **/bingo_rank**：查看總勝場與最高連勝的雙榜榮耀。\n"
        "• **/你知道嗎**：隨機掉落本喵的逆天冷知識。\n"
        "• **/小提示**：獲取本喵隨機提供的操作小技巧或廢話。\n"
        "• **/餵食**：給本喵一點貢品。\n"
        "• **/猜拳**：跟本喵一決高下。\n"
        "• **/求籤/祈福 [目標]**：每日運勢鑑定與專屬祈福。\n"
        "• **/36計**：讓本喵告訴你今天該用哪一計。\n"
        "• **/尋找色色群主**：呼叫色色的星音群主。\n"
        "• **/看雜魚小貓娘/逆天圖片**：開啟本喵私藏圖庫。"
    ), inline=False)
    
    embed.add_field(name="📊 數值檢測系統", value=(
        "• **/貓娘/男娘/男同指數**：鑑定目標的屬性數值喵。\n"
        "• **/雜魚/傲嬌/可愛指數**：分析個人特質，純屬娛樂喵。\n"
        "• **/共產/ㄌㄌ/隨機指數**：本喵的特色趣味鑑定喵。"
    ), inline=False)
    
    embed.add_field(name="🎂 生日與成就紀念", value=(
        "• **/成就百科**：查看你解鎖的成就清單與神祕提示喵！(試著挖掘隱藏關鍵詞來解鎖成就吧喵！)\n"
        "• **/生日設定/隱私權/倒數**：紀錄你的生日，本喵會給驚喜。"
    ), inline=False)
    
    embed.add_field(name="⚡ 自動觸發系統 (隱藏彩蛋)", value=(
        "• 包含多種關鍵詞互動（如：色色、刀、男娘等）。\n"
        "• 觸發特定關鍵詞可獲得隱藏成就與特殊回覆喵！"
    ), inline=False)
    
    embed.set_footer(text=f"💡 {random.choice(TIPS)} | 最後更新: 2026-06-13")
    await interaction.response.send_message(embed=embed)

# 防護等級變數
PROTECT_LEVEL = 1  
PROTECT_LEVEL_DESC = {
    1: "監控：僅記錄異常",
    2: "攔截：刪除訊息並禁言1小時",
    3: "防禦：刪除訊息並禁言3天",
    4: "壓制：踢出伺服器",
    5: "肅清：封鎖用戶"
}

@bot.tree.command(name="保護等級", description="[限管] 設定機器人防護等級")
@app_commands.describe(等級="1-5")
@admin_or_dev_only
async def set_protect_level(interaction: discord.Interaction, 等級: int):
    global PROTECT_LEVEL
    if 1 <= 等級 <= 5:
        PROTECT_LEVEL = 等級
        await interaction.response.send_message(f"✅ 喵！保護等級已調整為 {等級}: {PROTECT_LEVEL_DESC[等級]}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 喵！等級只能在 1 到 5 之間！", ephemeral=True)

@bot.tree.command(name="翻譯", description="翻譯文字")
@app_commands.describe(
    text="內容", 
    target="目標語言 (預設 zh-TW)", 
    source="原文語言 (預設 auto)", 
    service="服務 (預設 google)"
)
async def translate_slash(interaction: discord.Interaction, text: str, target: str = "zh-TW", source: str = "auto", service: str = "google"):
    await translate_command_logic(interaction, text, target, source, service)

@bot.tree.command(name="ai", description="向 AI 提問")
@app_commands.describe(
    model="選擇 AI 模型",
    prompt="輸入你想問的內容"
)
@app_commands.choices(
    model=MODEL_CHOICES
)
async def ai_slash(interaction: discord.Interaction, model: str, prompt: str):
    await interaction.response.defer()
    await get_ai_response(interaction, prompt, model)

@bot.tree.command(name="ai_reset", description="清除 AI 對話記憶")
async def ai_reset(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in memory_storage:
        memory_storage[user_id] = {"ai_messages": [], "dc_messages": []}
        await interaction.response.send_message("✅ AI 記憶已重置！", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 你目前沒有進行中的對話。", ephemeral=True)

@bot.tree.command(name="dsize", description="檢測你的那個大小喵")
@app_commands.describe(目標="要檢測的對象")
async def dsize(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    
    # 隨機數值
    length = random.randint(1, 50)
    width = random.randint(1, 10)
    
    # 建立視覺化長度 (每 2 公分一個 "=")
    visual_bar = "=" * (length // 2)
    
    # 顯示的文字敘述
    desc = (
        f"{t.mention} 的尺寸鑑定結果喵：\n\n"
        f"📏 **長度**: {length} cm\n"
        f"🧱 **粗度**: {width} cm\n\n"
        f"視覺化呈現：\n"
        f"8{visual_bar}D"
    )
    
    embed = discord.Embed(description=desc, color=0xffc0cb)
    await interaction.response.send_message(embed=embed)
    
    # 成就檢查
    if length >= 45:
        await check_and_notify_achievement(interaction, "GIANT_SIZE", "巨大化：這簡直是逆天的尺寸喵！")
    elif length <= 5:
        await check_and_notify_achievement(interaction, "MINI_SIZE", "袖珍型：...喵？沒看到喵？")

# EQ 指令
@bot.tree.command(name="eq", description="鑑定情緒商數喵！")
@app_commands.describe(目標="要鑑定的對象")
async def eq(interaction: discord.Interaction, 目標: discord.Member = None):
    target = 目標 or interaction.user
    score = random.randint(0, 180)
    
    # 針對 EQ 的吐槽邏輯
    if score < 60: comment = "你的情緒控制是災難等級的吧喵？"
    elif score < 120: comment = "勉強能正常社交，雜魚合格喵。"
    else: comment = "過於理性，看來是個冷血的雜魚呢喵。"
    
    embed = discord.Embed(title="情緒商數鑑定", color=0xff69b4)
    embed.description = f"{target.mention} 的 EQ 為：**{score}**\n{comment}"
    await interaction.response.send_message(embed=embed)

# IQ 指令
@bot.tree.command(name="iq", description="鑑定智商數值喵！")
@app_commands.describe(目標="要鑑定的對象")
async def iq(interaction: discord.Interaction, 目標: discord.Member = None):
    target = 目標 or interaction.user
    score = random.randint(0, 180)
    
    # 針對 IQ 的吐槽邏輯
    if score < 60: comment = "這智商，大概只剩基礎的呼吸功能了吧喵。"
    elif score < 120: comment = "普通的智商，也就是個路人雜魚喵。"
    else: comment = "這麼高分...該不會是為了魔改歷史而生的瘋子吧喵？"
    
    embed = discord.Embed(title="智商數值鑑定", color=0x4169e1)
    embed.description = f"{target.mention} 的 IQ 為：**{score}**\n{comment}"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="本喵要玩玩具", description="拿玩具出來逗本喵喵！")
@app_commands.choices(玩具=[
    app_commands.Choice(name="逗貓棒", value="逗貓棒"),
    app_commands.Choice(name="OO玩具", value="OO玩具"),
    app_commands.Choice(name="羽毛", value="羽毛"),
    app_commands.Choice(name="釣竿", value="釣竿"),
    app_commands.Choice(name="貓抓板", value="貓抓板"),
    app_commands.Choice(name="貓薄荷玩偶", value="貓薄荷玩偶"),
    app_commands.Choice(name="貓草球", value="貓草球")
])
async def play_toy(interaction: discord.Interaction, 玩具: app_commands.Choice[str]):
    toy_name = 玩具.value
    
    # 針對不同玩具的特殊反應
    responses = {
        "逗貓棒": "你揮著逗貓棒...本喵的眼睛跟著動了！這、這是本能反應，才不是想玩呢喵！",
        "OO玩具": "你...你這變態雜魚！拿這種東西出來，是想對本喵做什麼壞事嗎喵！(臉紅)",
        "羽毛": "輕飄飄的羽毛...本喵抓！看我的貓貓拳！...啊，被你看到了，真丟臉喵。",
        "釣竿": "你想釣本喵嗎？哼，太天真了，釣竿的誘惑力對本喵來說還差得遠呢喵！",
        "貓抓板": "磨爪子...呼，舒爽。你要一起來抓抓看嗎？...才不准你搶走呢喵！",
        "貓薄荷玩偶": "好香的味道...頭好暈，好舒服...這、這玩偶有毒！你是故意的吧喵？",
        "貓草球": "滾來滾去的...好玩！...咳咳，別以為一顆球就能收買本喵，但我還是會陪你玩的喵。"
    }
    
    embed = discord.Embed(
        description=responses.get(toy_name, f"你拿著「{toy_name}」...這是什麼新花樣嗎？本喵姑且看一下好了喵。"),
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed)

# 堵住嘴巴
@bot.tree.command(name="堵住嘴巴", description="強制讓目標閉嘴喵！")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute_user(interaction: discord.Interaction, 目標: discord.Member, 時間: int, 單位: str):
    units = {'s': 1, 'min': 60, 'hr': 3600, 'day': 86400, 'week': 604800}
    if 單位 not in units:
        await interaction.response.send_message("單位錯誤喵！", ephemeral=True)
        return
    await 目標.timeout(datetime.timedelta(seconds=時間 * units[單位]))
    embed = discord.Embed(description=f"🤐 {目標.mention} 被堵住嘴巴 {時間}{單位} 喵！", color=0xff0000)
    await interaction.response.send_message(embed=embed)

# 解除禁言
@bot.tree.command(name="解除禁言", description="解除目標的禁言狀態喵！")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute_user(interaction: discord.Interaction, 目標: discord.Member):
    await 目標.timeout(None)
    embed = discord.Embed(description=f"✨ {目標.mention} 的嘴巴解放了喵。", color=0xffff00)
    await interaction.response.send_message(embed=embed)

# 自我禁閉
@bot.tree.command(name="自我禁閉", description="自己把自己關起來反省喵！")
async def self_mute(interaction: discord.Interaction, 時間: int, 單位: str):
    units = {'s': 1, 'min': 60, 'hr': 3600, 'day': 86400}
    if 單位 not in units:
        await interaction.response.send_message("單位錯誤喵！", ephemeral=True)
        return
    await interaction.user.timeout(datetime.timedelta(seconds=min(時間 * units[單位], 86400)))
    embed = discord.Embed(description=f"🔒 {interaction.user.mention} 把自己關起來了，反省去吧喵。", color=0x4169e1)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="重置暱稱", description="[限管] 強制將機器人暱稱重置為空（即顯示原始名稱）")
@admin_or_dev_only
async def reset_bot_nick(interaction: discord.Interaction):
    try:
        # 將機器人自己的暱稱設為 None，Discord 就會恢復顯示原始名稱
        await interaction.guild.me.edit(nick=None)
        await interaction.response.send_message("✅ 喵！機器人暱稱已重置成功！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ 重置失敗：{e}", ephemeral=True)

@bot.tree.command(name="頂號", description="管理員/開發者專用公告指令")
@app_commands.describe(
    訊息="要發送的內容", 
    是否使用嵌入式訊息="T為Embed，F為純文字",
    標記類型="選擇要標記的對象"
)
@app_commands.choices(標記類型=[
    app_commands.Choice(name="無", value="none"),
    app_commands.Choice(name="@everyone", value="everyone"),
    app_commands.Choice(name="@here", value="here")
])
async def broadcast(
    interaction: discord.Interaction, 
    訊息: str, 
    是否使用嵌入式訊息: bool,
    標記類型: app_commands.Choice[str]
):
    # 權限判定：是開發者 OR 是管理員
    is_admin = interaction.user.guild_permissions.administrator
    if interaction.user.id != DEVELOPER_ID and not is_admin:
        return await interaction.response.send_message("你不是管理員或開發者，滾開喵！", ephemeral=True)

    # 處理 Mention 語法
    mention_content = ""
    if 標記類型.value == "everyone":
        mention_content = "@everyone"
    elif 標記類型.value == "here":
        mention_content = "@here"

    # 發送訊息
    author_text = f"\n\n— 由 {interaction.user.display_name} 發送"
    
    if 是否使用嵌入式訊息:
        embed = discord.Embed(title="📢 公告", description=訊息, color=0xffc0cb)
        embed.set_footer(text=f"發送者: {interaction.user.display_name}")
        await interaction.channel.send(content=mention_content, embed=embed)
    else:
        final_msg = f"{mention_content}\n{訊息}{author_text}" if mention_content else f"{訊息}{author_text}"
        await interaction.channel.send(final_msg)

# ==================== 開發者專用指令  ====================

@bot.tree.command(name="關機", description="強制關閉機器人視窗 (限開發者)")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.response.send_message("❌ 該指令僅限開發者使用。", ephemeral=True)
    
    embed = discord.Embed(
        title="系統關機中...",
        description="本喵要下線休息並關閉視窗了，雜魚們再見喵！(,,・ω・,,)🐾",
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)
    
    print("機器人正在強制關閉中...")
    # 強制終止當前進程，這會直接關閉終端機視窗
    os._exit(0)

@bot.tree.command(name="重啟", description="強制重啟機器人 (限開發者)")
async def restart(interaction: discord.Interaction):
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.response.send_message("❌ 該指令僅限開發者使用。", ephemeral=True)
    
    global is_ready
    is_ready = False
    
    embed = discord.Embed(
        title="系統重啟中...",
        description="正在關閉視窗並重啟，請稍候喵... (๑•́ ₃ •̀๑)",
        color=0x87ceeb
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)
    
    # 【核心修正】：獲取當前執行腳本的目錄，確保新視窗在正確位置啟動
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.abspath(__file__)
    
    # 指令改為：進入正確路徑，然後執行 Python
    cmd_command = f"cd /d \"{script_dir}\" && chcp 65001 >nul && {sys.executable} \"{script_path}\""
    
    subprocess.Popen(
        ['wt', 'cmd', '/k', cmd_command],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    os._exit(0)

@bot.tree.command(name="開發者重置統計", description="[開發者專用] 強制重置指定用戶的統計數據")
@app_commands.describe(target="要清除統計數據的目標成員喵")
async def dev_reset_stats(interaction: discord.Interaction, target: discord.User):
    # 權限檢查
    if interaction.user.id != DEVELOPER_ID:
        await interaction.response.send_message("❌ 走開，只有本喵的開發者能用喵！", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    
    try:
        await db.execute("DELETE FROM user_logs WHERE user_id = ?", (target.id,))
        await db.connection.commit()
        await interaction.followup.send(f"✅ 已強制清除 {target.display_name} 的所有互動統計數據喵。", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ 錯誤：{e}", ephemeral=True)

# ==================== 背景任務 ====================

@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id == 1493902370013188221:
        channel = bot.get_channel(1493902370013188221)
        if channel:
            embed = discord.Embed(
                title="✨ 新成員加入喵！",
                description=f"歡迎 {member.mention} 來到這裡喵！希望你不是雜魚喵！",
                color=0x808080
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    if member.guild.id == 1493902370013188221:
        channel = bot.get_channel(1493902370013188221)
        if channel:
            embed = discord.Embed(
                title="👋 成員離開喵...",
                description=f"{member.display_name} 離開了我們喵，真是個無情的傢伙QAQ。",
                color=0x808080
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    # 監聽點擊排行榜按鈕
    if interaction.data.get("custom_id") == "bingo_rank_btn":
        # 這裡會觸發你原本的 bingo_rank 指令函式
        await bingo_rank(interaction)
    
    # 如果有其他互動 (例如原本的 slash command)，交給 tree 去處理
    else:
        await bot.tree.on_interaction(interaction)

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command):
    # 定義不觸發成就的工具/管理指令名稱
    ignored_commands = [
        "ping", 
        "狀態監測", 
        "關鍵詞檢測", 
        "重置暱稱", 
        "刪除資料", 
        "成就", 
        "設定生日", 
        "生日倒數", 
        "生日隱私權"
        "刪除我的計數",
        "刪除統計",
    ]
    
    # 只要不在排除名單內，就觸發初次互動成就
    if command.name not in ignored_commands:
        await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

@bot.event
async def on_shutdown():
    await db.close()

async def start_bot_with_recovery():
    while True:
        try:
            await db.setup()
            print("✅ 資料庫已就緒")
            break # 成功則跳出迴圈
        except Exception as e:
            print(f"\n❌ 資料庫錯誤: {e}")
            print("\n請選擇操作:")
            print("1) 再試一次 (Retry)")
            print("2) 關閉程式 (Exit)")
            choice = input("輸入選項數字: ")
            
            if choice == '2':
                print("程式已關閉。")
                sys.exit()
            else:
                print("正在嘗試重新連線...")
                await asyncio.sleep(2)

async def main():
    # 確保資料庫只初始化一次
    await db.setup()
    
    if not TOKEN:
        print("❌ 錯誤：TOKEN 為空，請檢查 .env 檔案。")
        return
    print(f"🚀 正在嘗試連線至 Discord")
    # 這裡確保指令同步
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程式已由使用者手動停止。")
    finally:
        # 確保關閉資料庫，不要讓檔案鎖死
        asyncio.run(db.close())
