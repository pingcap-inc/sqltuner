import pymysql
import time
import os
from dotenv import load_dotenv, find_dotenv

host = 'gateway01.us-east-1.prod.aws.tidbcloud.com'
port = 4000  # TiDB default port is 4000
user = '48tps7f6KZGo1Gq.root'
database = 'sqltuner'
ssl_mode="VERIFY_IDENTITY"
ssl={"ca": "/etc/ssl/cert.pem"}

def get_password():
    _ = load_dotenv(find_dotenv())
    return os.getenv("TIDB_PASSWORD")

class Store: 
    def __init__(self):
        retry_count = 5  # Number of retries
        retry_delay = 2  # Delay between retries (in seconds)
        password = get_password()

        for _ in range(retry_count):
            try:
                self.connection = pymysql.connect(host=host, port=port, user=user, password=password, database=database, ssl=ssl)
                print("Connected to TiDB successfully!")
                return
            except pymysql.Error as e:
                print(e)
                print(f"Connection failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        raise Exception("Failed to connect to TiDB after multiple attempts.")


    # Function to insert a new record into the table
    def insert_record(self,original_sql, schemas, stats_info, tuned_sql, what_changed, index_suggestion):
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO history (original_sql, schemas_info, stats_info, tuned_sql, what_changed, index_suggestion) " \
                    "VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (original_sql, schemas, stats_info, tuned_sql, what_changed, index_suggestion))
            self.connection.commit()
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

    def get_count(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT COUNT(*) FROM history"
                cursor.execute(sql)
                return cursor.fetchone()[0]
        except pymysql.Error as e:
            print(f"Error getting table count: {e}")

    def get_first(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT min(id) FROM history"
                cursor.execute(sql)
                result = cursor.fetchone()
                return result[0] if result else None
        except pymysql.Error as e:
            print(f"Error getting first id: {e}")

    def get_next(self, id):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT id FROM history WHERE id > %s order by id limit 1"
                cursor.execute(sql, id)
                result = cursor.fetchone()
                return result[0] if result else None
        except pymysql.Error as e:
            print(f"Error getting next id: {e}")

    def get_prev(self, id):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT id FROM history WHERE id < %s order by id desc limit 1"
                cursor.execute(sql, id)
                result = cursor.fetchone()
                return result[0] if result else None
        except pymysql.Error as e:
            print(f"Error getting previous id: {e}")
    
    def close(self):
        self.connection.close()

if __name__ == "__main__":
    store = Store()
    
    # Example usage:
    store.insert_record("orginal_history", "schema_info", "stats_info", "tuned_sql", "changes", "index_suggestion")
    store.update_correct_field(1, 1)

    record = store.get_record_by_id(1)
    print(record)

    store.close()  # Close the connection when done
