import pyodbc
from extract import get_lake_db_connection, extract_data
from transform import clean_row_data # Changed from transform_single_row
from load import get_dw_db_connection, create_tables_if_not_exist, load_row_to_warehouse, update_source_on_success # Updated load imports

def main_etl_process():
    lake_conn = None
    dw_conn = None
    processed_count = 0
    error_count = 0

    try:
        # 1. Connect to Lake (Source) Database
        lake_conn = get_lake_db_connection()
        if not lake_conn:
            print("ETL Process: Failed to connect to Lake database. Aborting.")
            return
        lake_cursor = lake_conn.cursor()
        print("ETL Process: Connected to Lake database.")

        # 2. Connect to Data Warehouse
        dw_conn = get_dw_db_connection()
        if not dw_conn:
            print("ETL Process: Failed to connect to Data Warehouse. Aborting.")
            if lake_conn: lake_conn.close() # Close lake if open
            return
        dw_cursor = dw_conn.cursor()
        print("ETL Process: Connected to Data Warehouse.")
        
        # 3. Create DWH tables if they don't exist
        create_tables_if_not_exist(dw_cursor)
        dw_conn.commit() # Commit DDL changes
        print("ETL Process: DWH table check/creation complete.")

        # 4. Extract data from Lake (where is_transform = 0)
        source_data_rows = extract_data(lake_cursor) # List of dicts
        if not source_data_rows:
            print("ETL Process: No unprocessed data found in Lake.")
            return
        print(f"ETL Process: Extracted {len(source_data_rows)} unprocessed rows from Lake.")

        # 5. Clean, Load (user logic), and Update source status
        for raw_row_dict in source_data_rows:
            source_pk_value = raw_row_dict.get('id') # Primary key from source
            if source_pk_value is None:
                print(f"ETL Process: Skipping row due to missing PK 'id': {raw_row_dict}")
                error_count += 1
                continue
            
            print(f"ETL Process: Processing source row with id: {source_pk_value}")
            
            try:
                # 5a. Clean data
                cleaned_data = clean_row_data(raw_row_dict)
                if not cleaned_data:
                    print(f"ETL Process: Cleaning failed for source id: {source_pk_value}. Skipping.")
                    error_count += 1
                    continue
                print(f"ETL Process: Data cleaned for source id: {source_pk_value}")

                # 5b. Load to Data Warehouse (User Implemented Function)
                # This function (load_row_to_warehouse) is a placeholder in load.py
                # The user needs to implement the actual DWH loading logic there.
                # It should return True for success, False for failure.
                dwh_load_successful = load_row_to_warehouse(cleaned_data, dw_cursor)

                if dwh_load_successful:
                    # 5c. Update source table (mark as processed)
                    source_update_successful = update_source_on_success(source_pk_value, lake_cursor)
                    
                    if source_update_successful:
                        # Commit changes for this row in both databases
                        dw_conn.commit()   # Commit DWH changes (if any made by user logic)
                        lake_conn.commit() # Commit source update (is_transform = 1)
                        processed_count += 1
                        print(f"ETL Process: Successfully processed and marked source id: {source_pk_value}")
                    else:
                        print(f"ETL Process: Failed to mark source id {source_pk_value} as processed. Rolling back DWH changes for this row.")
                        dw_conn.rollback()   # Rollback DWH changes
                        lake_conn.rollback() # Rollback source update attempt
                        error_count += 1
                else:
                    print(f"ETL Process: DWH load (user logic) failed for source id: {source_pk_value}. Rolling back any Lake DB changes for this row (if any). DWH rollback should be handled in user function or here if appropriate.")
                    # dw_conn.rollback() # User's load_row_to_warehouse should ideally handle its own rollback on failure or main can do it.
                    lake_conn.rollback() # Ensure lake doesn't get committed if DWH load fails
                    error_count += 1

            except Exception as e_row:
                print(f"ETL Process: Error processing source id {source_pk_value}: {e_row}. Rolling back any partial changes for this row.")
                if dw_conn: dw_conn.rollback()
                if lake_conn: lake_conn.rollback()
                error_count += 1
                continue # Move to the next row

        print(f"\nETL Process Summary:")
        print(f"Successfully processed rows: {processed_count}")
        print(f"Rows with errors: {error_count}")

    except pyodbc.Error as db_err:
        print(f"ETL Process: Database error occurred: {db_err}")
        if dw_conn: dw_conn.rollback()
        if lake_conn: lake_conn.rollback()
    except Exception as e:
        print(f"ETL Process: A general error occurred: {e}")
        if dw_conn: dw_conn.rollback()
        if lake_conn: lake_conn.rollback()
    finally:
        if dw_cursor: dw_cursor.close()
        if dw_conn: dw_conn.close()
        if lake_cursor: lake_cursor.close()
        if lake_conn: lake_conn.close()
        print("ETL Process: Database connections closed.")

if __name__ == '__main__':
    print("Starting ETL process (New Simplified Flow)...")
    main_etl_process()
    print("ETL process (New Simplified Flow) finished.")