import pyodbc
from datetime import datetime
from config import DW_SQL_SERVER_CONFIG#LAKE for updating source

def get_dw_db_connection():
    """Establishes a connection to the Data Warehouse SQL Server database."""
    conn_str = (
        f"DRIVER={DW_SQL_SERVER_CONFIG['driver']};"
        f"SERVER={DW_SQL_SERVER_CONFIG['server']};"
        f"DATABASE={DW_SQL_SERVER_CONFIG['database']};"
        f"UID={DW_SQL_SERVER_CONFIG['username']};"
        f"PWD={DW_SQL_SERVER_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error connecting to Data Warehouse database: {sqlstate}")
        return None

def create_tables_if_not_exist(dw_cursor):
    """Creates the DWH tables if they do not already exist."""
    tables_ddl = {
        "Dim_Brand": """
            CREATE TABLE Dim_Brand (
                Brand_Key INT IDENTITY(1,1) PRIMARY KEY,
                Brand_Name NVARCHAR(255) UNIQUE NOT NULL
            );
        """,
        "Dim_Product": """
            CREATE TABLE Dim_Product (
                Product_Key INT IDENTITY(1,1) PRIMARY KEY,
                Product_ID_Shop_Platform NVARCHAR(255) UNIQUE,
                Product_Name_Display NVARCHAR(MAX),
                Product_Exact_Name NVARCHAR(300),
                Product_Category NVARCHAR(MAX),
                Product_Link NVARCHAR(MAX) 
            );
        """,
        "Dim_Product_Function": """
            CREATE TABLE Dim_Product_Function (
                Function_Key INT IDENTITY(1,1) PRIMARY KEY,
                Function_Name NVARCHAR(255) UNIQUE NOT NULL
            );
        """,
        "Product_Function_Bridge": """
            CREATE TABLE Product_Function_Bridge (
                Product_Key INT REFERENCES Dim_Product(Product_Key),
                Function_Key INT REFERENCES Dim_Product_Function(Function_Key),
                PRIMARY KEY (Product_Key, Function_Key)
            );
        """,            
        "Dim_Platform": """
            CREATE TABLE Dim_Platform (
                Platform_Key INT IDENTITY(1,1) PRIMARY KEY,
                Platform_Name NVARCHAR(255) UNIQUE NOT NULL
            );
        """,
        "Dim_Shop": """
            CREATE TABLE Dim_Shop (
                Shop_Key INT IDENTITY(1,1) PRIMARY KEY,
                Shop_ID_Platform NVARCHAR(255) UNIQUE,
                Shop_Address NVARCHAR(255),
                UNIQUE(Shop_ID_Platform, Shop_Address)
            );
        """,
        "Dim_Date": """
            CREATE TABLE Dim_Date (
                Date_Key INT IDENTITY(1,1) PRIMARY KEY,
                Date DATE UNIQUE NOT NULL,
                Day INT NOT NULL,
                Month INT NOT NULL,
                Year INT NOT NULL
            );
        """,
        "Fact_ProductSales": """
            CREATE TABLE Fact_ProductSales (
                ProductSales_ID INT IDENTITY(1,1) PRIMARY KEY,
                Product_Key INT REFERENCES Dim_Product(Product_Key),
                Date_Key INT REFERENCES Dim_Date(Date_Key),
                Shop_Key INT REFERENCES Dim_Shop(Shop_Key),
                Brand_Key INT REFERENCES Dim_Brand(Brand_Key),        -- Denormalized for easier BI, or could be removed if joining via Dim_Product
                Platform_Key INT REFERENCES Dim_Platform(Platform_Key),  -- Denormalized for easier BI
                Quantity_Sold INT,
                Display_Price DECIMAL(18, 2),
                Rating_Score DECIMAL(18, 2)
            );
        """
    }

    for table_name, ddl_query in tables_ddl.items():
        try:
            # Check if table exists
            dw_cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = 'dbo'") # Adjust schema if not dbo
            if dw_cursor.fetchone()[0] == 0:
                print(f"Table {table_name} does not exist. Creating...")
                dw_cursor.execute(ddl_query)
                print(f"Table {table_name} created successfully.")
            # No commit here, main ETL flow will handle commit
        except pyodbc.Error as e:
            print(f"Error creating table {table_name}: {e}")
            # Decide if to raise or continue

# --- Dimension Key Helper Functions ---

def get_or_create_brand_key(dw_cursor, brand_name):
    """Gets or creates a key for Dim_Brand using OUTPUT clause."""
    if not brand_name: 
        return None
    
    try:
        dw_cursor.execute("SELECT Brand_Key FROM Dim_Brand WHERE Brand_Name = ?", brand_name)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            # Use OUTPUT clause to get the inserted key
            dw_cursor.execute("INSERT INTO Dim_Brand (Brand_Name) OUTPUT inserted.Brand_Key VALUES (?)", brand_name)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError: 
        dw_cursor.execute("SELECT Brand_Key FROM Dim_Brand WHERE Brand_Name = ?", brand_name)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Brand_Key for {brand_name} after IntegrityError.")
            raise
    except Exception as e:
        print(f"Error in get_or_create_brand_key for '{brand_name}': {e}")
        raise

def get_or_create_platform_key(dw_cursor, platform_name):
    """Gets or creates a key for Dim_Platform using OUTPUT clause."""
    if not platform_name:
        return None

    try:
        dw_cursor.execute("SELECT Platform_Key FROM Dim_Platform WHERE Platform_Name = ?", platform_name)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            dw_cursor.execute("INSERT INTO Dim_Platform (Platform_Name) OUTPUT inserted.Platform_Key VALUES (?)", platform_name)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError:
        dw_cursor.execute("SELECT Platform_Key FROM Dim_Platform WHERE Platform_Name = ?", platform_name)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Platform_Key for {platform_name} after IntegrityError.")
            raise
    except Exception as e:
        print(f"Error in get_or_create_platform_key for '{platform_name}': {e}")
        raise

def get_or_create_shop_key(dw_cursor, shop_id_platform, shop_address):
    """Gets or creates a key for Dim_Shop using OUTPUT clause."""
    if shop_id_platform is None: 
        print(f"Warning: shop_id_platform is None. Cannot reliably get/create Dim_Shop key. Address: '{shop_address}'")
        return None 

    try:
        dw_cursor.execute("SELECT Shop_Key FROM Dim_Shop WHERE Shop_ID_Platform = ?", shop_id_platform)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            sql_shop_address = shop_address if shop_address else None
            dw_cursor.execute("INSERT INTO Dim_Shop (Shop_ID_Platform, Shop_Address) OUTPUT inserted.Shop_Key VALUES (?, ?)", 
                              shop_id_platform, sql_shop_address)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError: 
        dw_cursor.execute("SELECT Shop_Key FROM Dim_Shop WHERE Shop_ID_Platform = ?", shop_id_platform)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Shop_Key for Shop_ID_Platform {shop_id_platform} after IntegrityError.")
            raise
    except Exception as e:
        print(f"Error in get_or_create_shop_key for Shop_ID_Platform '{shop_id_platform}': {e}")
        raise

def get_or_create_date_key(dw_cursor, date_string):
    """Gets or creates a key for Dim_Date using OUTPUT clause."""
    if not date_string:
        return None
    date_string = datetime.strptime(date_string, '%Y-%m-%d')
    try:
        dw_cursor.execute("SELECT Date_Key FROM Dim_Date WHERE Date = ?", date_string)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            day = date_string.day
            month = date_string.month
            year = date_string.year
            dw_cursor.execute("INSERT INTO Dim_Date (Date, Day, Month, Year) OUTPUT inserted.Date_Key VALUES (?, ?, ?, ?)",
                              date_string, day, month, year)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError:
        dw_cursor.execute("SELECT Date_Key FROM Dim_Date WHERE Date = ?", date_string)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Date_Key for {date_string} after IntegrityError.")
            raise
    except Exception as e:
        print(f"Error in get_or_create_date_key for '{date_string}': {e}")
        raise

def get_or_create_product_function_key(dw_cursor, function_name):
    """Gets or creates a key for Dim_Product_Function using OUTPUT clause."""
    if not function_name or not isinstance(function_name, str):
        return None
    
    function_name_cleaned = function_name.strip()
    if not function_name_cleaned:
        return None

    try:
        dw_cursor.execute("SELECT Function_Key FROM Dim_Product_Function WHERE Function_Name = ?", function_name_cleaned)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            dw_cursor.execute("INSERT INTO Dim_Product_Function (Function_Name) OUTPUT inserted.Function_Key VALUES (?)", function_name_cleaned)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError:
        dw_cursor.execute("SELECT Function_Key FROM Dim_Product_Function WHERE Function_Name = ?", function_name_cleaned)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Function_Key for '{function_name_cleaned}' after IntegrityError.")
            raise 
    except Exception as e:
        print(f"Error in get_or_create_product_function_key for '{function_name_cleaned}': {e}")
        raise 

def link_product_to_functions(dw_cursor, product_key, function_names_list):
    """Links a product to its functions in Product_Function_Bridge."""
    if not product_key or not function_names_list or not isinstance(function_names_list, list):
        # print(f"Info: No functions to link for Product_Key {product_key}.")
        return

    for func_name in function_names_list:
        if not func_name or not isinstance(func_name, str) or not func_name.strip(): # Skip empty or invalid names
            continue
        
        function_key = get_or_create_product_function_key(dw_cursor, func_name)
        if function_key:
            try:
                dw_cursor.execute("INSERT INTO Product_Function_Bridge (Product_Key, Function_Key) VALUES (?, ?)", 
                                  product_key, function_key)
                # print(f"Linked Product_Key {product_key} to Function_Key {function_key} ('{func_name}')")
            except pyodbc.IntegrityError: # Already linked
                # print(f"Info: Product_Key {product_key} already linked to Function_Key {function_key} ('{func_name}').")
                pass 
            except Exception as e:
                print(f"Error linking Product_Key {product_key} to Function_Key {function_key} ('{func_name}'): {e}")
                # Decide if this should raise or just log

def get_or_create_product_key(dw_cursor, product_id_shop_platform, product_name_display, 
                               product_exact_name, product_category, product_link):
    """Gets or creates a key for Dim_Product. Product_Function is handled separately."""
    
    if product_id_shop_platform is None:
        print(f"Warning: product_id_shop_platform is None. Cannot reliably get/create Dim_Product key. Name: '{product_name_display}'")
        return None

    # Product_Function (cong_dung_sp) is no longer directly in Dim_Product table
    # It will be handled by get_or_create_product_function_key and link_product_to_functions

    try:
        # Prioritize lookup by Product_ID_Shop_Platform as it's marked UNIQUE in DDL
        dw_cursor.execute("SELECT Product_Key FROM Dim_Product WHERE Product_ID_Shop_Platform = ?", product_id_shop_platform)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            sql_product_name_display = product_name_display if product_name_display else None
            sql_product_exact_name = product_exact_name if product_exact_name else None
            sql_product_category = product_category if product_category else None
            sql_product_link = product_link if product_link else None

            insert_query = """
                INSERT INTO Dim_Product 
                (Product_ID_Shop_Platform, Product_Name_Display, Product_Exact_Name, Product_Category, Product_Link) 
                OUTPUT inserted.Product_Key
                VALUES (?, ?, ?, ?, ?)
            """
            dw_cursor.execute(insert_query, product_id_shop_platform, sql_product_name_display, sql_product_exact_name, 
                              sql_product_category, sql_product_link)
            new_key = dw_cursor.fetchone()[0]
            return new_key
    except pyodbc.IntegrityError: 
        dw_cursor.execute("SELECT Product_Key FROM Dim_Product WHERE Product_ID_Shop_Platform = ?", product_id_shop_platform)
        row = dw_cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"Error: Failed to get or create Product_Key for Product_ID_Shop_Platform {product_id_shop_platform} after IntegrityError.")
            raise
    except Exception as e:
        print(f"Error in get_or_create_product_key for Product_ID_Shop_Platform '{product_id_shop_platform}': {e}")
        raise

# --- End Dimension Key Helper Functions ---

def load_row_to_warehouse(cleaned_row_data, dw_cursor):
    """
    Loads a single cleaned row into the Data Warehouse.
    This function now uses helper functions to get/create dimension keys
    and then inserts into the fact table.
    Returns True if successful, False otherwise.
    """
    if not cleaned_row_data:
        print("Error: cleaned_row_data is None in load_row_to_warehouse.")
        return False

    try:
        # 1. Get/Create Dimension Keys
        brand_key = get_or_create_brand_key(dw_cursor, cleaned_row_data.get('thuong_hieu_sp'))
        platform_key = get_or_create_platform_key(dw_cursor, cleaned_row_data.get('nguon_du_lieu'))
        
        shop_key = get_or_create_shop_key(dw_cursor, 
                                          cleaned_row_data.get('ma_shop_platform'), 
                                          cleaned_row_data.get('dia_chi_shop'))
        
        date_key = get_or_create_date_key(dw_cursor, cleaned_row_data.get('ngay_cao_dlieu'))
        
        product_key = get_or_create_product_key(dw_cursor,
                                                cleaned_row_data.get('ma_sp_shop_platform'),
                                                cleaned_row_data.get('ten_sp_hien_thi'),
                                                cleaned_row_data.get('ten_chinh_xac_sp'),
                                                cleaned_row_data.get('loai_sp'),
                                                cleaned_row_data.get('link_sp'))

        # After getting/creating product_key, link its functions
        if product_key:
            product_functions_list = cleaned_row_data.get('cong_dung_sp') # This is a list from transform.py
            if isinstance(product_functions_list, str): # If it somehow came as a string, make it a list
                product_functions_list = [f.strip() for f in product_functions_list.split(',') if f.strip()]
            link_product_to_functions(dw_cursor, product_key, product_functions_list)

        # 2. Prepare data for Fact Table
        # FKs can be None if the corresponding dimension lookup returned None (and fact table FKs are nullable)
        quantity_sold = cleaned_row_data.get('so_sp_da_ban')
        display_price = cleaned_row_data.get('gia_hien_thi')
        rating_score = cleaned_row_data.get('danh_gia') # transform.py's clean_rating_score might return None or a float

        # Ensure numeric values are appropriate for DB (e.g. handle None if column not nullable)
        # For now, assuming fact table columns for these metrics are nullable or cleaning handles it.
        # If metrics like quantity_sold are essential and cannot be None for a fact, add checks.

        # 3. Insert into Fact_ProductSales
        fact_sql = """
            INSERT INTO Fact_ProductSales 
            (Product_Key, Date_Key, Shop_Key, Brand_Key, Platform_Key, 
             Quantity_Sold, Display_Price, Rating_Score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        dw_cursor.execute(fact_sql, product_key, date_key, shop_key, brand_key, platform_key,
                          quantity_sold, display_price, rating_score)
        
        # No commit here, main.py will handle it after successful source update.
        print(f"Successfully prepared and executed insert for Fact_ProductSales for source ID: {cleaned_row_data.get('id')}.")
        return True

    except Exception as e:
        # The main.py loop will catch this, print, and rollback dw_conn.
        # So, just printing here for more specific context.
        print(f"Error during DWH loading (dimensions or fact) for source ID {cleaned_row_data.get('id')}: {e}")
        # It's important that this function returns False on failure so main.py rollbacks.
        return False

def update_source_on_success(source_row_id, lake_cursor):
    """
    Updates the is_transform flag to 1 for the successfully processed row
    in the source (Lake) database.
    """
    if source_row_id is None:
        print("Error: Cannot update source data, source_row_id is None.")
        return False
    try:
        query = "UPDATE total_source_data SET is_transform = 1 WHERE id = ?"
        lake_cursor.execute(query, source_row_id)
        # Commit will be handled by main.py after successful DWH load and this update
        if lake_cursor.rowcount == 0:
            print(f"Warning: No rows updated in source for id = {source_row_id}. Record might not exist or already marked.")
            # Still return True because the operation didn't fail, it just didn't change anything.
            # Or, depending on desired logic, this could be False if an update was strictly expected.
            # For now, assume it's not a critical failure if 0 rows affected, but a warning.
        print(f"Successfully marked source row id = {source_row_id} as processed (is_transform = 1).")
        return True
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error updating source table for id = {source_row_id}: {sqlstate}")
        return False