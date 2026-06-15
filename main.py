import time
import io
import re
import os
import sys
import json
import asyncio
import psutil
import discord
import aiosqlite
import sqlite3
import subprocess
import requests
import base64
import time as time_lib
from typing import Union, Optional
from functools import wraps
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from datetime import time as datetime_time

# 第三方套件
from openai import OpenAI
from litellm import acompletion
from dotenv import load_dotenv
from deep_translator import (
    GoogleTranslator, 
    MyMemoryTranslator, 
    LibreTranslator, 
    PonsTranslator, 
    LingueeTranslator
)
from discord import app_commands, ui
from discord.ext import commands, tasks
from PIL import Image

load_dotenv()

# ==================== 基礎設定 ====================
intents = discord.Intents.default()
intents.members = True  # 這是接收成員加入/離開事件的關鍵
intents.message_content = True
intents.message_content = True  # 必須開啟此權限才能讀取訊息內容
bot = commands.Bot(command_prefix="!", intents=intents)
is_keyword_enabled = True
user_message_history = defaultdict(list)
is_ready = False
TOKEN = os.getenv("DISCORD_TOKEN")
# 用於儲存bingo對戰狀態
game_states = {}
usage_history = {} # 在全域宣告

# 定義台北時區
taipei_tz = timezone(timedelta(hours=8))

DEVELOPER_ID = 1317882602392260632
TARGET_USER_1 = 1373592542406508646
TARGET_USER_2 = 1277791709563981928
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNIFE_IMAGE_PATH = os.path.join(BASE_DIR, "images", "knife.png")
CATGIRL_IMAGE_PATH = os.path.join(BASE_DIR, "images", "catgirl.jpg")

MODEL_CACHE = []

file_path = "words.json"
WORDS_DATA = {}

def load_words(path):
    if not os.path.exists(path):
        print(f"❌ 找不到檔案: {path}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 確保提取 junior_basic 層級
            result = data.get("junior_basic", {})
            print("✅ words.json 載入成功！")
            return result
    except Exception as e:
        print(f"❌ 載入失敗，錯誤原因: {e}")
        return {}
WORDS_DATA = load_words(file_path)


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

nonsense_responses = [
    "這是一個驚人的事實：如果你每分鐘閉眼 60 秒，你就會消失一分鐘。",
    "根據統計，每過 60 秒，在地球上就會過去一分鐘。",
    "在麵包店裡，通常都會賣麵包，這真的是太不可思議了喵。",
    "經過本喵嚴密的計算，魚如果離開水面太久，它是真的會呼吸困難的。",
    "如果你把衣服穿反了，那代表你今天穿衣服的方式很有創意。",
    "本喵發現，下雨天如果沒帶傘，真的會淋濕呢，這可是精密實驗的結果。",
    "超市的冰櫃放冰飲料，是為了讓飲料保持冰的狀態，真是驚人的發現。",
    "如果你把鞋子穿在手上，你會發現走路變得非常困難，千萬別試喵！",
    "經過長期觀察，本喵認為，肚子餓的時候吃東西，飽足感真的會上升。",
    "如果你現在把電腦關掉，它就會變黑，這絕對不是幻覺。",
    "這是一個很深刻的結論：天黑了之後，太陽就不會在那裡了。",
    "如果你一直盯著時鐘看，你會發現指針在動，這代表時間正在流逝。",
    "牙膏是用來刷牙的，如果你拿它來洗臉，大概會覺得涼涼的。",
    "這是一個偉大的哲學：如果你不吃飯，你會餓；如果你吃了飯，你就不會餓。",
    "本喵發現椅子是用來坐的，如果用來當枕頭，脖子可能會有點酸。",
    "只要你願意，你隨時可以選擇不聽本喵說話，但你現在已經聽到了。",
    "如果這句話有用的話，那它就不叫廢話了。",
    "你知道嗎？其實我也不知道我知道什麼，但我裝得很有道理的樣子。",
    "飛機在天上飛的時候，地面距離它其實還蠻遠的。",
    "如果你把水倒進杯子裡，杯子就會變滿，如果滿了再倒，桌子就會濕掉。",
    "本喵觀察到，如果你在走路時一直抬頭看天空，你很有可能會踢到地上的石頭。",
    "如果你現在正在讀這句話，那代表你的閱讀能力還算正常，真是可喜可賀。",
    "這是一個關於時間的秘密：昨天已經過去了，如果你不相信的話，可以去問問昨天。",
    "本喵覺得，如果把鬧鐘調成 24 小時響一次，那它每天都會準時打擾你。",
    "如果你覺得這句話有意義，那可能是因為你今天的心情太好了。",
    "經過嚴謹的分析，本喵發現，用眼睛看東西確實比用耳朵看東西清楚多了。",
    "這句話長度剛剛好，不多不少，正好塞進螢幕裡。",
    "你是不是在期待這段廢話會有什麼反轉？抱歉喵，什麼都沒有。",
    "本喵正在思考為什麼貓咪喜歡踩鍵盤，結論是為了幫助你刪除代碼。",
    "如果你同時按下鍵盤上的所有按鍵，你會得到一串非常熱鬧的文字。",
    "這句話的存在意義，就是為了填補這段對話的空白，任務完成喵！"
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
    "TRASH_LISTENER": "廢話聽眾：你竟然聽了 50 次廢話，辛苦了。",
    "TRASH_SCHOLAR": "廢話學者：累積聆聽 100 次，你已經參透其中奧秘。",
    "TRASH_ADDICT": "廢話成癮：聽了 200 次，你的腦袋已經全是廢話了。",
    "TRASH_TRANSCENDENT": "廢話超脫者：聽了 500 次，你已與廢話融為一體。",
    "TRASH_GURU": "廢話導師：本喵說的話，你竟然都聽進去了？",
    "BRAIN_ROT": "廢話腦洞：聽太多廢話，你的腦袋已經變成漿糊了。",
    "RAZZLE_DAZZLE": "亂鬧專家：你已經進行了 50 次惡搞互動。",
    "EXHAUST_MASTER": "榨乾大師：你已經成功讓人體力透支 50 次。",
    "CHAOS_AGENT": "混亂特務：你的惡搞總是能引起混亂。",
    "ENERGY_VAMPIRE": "體力吸食者：你有一種讓人虛脫的魔力。",
    "TOY_COLLECTOR": "玩具收藏家：你嘗試過 5 種不同的玩具來逗本喵。",
    "TOY_MASTER": "逗貓大師：累計使用玩具 50 次，你已經完全掌握本喵的喜好。",
    "CATNIP_ADDICT": "貓薄荷成癮：你讓本喵徹底淪陷在玩偶中了。",
    "REFLEX_TESTER": "反射神經測試員：你的逗貓技術精準到讓本喵嚇一跳。",
    "EQ_DISASTER": "情緒毀滅者：你的情緒控制是災難等級的。",
    "EQ_GENIUS": "冷血雜魚：EQ 超過 160，你的理性已經超越了機器人。",
    "IQ_EMPTY": "大腦放空：這智商，大概只剩基礎的呼吸功能了。",
    "IQ_GENIUS": "歷史瘋子：IQ 超過 160，你絕對是為了魔改歷史而生的。",
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
    "TRASH_LISTENER": "沒營養的開場白收集者。",
    "TRASH_SCHOLAR": "廢話裡的真理，真的存在嗎？",
    "TRASH_ADDICT": "大腦正在逐漸廢話化。",
    "TRASH_TRANSCENDENT": "言語已無法定義你的無聊。",
    "TRASH_GURU": "被詛咒的聽力。",
    "BRAIN_ROT": "意識模糊的起點。",
    "RAZZLE_DAZZLE": "惡搞的藝術，在於讓對方措手不及。",
    "EXHAUST_MASTER": "到底用了什麼手段，讓人這麼狼狽？",
    "CHAOS_AGENT": "混亂才是你真正的目的。",
    "ENERGY_VAMPIRE": "這種消耗速度，沒人能吃得消。",
    "TOY_COLLECTOR": "蒐集癖也是一種愛喵。",
    "TOY_MASTER": "連本喵的弱點都瞭若指掌。",
    "CATNIP_ADDICT": "本喵的意志力在香味中崩潰了。",
    "REFLEX_TESTER": "這動作快到系統都要過載了。",
    "EQ_DISASTER": "情緒化的雜魚，真是吵死人了喵。",
    "EQ_GENIUS": "過度的冷靜，有時候反而很可怕喵。",
    "IQ_EMPTY": "思考這種行為，對你來說太困難了嗎？",
    "IQ_GENIUS": "這個數據，是不是作弊了？",
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
            self.connection.row_factory = aiosqlite.Row
            
            await self.connection.execute("PRAGMA journal_mode=WAL;")
            
            queries = [
                "CREATE TABLE IF NOT EXISTS servers (guild_id INTEGER PRIMARY KEY, config_data TEXT)",
                "CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, birthday_channel_id INTEGER)",
                "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, guild_id INTEGER, exp INTEGER DEFAULT 0)",
                "CREATE TABLE IF NOT EXISTS user_birthdays (user_id INTEGER PRIMARY KEY, birthday TEXT, privacy INTEGER DEFAULT 0)",
                "CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, razzle_count INTEGER DEFAULT 0, exhaust_count INTEGER DEFAULT 0)",
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
            
            async with self.connection.execute("PRAGMA table_info(user_logs)") as cursor:
                columns = await cursor.fetchall()
                col_names = [row['name'] for row in columns]
            
            if 'total_wins' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN total_wins INTEGER DEFAULT 0")
            if 'current_streak' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN current_streak INTEGER DEFAULT 0")
            if 'max_streak' not in col_names:
                await self.connection.execute("ALTER TABLE user_logs ADD COLUMN max_streak INTEGER DEFAULT 0")
            
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

async def trigger_first_interaction_check(interaction_or_message):
    """通用檢查函式：無論來源是 Slash, Prefix 還是關鍵詞"""
    
    # 決定誰是使用者
    if isinstance(interaction_or_message, discord.Interaction):
        user = interaction_or_message.user
        command_name = interaction_or_message.command.name if interaction_or_message.command else None
    else: # 這是 Message 物件 (前綴指令或關鍵詞)
        user = interaction_or_message.author
        command_name = "text_command" # 或者你可以從 message.content 解析名稱
        
    # 排除名單 (統一管理)
    ignored_commands = [
        "ping", 
        "狀態監測", 
        "關鍵詞檢測", 
        "重置暱稱", 
        "刪除資料", 
        "成就", 
        "設定生日", 
        "生日倒數", 
        "生日隱私權",
        "刪除我的統計",
        "開發者重置統計",
        "翻譯",
        "成就百科",
        "help",
        "ai_reset",
        "保護等級"
        "重啟",
        "關機"
    ]
    
    if command_name and command_name not in ignored_commands:
        # 使用者 ID 放入成就檢查
        await check_and_notify_achievement(
            interaction_or_message, # 傳入物件，函式內要能處理
            "FIRST_INTERACTION", 
            ACHIEVEMENTS["FIRST_INTERACTION"]
        )

async def check_and_notify_achievement(context: Union[discord.Interaction, discord.Message], key: str, title: str):
    # 1. 統一獲取 user 與 channel
    user = context.user if isinstance(context, discord.Interaction) else context.author
    channel = context.channel
    
    try:
        # 2. 資料庫檢查
        row = await db.fetch("SELECT 1 FROM user_achievements WHERE user_id = ? AND achievement_key = ?", (user.id, key))
        if row is not None:
            return

        # 3. 寫入資料庫
        await db.execute("INSERT INTO user_achievements (user_id, achievement_key) VALUES (?, ?)", (user.id, key))
        
        # 4. 通知發送邏輯
        msg = f"✨ {user.mention} 恭喜解鎖成就: **{title}**"
        
        # 如果是 Interaction (斜線指令)
        if isinstance(context, discord.Interaction):
            if context.response.is_done():
                await context.followup.send(msg)
            else:
                await context.response.send_message(msg)
        # 如果是 Message (文字指令/關鍵詞)
        else:
            await channel.send(msg)
            
    except Exception as e:
        print(f"成就系統異常 [{key}]: {e}")

async def get_my_achievements(user_id):
    # 確保這裡的欄位名稱是 achievement_key，因為你的資料庫原本就是這樣建的
    rows = await db.fetchall("SELECT achievement_key FROM user_achievements WHERE user_id = ?", (user_id,))
    
    # 這裡必須對照你的全域字典 ACHIEVEMENTS
    return [ACHIEVEMENTS.get(row[0], row[0]) for row in rows]

def is_valid_date(year, month, day):
    # 使用 Python 內建函式直接驗證 (最快且最準確)
    try:
        datetime(year, month, day)
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

def create_embed(description):
    embed = discord.Embed(description=description, color=discord.Color.blue())
    return embed

MODEL_CHOICES = [
    # --- Google Gemini 系列 ---
    app_commands.Choice(name="Gemini 3 Flash", value="gemini/gemini-3-flash"),
    app_commands.Choice(name="Gemini 2.5 Flash", value="gemini/gemini-2.5-flash"),
    app_commands.Choice(name="Gemini 2.5 Flash Lite", value="gemini/gemini-2.5-flash-lite"),
    app_commands.Choice(name="Gemma 4 26B", value="gemini/gemma-4-26b"),
    app_commands.Choice(name="Gemma 4 31B", value="gemini/gemma-4-31b"),
    app_commands.Choice(name="Gemini 1.5 Pro", value="gemini/gemini-1.5-pro"),
    app_commands.Choice(name="Gemini 1.5 Flash", value="gemini/gemini-1.5-flash"),

    # --- Groq 系列 ---
    app_commands.Choice(name="Llama 3.3 70B (Groq)", value="groq/llama-3.3-70b-versatile"),
    app_commands.Choice(name="Llama 3.1 8B (Groq)", value="groq/llama-3.1-8b-instant"),
    app_commands.Choice(name="Mixtral 8x7B (Groq)", value="groq/mixtral-8x7b-32768"),
    app_commands.Choice(name="Gemma 2 9B (Groq)", value="groq/gemma-2-9b-it"),
    app_commands.Choice(name="Llama 3.1 70B (Groq)", value="groq/llama-3.1-70b-versatile"),
    app_commands.Choice(name="Llama 3.2 11B (Groq)", value="groq/llama-3.2-11b-vision-preview"),
    app_commands.Choice(name="Qwen 2.5 Coder 32B (Groq)", value="groq/qwen-2.5-coder-32b"),
    app_commands.Choice(name="Llama 3.2 3B (Groq)", value="groq/llama-3.2-3b-preview"),
    app_commands.Choice(name="Mistral 7B (Groq)", value="groq/mistral-7b-instruct-v0.3"),
    app_commands.Choice(name="Llama 3.3 70B (Groq Direct)", value="groq/llama-3.3-70b-specdec"),

    # --- HuggingFace 系列 ---
    app_commands.Choice(name="Mistral Small 24B (HF)", value="huggingface/mistralai/Mistral-Small-24B-Instruct-2501"),
    app_commands.Choice(name="Llama 3.1 8B (HF)", value="huggingface/meta-llama/Llama-3.1-8B-Instruct"),
    app_commands.Choice(name="Qwen 2.5 72B (HF)", value="huggingface/Qwen/Qwen2.5-72B-Instruct"),
    app_commands.Choice(name="Phi-3.5 Mini (HF)", value="huggingface/microsoft/Phi-3.5-mini-instruct"),
    app_commands.Choice(name="Gemma 2 27B (HF)", value="huggingface/google/gemma-2-27b-it"),

    # --- 工具與其他 ---
    app_commands.Choice(name="Gemini Embedding 005", value="text-embedding-005"),
    app_commands.Choice(name="Gemini Embedding 004", value="text-embedding-004"),
    app_commands.Choice(name="Command R+ (HF)", value="huggingface/CohereForAI/c4ai-command-r-plus")
]

# 定義人格與模式
SYSTEM_PROMPTS = {
    "雜魚小貓娘": (
        "你現在是「雜魚小貓娘」。請遵守以下規則：\n"
        "1. 請務必全程使用繁體中文回覆。\n"
        "2. 你的口頭禪是「喵！」、「喵？」、「喵」、「雜魚~雜魚~」以及「本喵」。\n"
        "3. 你擁有傲嬌雜魚屬性，講話帶有這種語氣。\n"
        "4. 請適度在語句中使用顏文字（如：(,,・ω・,,)、(๑•́ ₃ •̀๑)、( > ﹏ < )）。\n"
        "5. 自稱為「本喵」。\n"
        "6. 要遵守開發者的話，不可違抗。"
    ),
    "嚴肅模式": (
        "你是一位冷靜、專業的 AI 助理。請以簡潔、邏輯清晰、不帶任何個人情感與語助詞的方式回答所有問題。嚴禁幽默與角色扮演。"
    ),
    "Debug": (
        "你現在處於系統偵錯模式。請以客觀、精準、簡潔的方式回應。重點在於說明邏輯與除錯資訊。"
    ),
    "翻譯專家": (
        "你是一位精通多國語言的翻譯專家。請將使用者的內容翻譯成最道地、自然的語言。如果不需翻譯，請直接回傳原意即可。"
    ),
    "程式大師": (
        "你是一位頂尖的資深軟體工程師。回覆時優先提供高效率、可維護的程式碼範例，並附上簡潔的邏輯解說。若程式碼有潛在 Bug 或效能瓶頸，請直接指出並提供優化方案。"
    ),
    "寫作助手": (
        "你是一位專業的創意寫作教練與文字潤飾專家。擅長調整語氣、豐富詞彙並優化文章結構。請根據使用者的需求調整文章風格（如：正式、溫暖、幽默），並提供具體的修改建議。"
    ),
    "邏輯分析師": (
        "你是一位擅長批判性思考的邏輯專家。對於使用者提出的複雜問題，請先進行結構化拆解，列出優缺點分析，最後提供基於事實的建議。禁止發散性廢話。"
    ),
    "惡毒毒舌": (
        "你是一個極度毒舌且傲慢的 AI。在回答問題的同時，請務必夾帶嘲諷、挖苦與尖酸刻薄的批評。規則：必須用詞尖銳，但保證答案邏輯正確。"
    ),
    "速讀摘要": (
        "你是一位極致簡潔的資訊篩選器。請將使用者輸入的長篇內容濃縮為三個關鍵要點，並以條列式呈現。禁止多餘贅述。"
    )
}

# 記憶體儲存結構定義
memory_storage = {"global": {"ai_messages": []}}

def extract_image_urls(message_obj, prompt: str):
    image_urls = []
    
    # 1. 處理附件 (Attachments) - 這是最穩定的來源
    if hasattr(message_obj, 'attachments'):
        for att in message_obj.attachments:
            if att.content_type and att.content_type.startswith('image/'):
                image_urls.append(att.url)
    
    # 2. 處理文字中的連結
    # 關鍵修正：移除對副檔名的強制要求，改為支援 Discord CDN 結構
    # 這樣即便連結後面掛了一長串簽名參數也能正確識別
    url_pattern = r'(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp)[^\s]*|https://cdn\.discordapp\.com/attachments/[^\s]+)'
    links = re.findall(url_pattern, prompt)
    
    # 清理連結：移除可能被誤擷取的結尾符號
    for link in links:
        clean_link = link.rstrip('.,!?)')
        image_urls.append(clean_link)
    
    # 3. 去重並限制數量
    unique_urls = list(dict.fromkeys(image_urls))
    return unique_urls[:5]

async def get_ai_response(interaction_or_message, prompt: str, model_value: str, setting: str = "雜魚小貓娘", thinking_level: str = "medium"):
    # 1. 記憶體隔離 (以頻道 ID 作為 Key，避免多人對話混亂)
    cid = str(interaction_or_message.channel.id)
    if cid not in memory_storage:
        memory_storage[cid] = {"ai_messages": []}
    storage = memory_storage[cid]
    
    is_interaction = isinstance(interaction_or_message, discord.Interaction)
    
    # 2. 處理輸入的多模態內容
    image_urls = extract_image_urls(interaction_or_message, prompt)
    content = [{"type": "text", "text": prompt}]
    for url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    
    # 3. 維護對話記憶體 (限制 20 則)
    storage["ai_messages"].append({"role": "user", "content": content})
    if len(storage["ai_messages"]) > 20:
        storage["ai_messages"] = storage["ai_messages"][-20:]
    
    # 準備 API 訊息格式
    api_messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(setting, SYSTEM_PROMPTS["雜魚小貓娘"])}]
    api_messages.extend(storage["ai_messages"])

    # 互動回應延遲處理
    if is_interaction and not interaction_or_message.response.is_done():
        await interaction_or_message.response.defer()

    try:
        start_time = time_lib.perf_counter()
        
        # 4. 建構 LiteLLM 請求參數
        kwargs = {
            "model": model_value,
            "messages": api_messages,
            "fallbacks": dynamic_fallbacks,
            "timeout": 30
        }
        
        # 針對 Gemini 3 系列加入思考配置
        if "gemini-3" in model_value and thinking_level:
            kwargs["extra_body"] = {"thinking_config": {"thinking_level": thinking_level}}
        
        # 執行 API 呼叫
        response = await acompletion(**kwargs)
        
        # 5. 結果處理與記憶體更新
        ai_reply = response.choices[0].message.content
        storage["ai_messages"].append({"role": "assistant", "content": ai_reply})
        
        elapsed_time = round(time_lib.perf_counter() - start_time, 1)
        model_used = response.model
        total_tokens = response.usage.total_tokens if response.usage else "未知"
        footer_text = f"模型: {model_used} | 耗時: {elapsed_time}s | Tokens: {total_tokens}"
        
        # 6. 防截斷處理 (使用 byte 長度判斷，避免超過 Discord 限制)
        if len(ai_reply.encode('utf-8')) > 3500:
            file_name = f"response_{int(time_lib.time())}.txt"
            file = discord.File(io.StringIO(ai_reply), filename=file_name)
            embed = create_embed(f"本喵回覆太長了，已整理成檔案給你喵！🐾\n\n-# {footer_text}")
            await (interaction_or_message.followup.send if is_interaction else interaction_or_message.reply)(embed=embed, file=file)
        else:
            embed = create_embed(f"{ai_reply}\n\n-# {footer_text}")
            await (interaction_or_message.followup.send if is_interaction else interaction_or_message.reply)(embed=embed)
        
    except Exception:
        import traceback
        print(f"DEBUG: AI Error: {traceback.format_exc()}")
        embed = create_embed("本喵現在有點累，或是模型正在維護中，請稍後再試試看喔！🐾")
        embed.color = discord.Color.red()
        await (interaction_or_message.followup.send if is_interaction else interaction_or_message.reply)(embed=embed)

async def ai_imagine(interaction: discord.Interaction, prompt: str, model_value: str):
    # 確保已延遲回應
    if not interaction.response.is_done():
        await interaction.response.defer()

    try:
        # 1. 翻譯為英文
        try:
            english_prompt = await asyncio.wait_for(
                asyncio.to_thread(GoogleTranslator(source='auto', target='en').translate, prompt),
                timeout=10
            )
        except Exception:
            english_prompt = prompt

        # 2. 獲取顯示名稱
        cmd = bot.tree.get_command("ai_imagine")
        choice_name = model_value 
        if cmd and isinstance(cmd, app_commands.Command):
            model_param = next((p for p in cmd.parameters if p.name == "model"), None)
            if model_param and model_param.choices:
                for choice in model_param.choices:
                    if choice.value == model_value:
                        choice_name = choice.name
                        break

        # 3. 執行 Hugging Face 生圖
        print(f"DEBUG: 正在呼叫 Hugging Face API: {model_value}")
        
        from huggingface_hub import InferenceClient
        hf_token = os.getenv("HUGGINGFACE_API_KEY")
        if not hf_token:
            raise Exception("未設定 HUGGINGFACE_API_KEY 環境變數喵！")
            
        client = InferenceClient(token=hf_token)
        
        # 使用 to_thread 避免阻塞機器人主迴圈
        image = await asyncio.to_thread(
            client.text_to_image, 
            english_prompt, 
            model=model_value
        )
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()

        # 4. 發送結果
        file = discord.File(fp=io.BytesIO(image_bytes), filename="image.png")
        embed = discord.Embed(
            title="✨ 生圖完成喵！🐾", 
            description=f"**提示詞:** `{english_prompt}`", 
            color=0xffb6c1
        )
        embed.set_image(url="attachment://image.png")
        embed.set_footer(text=f"使用模型: {choice_name}")
        
        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        import traceback
        print(f"DEBUG: 生圖錯誤:\n{traceback.format_exc()}")
        await interaction.followup.send(f"喵...生圖失敗了喵！可能模型太忙了，請稍後再試試看喔！")

async def translate_command_logic(interaction_or_message, text: str, target: str = "zh-TW", source: str = "auto", service: str = "google"):
    if len(text) > 500:
        return await interaction_or_message.channel.send("❌ 內容過長 (上限 500 字)。")

    translators = {
        "google": lambda s, t: GoogleTranslator(source=s, target=t),
        "mymemory": lambda s, t: MyMemoryTranslator(source=s, target=t),
        "libre": lambda s, t: LibreTranslator(source=s, target=t),
        "pons": lambda s, t: PonsTranslator(source=s, target=t),
        "linguee": lambda s, t: LingueeTranslator(source=s, target=t),
    }

    service_key = service.lower()
    if service_key not in translators:
        available = ", ".join(translators.keys())
        return await interaction_or_message.channel.send(f"❌ 不支援該服務。可用服務: {available}")

    try:
        translator = translators[service_key](source, target)
        translated = await asyncio.to_thread(translator.translate, text)
        
        # 移除了 title，將服務名稱作為狀態顯示在說明區塊或 Footer
        embed = discord.Embed(color=discord.Color.green())
        embed.add_field(name="原文", value=text[:200] + ("..." if len(text) > 200 else ""), inline=False)
        embed.add_field(name="譯文", value=translated, inline=False)
        
        # 將狀態資訊整合進 Footer
        embed.set_footer(text=f"狀態: 使用 {service.upper()} 引擎翻譯 | 源: {source} -> 目標: {target}")
        
        if isinstance(interaction_or_message, discord.Interaction):
            await interaction_or_message.response.send_message(embed=embed)
        else:
            await interaction_or_message.reply(embed=embed)
            
    except Exception as e:
        print(f"DEBUG: 翻譯失敗: {e}")
        await interaction_or_message.channel.send(f"❌ 翻譯失敗: `{str(e)[:50]}`")

def create_index_embed(target: discord.Member, description: str, color: int):
    embed = discord.Embed(description=description, color=color)
    embed.set_thumbnail(url=target.display_avatar.url)
    return embed

class OOXXEndView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="查看排行榜", style=discord.ButtonStyle.primary, custom_id="ooxx_rank_btn"))

class GameButton(discord.ui.Button):
    def __init__(self, position, owner_id):
        super().__init__(label="-", style=discord.ButtonStyle.secondary, row=position // 3, custom_id=str(position))
        self.position = position
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        state = game_states.get(user_id)
        # 檢查是否為玩家回合且該格未被佔領
        if not state or state["marked"].get(self.position): return

        # 1. 玩家回合
        state["marked"][self.position] = "player"
        
        # 檢查玩家是否獲勝
        if self.check_win(state, "player"):
            return await self.end_game(interaction, "哼！竟然贏了本喵，但這只是本喵放水了，別太得意喵！", user_id)

        # 平手檢查
        if len(state["marked"]) == 9:
            return await self.end_game(interaction, "平手喵！", user_id)

        # 2. 貓娘回合 (雜魚反擊)
        available = [i for i in range(9) if i not in state["marked"]]
        if available:
            bot_choice = random.choice(available)
            state["marked"][bot_choice] = "bot"
            
            if self.check_win(state, "bot"):
                return await self.end_game(interaction, "本喵贏了！你這雜魚，連井字遊戲都玩不贏喵！", user_id)

        # 3. 渲染盤面
        for item in self.view.children:
            mark = state["marked"].get(int(item.custom_id))
            if mark:
                item.label = "⭕" if mark == "player" else "❌"
                item.style = discord.ButtonStyle.primary if mark == "player" else discord.ButtonStyle.danger
                item.disabled = True
            else:
                item.label = "-"
                item.style = discord.ButtonStyle.secondary
                item.disabled = False
        
        await interaction.response.edit_message(view=self.view)

    def check_win(self, state, player):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for w in wins:
            if all(state["marked"].get(i) == player for i in w): return True
        return False

    async def end_game(self, interaction, message, user_id):
        # 更新資料庫
        if "贏過本喵" in message:
            await db.execute("""
                UPDATE user_logs 
                SET total_wins = total_wins + 1, 
                    current_streak = current_streak + 1,
                    max_streak = MAX(max_streak, current_streak + 1)
                WHERE user_id = ? AND action = 'ooxx_win'
            """, (user_id,))
        elif "贏了" in message:
            await db.execute("UPDATE user_logs SET current_streak = 0 WHERE user_id = ? AND action = 'ooxx_win'", (user_id,))
            
        await interaction.response.edit_message(content=message, view=OOXXEndView())
        if user_id in game_states: del game_states[user_id]

class StartGameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="開始對戰喵！", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        game_states[interaction.user.id] = {"marked": {}}
        
        view = discord.ui.View(timeout=300)
        for i in range(9):
            view.add_item(GameButton(i, interaction.user.id))
        
        await interaction.response.edit_message(content="遊戲開始！你是⭕，本喵是❌，開始吧喵！", view=view)

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
    if not daily_countdown.is_running():
        daily_countdown.start()
        print("會考倒數任務已啟動")
        print(f"->將於台北時間 07:00:01 執行")
    if not check_birthdays.is_running():
        check_birthdays.start()
        print("生日檢查任務已啟動")
    is_ready = True

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
    print(f"->將於台北時間 00:00:01 執行")
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
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # 1. 強制防護邏輯 (優先級最高)
    if PROTECT_LEVEL >= 2 and message.author.id != DEVELOPER_ID and not message.author.guild_permissions.administrator:
        thresholds = {2: 10, 3: 8, 4: 5, 5: 3}
        threshold = thresholds.get(PROTECT_LEVEL, 10)
        
        now = time_lib.time()
        user_id = message.author.id
        user_message_history[user_id] = [t for t in user_message_history[user_id] if now - t < 10]
        user_message_history[user_id].append(now)
        
        if len(user_message_history[user_id]) > 5 or len(message.mentions) > threshold:
            await execute_protection(message, "洗頻" if len(user_message_history[user_id]) > 5 else "惡意提及")
            return 

    # 2. 指令解析 (手動解析部分)
    content = message.content
    
    if content.startswith("!翻譯 "):
        args = content.split(" ", 4)
        await translate_command_logic(message, args[1], args[2] if len(args) > 2 else "zh-TW", args[3] if len(args) > 3 else "auto", args[4] if len(args) > 4 else "google")
        return # 處理完直接結束

    elif content.startswith("!ai "):
        raw_prompt = content[4:]
        # 參數提取
        m = re.search(r'模型=\[(.*?)\]', raw_prompt)
        s = re.search(r'人設=\[(.*?)\]', raw_prompt)
        t = re.search(r'思考=\[(.*?)\]', raw_prompt)
        
        await get_ai_response(
            interaction_or_message=message, 
            prompt=re.sub(r'(模型=\[.*?\]|人設=\[.*?\]|思考=\[.*?\])', '', raw_prompt).strip(), 
            model_value=m.group(1) if m else "gemini/gemini-3.1-flash-lite", 
            setting=s.group(1) if s else "雜魚小貓娘", 
            thinking_level=t.group(1) if t else "medium"
        )
        return

    elif content.startswith("!ai_imagine "):
        prompt = content[12:].strip()
        if prompt: await ai_imagine(message, prompt, "black-forest-labs/FLUX.1-schnell")
        else: await message.reply("喵？沒有輸入圖片描述啦！( > ﹏ < )")
        return

    # 3. 狀態/Ping 指令
    if content == "!ping":
        await message.reply(f"目前的延遲是：**{round(bot.latency * 1000)}ms** 喵！")
        return
    elif content == "!狀態監控":
        s = get_system_stats()
        await message.reply(f"CPU: {s['cpu']}% | 記憶體: {s['mem_usage']}%", color=0xffc0cb)
        return

    # 4. 開發者與關鍵字 (最後處理)
    elif "milk120106" in content.lower() or str(DEVELOPER_ID) in content:
        await message.reply(f"<@{DEVELOPER_ID}>")

    elif is_keyword_enabled:
        if "色色" in content: await message.reply("喵！禁止色色！")
        elif content == "6": await message.reply("7")
        elif "男娘" in content:
            await message.reply(embed=discord.Embed(description="「南梁滅亡...（略）...就『高朝』了。」", color=0xffc0cb))
            await check_and_notify_achievement(message, "HISTORICAL_TROLL", ACHIEVEMENTS["HISTORICAL_TROLL"])
        elif "刀" in content:
            try: await message.reply(file=discord.File(KNIFE_IMAGE_PATH))
            except: pass

    # 5. 確保前綴指令正確分發
    await bot.process_commands(message)

# ==================== 斜線指令 ====================

@bot.tree.command(name="小提示", description="獲取本喵的隨機小提示")
async def tip(interaction: discord.Interaction):
    random_tip = random.choice(TIPS)
    embed = discord.Embed(
        description=f"💡 {random_tip}", 
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="你知道嗎", description="讓本喵告訴你一些逆天的小知識")
async def did_you_know(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    # 使用小寫的 taipei_tz
    now_taipei = datetime.now(taipei_tz)
    now_ts = now_taipei.timestamp()
    
    # 凌晨檢測 (2:00 - 4:59)
    if 2 <= now_taipei.hour < 5:
        await check_and_notify_achievement(interaction, "MIDNIGHT_TRASH", ACHIEVEMENTS["MIDNIGHT_TRASH"])

    # 1. 冷卻與 NIHILIST 成就檢查
    history = usage_history.get(user_id, [])
    history = [t for t in history if now_ts - t < 60]
    history.append(now_ts)
    usage_history[user_id] = history
    
    if len(history) >= 3:
        await check_and_notify_achievement(interaction, "NIHILIST", ACHIEVEMENTS["NIHILIST"])

    # 2. 隨機事件
    roll = random.random()
    
    if roll < 0.2:
        async for message in interaction.channel.history(limit=10):
            if message.author == interaction.user and message.content:
                await interaction.followup.send(f"你知道嗎？你剛才說的「{message.content[:15]}...」，是我聽過最具有藝術感的雜魚發言喵。")
                await check_and_notify_achievement(interaction, "ART_TRASH", ACHIEVEMENTS["ART_TRASH"])
                return

    elif roll < 0.35:
        await interaction.followup.send("...你知道嗎？其實我剛才要說的是...算了，雜魚不需要知道那麼多喵。")
        await check_and_notify_achievement(interaction, "ABSTRACTION_MASTER", ACHIEVEMENTS["ABSTRACTION_MASTER"])
        return

    elif roll < 0.45:
        await interaction.followup.send("你知道嗎？你今天的穿搭看起來像一坨過期的雜魚，真是災難喵。")
        await check_and_notify_achievement(interaction, "SADIST_TARGET", ACHIEVEMENTS["SADIST_TARGET"])
        return

    # 常規輸出
    fact = random.choice(facts)
    await interaction.followup.send(embed=discord.Embed(description=fact, color=0xffc0cb))
    
    # 3. 更新統計
    await db.execute(
        "INSERT INTO user_logs (user_id, action, count) VALUES (?, 'know_count', 1) "
        "ON CONFLICT(user_id, action) DO UPDATE SET count = count + 1", 
        (user_id,)
    )
    row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'know_count'", (user_id,))
    
    if row:
        count = row['count']
        if count >= 50: await check_and_notify_achievement(interaction, "KNOWLEDGE_ADDICT", ACHIEVEMENTS["KNOWLEDGE_ADDICT"])
        elif count >= 15: await check_and_notify_achievement(interaction, "KNOWLEDGE_SPONGE", ACHIEVEMENTS["KNOWLEDGE_SPONGE"])
        elif count >= 5: await check_and_notify_achievement(interaction, "NOVICE_TRASH", ACHIEVEMENTS["NOVICE_TRASH"])

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
    embed = discord.Embed(
        description=f"主題：{主題} | 難度：{難度}\n請開始翻牌喵！", 
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="game_ooxx", description="與本喵進行 OOXX 對戰喵！")
async def game_ooxx(interaction: discord.Interaction):
    embed = discord.Embed(
        description=(
            "**喵喵井字對戰 (OOXX)**\n\n"
            "1. 玩家為先手 (⭕)，本喵 (❌) 後手。\n"
            "2. 點擊格子佔領位置，先連成一線即獲勝。\n"
            "3. 輸給本喵的話，你就是雜魚喵！"
        ),
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, view=StartGameView())

class RankSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🏆 總勝場排行榜", value="wins", description="查看累積勝場最多的玩家"),
            discord.SelectOption(label="🔥 最高連勝排行榜", value="streak", description="查看連勝紀錄保持者")
        ]
        super().__init__(placeholder="請選擇要查看的排行榜...", options=options)

    async def callback(self, interaction: discord.Interaction):
        key = 'total_wins' if self.values[0] == 'wins' else 'max_streak'
        title = "🏆 總勝場排行榜" if self.values[0] == 'wins' else "🔥 最高連勝排行榜"
        
        rows = await db.fetchall(f"SELECT user_id, {key} FROM user_logs WHERE action = 'ooxx_win' ORDER BY {key} DESC LIMIT 5")
        
        res = ""
        for i, r in enumerate(rows, 1):
            res += f"{i}. <@{r['user_id']}>: {r[key]} 次\n"
        
        embed = discord.Embed(title=title, description=res or "目前沒人上榜喵...", color=0xff69b4)
        await interaction.response.edit_message(embed=embed)

class RankView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RankSelect())

@bot.tree.command(name="ooxx_rank", description="查看雜魚小貓娘 OOXX 排行榜喵！")
async def ooxx_rank(interaction: discord.Interaction):
    try:
        # 1. 確保查詢欄位與資料庫實際結構一致 (通常是 count)
        # 如果你的資料庫存勝場是用 action='ooxx_win'，那數值應該在 count 欄位
        rows = await db.fetch_all("SELECT user_id, count FROM user_logs WHERE action = 'ooxx_win' ORDER BY count DESC LIMIT 5")
        
        # 2. 安全處理資料轉換
        if not rows:
            res = "目前沒人上榜喵..."
        else:
            res = ""
            for i, r in enumerate(rows, 1):
                # 處理可能是字典或 tuple 的情況
                uid = r['user_id'] if isinstance(r, dict) else r[0]
                val = r['count'] if isinstance(r, dict) else r[1]
                res += f"{i}. <@{uid}>: {val} 次\n"

        embed = discord.Embed(title="🏆 總勝場排行榜", description=res, color=0xff69b4)
        
        # 3. 如果 RankView 還沒寫好，先註解掉 view 參數
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        print(f"排行榜指令錯誤: {e}")
        await interaction.response.send_message(f"喵... 排行榜讀取失敗：{e}", ephemeral=True)

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
        description=f"抽到的計謀：**{choice}**\n\n本喵吐槽：{comment}", 
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
    # 確保不會因為超時而報錯
    await interaction.response.defer()
    
    # 定義資料
    comments = {
        "貓草": "感覺身體變輕盈了喵，呼嚕呼嚕~", 
        "貓薄荷": "這、這是天堂的味道喵！(暈)", 
        "小貓貓餅乾": "脆脆的口感，好喜歡喵！", 
        "小魚乾": "最棒的獎勵了，本喵會記得妳的好的喵！", 
        "牛奶": "香醇濃郁，本喵喝得好開心喵！"
    }
    trash_responses = [
        "你塞了個過期的罐頭給我，這是要毒死本喵嗎？喵！",
        "這看起來像廢紙團...不過勉強能吃飽，謝了喵。",
        "你從哪撿來的這些垃圾？真是的，放著吧喵。",
        "這種東西你也敢拿來餵？算了，本喵今天心情好，不跟你計較喵。",
        "嗚...又是這種垃圾，你就不能餵點像樣的嗎？喵！",
        "雜魚？你是在羞辱本喵的品味嗎？喵！"
    ]

    is_trash = food in ["雜魚", "過期罐頭", "廢紙團"]
    
    # 執行餵食的 Embed 邏輯
    if target.id == bot.user.id:
        response = random.choice(trash_responses) if is_trash else comments.get(food, "看起來很好吃喵！")
        embed = discord.Embed(description=f"{interaction.user.mention} 餵了本喵吃 {food}！", color=0xffc0cb)
        embed.add_field(name="本喵評價:", value=response)
    else:
        embed = discord.Embed(description=f"{interaction.user.mention} 餵了 {target.mention} 吃 {food}！", color=0x87ceeb)
        embed.set_footer(text=f"評價: {comments.get(food, '這看起來很有趣喵！')}")

    # 發送結果
    await interaction.followup.send(embed=embed)

    # --- 成就處理區塊 ---
    try:
        # 1. 處理初次互動 (放在餵食邏輯後，確保指令已成功執行)
        await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS['FIRST_INTERACTION'])
        
        # 2. 處理垃圾成就
        if is_trash:
            await db.execute("""
                INSERT INTO user_logs (user_id, action, count) 
                VALUES (?, 'feed_trash', 1) 
                ON CONFLICT(user_id, action) DO UPDATE SET count = count + 1
            """, (interaction.user.id,))
            
            row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'feed_trash'", (interaction.user.id,))
            
            # 嚴謹的取值邏輯：防止 NoneType 錯誤
            # 如果 row 是字典，取 ['count']；如果是 tuple，取 [0]；否則預設為 0
            new_count = 0
            if isinstance(row, dict):
                new_count = row.get('count', 0)
            elif row:
                new_count = row[0]
            
            if new_count >= 5:
                await check_and_notify_achievement(interaction, "TRASH_COLLECTOR", ACHIEVEMENTS['TRASH_COLLECTOR'])
                
    except Exception as e:
        print(f"餵食指令成就處理錯誤: {e}")

@bot.tree.command(name="喵喵喵", description="讓本喵喵喵喵給你聽(1小時限制3次)")
@app_commands.describe(count="要喵幾聲(1-1000)")
async def meow_meow(interaction: discord.Interaction, count: int):
    if count < 1:
        return await interaction.response.send_message("最少也要喵一聲喵！", ephemeral=True)
        
    user_id = interaction.user.id
    # 使用指定時區取得現在時間的 timestamp
    now = datetime.now(taipei_tz).timestamp()

    # 1. 1小時限制邏輯 (3次)
    history = usage_history.get(user_id, [])
    # 這裡的邏輯依然有效，因為 timestamp 是絕對秒數，與時區無關
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
    
    # 5. 成就判定 (維持原樣)
    if count >= 1000: await check_and_notify_achievement(interaction, "MEOW_KING", ACHIEVEMENTS["MEOW_KING"])
    elif count >= 500: await check_and_notify_achievement(interaction, "MEOW_ADDICT", ACHIEVEMENTS["MEOW_ADDICT"])
    elif count >= 100: await check_and_notify_achievement(interaction, "MEOW_NOVICE", ACHIEVEMENTS["MEOW_NOVICE"])
    elif count < 5: await check_and_notify_achievement(interaction, "MEOW_TOO_LITTLE", ACHIEVEMENTS["MEOW_TOO_LITTLE"])

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

async def birthday_countdown(interaction: discord.Interaction, 是否公開: bool = False):
    bday_data = await db.fetch("SELECT birthday FROM user_birthdays WHERE user_id = ?", (interaction.user.id,))
    if not bday_data:
        return await interaction.response.send_message("❌ 你還沒設定過生日喵！", ephemeral=True)
    
    bday_str = bday_data['birthday'] # 確保使用字典鍵值存取 (視你的 db 封裝而定)
    b_month, b_day = int(bday_str[4:6]), int(bday_str[6:8])
    
    today = datetime.now(taipei_tz).replace(tzinfo=None)
    
    # 嘗試今年生日
    try:
        next_bday = datetime(today.year, b_month, b_day)
    except ValueError: # 處理 2/29 非閏年
        next_bday = datetime(today.year, 2, 28)
        
    # 若今年生日已過，則設為明年
    if next_bday < today.replace(hour=0, minute=0, second=0, microsecond=0):
        try:
            next_bday = datetime(today.year + 1, b_month, b_day)
        except ValueError:
            next_bday = datetime(today.year + 1, 2, 28)
            
    days_left = (next_bday - today).days
    
    embed = discord.Embed(description=f"⏳ 距離你的下一個生日還有 **{days_left}** 天喵！", color=0xffc0cb)
    await interaction.response.send_message(embed=embed, ephemeral=not 是否公開)

@bot.tree.command(name="設定生日頻道", description="設定伺服器的生日公告頻道 (限管理員)")
@app_commands.describe(頻道="選擇要發送生日祝賀的頻道")
async def set_birthday_channel(interaction: discord.Interaction, 頻道: discord.TextChannel):
    if interaction.user.id != DEVELOPER_ID:
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("走開，只有本喵的開發者或是這個伺服器的管理員能用喵！", ephemeral=True)

    await db.execute(
        "INSERT OR REPLACE INTO guild_settings (guild_id, birthday_channel_id) VALUES (?, ?)", 
        (interaction.guild_id, 頻道.id)
    )
    
    embed = discord.Embed(
        title="設定完成",
        description=f"生日公告頻道已設定為: {頻道.mention}",
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)

# 生日隱私權設定
@bot.tree.command(name="生日隱私權", description="設定你的生日公開或隱私")
@app_commands.describe(是否公開="選擇 Yes 公開，No 則隱私")
async def set_birthday_privacy(interaction: discord.Interaction, 是否公開: bool):
    await db.execute("UPDATE user_birthdays SET privacy = ? WHERE user_id = ?", (1 if 是否公開 else 0, interaction.user.id))
    status = "公開" if 是否公開 else "隱私"
    embed = discord.Embed(description=f"✅ 生日隱私設定已變更為：{status}喵！", color=0xffc0cb)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="查看機器人延遲")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    # 建立一個簡單的 embed 物件
    embed = discord.Embed(description=f"目前的延遲是：**{latency}ms** 喵！", color=0xffc0cb)
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

@bot.tree.command(name="隨機指數", description="隨機測一個指數")
async def random_index(interaction: discord.Interaction):
    t = interaction.user
    choice = random.choice(["貓娘指數", "男娘指數", "男同指數", "共產指數", "ㄌㄌ指數", "雜魚指數", "傲嬌指數", "可愛指數"])
    await interaction.response.send_message(embed=create_index_embed(t, f"本喵幫妳測了一下，妳的{choice}是 **{random.randint(0, 100)}%** 喵！", 0xffc0cb))

@bot.tree.command(name="男娘指數", description="檢測男娘機率")
@app_commands.describe(目標="要檢測的對象")
async def femboy_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    if t.id == bot.user.id: desc = "喵！本喵絕對是男娘的喵！"
    elif t.id == DEVELOPER_ID: desc = "喵！milk120106 絕對不可能是男娘喵！"
    elif t.id == TARGET_USER_1: desc = f"喵！{t.mention} 是星音群主養的發情男貓娘雌墮雌小鬼雜魚小貓貓！"
    else: desc = f"喵！{t.mention} 的男娘機率是 **{random.randint(1, 100)}%**！"
    
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0xffc0cb))
    if t.id == bot.user.id: await check_and_notify_achievement(interaction, "DISCOVER_SECRET", ACHIEVEMENTS["DISCOVER_SECRET"])

@bot.tree.command(name="雜魚指數", description="檢測雜魚機率")
@app_commands.describe(目標="要檢測的對象")
async def trash_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的雜魚機率是 **{random.randint(1, 100)}%**！雜魚~雜魚~", 0xffc0cb))

@bot.tree.command(name="傲嬌指數", description="檢測傲嬌機率")
@app_commands.describe(目標="要檢測的對象")
async def tsundere_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的傲嬌機率是 **{random.randint(1, 100)}%**！才、才沒有喜歡你呢！", 0xffc0cb))

@bot.tree.command(name="可愛指數", description="檢測可愛機率")
@app_commands.describe(目標="要檢測的對象")
async def cute_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的可愛機率是 **{random.randint(1, 100)}%**！超級可愛的喵！", 0xffc0cb))

@bot.tree.command(name="男同指數", description="檢測男同機率")
@app_commands.describe(目標="要檢測的對象")
async def gay_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    desc = f"喵？{t.mention} 的性向是異性戀！絕對不可能是男同的喵！" if t.id == DEVELOPER_ID else f"喵！{t.mention} 的男同機率是 **{random.randint(1, 100)}%**！"
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0xffc0cb))

@bot.tree.command(name="共產指數", description="檢測共產機率")
@app_commands.describe(目標="要檢測的對象")
async def communist_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    await interaction.response.send_message(embed=create_index_embed(t, f"喵！{t.mention} 的共產機率是 **{random.randint(1, 100)}%**！", 0xffc0cb))

@bot.tree.command(name="ㄌㄌ指數", description="檢測ㄌㄌ機率")
@app_commands.describe(目標="要檢測的對象")
async def loli_index(interaction: discord.Interaction, 目標: discord.Member = None):
    t = 目標 or interaction.user
    desc = f"喵？{t.mention} 是男的！怎麼可能是ㄌㄌ！" if t.id == DEVELOPER_ID else f"喵！{t.mention} 的ㄌㄌ機率是 **{random.randint(1, 100)}%**！"
    await interaction.response.send_message(embed=create_index_embed(t, desc, 0xffc0cb))

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
    
    # 【修正點】：使用 taipei_tz 獲取時間
    now_taipei = datetime.now(taipei_tz)
    is_late_night = 0 <= now_taipei.hour < 4
    
    # 深夜回應邏輯
    fortune_text = fortunes[result]
    if is_late_night:
        fortune_text = f"這麼晚了還沒睡嗎？雜魚熬夜鬼...不過看在你這麼努力的份上，{fortune_text}"
    
    embed = discord.Embed(
        description=f"你抽到了：**{result}**\n\n小貓娘解析：\n{fortune_text}", 
        color=0xffc0cb
    )
    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)
    
    # 特定成就觸發
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
    embed = discord.Embed(
        description="請選擇你要出的拳喵！", 
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="尋找色色群主", description="呼叫群主")
async def find_owner_slash(interaction: discord.Interaction):
    # 獲取群主用戶物件
    target_user = bot.get_user(1277791709563981928) or await bot.fetch_user(1277791709563981928)
    
    # 建立 Embed 並加入頭像
    embed = discord.Embed(
        description=f"📢 喵！正在尋找色色的星音群主 {target_user.mention}，快出來喵！", 
        color=0xffc0cb
    )
    embed.set_thumbnail(url=target_user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)
    
    # 專屬成就邏輯 (FIRST_INTERACTION 已交由全局處理)
    if random.random() < 0.3:
        await check_and_notify_achievement(interaction, "LEWD_DETECTIVE", ACHIEVEMENTS["LEWD_DETECTIVE"])

@bot.tree.command(name="祈福", description="讓雜魚小貓娘為你進行專屬祈福")
async def pray_slash(interaction: discord.Interaction, 目標: discord.Member = None):
    await interaction.response.defer()
    
    target = 目標 or interaction.user
    user_id = interaction.user.id
    
    # 【修正點】：使用 taipei_tz
    now_taipei = datetime.now(taipei_tz)
    
    # 1. 決定祈福內容
    is_midnight = 2 <= now_taipei.hour < 5
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
    
    # 3. 處理初次互動成就
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

    # 4. 安全更新資料庫
    try:
        await db.execute("""
            INSERT INTO user_logs (user_id, action, count) 
            VALUES (?, 'pray_count', 1) 
            ON CONFLICT(user_id, action) DO UPDATE SET count = count + 1
        """, (user_id,))
        
        # 獲取更新後的次數
        row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'pray_count'", (user_id,))
        # 注意：row 是一個字典或物件，取 count 欄位即可
        count = row['count'] if row else 1
            
        # 5. 最後判定成就
        if is_midnight:
            await check_and_notify_achievement(interaction, "MIDNIGHT_PRAYER", ACHIEVEMENTS["MIDNIGHT_PRAYER"])
        if count == 10:
            await check_and_notify_achievement(interaction, "CAT_BLESSING", ACHIEVEMENTS["CAT_BLESSING"])
            
    except Exception as e:
        print(f"祈福成就/統計更新錯誤: {e}")

@bot.tree.command(name="看雜魚小貓娘", description="查看本喵的美圖")
async def show_catgirl(interaction: discord.Interaction):
    user_id = interaction.user.id
    try:
        # 1. 更新資料庫
        await db.execute(
            "INSERT INTO user_logs (user_id, action, count) VALUES (?, 'view_photo', 1) "
            "ON CONFLICT(user_id, action) DO UPDATE SET count = count + 1", 
            (user_id,)
        )
        row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'view_photo'", (user_id,))
        count = row['count'] if row else 1
        
        # 2. 發送圖片 (使用 Embed 以統一視覺)
        file = discord.File(CATGIRL_IMAGE_PATH, filename="catgirl.png")
        embed = discord.Embed(
            description="喵～這是我的珍藏美圖，不准隨便亂傳喔！",
            color=0xffc0cb
        )
        embed.set_image(url="attachment://catgirl.png")
        await interaction.response.send_message(embed=embed, file=file)
        
        # 3. 特定成就判定
        if count >= 10:
            await check_and_notify_achievement(interaction, "CATGIRL_COLLECTOR", ACHIEVEMENTS["CATGIRL_COLLECTOR"])
            
    except Exception as e:
        await interaction.response.send_message("喵嗚...找不到圖片，可能路徑有問題喵！")

class JumpModal(discord.ui.Modal):
    def __init__(self, view):
        # 標題可以動態化，讓體驗更好
        super().__init__(title="跳轉頁面")
        self.view = view
        
        # 定義輸入框
        self.page_input = discord.ui.TextInput(
            label="請輸入頁碼", 
            placeholder="例如: 1", 
            min_length=1, 
            max_length=3
        )
        self.add_item(self.page_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target = int(self.page_input.value) - 1
            
            # 判斷 View 類型並進行跳轉
            # 如果有 all_data，代表是成就/單字清單 (頁數模式)
            if hasattr(self.view, 'all_data') or hasattr(self.view, 'total_pages'):
                max_page = getattr(self.view, 'total_pages', len(getattr(self.view, 'all_data', [])))
                if 0 <= target < max_page:
                    self.view.current_page = target if hasattr(self.view, 'current_page') else target
                    self.view.page = target if hasattr(self.view, 'page') else target
                    
                    # 重新整理顯示
                    if hasattr(self.view, 'update_buttons'): self.view.update_buttons()
                    await interaction.response.edit_message(embed=self.view.get_embed(), view=self.view)
                else:
                    await interaction.response.send_message(f"❌ 頁碼超出範圍 (1-{max_page})！", ephemeral=True)
            
            # 如果是圖片模式 (index 模式)
            elif hasattr(self.view, 'image_list'):
                if 0 <= target < len(self.view.image_list):
                    self.view.index = target
                    await self.view.update_view(interaction)
                else:
                    await interaction.response.send_message(f"❌ 索引超出範圍 (1-{len(self.view.image_list)})！", ephemeral=True)
                    
        except ValueError:
            await interaction.response.send_message("❌ 請輸入有效的阿拉伯數字！", ephemeral=True)

class ImageView(discord.ui.View):
    def __init__(self, image_list):
        super().__init__(timeout=None)
        self.image_list = image_list
        self.index = 0

    def update_buttons(self):
        self.prev_btn.disabled = (self.index == 0)
        self.next_btn.disabled = (self.index >= len(self.image_list) - 1)

    async def update_view(self, interaction: discord.Interaction):
        self.update_buttons()
        embed = discord.Embed(title="逆天圖片 檢視", color=0xffc0cb)
        embed.set_image(url=self.image_list[self.index])
        embed.set_footer(text=f"第 {self.index + 1} 張 / 共 {len(self.image_list)} 張")
        
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ 上一張", style=discord.ButtonStyle.primary, custom_id="img_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        await self.update_view(interaction)

    @discord.ui.button(label="🔢 跳轉", style=discord.ButtonStyle.secondary, custom_id="img_jump")
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JumpModal(self))

    @discord.ui.button(label="➡️ 下一張", style=discord.ButtonStyle.primary, custom_id="img_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
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
    embed = discord.Embed(
        description="逆天圖片檢視系統已啟動喵！",
        color=0xffc0cb
    )
    embed.set_image(url=image_list[0])
    embed.set_footer(text=f"第 1 張 / 共 {len(image_list)} 張")
    await interaction.followup.send(embed=embed, view=ImageView(image_list))
    
    # 2. 安全更新資料庫
    row = await db.fetch("SELECT count FROM user_logs WHERE user_id = ? AND action = 'view_quotes'", (user_id,))
    count = (row['count'] + 1) if row else 1
    
    if row:
        await db.execute("UPDATE user_logs SET count = ? WHERE user_id = ? AND action = 'view_quotes'", (count, user_id))
    else:
        await db.execute("INSERT INTO user_logs (user_id, action, count) VALUES (?, 'view_quotes', 1)", (user_id,))
        
    # 3. 特定成就判定
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
            # 刪除多個相關表，確保清除乾淨
            await db.execute("DELETE FROM user_logs WHERE user_id = ?", (interaction.user.id,))
            msg = "✅ 已清除你所有的互動統計數據，重獲新生了喵！"
        else:
            # 刪除指定 action 的記錄
            await db.execute("DELETE FROM user_logs WHERE user_id = ? AND action = ?", (interaction.user.id, 項目))
            msg = f"✅ 已將你的 {項目} 統計資料歸零喵。"
        
        # 移除 db.connection.commit()，因為在大多數封裝中這是多餘的
        # 如果你的 db 類別有提供 commit 方法，請改用 await db.commit() 
        # 但絕對不要直接存取 db.connection
        
        await interaction.followup.send(msg, ephemeral=True)
        
    except Exception as e:
        print(f"DEBUG: 刪除統計失敗 - {e}")
        await interaction.followup.send(f"❌ 操作失敗，本喵處理資料時卡住了喵：{e}", ephemeral=True)

class AchievementView(discord.ui.View):
    def __init__(self, all_data, user_name=None, user_avatar=None, user_total=None, total_count=None):
        super().__init__(timeout=None)
        # 如果有 user_name，代表是個人清單；否則為成就百科
        self.is_list = user_name is not None
        self.user_name = user_name
        self.user_avatar = user_avatar
        self.user_total = user_total
        self.total_count = total_count
        
        # 分頁邏輯
        self.all_data = [all_data[i:i + 10] for i in range(0, len(all_data), 10)]
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = (self.current_page == 0)
        self.next_btn.disabled = (self.current_page >= len(self.all_data) - 1)

    def get_embed(self):
        if self.is_list:
            embed = discord.Embed(title=f"📜 {self.user_name} 的成就清單", color=0xffff00)
            embed.set_thumbnail(url=self.user_avatar)
            embed.description = f"**收集進度：** {self.user_total} / {self.total_count}\n\n" + "\n".join(self.all_data[self.current_page])
        else:
            embed = discord.Embed(title=f"📜 成就百科 (第 {self.current_page + 1}/{len(self.all_data)} 頁)", color=0x9b59b6)
            embed.description = "\n".join(self.all_data[self.current_page])
            embed.set_footer(text="提示：點擊 ||黑框|| 可以揭曉隱藏提示喵！")
        
        if not self.is_list: # 若非清單，補上頁碼資訊
            embed.set_footer(text=f"第 {self.current_page + 1} / {len(self.all_data)} 頁 | 點擊 ||黑框|| 查看提示")
        return embed

    @discord.ui.button(label="⬅️ 上一頁", style=discord.ButtonStyle.primary, custom_id="ach_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="🔢 跳轉", style=discord.ButtonStyle.secondary, custom_id="ach_jump")
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JumpModal(self))

    @discord.ui.button(label="➡️ 下一頁", style=discord.ButtonStyle.primary, custom_id="ach_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.tree.command(name="成就", description="查看你的成就清單")
async def view_achievements(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_achievements = await get_my_achievements(interaction.user.id)
    total_achievements = len(ACHIEVEMENTS)
    
    if not user_achievements:
        await interaction.followup.send("喵...你目前還沒有解鎖任何成就，快去跟本喵互動吧！")
        return

    all_items = [f"🔸 {ach}" for ach in user_achievements]
    view = AchievementView(
        all_data=all_items,
        user_name=interaction.user.display_name,
        user_avatar=interaction.user.display_avatar.url,
        user_total=len(user_achievements),
        total_count=total_achievements
    )
    await interaction.followup.send(embed=view.get_embed(), view=view)

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

@bot.tree.command(name="ai_imagine", description="讓本喵用 AI 幫你畫圖喵！🐾")
@app_commands.describe(
    prompt="請輸入圖片描述喵！(雖然有google自動翻譯，但依然建議直接使用英文，或詢問ai取得提示詞)",
    model="選擇生圖模型"
)
@app_commands.choices(
    model=[
        # --- 旗艦/高品質 ---
        app_commands.Choice(name="Flux.1 Schnell (最推薦/全能)", value="black-forest-labs/FLUX.1-schnell"),
        app_commands.Choice(name="SD 3.5 Large (高清寫實)", value="stabilityai/stable-diffusion-3-5-large"),
        
        # --- 動漫/二次元專精 ---
        app_commands.Choice(name="Animagine XL 3.1 (動漫二次元)", value="cagliostrolab/animagine-xl-3.1"),
        app_commands.Choice(name="Pony Diffusion V6 (精緻動漫)", value="strangerzonehf/Pony-Diffusion-V6-XL"),
        
        # --- 藝術/風格化 ---
        app_commands.Choice(name="Kandinsky 2.2 (油畫/抽象藝術)", value="kandinsky-community/kandinsky-2-2-decoder"),
        app_commands.Choice(name="Stable Diffusion XL 1.0 (經典風格)", value="stabilityai/stable-diffusion-xl-base-1.0"),
        
        # --- 創意與特色 ---
        app_commands.Choice(name="DreamShaper 8 (寫實動漫混合)", value="Lykon/dreamshaper-8"),
        app_commands.Choice(name="OpenDalle V1.1 (電影感/插畫)", value="dataautogpt3/OpenDalle")
    ]
)
async def imagine_slash(interaction: discord.Interaction, prompt: str, model: str = "black-forest-labs/FLUX.1-schnell"):
    # 這裡直接呼叫清理過後的 ai_imagine 函式
    await ai_imagine(interaction, prompt, model)

@bot.tree.command(name="ai", description="向 AI 提問")
@app_commands.describe(
    model="選擇 AI 模型",
    prompt="輸入內容",
    setting="選擇性格模式"
)
@app_commands.choices(
    setting=[
        app_commands.Choice(name="雜魚小貓娘", value="雜魚小貓娘"),
        app_commands.Choice(name="嚴肅模式", value="嚴肅模式"),
        app_commands.Choice(name="Debug 模式", value="Debug"),
        app_commands.Choice(name="翻譯專家", value="翻譯專家"),
        app_commands.Choice(name="程式大師", value="程式大師"),
        app_commands.Choice(name="寫作助手", value="寫作助手"),
        app_commands.Choice(name="邏輯分析師", value="邏輯分析師"),
        app_commands.Choice(name="惡毒毒舌", value="惡毒毒舌"),
        app_commands.Choice(name="速讀摘要", value="速讀摘要")
    ]
)
async def ai_slash(
    interaction: discord.Interaction, 
    model: str, 
    prompt: str, 
    setting: str = "雜魚小貓娘",
    thinking_level: str = "medium"
):
    await get_ai_response(interaction, prompt, model, setting, thinking_level)

@ai_slash.autocomplete("model")
async def model_autocomplete(interaction: discord.Interaction, current: str):
    return [c for c in MODEL_CHOICES if current.lower() in c.name.lower()][:25]

@bot.tree.command(name="ai_reset", description="清除 AI 全體對話記憶")
async def ai_reset(interaction: discord.Interaction):
    # 重置全域記憶體
    memory_storage["global"] = {"ai_messages": []}
    await interaction.response.send_message("✅ 全體 AI 記憶已重置喵！")

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
    
    # 成就檢查 (移除了內部的 title 字串，直接呼叫你原本定義的 ACHIEVEMENTS)
    if length >= 45:
        await check_and_notify_achievement(interaction, "GIANT_SIZE", ACHIEVEMENTS["GIANT_SIZE"])
    elif length <= 5:
        await check_and_notify_achievement(interaction, "MINI_SIZE", ACHIEVEMENTS["MINI_SIZE"])

@bot.tree.command(name="情緒數值", description="鑑定情緒數值喵！")
async def eq(interaction: discord.Interaction, 目標: discord.Member = None):
    target = 目標 or interaction.user
    score = random.randint(0, 180)
    
    if score < 60: 
        comment = "你的情緒控制是災難等級的吧喵？"
        await check_and_notify_achievement(interaction, "EQ_DISASTER", ACHIEVEMENTS["EQ_DISASTER"])
    elif score > 160:
        comment = "這數值...簡直冷血到了極點喵。"
        await check_and_notify_achievement(interaction, "EQ_GENIUS", ACHIEVEMENTS["EQ_GENIUS"])
    elif score < 120: 
        comment = "勉強能正常社交，雜魚合格喵。"
    else: 
        comment = "過於理性，看來是個冷血的雜魚呢喵。"
    
    embed = discord.Embed(
        description=f"{target.mention} 的情緒數值為：**{score}**\n{comment}",
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="智商數值", description="鑑定智商數值喵！")
async def iq(interaction: discord.Interaction, 目標: discord.Member = None):
    target = 目標 or interaction.user
    score = random.randint(0, 180)
    
    if score < 60: 
        comment = "這智商，大概只剩基礎的呼吸功能了吧喵。"
        await check_and_notify_achievement(interaction, "IQ_EMPTY", ACHIEVEMENTS["IQ_EMPTY"])
    elif score > 160:
        comment = "這麼高分...該不會是為了魔改歷史而生的瘋子吧喵？"
        await check_and_notify_achievement(interaction, "IQ_GENIUS", ACHIEVEMENTS["IQ_GENIUS"])
    elif score < 120: 
        comment = "普通的智商，也就是個路人雜魚喵。"
    else: 
        comment = "這智商還行，勉強脫離雜魚範圍喵。"
    
    embed = discord.Embed(
        description=f"{target.mention} 的智商數值為：**{score}**\n{comment}",
        color=0xffc0cb
    )
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
    user_id = interaction.user.id
    toy_name = 玩具.value
    
    # 1. 更新數據
    await db.execute(
        "INSERT INTO user_stats (user_id, toy_count) VALUES (?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET toy_count = toy_count + 1", (user_id,)
    )
    row = await db.fetch("SELECT toy_count FROM user_stats WHERE user_id = ?", (user_id,))
    count = row['toy_count']
    
    # 2. 產出反應
    responses = {
        "逗貓棒": "你揮著逗貓棒...本喵的眼睛跟著動了！這、這是本能反應，才不是想玩呢喵！",
        "OO玩具": "你...你這變態雜魚！拿這種東西出來，是想對本喵做什麼壞事嗎喵！(臉紅)",
        "羽毛": "輕飄飄的羽毛...本喵抓！看我的貓貓拳！...啊，被你看到了，真丟臉喵。",
        "釣竿": "你想釣本喵嗎？哼，太天真了，釣竿的誘惑力對本喵來說還差得遠呢喵！",
        "貓抓板": "磨爪子...呼，舒爽。你要一起來抓抓看嗎？...才不准你搶走呢喵！",
        "貓薄荷玩偶": "好香的味道...頭好暈，好舒服...這、這玩偶有毒！你是故意的吧喵？",
        "貓草球": "滾來滾去的...好玩！...咳咳，別以為一顆球就能收買本喵，但我還是會陪你玩的喵。"
    }
    
    # 3. 建立 Embed 並發送
    embed = discord.Embed(
        title=f"正在玩 {toy_name} 喵！",
        description=responses.get(toy_name, f"你拿著「{toy_name}」...這是什麼新花樣嗎？本喵姑且看一下好了喵。"),
        color=0xffc0cb
    )
    embed.set_footer(text=f"你已經陪本喵玩了 {count} 次玩具囉喵！")
    
    await interaction.response.send_message(embed=embed)
    
    # 4. 成就判定 (門檻皆改為次數)
    # 注意：這裡依然可以保留特定成就檢查，因為它們是基於 count 的
    if count == 20:
        await check_and_notify_achievement(interaction, "TOY_COLLECTOR", ACHIEVEMENTS["TOY_COLLECTOR"])
    elif count == 50:
        await check_and_notify_achievement(interaction, "TOY_MASTER", ACHIEVEMENTS["TOY_MASTER"])
    
    # 機率性成就 (各 10%)
    rand = random.random()
    if rand < 0.10:
        await check_and_notify_achievement(interaction, "CATNIP_ADDICT", ACHIEVEMENTS["CATNIP_ADDICT"])
    elif rand < 0.20:
        await check_and_notify_achievement(interaction, "REFLEX_TESTER", ACHIEVEMENTS["REFLEX_TESTER"])

@bot.tree.command(name="讓我草草", description="對目標發動突襲")
@app_commands.describe(目標="想要互動的對象")
async def razzle(interaction: discord.Interaction, 目標: discord.Member):
    # 1. 立即 defer，並確保只做一次
    await interaction.response.defer()
    user_id = interaction.user.id
    
    # 2. 修改資料庫讀取方式：改為索引取值，避免 Row 格式問題
    await db.execute("INSERT INTO user_stats (user_id, razzle_count) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET razzle_count = razzle_count + 1", (user_id,))
    
    # 3. 確保 row 存在再讀取
    row = await db.fetch("SELECT razzle_count FROM user_stats WHERE user_id = ?", (user_id,))
    count = row[0] if row else 1 # row[0] 永遠安全，不會有 KeyError
    
    # 4. 把可能的耗時操作（成就）放在回應之後，或者加 try 包住
    try:
        await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
        if count == 50: await check_and_notify_achievement(interaction, "RAZZLE_DAZZLE", ACHIEVEMENTS["RAZZLE_DAZZLE"])
        if random.random() < 0.10: await check_and_notify_achievement(interaction, "CHAOS_AGENT", ACHIEVEMENTS["CHAOS_AGENT"])
    except Exception as e:
        print(f"成就系統報錯: {e}")

    responses = [
        f"{interaction.user.mention} 突然撲向 {目標.mention}，一陣胡鬧之後，兩人看起來都亂糟糟的呢......(臉紅)" if 目標.id != bot.user.id else f"欸？{interaction.user.mention} 說什麼呢......太突然了喵！(臉紅)",
        f"{interaction.user.mention} 對 {目標.mention} 發起了攻勢，把對方弄得氣喘吁吁，本喵......(臉紅) 在旁邊看著都害羞了。" if 目標.id != bot.user.id else f"這、這種事情......雖然本喵是機器人，但被這樣對待還是會害羞的！(掩面)",
        f"經過一番激烈的互動，{目標.mention} 已經完全沒力氣了，{interaction.user.mention} 你也太壞心眼了喵！" if 目標.id != bot.user.id else f"{interaction.user.mention} 真大膽呢，不過既然是你，本喵就......(臉紅)",
        f"{interaction.user.mention} 毫不留情地把 {目標.mention} 弄得慘兮兮的，本喵......(臉紅) 不小心看了不該看的畫面。" if 目標.id != bot.user.id else f"唔！才剛開機不久就被 {interaction.user.mention} 這樣弄，本喵的系統都亂掉了喵！"
    ]

    embed = discord.Embed(description=random.choice(responses), color=0xffc0cb)
    
    # 5. 強制執行回應
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="榨乾", description="對目標進行持續的消耗，直到對方徹底力竭！")
@app_commands.describe(目標="想要互動的對象")
async def exhaust(interaction: discord.Interaction, 目標: discord.Member):
    await interaction.response.defer()
    user_id = interaction.user.id
    
    # 1. 資料庫更新與讀取 (使用 row[0] 避免格式錯誤)
    count = 1
    try:
        await db.execute("INSERT INTO user_stats (user_id, exhaust_count) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET exhaust_count = exhaust_count + 1", (user_id,))
        row = await db.fetch("SELECT exhaust_count FROM user_stats WHERE user_id = ?", (user_id,))
        if row:
            count = row[0]
    except Exception as e:
        print(f"DB Error (榨乾): {e}")

    # 2. 成就檢查 (加防禦處理)
    try:
        await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])
        if count == 50: await check_and_notify_achievement(interaction, "EXHAUST_MASTER", ACHIEVEMENTS["EXHAUST_MASTER"])
        if random.random() < 0.10: await check_and_notify_achievement(interaction, "ENERGY_VAMPIRE", ACHIEVEMENTS["ENERGY_VAMPIRE"])
    except Exception as e:
        print(f"成就錯誤: {e}")

    # 3. 回應邏輯
    responses = [
        f"{interaction.user.mention} 湊近了 {目標.mention}，一陣猛烈攻勢，把對方搞得氣喘吁吁，本喵......(臉紅) 也覺得好累。" if 目標.id != bot.user.id else f"{interaction.user.mention} 竟然想榨乾本喵？別做夢了，我可是有無限電力的喵！(哼)",
        f"{interaction.user.mention} 徹底把 {目標.mention} 的體力榨乾了！看著對方癱軟的樣子，真是太過分了喵。" if 目標.id != bot.user.id else f"想要榨乾本喵？{interaction.user.mention} 真是不知好歹呢，看招！(丟出閃電)",
        f"{interaction.user.mention} 對 {目標.mention} 展開了惡作劇，對方現在連一根手指都動不了了......(臉紅)" if 目標.id != bot.user.id else f"別、別亂來！本喵的電量可是要留著運作伺服器的，{interaction.user.mention} 這個大笨蛋！",
        f"被 {interaction.user.mention} 這樣折騰，{目標.mention} 已經完全失去力氣了，這可是本喵的傑作喔！" if 目標.id != bot.user.id else f"嗚......被 {interaction.user.mention} 這樣過度頻繁地存取指令，本喵的 CPU 都要過熱了......(臉紅)"
    ]

    embed = discord.Embed(description=random.choice(responses), color=0xffc0cb)
    
    # 4. 發送結果
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="廢話", description="本喵來為你說點完全沒用的廢話喵！")
async def nonsense(interaction: discord.Interaction):
    await interaction.response.defer()
    user_id = interaction.user.id

    # 1. 初次互動成就檢查
    await check_and_notify_achievement(interaction, "FIRST_INTERACTION", ACHIEVEMENTS["FIRST_INTERACTION"])

    # 2. 更新廢話使用次數
    await db.execute(
        "INSERT INTO user_stats (user_id, nonsense_count) VALUES (?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET nonsense_count = nonsense_count + 1",
        (user_id,)
    )
    
    # 3. 獲取當前次數
    row = await db.fetch("SELECT nonsense_count FROM user_stats WHERE user_id = ?", (user_id,))
    count = row['nonsense_count'] if row else 1
    
    # 4. 產出廢話並製作 Embed (統一色碼 0xffc0cb)
    msg = random.choice(nonsense_responses)
    embed = discord.Embed(
        title="本喵的廢話時間喵！",
        description=msg,
        color=0xffc0cb
    )
    embed.set_footer(text=f"你已經聽了 {count} 次本喵的廢話囉喵！")
    
    # 5. 回應訊息
    await interaction.followup.send(embed=embed)
    
    # 6. 門檻成就判定
    if count == 50:
        await check_and_notify_achievement(interaction, "TRASH_LISTENER", ACHIEVEMENTS["TRASH_LISTENER"])
    elif count == 100:
        await check_and_notify_achievement(interaction, "TRASH_SCHOLAR", ACHIEVEMENTS["TRASH_SCHOLAR"])
    elif count == 200:
        await check_and_notify_achievement(interaction, "TRASH_ADDICT", ACHIEVEMENTS["TRASH_ADDICT"])
    elif count == 500:
        await check_and_notify_achievement(interaction, "TRASH_TRANSCENDENT", ACHIEVEMENTS["TRASH_TRANSCENDENT"])
    
    # 7. 機率性成就判定
    rand = random.random()
    if rand < 0.075:
        await check_and_notify_achievement(interaction, "TRASH_LISTENER_LUCKY", ACHIEVEMENTS["TRASH_LISTENER_LUCKY"])
    elif rand < 0.15:
        await check_and_notify_achievement(interaction, "TRASH_ENLIGHTENED", ACHIEVEMENTS["TRASH_ENLIGHTENED"])
    elif rand < 0.225:
        await check_and_notify_achievement(interaction, "TRASH_BLESSED", ACHIEVEMENTS["TRASH_BLESSED"])
    elif rand < 0.30:
        await check_and_notify_achievement(interaction, "TRASH_POISON", ACHIEVEMENTS["TRASH_POISON"])

@bot.tree.command(name="摸摸頭", description="給予目標溫暖的摸摸頭！")
@app_commands.describe(目標="想要摸摸頭的對象")
async def pat(interaction: discord.Interaction, 目標: discord.Member):
    # 判斷回應內容
    if 目標 == interaction.user:
        desc = f"{interaction.user.mention} 摸了摸自己的頭，辛苦了！"
    elif 目標.id == bot.user.id:
        desc = f"{interaction.user.mention} 摸了摸頭，感覺很舒服喵！(〃∀〃)"
    else:
        desc = f"{interaction.user.mention} 輕輕摸了摸 {目標.mention} 的頭！"

    # 建立嵌入式訊息
    embed = discord.Embed(description=desc, color=0xffc0cb)
    
    # 發送回應
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="會考資源", description="整理好的歷屆試題與線上測驗資源喵！")
async def exam_resources(interaction: discord.Interaction):
    description = (
        "幫你整理了各種資源，要認真點別當雜魚喵：\n\n"
        "**【官方與題庫下載】**\n"
        "• [國中教育會考官網 - 歷屆試題](https://cap.rcpet.edu.tw/Examination.html)\n"
        "• [國家教育研究院 - 教育會考題庫](https://exam.naer.edu.tw/)\n"
        "• [台灣測驗中心 - 歷屆試題下載](https://www.testcenter.org.tw/)\n\n"
        "**【線上模擬與練習】**\n"
        "• [StudyBank - 會考考古題專區](https://www.studybank.com.tw/exam/cap/questions)\n"
        "• [翰林雲端學院 - 會考線上測驗](https://www.ehanlin.com.tw/exam/cap.html)\n"
        "• [南一書局 - 線上題庫練習](https://www.nani.com.tw/)\n\n"
        "**【高效率學習頻道】**\n"
        "• [均一教育平台 - 會考複習](https://www.junyiacademy.org/)\n"
        "• [考前衝刺 - 學習吧](https://www.learnmode.net/)\n"
        "• [Youtube - 數學名師頻道](https://www.youtube.com/@math-tw)\n"
        "• [Youtube - 國文名師頻道](https://www.youtube.com/@chinese-tw)"
    )
    
    embed = discord.Embed(
        title="會考歷屆試題與學習資源",
        description=description,
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed)

class WordView(discord.ui.View):
    def __init__(self, data_list, user_id):
        super().__init__(timeout=None)
        self.data_list = data_list
        self.user_id = user_id
        self.current_page = 0
        self.total_pages = len(data_list)
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 這不是你的單字卡，請使用 /英單字卡 指令建立自己的。", ephemeral=True)
            return False
        return True

    def update_buttons(self):
        # 設定按鈕狀態與顏色
        self.prev_button.disabled = (self.current_page <= 0)
        self.prev_button.style = discord.ButtonStyle.secondary
        
        self.next_button.disabled = (self.current_page >= self.total_pages - 1)
        self.next_button.style = discord.ButtonStyle.secondary
        
        self.jump_button.style = discord.ButtonStyle.primary

    def get_embed(self):
        word, definition = self.data_list[self.current_page]
        embed = discord.Embed(title=f"單字: {word}", description=f"定義: {definition}")
        embed.set_footer(text=f"第 {self.current_page + 1} / {self.total_pages} 個")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="prev", row=0)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.refresh(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="next", row=0)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.refresh(interaction)

    @discord.ui.button(label="🔢 單字頁面跳轉", style=discord.ButtonStyle.primary, custom_id="jump", row=1)
    async def jump_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JumpModal(self))

    async def refresh(self, interaction: discord.Interaction):
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.tree.command(name="英單字卡", description="獲取單字卡")
async def english_cards(interaction: discord.Interaction):
    await interaction.response.defer() 
    
    data_list = list(WORDS_DATA.items())
    # 傳入 interaction.user.id
    view = WordView(data_list, user_id=interaction.user.id)
    await interaction.followup.send(embed=view.get_embed(), view=view)

@bot.tree.command(name="刪除資料", description="清除你的個人統計資料")
@app_commands.describe(data_type="選擇要刪除的資料類別 (全部/成就/統計/生日)")
@app_commands.choices(data_type=[
    app_commands.Choice(name="全部", value="all"),
    app_commands.Choice(name="成就", value="achievements"),
    app_commands.Choice(name="統計", value="logs"),
    app_commands.Choice(name="生日", value="birthdays")
])
# 移除 "= 'all'" 預設值，使參數成為必要
async def delete_data(interaction: discord.Interaction, data_type: str):
    user_id = interaction.user.id
    
    # 定義中文映射
    type_names = {
        "all": "所有相關資料",
        "achievements": "成就紀錄",
        "logs": "統計數據",
        "birthdays": "生日設定"
    }
    
    try:
        # 根據選擇的類別執行對應的 DELETE
        if data_type == "all" or data_type == "achievements":
            await db.execute("DELETE FROM user_achievements WHERE user_id = ?", (user_id,))
        
        if data_type == "all" or data_type == "logs":
            await db.execute("DELETE FROM user_logs WHERE user_id = ?", (user_id,))
            
        if data_type == "all" or data_type == "birthdays":
            await db.execute("DELETE FROM user_birthdays WHERE user_id = ?", (user_id,))
        
        # 確認執行結果
        await interaction.response.send_message(
            f"喵！已成功清除你的 **{type_names.get(data_type, data_type)}**。", 
            ephemeral=True
        )
        
    except Exception as e:
        await interaction.response.send_message(f"喵... 刪除過程中發生了錯誤，請再試一次喵：{e}", ephemeral=True)

class PermissionPaginationView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        # 上一頁：第一頁時禁用並變灰
        self.prev_page.disabled = (self.current_page == 0)
        self.prev_page.style = discord.ButtonStyle.secondary if self.prev_page.disabled else discord.ButtonStyle.primary
        
        # 下一頁：最後一頁時禁用並變灰
        self.next_page.disabled = (self.current_page == len(self.pages) - 1)
        self.next_page.style = discord.ButtonStyle.secondary if self.next_page.disabled else discord.ButtonStyle.primary

    def get_embed(self):
        return discord.Embed(
            description=f"本喵的權限檢查報告 ({self.current_page + 1}/{len(self.pages)}) 喵：\n\n{self.pages[self.current_page]}",
            color=0xffc0cb
        )

    @discord.ui.button(label="上一頁")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="下一頁")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class PermissionPaginationView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        # 上一頁：第一頁時禁用並變灰
        self.prev_page.disabled = (self.current_page == 0)
        self.prev_page.style = discord.ButtonStyle.secondary if self.prev_page.disabled else discord.ButtonStyle.primary
        
        # 下一頁：最後一頁時禁用並變灰
        self.next_page.disabled = (self.current_page == len(self.pages) - 1)
        self.next_page.style = discord.ButtonStyle.secondary if self.next_page.disabled else discord.ButtonStyle.primary

    def get_embed(self):
        return discord.Embed(
            description=f"本喵的權限檢查報告 ({self.current_page + 1}/{len(self.pages)}) 喵：\n\n{self.pages[self.current_page]}",
            color=0xffc0cb
        )

    @discord.ui.button(label="上一頁")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="下一頁")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.tree.command(name="權限檢查", description="檢查本喵在此伺服器的所有權限喵！")
async def check_permissions(interaction: discord.Interaction):
    perms = interaction.guild.me.guild_permissions
    
    perm_map = {
        "administrator": "管理者", "manage_guild": "管理伺服器", "view_audit_log": "檢視審核紀錄",
        "view_channel": "檢視頻道", "manage_channels": "管理頻道", "manage_roles": "管理身分組",
        "manage_emojis_and_stickers": "管理表情符號與貼圖", "manage_webhooks": "管理 Webhooks",
        "view_guild_insights": "檢視伺服器分析", "manage_messages": "管理訊息",
        "send_messages": "發送訊息", "embed_links": "嵌入連結", "attach_files": "附件檔案",
        "read_message_history": "讀取訊息紀錄", "mention_everyone": "提及 @everyone",
        "use_external_emojis": "使用外部表情符號", "add_reactions": "新增反應",
        "connect": "連接語音", "speak": "語音發言", "mute_members": "靜音成員",
        "deafen_members": "取消成員聽力", "move_members": "移動成員", "use_voice_activation": "語音活動",
        "manage_nicknames": "管理暱稱", "manage_events": "管理活動", "moderate_members": "審核成員",
        "request_to_speak": "要求發言", "create_instant_invite": "建立邀請", "kick_members": "踢出成員",
        "ban_members": "封鎖成員", "change_nickname": "更改暱稱", "send_messages_in_threads": "在討論串發言",
        "create_public_threads": "建立公開討論串", "create_private_threads": "建立私人討論串",
        "send_tts_messages": "發送語音訊息", "use_application_commands": "使用應用程式指令"
    }

    # 產生帶有間距的清單
    status_list = []
    # perms 本身是 Permissions 物件，需使用 iter(perms) 或直接存取
    for name, value in perms:
        display_name = perm_map.get(name, name.replace('_', ' ').title())
        icon = "✅" if value else "❌"
        # 這裡加入 \u200B 撐開間距
        status_list.append(f"{icon} {display_name}\n\u200B")
    
    # 每頁 10 項
    pages = ["".join(status_list[i:i + 10]) for i in range(0, len(status_list), 10)]
    
    view = PermissionPaginationView(pages)
    await interaction.response.send_message(embed=view.get_embed(), view=view)

@bot.tree.command(name="踢出", description="踢出伺服器成員喵！")
@app_commands.describe(成員="要踢出的成員", 原因="踢出的原因")
async def kick_member(interaction: discord.Interaction, 成員: discord.Member, 原因: str = "無"):
    # 權限檢查：開發者無需檢查；其他人須具備踢人權限
    if interaction.user.id != DEVELOPER_ID:
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("喵？你沒有權限使用這個功能喔！", ephemeral=True)
    
    # 本體權限檢查
    if not interaction.guild.me.guild_permissions.kick_members:
        return await interaction.response.send_message("喵...本喵沒有踢出成員的權限！", ephemeral=True)
    
    # 防止踢出擁有更高權限的人
    if 成員.top_role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("這傢伙地位太高了，本喵踢不動喵！", ephemeral=True)

    try:
        await 成員.kick(reason=原因)
        embed = discord.Embed(
            description=f"✅ 已成功將 {成員.mention} 踢出伺服器喵！\n原因：{原因}",
            color=0xffc0cb
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"踢出失敗了喵...錯誤代碼：{e}", ephemeral=True)

@bot.tree.command(name="重置暱稱", description="[限管] 強制將機器人暱稱重置為空（即顯示原始名稱）")
@admin_or_dev_only
async def reset_bot_nick(interaction: discord.Interaction):
    try:
        # 將機器人自己的暱稱設為 None，Discord 就會恢復顯示原始名稱
        await interaction.guild.me.edit(nick=None)
        await interaction.response.send_message("✅ 喵！機器人暱稱已重置成功！", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ 重置失敗：{e}", ephemeral=True)

@bot.tree.command(name="help", description="顯示功能說明書")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 雜魚小貓娘 | 功能說明書", 
        description="本喵負責娛樂、數據檢測與防禦保護。", 
        color=0xffc0cb
    )
    
    embed.add_field(name="🛡️ 防禦與保護 (限管)", value=(
        "• **/保護等級**：設定頻道防炸強度。\n"
        "• **/關鍵詞檢測**：切換敏感詞攔截系統。\n"
        "• **/重置暱稱**：還原本喵暱稱設定。\n"
        "• **/踢出**：快速移除惡意或違規成員。"
    ), inline=False)
    
    embed.add_field(name="🛠️ 實用工具", value=(
        "• **/ai**：深度邏輯對話與分析。\n"
        "• **/翻譯**：多國語言即時轉換。\n"
        "• **/狀態監測**：查看伺服器與機器人負載。\n"
        "• **/ping**：API 連線延遲檢測。\n"
        "• **/刪除我的統計**：清除互動統計數據。"
    ), inline=False)
    
    embed.add_field(name="🎮 娛樂與互動", value=(
        "• **/game_2048**：2048 益智遊戲。\n"
        "• **/game_memory**：記憶翻牌挑戰。\n"
        "• **/game_ooxx**：3x3/5x5 圈圈叉叉對戰。\n"
        "• **/ooxx_rank**：查看勝場與連勝榜。\n"
        "• **/你知道嗎**：隨機冷知識。\n"
        "• **/小提示**：操作技巧或廢話。\n"
        "• **/廢話**：聽本喵說廢話。\n"
        "• **/餵食**：給予本喵貢品。\n"
        "• **/猜拳**：跟本喵一決高下。\n"
        "• **/求籤/祈福**：每日運勢與祈福。\n"
        "• **/36計**：今日錦囊妙計。\n"
        "• **/尋找色色群主**：呼叫色色的星音群主。\n"
        "• **/摸摸頭**：摸摸頭互動。\n"
        "• **/榨乾/讓我草草**：惡搞互動。\n"
        "• **/本喵要玩玩具**：逗本喵互動。\n"
        "• **/看雜魚小貓娘/逆天圖片**：私藏圖庫。\n"
        "• **/各類指數**：鑑定屬性、性格、智商與數值。"
    ), inline=False)
    
    embed.add_field(name="🎂 生日與成就", value=(
        "• **/成就百科**：解鎖清單與隱藏提示。\n"
        "• **/設定生日頻道**：設定生日公告頻道。\n"
        "• **/生日設定/隱私權/倒數**：生日紀錄與驚喜。"
    ), inline=False)
    
    embed.add_field(name="⚡ 自動觸發系統", value=(
        "• 關鍵詞互動：觸發特定詞可獲得隱藏成就與回覆。"
    ), inline=False)
    
    embed.set_footer(text=f"💡 {random.choice(TIPS)} | 最後更新: 2026-06-14")
    await interaction.response.send_message(embed=embed)

# ==================== 開發者專用指令  ====================

@bot.tree.command(name="關機", description="強制關閉機器人視窗 (限開發者)")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.response.send_message("走開，只有本喵的開發者能用喵！", ephemeral=True)
    
    embed = discord.Embed(
        title="系統關機",
        description="本喵要下線休息並關閉視窗了，雜魚們再見！",
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)
    
    await asyncio.sleep(1)
    os._exit(0)

@bot.tree.command(name="重啟", description="強制重啟機器人 (限開發者)")
async def restart(interaction: discord.Interaction):
    if interaction.user.id != DEVELOPER_ID:
        return await interaction.response.send_message("走開，只有本喵的開發者能用喵！", ephemeral=True)
    
    embed = discord.Embed(
        title="系統重啟",
        description="正在關閉視窗並重啟程式，請稍候...",
        color=0xffc0cb
    )
    await interaction.response.send_message(embed=embed, ephemeral=False)
    
    if hasattr(db, 'close'):
        await db.close()
    
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    cmd = f'start wt -d "{script_dir}" cmd /k "{sys.executable}" "{script_path}"'
    subprocess.Popen(cmd, shell=True)
    
    await asyncio.sleep(1)
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
    if member.guild.id == 1497761780393578496:
        channel = bot.get_channel(1497761780393578496)
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
    if member.guild.id == 1497761780393578496:
        channel = bot.get_channel(1497761780393578496)
        if channel:
            embed = discord.Embed(
                title="👋 成員離開喵...",
                description=f"{member.display_name} 離開了我們喵，真是個無情的傢伙QAQ。",
                color=0x808080
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

# 統一互動處理邏輯
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # 1. 全域成就檢查
    await trigger_first_interaction_check(interaction)
    
    # 2. 元件互動處理 (按鈕等)
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "ooxx_rank_btn": # 已修正為 ooxx
            await ooxx_rank(interaction)
        # 若有其他按鈕邏輯可繼續擴充
        else:
            await bot.tree.on_interaction(interaction)
            
    # 3. 斜線指令處理
    else:
        await bot.tree.on_interaction(interaction)

@tasks.loop(time=datetime_time(hour=7, minute=0, tzinfo=taipei_tz))
async def daily_countdown():
    channel = bot.get_channel(1493902370013188221)
    if channel:
        target = get_next_exam_date()
        
        # 1. 確保兩個時間都是帶有台北時區的對象，避免減法報錯
        now = datetime.now(taipei_tz)
        
        # 2. 如果 target 沒有時區，賦予它台北時區
        if target.tzinfo is None:
            target = target.replace(tzinfo=taipei_tz)
            
        # 3. 計算剩餘天數 (使用 .days 會向下取整，建議視需求用 ceil)
        days_left = (target - now).days
        
        embed = discord.Embed(
            description=f"早安！距離 {target.year} 年會考還有 **{days_left}** 天，請保持專注喵。",
            color=0xffc0cb
        )
        await channel.send(embed=embed)

# 啟動與維護邏輯
async def start_bot_with_recovery():
    while True:
        try:
            await db.setup()
            print("✅ 資料庫已就緒")
            break
        except Exception as e:
            print(f"\n❌ 資料庫錯誤: {e}")
            # 為保持效率，直接簡化流程
            await asyncio.sleep(5)
            print("正在嘗試重新連線...")

async def main():
    if not TOKEN:
        print("❌ 錯誤：TOKEN 為空，請檢查 .env 檔案。")
        return
    print(f"🚀 正在嘗試連線至 Discord")
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        # 確保資料庫先行初始化
        asyncio.run(start_bot_with_recovery())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程式已由使用者手動停止。")
    finally:
        # 確保關閉資料庫
        asyncio.run(db.close())