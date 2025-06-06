# Active Context: Simplified ETL Refactoring and Documentation

**Last Major Activity:**
Refactored the entire ETL Python pipeline to a new, simplified flow based on user request. The core change is that the user now implements the Data Warehouse (DWH) loading logic themselves within a specific placeholder function, while the script handles extraction, generic cleaning, and source flag updates based on the success of the user's DWH load.

**Recent Changes (within this session):**
1.  **`transform.py` overhauled:**
    *   Removed all DWH dimension lookup/creation logic.
    *   User implemented specific cleaning functions: `clean_cong_dung_sp` (returns a list), `just_capitalize`, `clean_adress` (using `VN_PROVINCES` from `config.py`), `clean_price`, `clean_quantity_sold`, `clean_rating_score`, `clean_exact_name`, `clean_product_type`, `clean_brand`.
    *   Implemented `clean_row_data(raw_row_dict)` to apply these specific cleanings.
2.  **`load.py` significantly enhanced:**
    *   Kept `get_dw_db_connection()`.
    *   Updated `create_tables_if_not_exist()` DDL:
        *   Added `Dim_Product_Function` and `Product_Function_Bridge` tables.
        *   Removed `Product_Function` from `Dim_Product`.
        *   Changed `Shop_ID_Platform` and `Product_ID_Shop_Platform` to `NVARCHAR(255)`; `Dim_Product.Product_Link` to `NVARCHAR(450)`.
    *   Added helper functions: `get_or_create_brand_key`, `get_or_create_platform_key`, `get_or_create_shop_key`, `get_or_create_date_key`, `get_or_create_product_key` (modified), and new `get_or_create_product_function_key`, `link_product_to_functions`.
        *   All `get_or_create_*_key` functions were modified to separate `INSERT` and `SELECT SCOPE_IDENTITY()` into two distinct `execute()` calls to prevent "No results" errors.
    *   `load_row_to_warehouse` function is now fully implemented by the script to populate all dimensions (including `Dim_Product_Function`), the `Product_Function_Bridge`, and then `Fact_ProductSales` using the helper functions. It no longer acts as a placeholder for user DWH loading logic.
    *   Kept `update_source_on_success(source_row_id, lake_cursor)`.
3.  **`extract.py` confirmed:**
    *   Ensured `extract_data(lake_cursor)` fetches from `total_source_data` where `is_transform = 0`.
4.  **`main.py` rewritten:**
    *   Orchestrates the new flow: extract, clean, call user's DWH load placeholder, call source update based on user load success, manage row-level transactions for Lake and DWH connections.
5.  **Documentation Updated:**
    *   `README.md` reflects the new simplified flow and user's responsibility for DWH loading.
    *   `memory-bank/projectbrief.md` updated.
    *   `memory-bank/productContext.md` updated.
4.  **`transform.py` fixed:**
    *   Resolved `UnboundLocalError` in `clean_price` function.

**Current Focus:**
Ensuring robust DWH loading, particularly the dimension key generation.

**Next Steps (Immediate):**
1.  User to re-test the ETL process.
2.  Update Memory Bank files (this step).
3.  Update `memory-bank/systemPatterns.md`.
4.  Update `memory-bank/techContext.md`.
5.  Update `memory-bank/progress.md`.
6.  Present the complete refactored solution and updated documentation to the user.
7.  Await user feedback, particularly on the placeholder function they need to implement and the generic cleaning provided.

**Active Decisions & Considerations:**
- **User Responsibility for DWH Load:** The critical DWH loading logic (interacting with dimensions, facts, star schema) is now entirely the user's responsibility within the `load_row_to_warehouse` function in `load.py`.
- **Script Handles DWH Load:** The `load_row_to_warehouse` function in `load.py` is now implemented by the script to handle dimension, bridge, and fact table population. User responsibility shifts to ensuring `transform.py` and `config.py` provide correct data for this process.
- **Specific Cleaning & List Output:** User-defined cleaning in `transform.py` (e.g., `clean_cong_dung_sp` outputting a list) is crucial for the new DWH loading logic.
- **Transaction Management:** `main.py` handles commits/rollbacks for each row based on the success of the script-implemented `load_row_to_warehouse` function and the subsequent source flag update.
- **Source PK:** Confirmed as `id`. 