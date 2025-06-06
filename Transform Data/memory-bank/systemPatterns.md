# System Patterns: Modular ETL Pipeline (Simplified Flow with User DWH Load)

**1. Overall Architecture:**
   The system employs a modified ETL (Extract, Transform, Load-Delegate) architecture as a Python batch process. It extracts from a source SQL Server "Lake", performs specific data cleaning (e.g., for addresses using `VN_PROVINCES`, product attributes, prices, quantities; product functions are returned as a list), and then the script itself handles the loading into a target SQL Server "Data Warehouse" (DWH) by populating dimensions (including `Dim_Product_Function`), a bridge table (`Product_Function_Bridge`), and the fact table. The script then updates a status flag in the source based on the success of this comprehensive load operation.

   ```mermaid
   graph TD
       A[Source SQL Server (Lake: Test_Crawl_Data)] -- Extract (is_transform=0) --> B(Python ETL Process);
       B -- Clean Data (Specific Rules, List for Functions) --> C_LoadLogic(load.py - Script Implemented DWH Load);
       C_LoadLogic -- Populates Dimensions & Bridge --> DWH_Dim_Bridge[Dim/Bridge Tables (SQL Server DWH)];
       C_LoadLogic -- Populates Fact --> DWH_Fact[Fact Table (SQL Server DWH)];
       DWH_Dim_Bridge --> C_LoadLogic; 
       DWH_Fact --> C_LoadLogic;
       C_LoadLogic -- Return Success/Failure --> B;
       B -- Update Status (is_transform=1 on success) --> A;

       subgraph Python ETL Process
           direction LR
           P_Main[main.py] -- Manages --> P_Extract(extract.py);
           P_Main -- Manages --> P_Transform(transform.py);
           P_Main -- Calls Load Logic In --> P_Load(load.py);
           P_Main -- Uses --> P_Config(config.py);
       end
       subgraph load.py - Script Implemented DWH Load
           direction TB
           GetCreateBrand[get_or_create_brand_key]
           GetCreatePlatform[get_or_create_platform_key]
           GetCreateShop[get_or_create_shop_key]
           GetCreateDate[get_or_create_date_key]
           GetCreateProduct[get_or_create_product_key]
           GetCreateProdFunc[get_or_create_product_function_key]
           LinkProdFunc[link_product_to_functions]
           FactInsert[Insert Fact_ProductSales]
           
           %% All get_or_create_* functions now use separate INSERT and SELECT SCOPE_IDENTITY() calls.
           GetCreateBrand --> FactInsert
           GetCreatePlatform --> FactInsert
           GetCreateShop --> FactInsert
           GetCreateDate --> FactInsert
           GetCreateProduct --> LinkProdFunc
           GetCreateProdFunc --> LinkProdFunc
           LinkProdFunc --> FactInsert
       end
   ```

**2. Key Technical Decisions:**
   - **Modular Design:** ETL logic separated (`extract.py`, `transform.py`, `load.py`, `main.py`, `config.py`).
   - **Script-Implemented DWH Load:** The logic for loading data into the DWH star schema (dimensions including `Dim_Product_Function`, bridge table `Product_Function_Bridge`, and facts) is now implemented within `load.py` by the script, using various helper functions.
   - **Specific Cleaning in `transform.py`:** User has implemented specific cleaning functions. `clean_cong_dung_sp` returns a list of functions, which `load.py` iterates over for `Dim_Product_Function` and `Product_Function_Bridge`.
   - **Configuration-Driven Connections & Data:** `config.py` for database parameters and lists like `VN_PROVINCES`.
   - **`is_transform` Flag & PK `id`:** Source table uses `is_transform` (updated based on script's load success) and `id` as the primary key for updates.
   - **Row-by-Row Processing with Transactions:** `main.py` processes data row by row. Cleaning, DWH load (dimensions, bridge, fact), and source flag update form a transactional unit.
   - **DDL Management:** `load.py` includes `create_tables_if_not_exist` for DWH schema setup, including new `Dim_Product_Function` and `Product_Function_Bridge`. Key ID columns (`Shop_ID_Platform`, `Product_ID_Shop_Platform`) in DDL are now `NVARCHAR`, and `Dim_Product.Product_Link` is `NVARCHAR(450)`.
   - **SCOPE_IDENTITY Handling:** All `get_or_create_*_key` functions in `load.py` now separate `INSERT` and `SELECT SCOPE_IDENTITY()` into distinct database calls for robustness.

**3. Design Patterns in Use:**
   - **ETL (Extract, Transform, Load):** The script now handles the full load part into the DWH structure.
   - **Modular Programming.**
   - **Helper/Utility Functions:** For dimension key generation and bridge table population.
   - **Configuration File.**

**4. Component Relationships:**
   - `main.py`: Orchestrator. Calls `extract.py`, `transform.py` (for `clean_row_data`), then `load.py` (for user's `load_row_to_warehouse` and `update_source_on_success`). Manages DB connections and transactions.
   - `config.py`: Provides DB connection details and lists like `VN_PROVINCES`.
   - `extract.py`: Extracts unprocessed data (`is_transform = 0`) from Lake.
   - `transform.py`: Provides `clean_row_data()` applying user-defined specific data cleaning functions. `clean_cong_dung_sp` provides a list of functions.
   - `load.py`:
     - Provides `get_dw_db_connection()` and `create_tables_if_not_exist()` (with updated DDL for product functions and ID types).
     - Contains helper functions: `get_or_create_brand_key`, `get_or_create_platform_key`, `get_or_create_shop_key`, `get_or_create_date_key`, `get_or_create_product_key` (modified), `get_or_create_product_function_key`, `link_product_to_functions`. (All updated for separate SCOPE_IDENTITY selects).
     - **Implements `load_row_to_warehouse(cleaned_data, dw_cursor)`:** Uses helpers to populate dimensions/bridge and inserts into fact table. Returns `True`/`False`.
     - Contains `update_source_on_success(source_id, lake_cursor)`: Updates `is_transform` flag in Lake. 