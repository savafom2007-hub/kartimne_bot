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

if not all([YOUTUBE_API_KEY, TELEGRAM_TOKEN, CHAT_ID, VK_TOKEN]):
    print("❌ Missing ENV variables")
    exit()

# ================= SETTINGS =================

KEYWORDS = [
    "как оформить карту",
    "дебетовая карта",
    "лучшая карта",
    "банк отзывы"
]

CHECK_INTERVAL = 30

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

vk = vk_api.VkApi(token=VK_TOKEN)
vk_api_client = vk.get_api()

checked_comments = set()

# ================= SCORE =================

def get_lead_score(text):
    text = text.lower()
    score = 0

    strong = ["хочу карту", "оформить карту", "нужна карта", "скинь ссылку"]
    medium = ["как оформить", "где взять", "как получить"]

    for w in strong:
        if w in text:
            score += 3

    for w in medium:
        if w in text:
            score += 1

    return score

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        pass

# ================= VK =================

def search_vk():
    results = []

    for keyword in KEYWORDS:
        posts = vk_api_client.newsfeed.search(q=keyword, count=5)

        for post in posts["items"]:
            owner_id = post["owner_id"]
            post_id = post["id"]

            comments = vk_api_client.wall.getComments(
                owner_id=owner_id,
                post_id=post_id,
                count=20
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

# ================= YOUTUBE =================

def search_youtube():
    results = []

    videos = youtube.search().list(
        q=" OR ".join(KEYWORDS),
        part="id,snippet",
        type="video",
        order="date",
        maxResults=5
    ).execute().get("items", [])

    for video in videos:
        video_id = video["id"]["videoId"]

        comments = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=20
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

# ================= TIKTOK =================

def search_tiktok():
    results = []

    try:
        with TikTokApi() as api:
            for keyword in KEYWORDS:
                videos = api.search.videos(keyword, count=3)

                for video in videos:
                    for c in video.comments(count=20):
                        results.append({
                            "id": f"tt_{c.id}",
                            "text": c.text,
                            "link": f"https://www.tiktok.com/video/{video.id}",
                            "platform": "TikTok"
                        })
    except Exception as e:
        print("TikTok error:", e)

    return results

# ================= PROCESS =================

def process_comments(comments):
    for comment in comments:
        if comment["id"] in checked_comments:
            continue

        checked_comments.add(comment["id"])

        score = get_lead_score(comment["text"])
        if score >= 1:
            send_telegram(
                f"🔥 {comment['platform']} ЛИД\n\n{comment['text']}\n\n{comment['link']}"
            )

# ================= MAIN =================

def main():
    print("🚀 Bot started (no auto replies)")

    while True:
        try:
            process_comments(search_vk())
            process_comments(search_youtube())
            process_comments(search_tiktok())

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
