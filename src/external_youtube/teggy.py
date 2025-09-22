from datetime import datetime

date_str = "20250722"
date_obj = datetime.strptime(date_str, "%Y%m%d")
print(date_obj)  # 2025-07-22 00:00:00
