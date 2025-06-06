import requests
from config import BASE_URL, HEADERS
from utils import insert_products_batch, clean_text, create_products_table, extract_product_info_with_gemini
from datetime import datetime

def scrape_lazada(query, pages_begin_scrape, pages_end_scrape):
    """Hàm chính để cào dữ liệu từ Lazada sử dụng API trên nhiều trang"""

    #B1: Tạo bảng
    create_products_table()
    
    #B2: Duyệt qua tất cả trang
    for page in range(pages_begin_scrape, pages_end_scrape + 1):
        all_scraped_items = []
        
        print(f"\n{'='*50}")
        print(f"Đang lấy dữ liệu cho truy vấn: '{query}' - Trang {page}")
        print(f"{'='*50}")
                
        # Xây dựng URL API với tham số trang
        url = f"{BASE_URL}ajax=true&catalog_redirect_tag=true&isFirstRequest=true&page={page}&q={query}"
        
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Lỗi: Không thể truy cập {url}. Mã trạng thái: {response.status_code}")
            continue
        
        data_json = response.json()
        products = data_json.get("mods", {}).get("listItems", [])
        
        if not products:
            print(f"Không tìm thấy sản phẩm nào trên trang {page}")
            continue
            
        print(f"Tìm thấy {len(products)} sản phẩm trên trang {page}")
        
        for i, product in enumerate(products, 1):
            try:
                original_name = clean_text(product.get("name", "N/A"))
                gemini_extracted_info = extract_product_info_with_gemini(original_name)

                item = {
                    "crawl_date": datetime.now().strftime("%d/%m/%Y"),
                    "name": original_name,
                    "product_id": clean_text(product.get("itemId", "N/A")),
                    "priceShow": clean_text(product.get("priceShow", "N/A")),
                    "rating": clean_text(product.get("ratingScore", "N/A")),
                    "location": clean_text(product.get("location", "N/A")),
                    "seller_id": clean_text(product.get("sellerId", "N/A")),
                    "seller_name": clean_text(product.get("sellerName", "N/A")),
                    "brand_name": clean_text(product.get("brandName", "N/A")),
                    "original_price": clean_text(product.get("originalPrice", "N/A")),
                    "sold_quantity": clean_text(product.get("itemSoldCntShow", "N/A")),
                    "review_count": clean_text(product.get("review", "N/A")),
                    "image_url": product.get("image", "N/A"),
                    "item_url": "https:" + product.get("itemUrl", "N/A"),
                    "product_name_extracted": gemini_extracted_info.get("product_name_extracted", "N/A"),
                    "product_use_extracted": gemini_extracted_info.get("product_use_extracted", "N/A"),
                    "product_material_extracted": gemini_extracted_info.get("product_material_extracted", "N/A")
                }
                all_scraped_items.append(item)
                print(f"✓ Đã xử lý sản phẩm {i}/{len(products)} (Trang {page})")
                
            except Exception as e:
                print(f"✗ Lỗi khi xử lý sản phẩm {i} trên trang {page}: {e}")
                continue
        
        # Lưu trữ từng page
        print(f"Lưu trữ dữ liệu trang {page} ...")
        try:
            insert_products_batch(all_scraped_items)
        except Exception as e:
            print(f"✗ Lỗi khi lưu dữ liệu: {e}")
    
    return all_scraped_items

if __name__ == "__main__":
    list_query = [
        # "toner",
        # "kem chống nắng",
        # "ngăn ngừa tàn nhang",
        # "dưỡng ẩm",
        # "tẩy tế bào chết",
        # "bông tẩy trang",
        # "nước tẩy trang",
        # "serum",
        # "kem dưỡng mắt",
        # "kem chống lão hóa",
        # "son dưỡng môi",
        "mặt nạ dưỡng da"
    ]
    
    for query in list_query:
        
        # Trang bắt đầu muốn cào nè
        pages_begin_scrape = 1
        
        # Trang kết thúc muốn cào
        pages_end_scrape = 1
                
        # In ra thông tin cào dữ liệu
        print(f"Bắt đầu cào dữ liệu Lazada...")
        print(f"Query: {query}")
        print(f"Trang: {pages_begin_scrape} - {pages_end_scrape}")
        
        try:
        # Cào rồi lưu vào biến scraped_data
            scraped_data = scrape_lazada(query, pages_begin_scrape, pages_end_scrape)
        except Exception as e:
            print(f"Gặp lỗi ở query {e}")
            continue
    
    # In ra thông tin kết thúc cào dữ liệu
    if scraped_data:
        print(f"\nKết thúc cào dữ liệu!")