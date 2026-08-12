import os 
import pyodbc 
from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel 
 
app = FastAPI(title="Customer API") 
 
 
class Customer(BaseModel): 
    id: int 
    name: str 
    salary: float 
    address: str 
 
 
def get_sql_connection(): 
    server = os.environ["SQL_SERVER"] 
    database = os.environ["SQL_DATABASE"] 
    username = os.environ["SQL_USER"] 
    password = os.environ["SQL_PASSWORD"] 
    driver = os.environ.get( 
        "SQL_DRIVER", 
        "ODBC Driver 18 for SQL Server" 
    ) 
 
    conn_str = ( 
        f"DRIVER={{{driver}}};" 
        f"SERVER={server};" 
        f"DATABASE={database};" 
f"UID={username};" 
        f"PWD={password};" 
        "Encrypt=yes;" 
        "TrustServerCertificate=no;" 
        "Connection Timeout=30;" 
    ) 
 
    return pyodbc.connect(conn_str) 
 
 
@app.get("/health") 
def health(): 
    return {"status": "ok"} 
 
 
@app.post("/customers") 
def create_customer(customer: Customer): 
    try: 
        conn = get_sql_connection() 
        cursor = conn.cursor() 
 
        cursor.execute( 
            """ 
            INSERT INTO Customers 
            (CustomerId, Name, Salary, Address) 
            VALUES (?, ?, ?, ?) 
            """, 
            customer.id, 
            customer.name, 
            customer.salary, 
            customer.address, 
        ) 
 
        conn.commit() 
 
        cursor.close() 
        conn.close() 
 
        return { 
            "message": "Customer loaded into Cloud SQL",
            "customer_id": customer.id 
        }
    
    except Exception as ex: 
        raise HTTPException ( 
            status_code=500, 
            detail=str(ex) 
        ) 
    