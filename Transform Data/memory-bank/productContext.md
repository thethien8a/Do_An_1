# Product Context: SQL Server ETL (Simplified Flow) for Sales Analysis

**1. Why This Project Exists:**
   This project exists to transform raw, operational product sales data into a cleaned format. It then empowers the user to load this cleaned data into a structured Data Warehouse (DWH) suitable for business intelligence and reporting, using their own custom logic for the DWH insertion (star schema interaction).

**2. Problem It Solves:**
   - **Data Siloing/Unstructured Data:** Raw sales data in the source system (`total_source_data`) is likely in a format optimized for transactions, not analytics.
   - **Complex DWH Loading Logic:** Loading data into a star schema (dimensions and facts) can be intricate and application-specific. This project allows the user to own this critical piece.
   - **Need for Pre-Processing:** Provides a standardized way to extract and perform initial cleaning on the data before the user applies their DWH loading logic.
   - **Automated Source Flagging:** Automates the tedious task of marking source records as processed (`is_transform = 1`) once the user confirms successful DWH loading for a row.

**3. How It Should Work (User Experience):**
   - The user (a developer/data engineer) runs `main.py`.
   - Configuration (`config.py`) is centralized, including `VN_PROVINCES` for address cleaning.
   - The script extracts unprocessed data, cleans it using specific rules in `transform.py` (e.g., for addresses, product uses which become a list, pricing, quantity sold).
   - For each cleaned row, the script calls `load_row_to_warehouse(cleaned_row, dw_cursor)` in `load.py`.
     - This function now internally handles getting or creating keys for all dimensions (`Dim_Brand`, `Dim_Platform`, `Dim_Shop`, `Dim_Date`, `Dim_Product`, `Dim_Product_Function`).
     - It also populates the `Product_Function_Bridge` table to link products to their multiple functions.
     - Finally, it inserts the relevant foreign keys and measures into `Fact_ProductSales`.
     - It returns `True` if the entire row (all dimensions, bridge, and fact) was successfully processed and inserted into the DWH, `False` otherwise.
   - Based on the return value from `load_row_to_warehouse`, `main.py` orchestrates updating `is_transform = 1` in the source table and commits/rollbacks transactions for that row across both databases.
   - Console output shows progress, DWH table creation status (including new tables), extraction counts, cleaning status, calls to load function, and success/failure of source update.
   - The DWH schema (dimension, fact, and bridge tables) can be automatically created by `create_tables_if_not_exist` if not present.

**4. User Experience Goals:**
   - **Simplicity (for script usage):** Easy to set up, configure, and run. The script now handles DWH structural loading.
   - **Control (for DWH loading - now reduced focus):** User's primary focus shifts from implementing `load_row_to_warehouse` to ensuring data in `config.py` and `transform.py` is accurate for the DWH loading logic provided by the script.
   - **Transparency:** Clear feedback on script operations, including dimension/bridge table population.
   - **Reliability:** Consistent extraction, cleaning, and source flagging. Robust transaction management for operations controlled by the script.
   - **Maintainability:** Well-organized script code. User focuses on DWH loading logic in a designated function. 