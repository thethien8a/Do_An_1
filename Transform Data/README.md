# SQL Server ETL Project (Simplified Flow)

This project implements an ETL (Extract, Transform, Load) process with a simplified workflow. It extracts data from a source SQL Server database (Lake), cleans it, and then relies on user-implemented logic to load it into a destination SQL Server Data Warehouse (DWH). The script automates the source flag update (`is_transform`) based on the success of the user's loading step.

## Project Structure

```
Transform Data/
├── config.py           # Database connection configurations
├── extract.py          # Functions for extracting unprocessed data from the source
├── transform.py        # Functions for cleaning data
├── load.py             # Contains DDL, user's DWH loading logic (placeholder), and source flag update
├── main.py             # Main script to orchestrate the ETL process
└── memory-bank/        # Documentation and context for the AI assistant
    ├── projectbrief.md
    ├── productContext.md
    ├── activeContext.md
    ├── systemPatterns.md
    ├── techContext.md
    └── progress.md
```

## How it Works

1.  **Configuration (`config.py`):**
    *   Contains connection details for both the source SQL Server (referred to as `LAKE_SQL_SERVER_CONFIG`) and the target Data Warehouse SQL Server (`DW_SQL_SERVER_CONFIG`).

2.  **Extraction (`extract.py`):**
    *   Connects to the source SQL Server.
    *   Fetches rows from `total_source_data` where `is_transform = 0` (unprocessed data). The primary key of this table is assumed to be `id`.
    *   Returns data as a list of dictionaries.

3.  **Transformation (`transform.py`):**
    *   `clean_row_data(raw_row_dict)`: Takes a raw data row (dictionary).
    *   Applies generic cleaning functions (text stripping, date parsing, numeric conversion) to known columns (`ngay_cao_dlieu`, `gia_hien_thi`, `so_sp_da_ban`, `danh_gia`, and various text fields).
    *   Returns a cleaned data dictionary.

4.  **Loading & Source Update (`load.py`):**
    *   `create_tables_if_not_exist(dw_cursor)`: (Kept from previous version) Contains DDL statements to create the necessary dimension and fact tables in the DWH if they don't exist.
    *   `load_row_to_warehouse(cleaned_row_data, dw_cursor)`: **This is a placeholder function that YOU (the user) need to implement.** It should take the cleaned data and load it into your DWH star schema. It must return `True` for a successful load of that row, and `False` for a failure.
    *   `update_source_on_success(source_row_id, lake_cursor)`: If `load_row_to_warehouse` returns `True`, this function is called by `main.py` to update `is_transform = 1` in the source `total_source_data` table for the processed row, using its `id`.

5.  **Orchestration (`main.py`):**
    *   Manages connections to both source and DWH databases.
    *   Calls `create_tables_if_not_exist()` from `load.py` to set up the DWH schema.
    *   Fetches unprocessed data using `extract_data()` from `extract.py`.
    *   Iterates through each source row:
        *   Calls `clean_row_data()` from `transform.py`.
        *   Calls `load_row_to_warehouse()` (your implemented function) from `load.py`.
        *   If `load_row_to_warehouse()` returns `True`:
            *   Calls `update_source_on_success()` from `load.py`.
            *   Commits changes to both Lake and DWH databases for that row.
        *   If `load_row_to_warehouse()` returns `False` (or an error occurs):
            *   Rolls back changes for that row in both databases.
            *   Logs an error.
    *   Prints a summary of processed and error rows.

## Setup

1.  **Database Setup:**
    *   Ensure you have two SQL Server instances accessible.
    *   **Source (Lake):** A database (e.g., `Test_Crawl_Data`) with `total_source_data` table. This table must have an `id` (primary key) column and an `is_transform` (BIT/INT) column, plus data columns.
    *   **Data Warehouse:** A database (e.g., `Data_Warehouse`) where dimension/fact tables will be created by `create_tables_if_not_exist` if they don't exist.
2.  **Implement DWH Loading:**
    *   **Crucial:** You MUST implement the logic inside the `load_row_to_warehouse` function in `load.py` to correctly insert cleaned data into your DWH's star schema tables.
3.  **Configuration:**
    *   Update `config.py` with correct SQL Server connection details.
4.  **Dependencies:**
    *   Requires `pyodbc`: `pip install pyodbc`

## Running the ETL

Execute the main script:
```bash
python main.py
```
The script will process data row by row, calling your DWH loading logic for each. Ensure your `load_row_to_warehouse` function is robust. 