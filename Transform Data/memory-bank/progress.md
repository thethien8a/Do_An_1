# Progress: ETL Refactored to Simplified Flow, User DWH Load Pending

**1. What Works (Script-Side):**
   - **Modular Code Structure:** Refactored to `config.py`, `extract.py`, `transform.py`, `load.py`, `main.py` for the new simplified flow.
   - **Configuration (`config.py`):** Centralized DB connection details.
   - **Extraction Logic (`extract.py`):**
     - Connects to Lake SQL Server.
     - Fetches rows from `total_source_data` where `is_transform = 0` (using `id` as PK).
     - Returns data as list of dictionaries.
   - **Transformation Logic (`transform.py`):
     - `clean_row_data()` applies user-defined specific cleaning functions for columns like `cong_dung_sp` (returns a list of strings), `dia_chi_shop` (using `VN_PROVINCES` from `config.py`), `gia_hien_thi`, `so_sp_da_ban`, `danh_gia`, etc.
     - No DWH dimension lookups are done by this script module anymore.
   - **Loading Logic - Script Part (`load.py`):
     - `create_tables_if_not_exist()`: DDL for DWH schema setup updated to include `Dim_Product_Function`, `Product_Function_Bridge`, remove `Product_Function` from `Dim_Product`, set `Shop_ID_Platform` / `Product_ID_Shop_Platform` to `NVARCHAR`, and `Dim_Product.Product_Link` to `NVARCHAR(450)`.
     - Helper functions for all dimensions are implemented: `get_or_create_brand_key`, `get_or_create_platform_key`, `get_or_create_shop_key`, `get_or_create_date_key`, `get_or_create_product_key` (modified), and new `get_or_create_product_function_key`. All these functions now use separate `INSERT` and `SELECT SCOPE_IDENTITY()` calls for robustness.
     - `link_product_to_functions()`: New function to populate `Product_Function_Bridge`.
     - `load_row_to_warehouse()`: Now fully implemented by the script. It uses all helper functions to populate `Dim_Brand`, `Dim_Platform`, `Dim_Shop`, `Dim_Date`, `Dim_Product`, `Dim_Product_Function`, and `Product_Function_Bridge`, then inserts into `Fact_ProductSales`.
     - `update_source_on_success()`: Updates `is_transform = 1` in source table if `load_row_to_warehouse` is successful.
   - **Orchestration (`main.py`):
     - Manages Lake and DWH connections.
     - Executes DDL setup.
     - For each unprocessed row from source:
       - Calls `clean_row_data()`.
       - Calls the script-implemented `load_row_to_warehouse()`.
       - If successful, calls `update_source_on_success()`.
       - Manages row-level commits/rollbacks for Lake and DWH connections based on success.
   - **Documentation:**
     - `README.md` and Memory Bank files (`projectbrief.md`, `productContext.md`, `activeContext.md`, `systemPatterns.md`, `techContext.md`) updated to reflect the new simplified flow and user responsibilities.

**2. What's Left for the User to Implement:**
   - **(Primarily Verification & Configuration)**
   - **Verify DDL and Data Types:** User should double-check the DDL in `load.py` (especially `NVARCHAR` types for `Shop_ID_Platform`, `Product_ID_Shop_Platform`, and `Product_Link` as `NVARCHAR(450)`) against their actual source data characteristics and DWH requirements.
   - **Verify Cleaning Logic:** User should ensure their cleaning functions in `transform.py` (especially `clean_cong_dung_sp` returning a list of strings, `clean_price` fix for `UnboundLocalError`, and others like `clean_adress`) are accurate and robust for the data being processed, as this output directly feeds the DWH loading logic.
   - **Configuration Review:** Ensure `config.py` (SQL Server details, `VN_PROVINCES`) is accurate.
   - **Verify SCOPE_IDENTITY Logic:** User should confirm the updated `get_or_create_*_key` functions (with separate INSERT/SELECT) work correctly in their SQL Server environment.

**3. What's Left to Build/Verify (After User Implementation):**
   - **End-to-End Testing:** The complete pipeline (`main.py`) needs thorough testing with actual SQL Server databases.
     - Verify correct data extraction and application of specific cleaning rules (including list output for functions).
     - Verify the script's DWH loading logic correctly populates all dimensions, the bridge table, and the fact table, especially focusing on key generation with the new `SCOPE_IDENTITY` approach.
     - Verify correct update of `is_transform` flag.
   - **Schema and Column Name Alignment:** Ensure all assumed column names and data types in the script match the actual source and target DWH schemas.

**4. Current Status:**
   - **Development Phase:** Script-side refactoring to the simplified flow is complete. Core framework is in place.
   - **Awaiting:** User implementation of `load_row_to_warehouse` in `load.py`.

**5. Known Issues/Risks:**
   - **Dependency on User Code (Shifted):** Success now critically depends on the user's cleaning logic in `transform.py` (especially `clean_cong_dung_sp` providing a list) and `config.py` data being correct for the script's loading process.
   - **Specific Cleaning Limitations:** The user-provided specific cleaning functions should be reviewed by the user for completeness and correctness against their data and DWH schema requirements (e.g., string lengths for `Dim_Product_Function.Function_Name`).
   - **Configuration Sensitivity:** Relies on correct `config.py` (including `VN_PROVINCES` if `clean_adress` is used) and matching column names between `transform.py` output and `load.py` expectations.
   - **Database Behavior:** Correct functioning of `SCOPE_IDENTITY()` as separate calls is assumed.
   - **Error Handling in `get_or_create`:** The separated INSERT/SELECT logic might need more nuanced error handling if the SELECT SCOPE_IDENTITY somehow fails after a successful INSERT (though less likely).
   - **Performance:** Row-by-row processing may be slow for very large datasets.
   - **Untested Code:** The newly refactored and assembled pipeline has not yet been run end-to-end. Bugs are likely.
   - **Data Type Mismatches:** Potential for data type issues between source data, Python processing, and SQL Server DWH table definitions that might only appear during runtime with actual data.
   - **Error Handling Granularity:** While row-level rollback is implemented, error reporting is basic (console prints). More sophisticated error logging or alerting is not in scope.
   - **Concurrency:** The `get_or_create_key` functions in `transform.py` have basic handling for race conditions (re-querying after a failed insert), but this might not be foolproof under high concurrency if multiple ETL processes were run simultaneously against the same DWH (which is not the current design).

**6. Recent Fixes:**
  - Corrected `Dim_Product.Product_Link` DDL to `NVARCHAR(450) UNIQUE` to avoid index errors (`load.py`).
  - Fixed `UnboundLocalError` in `clean_price` function in `transform.py`.
  - Modified all `get_or_create_*_key` functions in `load.py` to use separate `INSERT` and `SELECT SCOPE_IDENTITY()` calls to resolve "No results. Previous SQL was not a query." errors. 