import json

import yt_dlp

# def parse_yt_dlp_data_about_video(data: dict[str, str]):

def get_video_info(url):
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        return info

data = get_video_info('''https://www.youtube.com/watch?v=GAeB5jpYokk''')
print(type(data))
with open('video_info_no_beast.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
