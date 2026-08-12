import os
import csv
import io
import time
import logging
from azure.storage.blob import BlobServiceClient
import pyodbc

# Environment Variables
STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
INPUT_CONTAINER = os.getenv("INPUT_CONTAINER", "input")
PROCESSED_CONTAINER = os.getenv("PROCESSED_CONTAINER", "processed")
FAILED_CONTAINER = os.getenv("FAILED_CONTAINER", "failed")
SQL_SERVER = os.environ["SQL_SERVER"]
SQL_DATABASE = os.environ["SQL_DATABASE"]
SQL_USERNAME = os.environ["SQL_USERNAME"]
SQL_PASSWORD = os.environ["SQL_PASSWORD"]
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Blob Storage Client
blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)

def get_sql_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def move_blob(blob_name, target_container):
    source_blob = blob_service.get_blob_client(INPUT_CONTAINER, blob_name)
    target_blob = blob_service.get_blob_client(target_container, blob_name)
    target_blob.start_copy_from_url(source_blob.url)
    source_blob.delete_blob()

def process_csv_blob(blob_name):
    logging.info("Processing blob: %s", blob_name)
    blob_client = blob_service.get_blob_client(INPUT_CONTAINER, blob_name)

    content = (
        blob_client.download_blob()
        .readall()
        .decode("utf-8-sig")
    )

    reader = csv.DictReader(io.StringIO(content))

    with get_sql_connection() as conn:
        cursor = conn.cursor()
        for index, row in enumerate(reader, start=1):
            cursor.execute(
                """
                INSERT INTO dbo.uploaded_files_data
                (file_name, row_number, customer_name, amount)
                VALUES (?, ?, ?, ?)
                """,
                blob_name,
                index,
                row.get("customer_name"),
                float(row.get("amount", 0) or 0)
            )
        conn.commit()

    move_blob(blob_name, PROCESSED_CONTAINER)
    logging.info("Completed blob: %s", blob_name)

def main_loop():
    container_client = blob_service.get_container_client(INPUT_CONTAINER)

    while True:
        blobs = list(container_client.list_blobs())

        if not blobs:
            logging.info("No files found. Sleeping.")
            time.sleep(POLL_SECONDS)
            continue

        for blob in blobs:
            try:
                process_csv_blob(blob.name)
            except Exception:
                logging.exception("Failed to process blob: %s", blob.name)
                try:
                    move_blob(blob.name, FAILED_CONTAINER)
                except Exception:
                    logging.exception("Could not move failed blob: %s", blob.name)

if __name__ == "__main__":
    main_loop()
 