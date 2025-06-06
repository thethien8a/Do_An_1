# Project Brief: SQL Server ETL for Product Sales Data (Simplified Flow)

**1. Project Goal:**
   To develop an ETL (Extract, Transform, Load) process that moves product sales data from a source SQL Server database (`Test_Crawl_Data`, table `total_source_data`) to a destination Data Warehouse (`Data_Warehouse`) also on SQL Server. The process will extract unprocessed data, perform generic data cleaning, and then delegate the actual loading into the DWH (star schema) to user-implemented Python logic. The ETL script will handle updating a source flag (`is_transform`) based on the success of the user's loading step.

**2. Core Requirements:**
   - **Extraction:** Read unprocessed data from `total_source_data` where `is_transform = 0`. The primary key of the source table is `id`.
   - **Transformation (`transform.py`):**
     - Perform specific data cleaning on a row-by-row basis using user-defined functions for columns such as `cong_dung_sp` (which returns a list of functions), `dia_chi_shop` (utilizing `VN_PROVINCES` from `config.py`), `gia_hien_thi`, `so_sp_da_ban`, `danh_gia`, `ten_chinh_xac_sp`, `loai_sp`, and `thuong_hieu_sp`.
     - Return a cleaned data dictionary.
   - **Loading (`load.py` - User Implemented & Script Implemented for Dimensions/Bridge):
     - Script implements helper functions to get/create keys for `Dim_Brand`, `Dim_Platform`, `Dim_Shop`, `Dim_Date`, `Dim_Product`, and the new `Dim_Product_Function`.
     - Script implements logic to populate the new `Product_Function_Bridge` table, linking products to their multiple functions.
     - The DWH loading logic within `load_row_to_warehouse` now uses these helpers to populate all dimensions and the bridge table, then inserts into the `Fact_ProductSales` table.
     - This effectively means the script handles the structural loading into the DWH based on cleaned data, fulfilling the user's previous request for these helper functions.
   - **Source Update (`load.py` - Script Implemented):
     - Based on the boolean return from the user's `load_row_to_warehouse` function, an `update_source_on_success(source_row_id, lake_cursor)` function will update the `is_transform` flag to `1` in the source table for successfully processed rows.
   - **Database:** Both source and destination are SQL Server.
   - **Idempotency (Conceptual):** Achieved by processing only `is_transform = 0` records and updating this flag.
   - **Error Handling:** Basic error logging (print statements). Row-level transaction management: commit on full row success (clean, user-load, source-update), rollback on failure at any step for that row.
   - **Modularity:** Code organized into `config.py`, `extract.py`, `transform.py`, `load.py`, `main.py`.
   - **DDL Management:** `load.py` includes `create_tables_if_not_exist` for DWH schema setup, including `Dim_Product_Function` and `Product_Function_Bridge`. `Shop_ID_Platform` and `Product_ID_Shop_Platform` types updated to `NVARCHAR` in DDL.

**3. Scope:**
   - **In Scope:** Development of Python scripts for extraction, specific cleaning, orchestration (including population of dimension and bridge tables from cleaned data), source flag update, DDL for DWH schema.
   - **Out of Scope:** Advanced logging, complex error recovery beyond row-level rollback, GUI, API development. The user no longer needs to implement the core DWH dimension/bridge loading logic as this is now handled by the script using the helper functions.

**4. Key Stakeholders:**
   - User (Developer responsible for implementing `load_row_to_warehouse`).

**5. Success Criteria:**
   - Unprocessed data from the source table is correctly extracted and cleaned.
   - The script correctly calls the user-provided `load_row_to_warehouse` function.
   - The `is_transform` flag in the source table is correctly updated based on the success of the user's DWH loading function.
   - The ETL process handles basic errors gracefully and maintains data integrity through transactions.
   - The code is modular, and the user's responsibility for DWH loading is clearly defined. 