# config.py

# URL cơ bản của trang tìm kiếm trên Lazada
BASE_URL = "https://www.lazada.vn/catalog/?"

# Headers để giả lập trình duyệt
HEADERS = {
    "User-Agent": "", #FILL IN HERE
    "Accept": "", #FILL IN HERE
    "Accept-Language": "", #FILL IN HERE
    "Referer": "https://www.lazada.vn/",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cookie": "" #FILL IN HERE
}

# Database config
DB_CONFIG = {
    'server': 'localhost',  # e.g., 'localhost' or 'server.database.windows.net'
    'database': 'Test_Crawl_Data',
    'username': '', #FILL IN HERE
    'password': '' #FILL IN HERE
}

# Gemini API Key
GEMINI_API_KEY = [#FILL IN HERE
                  ]