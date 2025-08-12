import subprocess
from datetime import datetime

# === Настройки ===
channels = [
    "https://www.youtube.com/@jp-f6s",
    # Добавь сюда сколько угодно каналов
]

# Укажи временной промежуток
date_start = "20250710"  # формат YYYYMMDD
date_end = "20250713"    # формат YYYYMMDD

# Путь к лог-файлу
log_file = "yt_download_log.txt"


def download_videos(channel_url, start_date, end_date):
    print(f"📥 Загрузка видео с канала: {channel_url}")
    command = [
        "yt-dlp",
        "--dateafter", start_date,
        "--datebefore", end_date,
        "--output", "%(uploader)s/%(upload_date)s_%(title)s.%(ext)s",
        "--yes-playlist",  # если это плейлист, скачает весь
        channel_url
    ]

    try:
        result = subprocess.run(command, text=True, capture_output=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] Канал: {channel_url}\n")
            f.write(result.stdout)
            f.write(result.stderr)
        print("✅ Завершено\n")
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")


def main():
    print("=== Старт загрузки видео ===\n")
    for channel in channels:
        download_videos(channel, date_start, date_end)
    print("=== Все загрузки завершены ===")


if __name__ == "__main__":
    main()
