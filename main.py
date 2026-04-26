import os
import time
import requests
from googleapiclient.discovery import build
import vk_api
from TikTokApi import TikTokApi

# ================= ENV =================

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
VK_TOKEN = os.getenv("VK_TOKEN")

# ================= SETTINGS =================

KEYWORDS = [
    "как оформить карту",
    "как получить карту",
    "где взять карту",
    "дебетовая карта",
    "кредитная карта",
    "какую карту выбрать",
    "банк отзывы",
    "карта условия",
    "как открыть счет",
    "нужна карта",
    "посоветуйте банк",
    "какой банк лучше"
]

CHECK_INTERVAL = 60

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
vk = vk_api.VkApi(token=VK_TOKEN)
vk_api_client = vk.get_api()

checked_comments = set()

# ================= SCORE =================

def get_lead_score(text):
    text = text.lower()
    score = 0

    strong = ["хочу", "нужна карта", "оформить карту", "скинь", "где оформить"]
    medium = ["как", "где", "какой банк", "посоветуйте", "что лучше"]

    for w in strong:
        if w in text:
            score += 3

    for w in medium:
        if w in text:
            score += 1

    return score

def get_level(score):
    if score >= 4:
        return "🔥 ГОРЯЧИЙ"
    elif score >= 2:
        return "🟡 ТЁПЛЫЙ"
    else:
        return "⚪ СЛАБЫЙ"

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ================= YOUTUBE =================

def search_youtube():
    results = []

    for keyword in KEYWORDS:
        videos = youtube.search().list(
            q=keyword,
            part="id",
            type="video",
            order="relevance",
            maxResults=25
        ).execute().get("items", [])

        for video in videos:
            video_id = video["id"]["videoId"]

            comments = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100
            ).execute().get("items", [])

            for c in comments:
                text = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                cid = c["snippet"]["topLevelComment"]["id"]

                results.append({
                    "id": cid,
                    "text": text,
                    "link": f"https://youtube.com/watch?v={video_id}",
                    "platform": "YouTube"
                })

    return results

# ================= VK =================

def search_vk():
    results = []

    for keyword in KEYWORDS:
        posts = vk_api_client.newsfeed.search(q=keyword, count=20)

        for post in posts["items"]:
            owner_id = post["owner_id"]
            post_id = post["id"]

            comments = vk_api_client.wall.getComments(
                owner_id=owner_id,
                post_id=post_id,
                count=50
            )["items"]

            for c in comments:
                text = c.get("text", "")
                cid = f"vk_{c['id']}"

                results.append({
                    "id": cid,
                    "text": text,
                    "link": f"https://vk.com/wall{owner_id}_{post_id}",
                    "platform": "VK"
                })

    return results

# ================= TIKTOK =================

def search_tiktok():
    results = []

    try:
        with TikTokApi() as api:
            for keyword in KEYWORDS:
                videos = api.search.videos(keyword, count=5)

                for video in videos:
                    for c in video.comments(count=30):
                        results.append({
                            "id": f"tt_{c.id}",
                            "text": c.text,
                            "link": f"https://www.tiktok.com/video/{video.id}",
                            "platform": "TikTok"
                        })
    except:
        pass

    return results

# ================= PROCESS =================

def process_comments(comments):
    for comment in comments:
        if comment["id"] in checked_comments:
            continue

        checked_comments.add(comment["id"])

        score = get_lead_score(comment["text"])
        level = get_level(score)

        if score >= 1:
            send_telegram(
                f"{level} {comment['platform']}\n\n{comment['text']}\n\n{comment['link']}"
            )

# ================= MAIN =================

def main():
    print("🚀 ULTRA BOT STARTED")

    while True:
        try:
            process_comments(search_youtube())
            process_comments(search_vk())
            process_comments(search_tiktok())

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
