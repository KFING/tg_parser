import re
from pathlib import Path


def extract_clean_text_from_srt(srt_path: Path) -> str:

    try:
        content = srt_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = srt_path.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            content = srt_path.read_text(encoding='latin-1')

    content = re.sub(r'\[.*?\]', '', content)

    lines = content.split('\n')
    text_lines = []

    for line in lines:
        line = line.strip()
        if not line or line.isdigit() or '-->' in line:
            continue
        text_lines.append(line)
    clean_text = ' '.join(text_lines)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

