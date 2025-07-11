"""from googleapiclient.discovery import build

# Ваш API-ключ
API_KEY = "AIzaSyBdw01J_cNbZE5iv26nnNeyQjzW9zKpiHk"

# ID видео, для которого нужно получить субтитры
VIDEO_ID = "zajUgQLviwk"  # Пример ID видео

# Создаем сервис
youtube = build("youtube", "v3", developerKey=API_KEY)

# Получаем список субтитров
request = youtube.captions().list(part="snippet", videoId=VIDEO_ID)
response = request.execute()

# Выводим доступные субтитры
for item in response["items"]:
    print(f"Язык: {item['snippet']['language']}, ID субтитров: {item['id']}")
"""
