# utils.py
from config import DB_CONFIG, GEMINI_API_KEY
from fake_useragent import UserAgent
import pyodbc
import google.generativeai as genai
import json
import random

#config API
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 1,
    "max_output_tokens": 3000,
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def get_random_user_agent():
    """Tạo và trả về một User-Agent ngẫu nhiên."""
    ua = UserAgent()
    return ua.random

def get_db_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return pyodbc.connect(conn_str)

def create_products_table():
    # Hàm này nên được gọi trước khi bắt đầu cào dữ liệu
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='raw_lazada_products' AND xtype='U')
        CREATE TABLE raw_lazada_products (
            id INT IDENTITY(1,1) PRIMARY KEY,
            crawl_date NVARCHAR(20),
            name NVARCHAR(MAX), 
            product_id NVARCHAR(50),
            priceShow NVARCHAR(50),
            rating NVARCHAR(30),
            location NVARCHAR(100),
            seller_id NVARCHAR(50),
            seller_name NVARCHAR(255),
            brand_name NVARCHAR(255),
            original_price NVARCHAR(50),
            sold_quantity NVARCHAR(50),
            review_count NVARCHAR(50),
            image_url NVARCHAR(500),
            item_url NVARCHAR(500),
            product_name_extracted NVARCHAR(255),
            product_use_extracted NVARCHAR(MAX),
            product_material_extracted NVARCHAR(100)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Hiện tại không dùng hàm này nữa
def insert_product(product):    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO raw_lazada_products (
            crawl_date, name, product_id, priceShow, rating, location, seller_id, seller_name, brand_name, original_price, sold_quantity, review_count, image_url, item_url, product_name_extracted, product_use_extracted, product_material_extracted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product["crawl_date"],
        product["name"],
        product["product_id"],
        product["priceShow"],
        product["rating"],
        product["location"],
        product["seller_id"],
        product["seller_name"],
        product["brand_name"],
        product["original_price"],
        product["sold_quantity"],
        product["review_count"],
        product["image_url"],
        product["item_url"],
        product.get("product_name_extracted", "N/A"),
        product.get("product_use_extracted", "N/A"),
        product.get("product_material_extracted", "N/A")
    ))
    conn.commit()
    cursor.close()
    conn.close()

def insert_products_batch(products_list):
    if not products_list:
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO raw_lazada_products (
            crawl_date, name, product_id, priceShow, rating, location, seller_id, seller_name, 
            brand_name, original_price, sold_quantity, review_count, image_url, item_url, 
            product_name_extracted, product_use_extracted, product_material_extracted
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    data_to_insert = []
    for product in products_list:
        data_to_insert.append((
            product["crawl_date"],
            product["name"],
            product["product_id"],
            product["priceShow"],
            product["rating"],
            product["location"],
            product["seller_id"],
            product["seller_name"],
            product["brand_name"],
            product["original_price"],
            product["sold_quantity"],
            product["review_count"],
            product["image_url"],
            product["item_url"],
            product.get("product_name_extracted", "N/A"),
            product.get("product_use_extracted", "N/A"),
            product.get("product_material_extracted", "N/A")
        ))
    
    try:
        cursor.executemany(sql, data_to_insert)
        conn.commit()
        print(f"Đã chèn thành công {len(data_to_insert)} sản phẩm vào database.")
    except Exception as e:
        print(f"Lỗi khi chèn hàng loạt sản phẩm: {e}")
        conn.rollback() # Rollback nếu có lỗi
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def clean_text(text):
    """Loại bỏ khoảng trắng thừa trong chuỗi và xử lý đầu vào không phải chuỗi"""
    if text is None:
        return "N/A"
    if not isinstance(text, str):
        text = str(text)
    return " ".join(text.split()).strip()

def extract_product_info_with_gemini(lazada_product_name):
    # Nhẽ ra là câu lệnh này nên được đặt bên ngoài (nếu như tôi không dùng random.choice)
    # Khởi tạo model
    genai.configure(api_key=random.choice(GEMINI_API_KEY))

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # Thực thi chính
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("Cảnh báo: GEMINI_API_KEY chưa được cấu hình. Bỏ qua trích xuất thông tin sản phẩm.")
        return {"product_name_extracted": "N/A", "product_use_extracted": "N/A", "product_material_extracted": "N/A"}

    prompt_parts = [
        f"""Trích xuất thông tin chi tiết từ tên sản phẩm Lazada sau: "{lazada_product_name}"

        Hãy trả về kết quả dưới dạng một đối tượng JSON với các trường sau:
        - "product_name_extracted": Tên sản phẩm cụ thể và chính xác nhất. Ví dụ: "Kimax", "iPhone 15 Pro Max".
        - "product_use_extracted": Công dụng chính của sản phẩm. Ví dụ: "giảm thâm, lành mụn", "chụp ảnh, chơi game". Nếu có nhiều công dụng, cách các công dụng bởi dấu ","
        - "product_material_extracted": Đây KHÔNG PHẢI CHẤT LIỆU SẢN PHẨM (KHÔNG PHẢI cotton, ...) mà đây chính là loại sản phẩm. Ví dụ: "Kem bôi mụn", "kem chống nắng", "bông tẩy trang","serum dưỡng ẩm",...

        Nếu không thể xác định một trường nào đó, hãy trả về "N/A" cho trường đó.
        Chỉ trả về đối tượng JSON, không có bất kỳ giải thích hay văn bản nào khác.

        Ví dụ yêu cầu: "Kem bôi mụn Kimax, giúp giảm thâm, lành mụn"
        Ví dụ kết quả JSON:
        {{
          "product_name_extracted": "Kimax",
          "product_use_extracted": "giảm thâm, lành mụn",
          "product_material_extracted": "Kem bôi mụn"
        }}

        Ví dụ yêu cầu: "Sữa rửa mặt Cosrx 500ml sáng da, mờ thâm"
        Ví dụ kết quả JSON:
        {{
          "product_name_extracted": "Cosrx",
          "product_use_extracted": "sáng da, mờ thâm",
          "product_material_extracted": "Sữa rửa mặt"
        }}

        Ví dụ yêu cầu: "Kem dưỡi mắt The Face Shop 10ml"
        Ví dụ kết quả JSON:
        {{
          "product_name_extracted": "The Face Shop",
          "product_use_extracted": "dưỡi mắt",
          "product_material_extracted": "Kem dưỡi mắt"
        }} 
        
        Ví dụ yêu cầu: "Bông tẩy trang cừu Habaria Sheep 100% Cotton Bịch 234 Miếng, Mềm Mại, Dày Dặn"
        Ví dụ kết quả JSON:
        {{
          "product_name_extracted": "Habaria Sheep",
          "product_use_extracted": "Tẩy trang",
          "product_material_extracted": "Bông tẩy trang"
        }} 
        
        """
    ]

    try:
        response = model.generate_content(prompt_parts)
        # Làm sạch dữ liệu
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # Xử lý trong TH gemini không trả kết quả dưới dạng JSON
        if not cleaned_response_text.startswith("{") or not cleaned_response_text.endswith("}"):
             print(f"Cảnh báo: Gemini trả về không phải JSON: {cleaned_response_text}. Sử dụng N/A cho các trường trích xuất.")
             return {"product_name_extracted": "N/A", "product_use_extracted": "N/A", "product_material_extracted": "N/A"}

        extracted_info = json.loads(cleaned_response_text)
        
        return {
            "product_name_extracted": extracted_info.get("product_name_extracted", "N/A"),
            "product_use_extracted": extracted_info.get("product_use_extracted", "N/A"),
            "product_material_extracted": extracted_info.get("product_material_extracted", "N/A"),
        }
    except Exception as e:
        print(f"Lỗi khi gọi Gemini API hoặc xử lý kết quả: {e}")
        return {"product_name_extracted": "N/A", "product_use_extracted": "N/A", "product_material_extracted": "N/A"}

