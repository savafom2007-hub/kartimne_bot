import time
import requests
from googleapiclient.discovery import build

# ================= НАСТРОЙКИ =================

# Что ищем
KEYWORDS = [
    "как оформить карту т банк",
    "дебетовая карта 2026",
    "лучшая банковская карта",
    "т банк отзывы"
]

# "Сигналы" горячих клиентов
TRIGGERS = [
    "как оформить",
    "как сделать",
    "где взять",
    "скинь ссылку",
    "хочу карту",
    "как получить",
    "что нужно"
]

CHECK_INTERVAL = 180  # каждые 3 минуты

# ============================================

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
checked_comments = set()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except:
        pass

def search_videos():
    request = youtube.search().list(
        q=" OR ".join(KEYWORDS),
        part="id,snippet",
        type="video",
        order="date",
        maxResults=5
    )
    response = request.execute()
    return response["items"]

def get_comments(video_id):
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=20,
            order="time"
        )
        response = request.execute()
        return response["items"]
    except:
        return []

def is_hot_comment(text):
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in TRIGGERS)

def main():
    print("🚀 Бот запущен...")

    while True:
        try:
            videos = search_videos()

            for video in videos:
                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]

                comments = get_comments(video_id)

                for comment in comments:
                    comment_data = comment["snippet"]["topLevelComment"]
                    comment_id = comment_data["id"]
                    text = comment_data["snippet"]["textDisplay"]

                    if comment_id in checked_comments:
                        continue

                    checked_comments.add(comment_id)

                    if is_hot_comment(text):
                        message = (
                            f"🔥 Найден потенциальный клиент!\n\n"
                            f"💬 Комментарий:\n{text}\n\n"
                            f"🎥 Видео: {title}\n"
                            f"https://youtube.com/watch?v={video_id}"
                        )
                        send_telegram(message)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
