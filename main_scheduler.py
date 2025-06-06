import schedule
import time
import os

def run_crawl_1():
    os.system(r"")  # File crawl đầu tiên
    print("Đã chạy file để crawl data từ Lazada")

def run_crawl_2():
    os.system(r"")  # File crawl thứ hai
    print("Đã chạy file để crawl data từ Shopee")

def run_etl():
    os.system(r"")  # File ETL
    print("Đã chạy ETL")

# Lập lịch chạy các file
# Ví dụ: chạy crawl_1 và crawl_2 song song, sau đó chạy ETL mỗi ngày lúc 8h sáng
schedule.every().day.at("08:00").do(run_crawl_1)
schedule.every().day.at("08:00").do(run_crawl_2)
schedule.every().day.at("09:00").do(run_etl)  # Chạy ETL sau khi crawl xong

# Vòng lặp để kiểm tra và chạy lịch
while True:
    schedule.run_pending()
    time.sleep(60)  # Kiểm tra mỗi 60 giây