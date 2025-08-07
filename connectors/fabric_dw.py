"""
Microsoft Fabric Data Warehouse connector with enhanced metadata capabilities
"""
import os
import pyodbc
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# TLS adapter for better SSL/TLS handling
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# Fabric SQL config
FABRIC_SQL_SERVER = os.getenv("FABRIC_SQL_SERVER")
FABRIC_SQL_DATABASE = os.getenv("FABRIC_SQL_DATABASE")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

def get_access_token():
    """Get Azure AD access token for Fabric authentication"""
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "resource": "https://database.windows.net/"
    }
    session = requests.Session()
    resp = session.post(url, headers=headers, data=data, verify=certifi.where())
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_fabric_conn():
    """Establish connection to Fabric Data Warehouse"""
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={FABRIC_SQL_SERVER};"
        f"DATABASE={FABRIC_SQL_DATABASE};"
        "Authentication=ActiveDirectoryServicePrincipal;"
        f"UID={AZURE_CLIENT_ID};"
        f"PWD={AZURE_CLIENT_SECRET};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    conn = pyodbc.connect(conn_str)
    return conn

def get_all_schema():
    """Get complete database schema information"""
    query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA in ('dbo','silver','gold')
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    with get_fabric_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
    
    schema = {}
    for row in rows:
        table = row.TABLE_NAME
        column_info = {
            'name': row.COLUMN_NAME,
            'type': row.DATA_TYPE,
            'nullable': row.IS_NULLABLE == 'YES',
            'default': row.COLUMN_DEFAULT
        }
        schema.setdefault(table, []).append(column_info)
    
    return schema

def get_table_metadata(table_name):
    """Get detailed metadata for a specific table"""
    # Column information
    column_query = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = ?
    ORDER BY ORDINAL_POSITION
    """
    
    # Row count
    count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
    
    # Sample data
    sample_query = f"SELECT TOP 3 * FROM {table_name}"
    
    with get_fabric_conn() as conn:
        cursor = conn.cursor()
        
        # Get column info
        cursor.execute(column_query, table_name)
        columns = cursor.fetchall()
        
        column_info = []
        for col in columns:
            column_info.append({
                'name': col.COLUMN_NAME,
                'type': col.DATA_TYPE,
                'nullable': col.IS_NULLABLE == 'YES',
                'default': col.COLUMN_DEFAULT,
                'max_length': col.CHARACTER_MAXIMUM_LENGTH
            })
        
        # Get row count
        cursor.execute(count_query)
        row_count = cursor.fetchone().row_count
        
        # Get sample data
        cursor.execute(sample_query)
        sample_rows = cursor.fetchall()
        sample_columns = [column[0] for column in cursor.description]
        samples = [dict(zip(sample_columns, row)) for row in sample_rows]
        
    return {
        'table_name': table_name,
        'columns': column_info,
        'row_count': row_count,
        'sample_data': samples
    }

def execute_sql(sql: str):
    """Execute SQL query and return results"""
    with get_fabric_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Handle both SELECT and non-SELECT queries
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            return {"rows_affected": cursor.rowcount}