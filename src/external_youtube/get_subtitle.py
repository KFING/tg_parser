import json

import yt_dlp

def get_video_info(url):
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        return info

data = get_video_info('''https://www.youtube.com/watch?v=Z4hVGCWH1Kc''')
with open('video_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
