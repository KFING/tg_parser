# pip install pysrt
import pysrt


def extract_text_with_pysrt(srt_file_path: str) -> str:
    subs = pysrt.open(srt_file_path)
    text_lines = []

    for sub in subs:
        # Удаляем текст в скобках и лишние пробелы
        clean_text = re.sub(r'\[.*?\]', '', sub.text).strip()
        if clean_text:
            text_lines.append(clean_text)

    return ' '.join(text_lines)


# Использование
text = extract_text_with_pysrt('subtitles.srt')
print(text)
