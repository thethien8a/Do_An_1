# Đồ án 1: Hệ thống thu thập, xử lý và trực quan hóa dữ liệu E-commerce

## 1. Mô tả dự án

Đây là dự án xây dựng một hệ thống dữ liệu hoàn chỉnh với mục tiêu tự động thu thập dữ liệu sản phẩm từ hai trang thương mại điện tử lớn là Lazada và Shopee. Sau khi thu thập, dữ liệu sẽ được xử lý, làm sạch và cuối cùng được trực quan hóa trên Power BI Dashboard để phục vụ cho việc phân tích.

## 2. Sơ lược về hệ thống

Hệ thống được thiết kế để hoạt động một cách tự động theo lịch trình định sẵn:

1.  **Lập lịch (Scheduler)**: `main_scheduler.py` đóng vai trò là trình điều phối trung tâm, sử dụng thư viện `schedule` của Python để kích hoạt các tác vụ thu thập và xử lý dữ liệu mỗi ngày.
2.  **Thu thập dữ liệu (Crawling)**:
    *   Các script trong thư mục `Crawl Lazada` và `Crawl Shopee` chịu trách nhiệm truy cập vào các trang web và trích xuất thông tin sản phẩm cần thiết.
    *   Lịch chạy: 8:00 sáng hàng ngày.
3.  **Xử lý dữ liệu (ETL - Extract, Transform, Load)**:
    *   Script trong thư mục `Transform Data` sẽ lấy dữ liệu thô từ quá trình crawl, thực hiện làm sạch, chuẩn hóa và chuyển đổi sang một cấu trúc phù hợp cho việc phân tích.
    *   Lịch chạy: 9:00 sáng hàng ngày (sau khi quá trình crawl hoàn tất).
4.  **Trực quan hóa (Visualization)**:
    *   File `Dashboard.pbix` là một Power BI Dashboard đã được thiết kế sẵn.
    *   Người dùng có thể mở file này bằng Power BI Desktop để xem các biểu đồ và phân tích đã được xây dựng từ dữ liệu đã qua xử lý.

## 3. Cấu trúc thư mục

```
.
├── Crawl Lazada/
│   ├── scraper.py             # Script chính để crawl dữ liệu từ Lazada
│   ├── config.py              # File cấu hình
│   ├── utils.py               # Các hàm phụ trợ
│   └── requirements.txt       # Các thư viện Python cần thiết cho crawler
│
├── Crawl Shopee/
│   └── test_another_ver.py    # Script để crawl dữ liệu từ Shopee
│
├── Transform Data/
│   └── test_another_ver.py    # Script xử lý và chuyển đổi dữ liệu (ETL)
│
├── main_scheduler.py          # Script chính để lập lịch và điều phối các tác vụ
└── Dashboard.pbix             # File Power BI Dashboard
```

## 4. Công nghệ sử dụng

-   **Ngôn ngữ lập trình**: Python
-   **Thư viện Python**:
    -   `schedule`: Để lập lịch các tác vụ.
    -   `requests`, `beautifulsoup4`, `undetected_chromedriver`: Để thu thập dữ liệu web.
    -   `pandas` (dự đoán): Thường được sử dụng trong xử lý dữ liệu.
    -   Và các thư viện khác được liệt kê trong `Crawl Lazada/requirements.txt`.
-   **Trực quan hóa dữ liệu**: Microsoft Power BI

## 5. Hướng dẫn cài đặt và sử dụng

### Yêu cầu

-   Python 3.x
-   Microsoft Power BI Desktop

### Cài đặt

1.  **Clone repository (nếu có) hoặc tải mã nguồn về máy.**

2.  **Cài đặt các thư viện Python cần thiết:**

    Mở terminal và chạy lệnh sau cho từng crawler (ví dụ cho Lazada):
    ```bash
    cd "Crawl Lazada"
    pip install -r requirements.txt
    ```
    *Lưu ý: Cần tạo file `requirements.txt` cho các thư mục `Crawl Shopee` và `Transform Data` nếu chúng có các thư viện riêng.*

3.  **Cấu hình các script chạy:**

    Mở file `main_scheduler.py` và cập nhật các lệnh `os.system(r"")` với đường dẫn chính xác để thực thi các script Python. Ví dụ:
    ```python
    import schedule
    import time
    import os

    def run_crawl_1():
        os.system(r"python \"Crawl Lazada/scraper.py\"")
        print("Đã chạy file để crawl data từ Lazada")

    def run_crawl_2():
        os.system(r"python \"Crawl Shopee/test_another_ver.py\"")
        print("Đã chạy file để crawl data từ Shopee")

    def run_etl():
        os.system(r"python \"Transform Data/test_another_ver.py\"")
        print("Đã chạy ETL")

    # ... (phần còn lại của file)
    ```

### Sử dụng

1.  **Chạy Scheduler:**
    Mở terminal tại thư mục gốc của dự án và chạy:
    ```bash
    python main_scheduler.py
    ```
    Scheduler sẽ chạy nền và tự động kích hoạt các tác vụ theo lịch đã định (8:00 và 9:00 hàng ngày).

2.  **Xem Dashboard:**
    - Mở file `Dashboard.pbix` bằng Power BI Desktop.
    - Kết nối Dashboard với nguồn dữ liệu đã được xử lý (ví dụ: file CSV, database, ... tùy theo thiết kế của script ETL).
    - Refresh dữ liệu để cập nhật dashboard với thông tin mới nhất. 