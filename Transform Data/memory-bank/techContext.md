# Technical Context: Python ETL (Simplified Flow) with pyodbc for SQL Server

**1. Core Technologies:**
   - **Programming Language:** Python (version 3.x)
   - **Database Connectivity:** `pyodbc` library for SQL Server.
   - **Databases:** Microsoft SQL Server (Source/Lake and Destination/DWH).

**2. Development Setup & Environment:**
   - **Python Environment:** Python 3 with `pyodbc` installed.
   - **SQL Server ODBC Driver:** Required on the execution machine.
   - **User Responsibility:** User needs to be able to implement Python code within `load.py` for their DWH loading logic.

**3. Key Libraries and Modules Used:**
   - **`pyodbc`:** All database interactions.
   - **`datetime` (standard library):** Used in `transform.py` for date parsing (though current user functions might not use it directly, it's imported).
   - **Custom Modules:**
     - `config.py`: DB connection parameters and lists like `VN_PROVINCES`.
     - `extract.py`: Source data extraction (`is_transform = 0`).
     - `transform.py`: User-defined specific data cleaning functions (e.g., `clean_adress`, `clean_cong_dung_sp` which returns a list, `clean_price`, `clean_quantity_sold`) and `clean_row_data()` to apply them.
     - `load.py`:
         - DWH DDL (`create_tables_if_not_exist`) including `Dim_Product_Function` and `Product_Function_Bridge`, and type changes for ID columns (`NVARCHAR`) and `Dim_Product.Product_Link` (`NVARCHAR(450)`).
         - Helper functions for all dimension key generation (e.g., `get_or_create_brand_key`, `get_or_create_product_function_key`), all updated to use separate `INSERT` and `SELECT SCOPE_IDENTITY()` calls.
         - Bridge table population logic (`link_product_to_functions`).
         - Fully implemented `load_row_to_warehouse` for populating all DWH tables (dimensions, bridge, fact).
         - Source flag update (`update_source_on_success`).
     - `main.py`: Orchestrates the ETL flow, calling other modules and managing transactions.

**4. Database Interaction Details:**
   - **Connection Strings:** Dynamically built in `extract.py` and `load.py` from `config.py`.
   - **Cursors:** Standard `pyodbc` cursors.
   - **SQL Queries:** Standard SQL (T-SQL). Includes `SELECT WHERE is_transform = 0`, `UPDATE SET is_transform = 1 WHERE id = ?`, DDL (`CREATE TABLE IF NOT EXISTS` logic), and all SQL for dimension/bridge/fact inserts within `load.py` helper functions. `INSERT`s followed by separate `SELECT SCOPE_IDENTITY()` for key retrieval.
   - **User DWH SQL:** The user no longer directly implements DWH SQL; it is handled by the script in `load.py`.
   - **Transaction Management:** `main.py` controls row-level transactions. Commits for a row (to Lake and DWH connections) happen if script-implemented `load_row_to_warehouse` returns `True` AND source update is successful. Rollback otherwise.

**5. Technical Constraints & Assumptions:**
   - **SQL Server Accessibility & Permissions:** As before, script needs access and permissions for read/update on source, and DDL/read/write on DWH.
   - **Source Table Structure:** `total_source_data` must have `id` (PK) and `is_transform` (BIT/INT), and columns matching those expected by `transform.py` and `load.py`.
   - **User Code Quality (Shifted Focus):** The success now depends on the accuracy of cleaning logic in `transform.py` and data in `config.py` to feed the script's DWH loading logic. The `clean_cong_dung_sp` in `transform.py` must return a list of strings for product functions.
   - **Data Volume:** Row-by-row processing remains; may not be optimal for huge volumes.
   - **No External Dependencies beyond `pyodbc`:** The project aims for simplicity by not introducing other external libraries for tasks like advanced logging or data manipulation (like Pandas, though it was present in an earlier iteration and then removed). 