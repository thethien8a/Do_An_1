from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import easyocr
import time
import random
import undetected_chromedriver as uc
import traceback
import threading
from datetime import datetime
import re
import os
import google.generativeai as genai
import random
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


GEMINI_API_KEY = [ ## FILL IN HERE
                  ]

def extract_product_info_with_gemini(product_name):
    """
    Sử dụng Google Gemini để trích xuất thông tin từ tên sản phẩm
    
    Args:
        product_name: Tên sản phẩm cần trích xuất thông tin
        
    Returns:
        dict: Thông tin được trích xuất (thương hiệu, công dụng, dung tích, xuất xứ)
    """
    # Lấy API key từ biến môi trường
    api_key = random.choice(GEMINI_API_KEY)
    
    # Cấu hình Gemini với API key
    genai.configure(api_key=api_key)
    
    # Chọn model (Gemini Pro là phiên bản phù hợp nhất cho nhiệm vụ này)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Tạo prompt - Yêu cầu chỉ trả về JSON thuần túy
    prompt = f"""
    Phân tích tên sản phẩm sau và trích xuất các thông tin sau (nếu có):
    Tên sản phẩm: "{product_name}"
    
    1. Loại sản phẩm: (Ví dụ: Sữa rửa mặt, Kem chống nắng, Son môi, Nước tẩy trang, Bông tẩy trang, Kem trị mụn)
    2. Tên riêng sản phẩm: (Tên thương hiệu chính hoặc tên đặc trưng của sản phẩm sau khi đã tách loại sản phẩm. Ví dụ: Cosrx, HadaLabo, Dermaforte, La Roche-Posay Anthelios)
    3. Thương hiệu: (Tên hãng/thương hiệu của sản phẩm, có thể trùng với Tên riêng sản phẩm nếu đó là thương hiệu)
    4. Công dụng chính: (Công dụng chính của sản phẩm). Nếu có nhiều công dụng, cách cac cong dung boi dau ",". Nếu trong tên không có rõ, hãy sử dụng kiến thức của bạn để điền vào
    5. Dung tích/khối lượng: (Kích thước, ml, g, oz, etc.)
    6. Xuất xứ: (Nơi sản xuất)
    
    Ví dụ mong muốn:
    - Tên sản phẩm: "Sữa rửa mặt Cosrx Low pH Good Morning Gel Cleanser 150ml"
      Loại sản phẩm: "Sữa rửa mặt"
      Công dụng: Không xác định
      * Lưu ý: nếu công dụng nếu bạn biết thì hãy điền vào, không giá trị mặc định là "Không xác định"
      Tên riêng sản phẩm: "Cosrx Low pH Good Morning Gel Cleanser"
      Thương hiệu: "Cosrx"
    - Tên sản phẩm: "Bông tẩy trang HadaLabo Cleansing Cotton 80 miếng"
      Loại sản phẩm: "Bông tẩy trang"
      Tên riêng sản phẩm: "HadaLabo Cleansing Cotton"
      Công dụng: không xác định
      Thương hiệu: "HadaLabo"
    - Tên sản phẩm: "Kem trị mụn Dermaforte Gel 15g giảm mụn trứng cá, mờ thâm sẹo"
      Loại sản phẩm: "Kem trị mụn"
      Tên riêng sản phẩm: "Dermaforte Gel"
      Công dụng: giảm mụn trứng cá, mờ thâm sẹo
      Thương hiệu: "Dermaforte"

    Nếu thông tin xuất xứ không có trong tên sản phẩm, vui lòng dựa vào kiến thức của bạn để xác định xuất xứ của thương hiệu này.
    
    QUAN TRỌNG: Trả về KẾT QUẢ CHÍNH XÁC CHỈ TRONG ĐỊNH DẠNG JSON MÀ KHÔNG CÓ VĂN BẢN NÀO KHÁC:
    {{
        "loai_san_pham": "loại sản phẩm tìm được",
        "ten_sp_chinh_xac": "tên riêng sản phẩm tìm được",
        "thuong_hieu": "tên thương hiệu",
        "cong_dung": "công dụng chính",
        "dung_tich": "dung tích/khối lượng",
        "xuat_xu": "xuất xứ"
    }}
    
    Nếu không thể xác định thông tin nào, điền "Không xác định". KHÔNG VIẾT BẤT CỨ VĂN BẢN GIẢI THÍCH NÀO KHÁC.
    """
    
    # Gọi API Gemini
    try:
        # Cấu hình để yêu cầu kết quả là JSON
        generation_config = {
            "temperature": 0.2,  # Giảm nhiệt độ để đảm bảo kết quả nhất quán
            "response_mime_type": "application/json",  # Yêu cầu phản hồi JSON
        }
        
        response = model.generate_content(
            prompt, 
            generation_config=generation_config
        )
        
        # Xử lý phản hồi
        if hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        # Tìm cấu trúc JSON trong phản hồi
        import json
        
        try:
            # Cố gắng phân tích trực tiếp phản hồi
            result = json.loads(response_text)
            time.sleep(random.uniform(1,1.5))
        except json.JSONDecodeError:
            # Nếu không thể phân tích trực tiếp, tìm và trích xuất phần JSON
            print(f"Không thể phân tích trực tiếp phản hồi JSON. Đang thử tìm kiếm chuỗi JSON...")
            json_match = re.search(r'({[\s\S]*})', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"Lỗi khi phân tích chuỗi JSON đã trích xuất: {str(e)}")
                    print(f"Chuỗi JSON: {json_str}")
                    # Trả về kết quả mặc định
                    result = {
                        "loai_san_pham": "Không xác định",
                        "ten_sp_chinh_xac": "Không xác định",
                        "thuong_hieu": "Không xác định",
                        "cong_dung": "Không xác định", 
                        "dung_tich": "Không xác định",
                        "xuat_xu": "Không xác định"
                    }
            else:
                print(f"Không tìm thấy chuỗi JSON trong phản hồi")
                # Trả về kết quả mặc định
                result = {
                    "loai_san_pham": "Không xác định",
                    "ten_sp_chinh_xac": "Không xác định",
                    "thuong_hieu": "Không xác định",
                    "cong_dung": "Không xác định", 
                    "dung_tich": "Không xác định",
                    "xuat_xu": "Không xác định"
                }
        
        # Đảm bảo tất cả các khóa cần thiết đều tồn tại
        required_keys = ["loai_san_pham", "ten_sp_chinh_xac", "thuong_hieu", "cong_dung", "dung_tich", "xuat_xu"]
        for key in required_keys:
            if key not in result:
                result[key] = "Không xác định"
        
        return result
    
    except Exception as e:
        print(f"Lỗi khi sử dụng Gemini API: {str(e)}")
        return {
            "loai_san_pham": "Không xác định",
            "ten_sp_chinh_xac": "Không xác định",
            "thuong_hieu": "Không xác định",
            "cong_dung": "Không xác định", 
            "dung_tich": "Không xác định",
            "xuat_xu": "Không xác định"
        }

def get_item_shop_cat(url):
    itemid, shopid, catid = None, None, None
    if url:
        try:
            # Tìm itemid
            item_match = re.search(r'i\.(\d+)\.', url)
            if item_match:
                itemid = item_match.group(1)
            elif re.search(r'itemid=(\d+)', url):
                itemid = re.search(r'itemid=(\d+)', url).group(1)
            
            # Tìm shopid
            shop_match = re.search(r'\.(\d+)\.', url)
            if shop_match and shop_match.group(1) != itemid:
                shopid = shop_match.group(1)
            elif re.search(r'shopid=(\d+)', url):
                shopid = re.search(r'shopid=(\d+)', url).group(1)
            
            # Tìm catid từ URL
            if re.search(r'catid=(\d+)', url):
                catid = re.search(r'catid=(\d+)', url).group(1)
        except Exception as e:
            print(f"Lỗi khi phân tích URL: {e}, URL: {url}")
    return itemid, shopid, catid
 
def input_with_timeout(prompt, timeout=10):
    """
    Hàm đọc input với timeout, trả về None nếu hết thời gian chờ
    """
    print(prompt, end='', flush=True)
    
    # Biến để lưu kết quả input
    result = [None]
    input_event = threading.Event()
    
    # Định nghĩa hàm đọc input
    def get_input():
        result[0] = input()
        input_event.set()
    
    # Tạo và bắt đầu thread đọc input
    input_thread = threading.Thread(target=get_input)
    input_thread.daemon = True
    input_thread.start()
    
    # Đợi đến khi có input hoặc hết thời gian timeout
    input_received = input_event.wait(timeout)
    
    if not input_received:
        # Hết thời gian mà không có input
        print(f"\nĐã hết thời gian chờ ({timeout} giây). Tự động tiếp tục...")
        return None
    
    return result[0]

def convert_image_url(url):
    # Hàm xử lý riêng cho các trường hợp cụ thể trong "chỉ báo khuyến mãi"
    dict = {
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/a0842aa9294375794fd2.png": "Mall",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/4bce1bc553abb9ce061d.png": "Xử lý bởi Shopee",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/f7b68952a53e41162ad3.png": "Xử lý bởi Shopee",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/ef5ae19bc5ed8a733a70.png": "Yêu thích",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/f7b342784ff25c9e4403.png": "Yêu thích+",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/06ac2f74334798aeb1e0.png": "Choice",
        "https://deo.shopeemobile.com/shopee/modules-federation/live/0/shopee__item-card-standard-v2/0.1.59/pc/29ae698914953718838e.png": "Premium"
    }
    if url in dict:
        return dict[url]
    
    # Trong TH là text không có trong dict ở trên
    # Khởi tạo EasyOCR với tiếng Việt
    reader = easyocr.Reader(['vi'])
    results = reader.readtext(url)
    text = ""
    for result in results:
        text = result[1]
    return text

def crawl_shopee(driver, search_term, start_page, num_pages):
    all_products_for_this_term = [] 
    
    try:
        # The driver is already initialized and on shopee.vn (or handled CAPTCHA)
        # So we can proceed directly to searching for the term.
            
        # Cào thông tin cơ bản về sản phẩm
        for page_idx in range(num_pages):
            current_page = start_page + page_idx
            encoded_term = search_term.replace(" ", "%20")
            url = f"https://shopee.vn/search?keyword={encoded_term}&page={current_page}"
            
            print(f"\n=== Đang xử lý trang {page_idx+1}/{num_pages} (Trang thực tế: {current_page}): {url} ===")
            driver.get(url) # Navigate to the search results page for the current term
            time.sleep(5) # Allow page to load
            scroll_page(driver)
            
            page_products = crawl_products(driver, search_term)

            if page_products:
                all_products_for_this_term.extend(page_products)
            
            print(f"\n=== Tổng kết trang {page_idx+1}/{num_pages} ===")
            print(f"- Đã cào được {len(page_products)} sản phẩm từ trang này")
            
            if page_idx < num_pages - 1:
                delay = random.uniform(5, 10)
                print(f"Đợi {delay:.1f} giây trước khi chuyển trang tiếp...")
                time.sleep(delay)
                # The input_with_timeout might still be useful if you want to pause between pages of the *same* search term
                response = input_with_timeout("Nhấn Enter để tiếp tục trang tiếp theo cho cùng từ khóa, hoặc 'q' để dừng từ khóa này: ", 10)
                if response and response.lower() == 'q':
                    print(f"Dừng cào cho từ khóa hiện tại: {search_term}")
                    break # Break from an inner loop (pages for current search term)
        
            # Database saving for products of the current page/term
        
            connection_string = "DRIVER={SQL Server};SERVER=localhost;DATABASE=Test_Crawl_Data;UID=;PWD=" #Fill in here: UID example: sa, PWD: password
            table_name = "raw_shopee_products"
            if page_products: # Save products collected from this page
                save_to_database(page_products, connection_string=connection_string, table_name=table_name)
            
    except Exception as e:
        print(f"Lỗi trong quá trình cào dữ liệu cho từ khóa '{search_term}': {e}")
        traceback.print_exc()
    
    return all_products_for_this_term

def scroll_page(driver):
    """
    Cuộn trang từ trên xuống dưới để tải tất cả sản phẩm
    """
    print("Đang cuộn trang để tải tất cả sản phẩm...")
    
    # Khởi tạo các biến theo dõi
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0
    scroll_step = 800  # Mỗi lần cuộn 800px
    
    # Đợi cho trang tải ban đầu
    time.sleep(3)
    
    # Cuộn từng bước đến cuối trang
    while current_position < total_height:
        # Cuộn xuống một đoạn
        current_position += scroll_step
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        print(f"Đã cuộn xuống vị trí {current_position}px / {total_height}px")
        
        # Đợi để trang tải các sản phẩm mới
        time.sleep(random.uniform(1, 2))
        
        # Cập nhật lại chiều cao trang (có thể đã thay đổi do lazy loading)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height > total_height:
            print(f"Trang đã mở rộng từ {total_height}px lên {new_height}px")
            total_height = new_height
    
    print("Đã cuộn đến cuối trang")
    
    # Cuộn lại lên trên cùng để bắt đầu cào dữ liệu
    driver.execute_script("window.scrollTo(0, 0);")
    print("Đã cuộn lại lên đầu trang và sẵn sàng cào dữ liệu")
    time.sleep(10)  # Đợi một chút sau khi cuộn lên

def crawl_products(driver, category):
    """
    Cào dữ liệu sản phẩm sau khi đã cuộn trang
    
    Args:
        driver: WebDriver đang chạy
        category: Danh mục sản phẩm (từ khóa tìm kiếm)
        
    Returns:
        Danh sách các sản phẩm đã cào được
    """
    print("Bắt đầu cào dữ liệu sản phẩm...")
    products = []
    processed_names = set()  # Tránh trùng lặp sản phẩm
    
    # Lấy ngày giờ hiện tại để thêm vào sản phẩm
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    try:
        # Wait for the product container to be present
        print("Đang chờ container sản phẩm xuất hiện...")
        product_container_selector = "ul.row.shopee-search-item-result__items"
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, product_container_selector))
        )
        print("Container sản phẩm đã xuất hiện.")
        
        # Tìm container chính của sản phẩm 
        product_container = driver.find_element(By.CSS_SELECTOR, product_container_selector)
        # Tìm tất cả các sản phẩm trong container
        product_items = product_container.find_elements(By.CSS_SELECTOR, "li.col-xs-2-4.shopee-search-item-result__item")
        print(f"Tìm thấy tổng cộng {len(product_items)} sản phẩm")
    except Exception as e:
        print(f"Không tìm thấy container sản phẩm: {e}")
        return []
    
    # Xử lý từng sản phẩm
    for index, item in enumerate(product_items, 1):
        try:
            # Tìm tên sản phẩm - cập nhật theo bộ chọn CSS chính xác và đầy đủ từ người dùng
            try:
                # Bộ chọn chính xác và đầy đủ cho tên sản phẩm
                name_element = item.find_element(By.CSS_SELECTOR, "div.line-clamp-2.break-words.min-w-0.min-h-\\[2\\.5rem\\].text-sm")
                name = name_element.text.strip()
            except:
                # Thử các bộ chọn khác nếu bộ chọn chính không hoạt động
                try:
                    name_element = item.find_element(By.CSS_SELECTOR, "div.line-clamp-2.break-words")
                    name = name_element.text.strip()
                except:
                    try:
                        name_element = item.find_element(By.CSS_SELECTOR, "div.ie3A\\+n, div[class*='ie3A+n']")
                        name = name_element.text.strip()
                    except:
                        print(f"Không thể tìm thấy tên sản phẩm {index}, đang chuyển đến sản phẩm tiếp theo")
                        continue
            
            # Bỏ qua nếu đã xử lý sản phẩm này rồi hoặc tên rỗng
            if name in processed_names or not name:
                continue
            
            # Trích xuất thông tin bổ sung từ tên sản phẩm sử dụng Google Gemini
            product_info = {
                "loai_san_pham": "Không xác định",
                "ten_sp_chinh_xac": "Không xác định",
                "thuong_hieu": "Không xác định",
                "cong_dung": "Không xác định", 
                "dung_tich": "Không xác định",
                "xuat_xu": "Không xác định"
            }
            
            if name:
                print(f"Đang trích xuất thông tin bổ sung cho sản phẩm: {name}")
                try:
                    product_info = extract_product_info_with_gemini(name)
                    print(f"Đã trích xuất thành công thông tin bổ sung")
                except Exception as e:
                    print(f"Lỗi khi trích xuất thông tin bổ sung: {str(e)}")
            
            # Lấy thông tin giá - cập nhật theo cấu trúc HTML thực tế
            try:
                # Sử dụng bộ chọn chính xác cho giá 
                price_container = item.find_element(By.CSS_SELECTOR, "div.truncate.flex.items-baseline")
                
                # Tìm thẻ span chứa giá thực tế (thẻ span thứ hai trong container)
                price_elements = price_container.find_elements(By.CSS_SELECTOR, "span")
                
                if len(price_elements) >= 2:
                    # Span đầu tiên thường chứa ký hiệu tiền tệ (đ), span thứ hai chứa giá trị
                    currency = price_elements[0].text.strip()
                    price_value = price_elements[1].text.strip()
                    price = currency + price_value
                else:
                    # Nếu không tìm thấy đủ span, lấy toàn bộ nội dung của container
                    price = price_container.text.strip()
            except:
                # Thử các bộ chọn khác nếu bộ chọn chính không hoạt động
                try:
                    # Thử nhiều bộ chọn khác nhau cho giá
                    selectors = [
                        "div.vioxXd, div[class*='vioxXd']", 
                        "span.ZEgDH9", 
                        "div[class*='price']",
                        "div.kPYiVF", # Bộ chọn giá phổ biến trên Shopee
                        "span[class*='font-medium'][class*='text-base']" # Bộ chọn dựa trên mẫu HTML
                    ]
                    
                    price = None
                    for selector in selectors:
                        try:
                            price_element = item.find_element(By.CSS_SELECTOR, selector)
                            price = price_element.text.strip()
                            if price:  # Nếu tìm thấy giá không rỗng, thoát khỏi vòng lặp
                                break
                        except:
                            continue
                    
                    if not price:
                        price = "Không có thông tin giá"
                except:
                    price = "Không có thông tin giá"
            
            # [Phần còn lại của mã code hiện tại để lấy các thông tin khác...]
            
            # Lấy thông tin đã bán
            try:
                sold_selectors = [
                    "div.truncate.text-shopee-black87.text-xs.min-h-4",
                    "div.r6HknA, div[class*='r6HknA']"
                ]
                
                sold = None
                for selector in sold_selectors:
                    try:
                        sold_element = item.find_element(By.CSS_SELECTOR, selector)
                        sold = sold_element.text.strip()
                        if sold:  # Nếu tìm thấy thông tin bán không rỗng, thoát khỏi vòng lặp
                            break
                    except:
                        continue
                
                if not sold:
                    sold = "Chưa có thông tin"
            except:
                sold = "Chưa có thông tin"
            
            # Lấy đường dẫn sản phẩm
            try:
                link_element = item.find_element(By.CSS_SELECTOR, "a")
                link = link_element.get_attribute("href")

            except:
                link = "Không có đường dẫn"
            
            # Lấy thông tin giảm giá
            try:
                # Tìm thẻ div chứa thông tin giảm giá từ bộ chọn CSS chính xác mà người dùng cung cấp
                discount_element = item.find_element(By.CSS_SELECTOR, "div.text-shopee-primary.font-medium.bg-shopee-pink.py-0\\.5.px-1.text-sp10\\/3.h-4.rounded-\\[2px\\].shrink-0.mr-1")
                discount = discount_element.text.strip()
            except:
                # Thử các bộ chọn khác nếu bộ chọn chính không hoạt động
                try:
                    # Thử tìm các thẻ có chứa thuộc tính aria-label với giá trị có dấu %
                    discount_elements = item.find_elements(By.CSS_SELECTOR, "span[aria-label*='%']")
                    if discount_elements:
                        discount = discount_elements[0].get_attribute("aria-label")
                    else:
                        # Tìm các thẻ div có class chứa từ khóa liên quan đến giảm giá
                        discount_elements = item.find_elements(By.CSS_SELECTOR, "div[class*='shopee-pink'], div[class*='discount'], div[class*='sale']")
                        if discount_elements:
                            discount = discount_elements[0].text.strip()
                        else:
                            discount = "Không giảm giá"
                except:
                    discount = "Không giảm giá"
            
            # [Phần còn lại của mã code hiện tại...]
            
            # Lấy thông tin nhãn sản phẩm (yêu thích, yêu thích+, mall, v.v.)
            try:
                label_image_selectors = [
                    "img[alt='flag-label']",
                    "img.h-sp14",
                    "img.inline-block"
                ]
                
                label_image_url = None
                for selector in label_image_selectors:
                    try:
                        label_image_elements = name_element.find_elements(By.CSS_SELECTOR, selector)
                        if label_image_elements:
                            label_image_url = label_image_elements[0].get_attribute("src")
                            if label_image_url:  # Nếu tìm thấy URL, thoát khỏi vòng lặp
                                break
                    except:
                        continue
                
                if label_image_url:
                    label = convert_image_url(label_image_url)
                else:
                    label = "Không có nhãn"
            except Exception as e:
                print(f"Lỗi khi xử lý nhãn sản phẩm: {str(e)}")
                label = "Không có nhãn"

            # Lấy thông tin ưu đãi (voucher, khuyến mãi)
            try:
                uu_dai_selectors = [
                    "div.truncate.bg-shopee-voucher-yellow.text-white.leading-4.text-sp10.px-px",
                    "div[class*='voucher-yellow']",
                    "div[class*='bg-shopee-voucher']",
                    "div[bis_skin_checked='1']"
                ]
                
                uu_dai = None
                for selector in uu_dai_selectors:
                    try:
                        uu_dai_elements = item.find_elements(By.CSS_SELECTOR, selector)
                        if uu_dai_elements:
                            uu_dai = uu_dai_elements[0].text.strip()
                            if uu_dai:  # Nếu tìm thấy thông tin ưu đãi không rỗng, thoát khỏi vòng lặp
                                break
                    except:
                        continue
                
                if not uu_dai:
                    uu_dai = "Không có ưu đãi"
            except Exception as e:
                print(f"Lỗi khi xử lý ưu đãi: {str(e)}")
                uu_dai = "Không có ưu đãi"

            # Lấy thông tin chỉ báo khuyến mãi (Rẻ Vô Địch, Mua Kèm Deal Sốc, v.v.)
            try:
                promo_indicator_selectors = [
                    "div.box-border.flex.items-center span.truncate",
                    "div[aria-hidden='true'] span.truncate[style*='color: rgb(238, 77, 45)']",
                    "div.overflow-hidden.h-4 span.truncate",
                    "div.relative.relative.flex.items-center span.truncate",
                    "div.box-border.flex.space-x-1.h-5 div.pointer-events-none span.truncate"
                ]
                
                promo_indicators = []
                for selector in promo_indicator_selectors:
                    try:
                        promo_elements = item.find_elements(By.CSS_SELECTOR, selector)
                        for element in promo_elements:
                            text = element.text.strip()
                            if text and text not in promo_indicators:  # Tránh trùng lặp
                                parent_element = driver.execute_script("return arguments[0].parentElement", element)
                                parent_text = parent_element.text.strip() if parent_element else ""
                                if "₫" not in text and "₫" not in parent_text:
                                    promo_indicators.append(text)
                    except Exception as e:
                        continue
                
                if promo_indicators:
                    promo_text = " - ".join(promo_indicators)
                else:
                    promo_text = "Không có"
            except Exception as e:
                print(f"Lỗi khi xử lý chỉ báo khuyến mãi: {str(e)}")
                promo_text = "Không có"
                        
            # Lấy thông tin đánh giá sản phẩm
            try:
                rating_selectors = [
                    "div.text-shopee-black87.text-xs\\/sp14.flex-none",
                    "div.text-shopee-black87",
                    "div[class*='rating']",
                    "div[bis_skin_checked='1']:not([class*='truncate'])"
                ]
                
                rating = None
                for selector in rating_selectors:
                    try:
                        rating_elements = item.find_elements(By.CSS_SELECTOR, selector)
                        for element in rating_elements:
                            text = element.text.strip()
                            if text and any(char.isdigit() for char in text):
                                try:
                                    float_val = float(text)
                                    if 0 <= float_val <= 5:  # Ratings thường từ 0-5
                                        rating = text
                                        break
                                except ValueError:
                                    continue
                        if rating:  # Nếu đã tìm thấy rating, thoát khỏi vòng lặp
                            break
                    except Exception as e:
                        continue
                
                if not rating:
                    rating = "Chưa có đánh giá"
            except Exception as e:
                print(f"Lỗi khi xử lý đánh giá sản phẩm: {str(e)}")
                rating = "Chưa có đánh giá"

            # Lấy thông tin địa chỉ/vị trí của sản phẩm
            try:
                location_selectors = [
                    "div.flex-shrink.min-w-0.truncate.text-shopee-black54.text-sp10 span.ml-\\[3px\\]",
                    "span[aria-label^='location-']",
                    "span.align-middle:not(:first-child)",
                    "div[class*='text-shopee-black54'] span.align-middle"
                ]
                
                location = None
                for selector in location_selectors:
                    try:
                        location_elements = item.find_elements(By.CSS_SELECTOR, selector)
                        if location_elements:
                            for element in location_elements:
                                text = element.text.strip()
                                if text:
                                    location = text
                                    break
                        
                        if not location and selector == "span[aria-label^='location-']":
                            aria_elements = item.find_elements(By.CSS_SELECTOR, selector)
                            if aria_elements:
                                aria_label = aria_elements[0].get_attribute("aria-label")
                                if aria_label and aria_label.startswith("location-"):
                                    location = aria_label.replace("location-", "")
                        
                        if location:  # Nếu tìm thấy địa chỉ, thoát khỏi vòng lặp
                            break
                    except Exception as e:
                        continue
                
                if not location:
                    location = "Không có thông tin"
            except Exception as e:
                print(f"Lỗi khi xử lý thông tin địa chỉ: {str(e)}")
                location = "Không có thông tin"
            
            # Lấy thông tin item_id, shop_id, cat_id
            item_id, shop_id, cat_id = None, None, None
            try:
                # Trước tiên, tìm chính xác thẻ "Tìm sản phẩm tương tự"
                similar_product_link = None
                
                try:
                    similar_element = item.find_element(By.CSS_SELECTOR, 
                        "a.text-white.text-secondary, a[class*='text-white'][class*='text-secondary'], a[class*='bg-shopee-primary']")
                    
                    if "Tìm sản phẩm tương tự" in similar_element.text:
                        similar_product_link = similar_element.get_attribute("href")
                except:
                    pass
                    
                if not similar_product_link:
                    try:
                        similar_element = item.find_element(By.XPATH, ".//a[contains(text(), 'Tìm sản phẩm tương tự')]")
                        similar_product_link = similar_element.get_attribute("href")
                    except:
                        pass
                
                if not similar_product_link:
                    try:
                        all_links = item.find_elements(By.TAG_NAME, "a")
                        for link in all_links:
                            href = link.get_attribute("href")
                            if href and "find_similar_products" in href:
                                similar_product_link = href
                                break
                    except Exception as e:
                        print(f"Lỗi khi tìm tất cả thẻ a: {e}")
                
                # Trích xuất ID từ link "Tìm sản phẩm tương tự" nếu có
                if similar_product_link and "find_similar_products" in similar_product_link:
                    try:
                        if "catid=" in similar_product_link:
                            cat_id = re.search(r'catid=(\d+)', similar_product_link).group(1)
                        if "itemid=" in similar_product_link:
                            item_id = re.search(r'itemid=(\d+)', similar_product_link).group(1)
                        if "shopid=" in similar_product_link:
                            shop_id = re.search(r'shopid=(\d+)', similar_product_link).group(1)
                    except Exception as e:
                        print(f"Lỗi khi trích xuất ID từ URL: {e}")
                
                # Nếu vẫn không tìm thấy, thử lấy từ URL chính của sản phẩm
                if not (item_id and shop_id):
                    try:
                        main_link = item.find_element(By.CSS_SELECTOR, "a.contents, a[class*='contents']")
                        product_url = main_link.get_attribute("href")
                        
                        item_id_shop_id_pattern = re.search(r'i\.(\d+)\.(\d+)', product_url)
                        if item_id_shop_id_pattern:
                            item_id = item_id if item_id else item_id_shop_id_pattern.group(1)
                            shop_id = shop_id if shop_id else item_id_shop_id_pattern.group(2)
                    except Exception as e:
                        print(f"Lỗi khi phân tích URL sản phẩm: {e}")

            except Exception as e:
                print(f"Lỗi khi xử lý item_id, shop_id, cat_id: {str(e)}")

            # Hiển thị tiến độ
            if index % 5 == 0 or index == 1:  # Hiển thị cho sản phẩm đầu tiên và sau mỗi 5 sản phẩm
                print(f"Đang xử lý sản phẩm {index}/{len(product_items)}")

            # Chuẩn bị thông tin trích xuất để đảm bảo không có lỗi
            loai_san_pham = "Không xác định"
            ten_sp_chinh_xac = "Không xác định"
            thuong_hieu = "Không xác định"
            cong_dung = "Không xác định"
            dung_tich = "Không xác định"
            xuat_xu = "Không xác định"
            
            if product_info:
                # Đảm bảo các khóa tồn tại và giá trị không phải None
                if "loai_san_pham" in product_info and product_info["loai_san_pham"]:
                    loai_san_pham = str(product_info["loai_san_pham"])
                if "ten_sp_chinh_xac" in product_info and product_info["ten_sp_chinh_xac"]:
                    ten_sp_chinh_xac = str(product_info["ten_sp_chinh_xac"])
                if "thuong_hieu" in product_info and product_info["thuong_hieu"]:
                    thuong_hieu = str(product_info["thuong_hieu"])
                if "cong_dung" in product_info and product_info["cong_dung"]:
                    cong_dung = str(product_info["cong_dung"])
                if "dung_tich" in product_info and product_info["dung_tich"]:
                    dung_tich = str(product_info["dung_tich"])
                if "xuat_xu" in product_info and product_info["xuat_xu"]:
                    xuat_xu = str(product_info["xuat_xu"])
            
            # Thêm vào danh sách kết quả
            product = {
                "Ngày cào": current_date,
                "Mã sản phẩm": item_id,
                "Mã shop": shop_id,
                "Mã danh mục": cat_id,
                "Tên sản phẩm": name,
                "Loại sản phẩm": loai_san_pham,
                "Tên SP chính xác": ten_sp_chinh_xac,
                "Giá bán hiển thị trên feed": price,
                "Giảm giá hiển thị trên feed": discount,
                "Đã bán": sold,
                "Nhãn": label,
                "Ưu đãi": uu_dai,
                "Chỉ báo khuyến mãi": promo_text,
                "Đánh giá": rating,
                "Địa chỉ": location,
                "Danh mục sản phẩm": category,
                "Link": link,
                "Thương hiệu": thuong_hieu,
                "Công dụng chính": cong_dung,
                "Dung tích/khối lượng": dung_tich,
                "Xuất xứ": xuat_xu
            }
            
            products.append(product)
            processed_names.add(name)
            
            # Thêm độ trễ nhỏ để tránh quá tải
            if index % 10 == 0:
                time.sleep(random.uniform(0.5, 1))
                
        except Exception as e:
            print(f"Lỗi khi xử lý sản phẩm {index}: {str(e)}")
            # Ghi log lỗi chi tiết
            traceback.print_exc()
            continue
    
    print(f"Hoàn thành cào dữ liệu. Đã thu thập {len(products)} sản phẩm.")
    return products

def save_to_database(products, connection_string=None, table_name=None):
    """
    Lưu dữ liệu sản phẩm vào database SQL Server
    
    Args:
        products: Danh sách sản phẩm cần lưu
        connection_string: Chuỗi kết nối SQL Server, mặc định sẽ sử dụng giá trị trong hàm
        table_name: Tên bảng để lưu dữ liệu, mặc định là "shopee_products"
    """
    
    # Default table name if none provided
    if table_name is None:
        table_name = "#temp_shopee_products"
    
    # Count successful inserts
    successful_inserts = 0
    
    try:
        # Import pyodbc for SQL Server connection
        import pyodbc
        
        # Create connection
        print(f"Đang kết nối đến SQL Server...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print(f"Kết nối thành công!")
        
        # Create table if it doesn't exist - thêm các cột mới
        print(f"Kiểm tra và tạo bảng {table_name} nếu chưa tồn tại...")
        create_table_query = f"""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{table_name}]') AND type in (N'U'))
        BEGIN
        CREATE TABLE [dbo].[{table_name}] (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ngay_cao DATETIME,
            ma_san_pham BIGINT NULL,
            ma_shop BIGINT NULL,
            ma_danh_muc BIGINT NULL,
            ten_san_pham NVARCHAR(MAX),
            loai_san_pham NVARCHAR(MAX) NULL,
            ten_sp_chinh_xac NVARCHAR(MAX) NULL,
            gia_ban BIGINT NULL,
            giam_gia NVARCHAR(255),
            da_ban FLOAT NULL,
            nhan NVARCHAR(255),
            uu_dai NVARCHAR(255),
            chi_bao_khuyen_mai NVARCHAR(MAX),
            danh_gia NVARCHAR(255),
            dia_chi NVARCHAR(255),
            danh_muc_san_pham NVARCHAR(255),
            link NVARCHAR(MAX),
            thuong_hieu NVARCHAR(255),
            cong_dung_chinh NVARCHAR(MAX),
            dung_tich_khoi_luong NVARCHAR(255),
            xuat_xu NVARCHAR(255)
        )
        END
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print(f"Bảng đã sẵn sàng!")
        
        # Insert data into table
        print(f"Bắt đầu thêm {len(products)} sản phẩm vào database...")
        for product in products:
            insert_query = f"""
            INSERT INTO [dbo].[{table_name}] (
                ngay_cao, ma_san_pham, ma_shop, ma_danh_muc, ten_san_pham, 
                loai_san_pham, ten_sp_chinh_xac,
                gia_ban, giam_gia, da_ban, nhan, uu_dai, 
                chi_bao_khuyen_mai, danh_gia, dia_chi, danh_muc_san_pham, link,
                thuong_hieu, cong_dung_chinh, dung_tich_khoi_luong, xuat_xu
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Chuyển đổi kiểu dữ liệu trước khi insert
            
            # Chuyển đổi Ngày cào sang DATETIME
            try:
                from datetime import datetime
                ngay_cao_str = product.get("Ngày cào", "")
                if ngay_cao_str:
                    ngay_cao = datetime.strptime(ngay_cao_str, "%d/%m/%Y")
                else:
                    ngay_cao = datetime.now()  # Mặc định ngày hiện tại
            except Exception as e:
                print(f"Lỗi chuyển đổi ngày: {e}, sử dụng ngày hiện tại")
                ngay_cao = datetime.now()
                
            # Chuyển đổi Mã sản phẩm sang INT
            try:
                ma_san_pham_str = product.get("Mã sản phẩm", "")
                ma_san_pham = int(ma_san_pham_str) if ma_san_pham_str and ma_san_pham_str.isdigit() else None
            except:
                ma_san_pham = None
                
            # Chuyển đổi Mã shop sang INT
            try:
                ma_shop_str = product.get("Mã shop", "")
                ma_shop = int(ma_shop_str) if ma_shop_str and ma_shop_str.isdigit() else None
            except:
                ma_shop = None
                
            # Chuyển đổi Mã danh mục sang INT
            try:
                ma_danh_muc_str = product.get("Mã danh mục", "")
                ma_danh_muc = int(ma_danh_muc_str) if ma_danh_muc_str and ma_danh_muc_str.isdigit() else None
            except:
                ma_danh_muc = None
                
            # Chuyển đổi Giá bán sang INT (loại bỏ ký tự đ và dấu chấm)
            try:
                gia_ban_str = product.get("Giá bán hiển thị trên feed", "")
                # Loại bỏ ký tự đ và dấu chấm, phẩy
                gia_ban_str = gia_ban_str.replace("₫", "").replace(".", "").replace(",", "").strip()
                gia_ban = int(gia_ban_str) if gia_ban_str and gia_ban_str.isdigit() else None
            except:
                gia_ban = None
                
            # Chuyển đổi Đã bán sang FLOAT (loại bỏ "đã bán" hoặc các text khác)
            try:
                da_ban_str = product.get("Đã bán", "")
                # Trích xuất số từ chuỗi (ví dụ: "Đã bán 1.2k" -> 1200)
                import re
                da_ban_matches = re.search(r'(\d+[\.,]?\d*)\s*k?', da_ban_str)
                if da_ban_matches:
                    da_ban_value = da_ban_matches.group(1).replace(",", ".")
                    da_ban = float(da_ban_value)
                    # Nếu có "k" thì nhân với 1000
                    if "k" in da_ban_str.lower():
                        da_ban *= 1000
                else:
                    da_ban = None
            except:
                da_ban = None

            # Đảm bảo các giá trị cho cột được xử lý an toàn
            loai_san_pham_val = product.get("Loại sản phẩm", "Không xác định")
            ten_sp_chinh_xac_val = product.get("Tên SP chính xác", "Không xác định")
            thuong_hieu = product.get("Thương hiệu", "Không xác định")
            cong_dung_chinh = product.get("Công dụng chính", "Không xác định")
            dung_tich = product.get("Dung tích/khối lượng", "Không xác định")
            xuat_xu = product.get("Xuất xứ", "Không xác định")
            
            if not isinstance(loai_san_pham_val, str):
                loai_san_pham_val = str(loai_san_pham_val) if loai_san_pham_val is not None else "Không xác định"
            if not isinstance(ten_sp_chinh_xac_val, str):
                ten_sp_chinh_xac_val = str(ten_sp_chinh_xac_val) if ten_sp_chinh_xac_val is not None else "Không xác định"
            if not isinstance(thuong_hieu, str):
                thuong_hieu = str(thuong_hieu) if thuong_hieu is not None else "Không xác định"
            if not isinstance(cong_dung_chinh, str):
                cong_dung_chinh = str(cong_dung_chinh) if cong_dung_chinh is not None else "Không xác định"
            if not isinstance(dung_tich, str):
                dung_tich = str(dung_tich) if dung_tich is not None else "Không xác định"
            if not isinstance(xuat_xu, str):
                xuat_xu = str(xuat_xu) if xuat_xu is not None else "Không xác định"
            
            values = (
                ngay_cao,                                         # DATETIME
                ma_san_pham,                                      # INT
                ma_shop,                                          # INT
                ma_danh_muc,                                      # INT
                product.get("Tên sản phẩm", ""),                  # NVARCHAR(MAX)
                loai_san_pham_val,                                # NVARCHAR(MAX)
                ten_sp_chinh_xac_val,                             # NVARCHAR(MAX)
                gia_ban,                                          # INT
                product.get("Giảm giá hiển thị trên feed", ""),   # NVARCHAR(255)
                da_ban,                                           # FLOAT
                product.get("Nhãn", ""),                          # NVARCHAR(255)
                product.get("Ưu đãi", ""),                        # NVARCHAR(255)
                product.get("Chỉ báo khuyến mãi", ""),            # NVARCHAR(MAX)
                product.get("Đánh giá", ""),                      # NVARCHAR(255)
                product.get("Địa chỉ", ""),                       # NVARCHAR(255)
                product.get("Danh mục sản phẩm", ""),             # NVARCHAR(255)
                product.get("Link", ""),                          # NVARCHAR(MAX)
                thuong_hieu,                                      # NVARCHAR(255)
                cong_dung_chinh,                                  # NVARCHAR(MAX)
                dung_tich,                                        # NVARCHAR(255)
                xuat_xu                                           # NVARCHAR(255)
            )
            
            cursor.execute(insert_query, values)
            successful_inserts += 1
            
            # Commit every 100 records to avoid transaction log overflow
            if successful_inserts % 100 == 0:
                conn.commit()
                print(f"Đã lưu {successful_inserts}/{len(products)} sản phẩm vào database...")
        
        # Final commit for any remaining records
        conn.commit()
        
    except Exception as e:
        print(f"Lỗi khi lưu vào database: {e}")
        print(f"Chi tiết lỗi: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("Đã đóng kết nối database.")

if __name__ == "__main__":
    print("\n=== CÔNG CỤ CÀO DỮ LIỆU SHOPEE VỚI UNDETECTED_CHROMEDRIVER VÀ GOOGLE GEMINI AI ===")
    print("Lưu ý: Trình duyệt sẽ hiển thị để bạn theo dõi quá trình cào dữ liệu")
    print("Công cụ này sử dụng undetected_chromedriver để tránh phát hiện bot\n")

    skincare_product_list = [
        "sữa rửa mặt",
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
        # "mặt nạ dưỡng da"
    ]

    all_scraped_products_from_all_terms = []

    # Trang bắt đầu
    start_page = 0
    # Số trang cần cào cho mỗi sản phẩm
    num_pages = 20

    driver = None  # Initialize driver to None for the finally block
    try:
        print("Đang khởi tạo trình duyệt với undetected_chromedriver...")
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        profile_path = os.path.join(os.getcwd(), "shopee_chrome_profile")
        if not os.path.exists(profile_path):
            os.makedirs(profile_path, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        
        driver = uc.Chrome(options=chrome_options, version_main=136)
        driver.set_window_size(1920, 1080)
        
        driver.get("https://shopee.vn")
        main_search_bar_class = "shopee-searchbar-input__input"
        try:
            print("Kiểm tra sự hiện diện của trang Shopee chính (tìm kiếm thanh tìm kiếm)...")
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CLASS_NAME, main_search_bar_class))
            )
            print("Thanh tìm kiếm được tìm thấy. Giả sử không có CAPTCHA toàn trang hoặc đăng nhập đã được xử lý bởi hồ sơ.")
            time.sleep(2) 
        except TimeoutException:
            print(f"Không tìm thấy thanh tìm kiếm (class: {main_search_bar_class}) trong 15 giây. Có khả năng CAPTCHA hoặc pop-up đang hiển thị.")
            input("Vui lòng xử lý CAPTCHA, đăng nhập hoặc bất kỳ pop-up nào, sau đó nhấn Enter để tiếp tục: ")
        except Exception as e:
            print(f"Đã xảy ra lỗi không mong muốn khi kiểm tra thanh tìm kiếm: {e}")
            print("Tiếp tục với việc yêu cầu xử lý thủ công...")
            input("Vui lòng xử lý CAPTCHA, đăng nhập hoặc bất kỳ pop-up nào, sau đó nhấn Enter để tiếp tục: ")

        for search_term in skincare_product_list:
            print(f"\n\n>>> Bắt đầu cào dữ liệu cho từ khóa: '{search_term}', từ trang {start_page}, số lượng {num_pages} trang. <<<")
            
            products_for_this_term = crawl_shopee(driver, search_term, start_page, num_pages)
            
            if products_for_this_term:
                all_scraped_products_from_all_terms.extend(products_for_this_term)
                print(f"\n>>> Đã cào được {len(products_for_this_term)} sản phẩm cho từ khóa '{search_term}'. <<<")
            else:
                print(f"\n>>> Không cào được sản phẩm nào cho từ khóa '{search_term}'. <<<")
            
            if skincare_product_list.index(search_term) < len(skincare_product_list) - 1:
                print("\n--- Chuyển sang từ khóa tiếp theo ---")
                # Optional: Add a small delay between different search terms if Shopee is sensitive to rapid searches
                # time.sleep(random.uniform(3, 7))

    except Exception as e:
        print(f"Lỗi tổng thể trong quá trình thực thi: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print("\nĐã hoàn thành tất cả các từ khóa. Đang đóng trình duyệt...")
            driver.quit()
            print("Đã đóng trình duyệt thành công.")

    if all_scraped_products_from_all_terms:
        print(f"\n\n*** HOÀN TẤT TẤT CẢ CÁC TỪ KHÓA ***")
        print(f"Tổng cộng đã cào được {len(all_scraped_products_from_all_terms)} sản phẩm từ tất cả các từ khóa.")
    else:
        print(f"\n\n*** HOÀN TẤT TẤT CẢ CÁC TỪ KHÓA ***")
        print("Không cào được sản phẩm nào từ tất cả các từ khóa.")