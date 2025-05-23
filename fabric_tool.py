#fabric_tool.py
import os
import pyodbc
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from dotenv import load_dotenv
from openai import AzureOpenAI
import certifi
import re

# TLS adapter for better SSL/TLS handling
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# Load environment variables
load_dotenv()

# Azure OpenAI config
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Fabric SQL config
FABRIC_SQL_SERVER = os.getenv("FABRIC_SQL_SERVER")
FABRIC_SQL_DATABASE = os.getenv("FABRIC_SQL_DATABASE")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

def get_access_token():
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "resource": "https://database.windows.net/"
    }
    session = requests.Session()
    # session.mount("https://", TLSAdapter())   # (You can comment this out for now)
    resp = session.post(url, headers=headers, data=data, verify=certifi.where())
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_fabric_conn():
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

def get_schema_description():
    query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
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
        column = f"{row.COLUMN_NAME} {row.DATA_TYPE}"
        schema.setdefault(table, []).append(column)
    description = "\n".join([f"Table: {table} ({', '.join(cols)})" for table, cols in schema.items()])
    return description

def generate_sql(question: str, schema: str) -> str:
    prompt = f"""
You are an expert SQL assistant. Given the schema:
{schema}

User question: "{question}"

Write a correct, safe T-SQL query that answers the question.
Return ONLY the SQL query, nothing else.
"""
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    sql = response.choices[0].message.content.strip()
    # Remove all ```...``` code blocks if present
    sql = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).replace('```sql', '').replace('```', '').strip(), sql)

    return sql

def execute_sql(sql: str) -> list:
    with get_fabric_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
