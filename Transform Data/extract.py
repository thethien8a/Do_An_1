import pyodbc
from config import LAKE_SQL_SERVER_CONFIG

def get_lake_db_connection():
    """Establishes a connection to the Lake SQL Server database."""
    conn_str = (
        f"DRIVER={LAKE_SQL_SERVER_CONFIG['driver']};"
        f"SERVER={LAKE_SQL_SERVER_CONFIG['server']};"
        f"DATABASE={LAKE_SQL_SERVER_CONFIG['database']};"
        f"UID={LAKE_SQL_SERVER_CONFIG['username']};"
        f"PWD={LAKE_SQL_SERVER_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error connecting to Lake database: {sqlstate}")
        print(f"Attempted connection string for Lake: {conn_str}")
        return None

def extract_data(lake_cursor):
    """Fetches rows from total_source_data where is_transform = 0.
    Returns data as a list of dictionaries.
    """
    try:
        # Ensure is_transform = 0 is in the where clause
        query = 'SELECT * FROM total_source_data WHERE is_transform = 0'
        lake_cursor.execute(query)
        columns = [column[0] for column in lake_cursor.description]
        rows = lake_cursor.fetchall()
        # Convert rows to list of dicts
        data = [dict(zip(columns, row)) for row in rows]
        return data
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error querying source database in extract_data: {sqlstate}")
        return [] # Return empty list on error

