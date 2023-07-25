import pymysql
import time
import os
from dotenv import load_dotenv, find_dotenv
import platform
from pathlib import Path
import sys

ssl_mode="VERIFY_IDENTITY"

os_name = platform.system()
if os_name == "Darwin":  # macOS
    ssl={"ca": "/etc/ssl/cert.pem"}
elif os_name == "Linux":
    ssl={"ca": "/etc/pki/tls/certs/ca-bundle.crt"}
else:
    print(f"Doesn't support {os_name}")
    sys.exit(1)  # Exit the application with an error code

def get_db_config():
    _ = load_dotenv(find_dotenv())
    return os.getenv("TIDB_HOST"), os.getenv("TIDB_PORT"), os.getenv("TIDB_USER"), os.getenv("TIDB_PASSWORD"), os.getenv("TIDB_DATABASE")

class Store: 
    def __init__(self):
        retry_count = 5  # Number of retries
        retry_delay = 2  # Delay between retries (in seconds)
        host, port, user, password, database = get_db_config()

        for _ in range(retry_count):
            try:
                self.connection = pymysql.connect(host=host, port=int(port), user=user, password=password, database=database, ssl=ssl)
                print("Connected to TiDB successfully!")
                return
            except pymysql.Error as e:
                print(e)
                print(f"Connection failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        raise Exception("Failed to connect to TiDB after multiple attempts.")


    # Function to insert a new record into the table
    def insert_record(self,original_sql, schemas, execution_plan, tuned_sql, what_changed, index_suggestion,gpt_version):
        
        try:
            cursor = self.connection.cursor()
            sql = "INSERT INTO history (original_sql, schemas_info, execution_plan, tuned_sql, what_changed, index_suggestion,gpt_version) " \
                    "VALUES (%s, %s, %s, %s, %s, %s,%s)"
            cursor.execute(sql, (original_sql, schemas, execution_plan, tuned_sql, what_changed, index_suggestion,gpt_version))
            self.connection.commit()
            id = cursor.lastrowid
            cursor.close()
            return id

        except pymysql.Error as e:
            print(f"Error inserting record: {e}")

    # Function to update the 'correct' field by id
    def update_correct_field(self, id, correct_value):
        try:
            with self.connection.cursor() as cursor:
                sql = "UPDATE history SET correct = %s WHERE id = %s"
                cursor.execute(sql, (correct_value, id))
            self.connection.commit()
        except pymysql.Error as e:
            print(f"Error updating 'correct' field: {e}")

    # Function to retrieve a record by id
    def get_record_by_id(self, id):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM history WHERE id = %s"
                cursor.execute(sql, (id,))
                return cursor.fetchone()
        except pymysql.Error as e:
            print(f"Error retrieving record: {e}")

    def get_histories_with_page(self, page, per_page):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM history ORDER BY id DESC LIMIT %s OFFSET %s"
                cursor.execute(sql, (per_page, (page - 1) * per_page))
                result = cursor.fetchall()
                sql = "SELECT COUNT(*) FROM history"
                cursor.execute(sql)
                count = cursor.fetchone()[0]
                return result, count
        except pymysql.Error as e:
            print(f"Error getting histories with page: {e}")

    def delete_history(self, id):
        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM history WHERE id = %s"
                cursor.execute(sql, (id,))
            self.connection.commit()
        except pymysql.Error as e:
            print(f"Error deleting history: {e}")

    
    def close(self):
        print("Closing connection to TiDB...")
        self.connection.close()

if __name__ == "__main__":
    store = Store()
    
    # Example usage:
    store.insert_record("orginal_history", "schema_info", "execution_plan", "tuned_sql", "changes", "index_suggestion", "gpt_version")
    store.update_correct_field(1, 1)

    record = store.get_record_by_id(1)
    print(record)

    store.close()  # Close the connection when done
