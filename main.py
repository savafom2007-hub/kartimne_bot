import os
import time
import requests
from googleapiclient.discovery import build
import vk_api

# ================= ENV =================

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
VK_TOKEN = os.getenv("VK_TOKEN")

# ================= SETTINGS =================

KEYWORDS = [
    "как оформить карту",
    "дебетовая карта",
    "какую карту выбрать"
]

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
vk = vk_api.VkApi(token=VK_TOKEN)
vk_api_client = vk.get_api()

checked_comments = set()
video_cache = []

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ================= SCORE =================

def get_lead_score(text):
    text = text.lower()

    if any(x in text for x in ["хочу", "оформить", "скинь", "где оформить"]):
        return 3
    if any(x in text for x in ["как", "где", "посоветуйте"]):
        return 1
    return 0

# ================= YOUTUBE =================

def update_videos():
    global video_cache

    print("🔎 обновляем видео...")

    try:
        res = youtube.search().list(
            q=" OR ".join(KEYWORDS),
            part="id",
            type="video",
            order="date",
            maxResults=3
        ).execute()

        video_cache = [v["id"]["videoId"] for v in res["items"]]

    except Exception as e:
        print("YT search error:", e)

def check_youtube_comments():
    for vid in video_cache:
        try:
            res = youtube.commentThreads().list(
                part="snippet",
                videoId=vid,
                maxResults=5
            ).execute()

            for item in res["items"]:
                c = item["snippet"]["topLevelComment"]
                text = c["snippet"]["textDisplay"]
                cid = c["id"]

                if cid in checked_comments:
                    continue

                checked_comments.add(cid)

                score = get_lead_score(text)

                if score >= 1:
                    send_telegram(f"🔥 YouTube\n\n{text}\n\nhttps://youtube.com/watch?v={vid}")

        except Exception as e:
            print("YT comment error:", e)

# ================= VK =================

def check_vk():
    try:
        posts = vk_api_client.newsfeed.search(q="карта банк", count=5)

        for post in posts["items"]:
            owner_id = post["owner_id"]
            post_id = post["id"]

            comments = vk_api_client.wall.getComments(
                owner_id=owner_id,
                post_id=post_id,
                count=10
            )["items"]

            for c in comments:
                text = c.get("text", "")
                cid = f"vk_{c['id']}"

                if cid in checked_comments:
                    continue

                checked_comments.add(cid)

                score = get_lead_score(text)

                if score >= 1:
                    send_telegram(f"🔥 VK\n\n{text}\n\nhttps://vk.com/wall{owner_id}_{post_id}")

    except Exception as e:
        print("VK error:", e)

# ================= MAIN =================

def main():
    print("🚀 BOT STARTED")

    last_update = 0

    while True:
        try:
            now = time.time()

            # обновляем видео раз в 30 минут
            if now - last_update > 1800:
                update_videos()
                last_update = now

            check_youtube_comments()
            check_vk()

            time.sleep(120)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
