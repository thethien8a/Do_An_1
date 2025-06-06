import datetime
from config import VN_PROVINCES

def clean_cong_dung_sp(value):
    """Nhận vào giá trị chuỗi công dụng cách nhau bởi dấu , và trả về list các công dụng"""
    if value == 'N/A':
        return "Không xác định"

    if value is None:
        return "Không xác định"
    
    if "," in value:
        # Split by comma and clean each item
        cong_dung_list = [item.strip().capitalize() for item in value.split(',')] 
        
        seen = set()
        # Using a list comprehension to filter out empty strings and duplicates while preserving order
        return [x for x in cong_dung_list if x and not (x in seen or seen.add(x))]
    else:
        return value.capitalize().strip()


def just_capitalize(value):
    if value == "N/A":
        return "Không xác định"
    
    if value is None:
        return "Không xác định"
    
    return value.capitalize()

def clean_address(value):
    if value == 'N/A' or value is None:
        return "Không có thông tin"
    if value == "Vietnam":
        return "Việt Nam"
    if value.startswith("TP."):
        return value.replace("TP.", "")
    if value in VN_PROVINCES:
        return value
    else:
        return "Nước ngoài"
    
def clean_price(value, to_type=float):
    if value is None:
        return None
    # Ensure replace_value is defined before being used in the condition
    replace_value = str(value).replace("₫", "").replace(".", "").replace(",", "").strip()
    if replace_value == "":
        return None
    return to_type(replace_value)

def clean_quantity_sold(value, to_type=int):
    if value is None:
        return None
    if value == 'N/A':
        return None
    value = value.replace("sold", "").strip()
    if "K" in value:
        number = float(value.replace("K", ""))
        number *= 1000
        return int(number)
    if "M" in value:
        number = float(value.replace("M", ""))
        number *= 1000000
        return int(number)
    
    return int(round(float(value)))

def clean_rating_score(value, to_type=float):
    if value is None:
        return None
    if value == "":
        return None
    if value == "Chưa có đánh giá":
        return None
    return to_type(value)

def clean_exact_name(value):
    if value is None:
        return "Không xác định"
    if value == "N/A":
        return "Không xác định"
    return value

def clean_product_type(value):
    if value is None:
        return "Không xác định"
    return value.capitalize().strip()

def clean_brand(value):
    if value is None:
        return "Không xác định"
    if value == "N/A":
        return "Không xác định"
    return value.capitalize().strip()

# Main transformation function
def clean_row_data(raw_row_dict):
    """
    Cleans data for a single row using helper functions.
    Converts data types to be ready for DWH.
    raw_row_dict is a dictionary representing a row from the source.
    """
    if not raw_row_dict:
        return None

    cleaned_row = {}
    
    # Apply cleaning to known columns. Add more as needed.
    # Assuming 'id' is the primary key and doesn't need cleaning itself, just passed through.
    cleaned_row['id'] = raw_row_dict.get('id')

    cleaned_row["ten_chinh_xac_sp"] = clean_exact_name(raw_row_dict.get("ten_chinh_xac_sp"))
    cleaned_row["loai_sp"] = clean_product_type(raw_row_dict.get("loai_sp"))
    cleaned_row["thuong_hieu_sp"] = clean_brand(raw_row_dict.get("thuong_hieu_sp"))
    cleaned_row["ten_sp_hien_thi"] = raw_row_dict.get("ten_sp_hien_thi")
    cleaned_row["link_sp"] = raw_row_dict.get("link_sp")
    cleaned_row["cong_dung_sp"] = clean_cong_dung_sp(raw_row_dict.get("cong_dung_sp")) 
    cleaned_row["nguon_du_lieu"] = raw_row_dict.get("nguon_du_lieu")
    cleaned_row["ma_sp_shop_platform"] = raw_row_dict.get("product_id_shop_platform") 
    cleaned_row["ma_shop_platform"] = raw_row_dict.get("shop_id_platform")
    cleaned_row['ngay_cao_dlieu'] = raw_row_dict.get('ngay_cao_dlieu')
    cleaned_row['dia_chi_shop'] = clean_address(raw_row_dict.get('dia_chi_shop'))
    # Numeric columns
    cleaned_row['gia_hien_thi'] = clean_price(raw_row_dict.get('gia_hien_thi'), to_type=float)
    cleaned_row['so_sp_da_ban'] = clean_quantity_sold(raw_row_dict.get('so_sp_da_ban'), to_type=int)
    cleaned_row['danh_gia'] = clean_rating_score(raw_row_dict.get('danh_gia'), to_type=float)
    

    return cleaned_row
