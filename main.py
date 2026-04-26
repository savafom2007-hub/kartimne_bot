import os
import time
import requests
from googleapiclient.discovery import build

# ================= ENV =================

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not all([YOUTUBE_API_KEY, TELEGRAM_TOKEN, CHAT_ID]):
    print("❌ Missing environment variables")
    exit()

# ================= SETTINGS =================

KEYWORDS = [
    "как оформить карту т банк",
    "дебетовая карта 2026",
    "лучшая банковская карта",
    "т банк отзывы"
]

CHECK_INTERVAL = 180  # 3 min

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

checked_comments = set()

# ================= SMART LEAD SCORE =================

def get_lead_score(text):
    text = text.lower()
    score = 0

    strong = [
        "хочу карту",
        "оформить карту",
        "заказать карту",
        "как получить карту",
        "где оформить",
        "скинь ссылку",
        "нужна карта",
        "хочу оформить"
    ]

    medium = [
        "как оформить",
        "как сделать",
        "где взять",
        "как получить",
        "условия",
        "какая карта",
        "подскажите карту"
    ]

    weak = [
        "как",
        "что",
        "скинь",
        "можно",
        "есть",
        "подскажите"
    ]

    for w in strong:
        if w in text:
            score += 3

    for w in medium:
        if w in text:
            score += 1

    for w in weak:
        if w in text:
            score += 0.2

    return score

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram error:", e)

# ================= YOUTUBE =================

def search_videos():
    try:
        request = youtube.search().list(
            q=" OR ".join(KEYWORDS),
            part="id,snippet",
            type="video",
            order="date",
            maxResults=5
        )
        return request.execute().get("items", [])
    except Exception as e:
        print("Search error:", e)
        return []

def get_comments(video_id):
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=20,
            order="time"
        )
        return request.execute().get("items", [])
    except:
        return []

# ================= MAIN =================

def main():
    print("🚀 Railway bot started")

    while True:
        try:
            videos = search_videos()

            for video in videos:
                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]

                comments = get_comments(video_id)

                for comment in comments:
                    c = comment["snippet"]["topLevelComment"]
                    comment_id = c["id"]
                    text = c["snippet"]["textDisplay"]

                    if comment_id in checked_comments:
                        continue

                    checked_comments.add(comment_id)

                    score = get_lead_score(text)

                    # только реальные лиды
                    if score >= 3:

                        if score >= 5:
                            level = "🔴 HOT LEAD"
                        else:
                            level = "🟠 warm lead"

                        message = (
                            f"{level}\n\n"
                            f"💬 {text}\n\n"
                            f"🎥 {title}\n"
                            f"https://youtube.com/watch?v={video_id}"
                        )

                        send_telegram(message)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
