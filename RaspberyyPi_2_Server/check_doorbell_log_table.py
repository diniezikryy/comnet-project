import sqlite3
from datetime import datetime

def print_doorbell_log(cursor):
	print("\nDoorbellLog Entries: ")
	print("-" * 70)
	print("ID | TIMESTAMP | IMAGE")
	print("-" * 70)
	
	cursor.execute("SELECT id, timestamp, image FROM doorbell_log ORDER BY timestamp DESC")
	rows = cursor.fetchall()
	for row in rows:
		id, timestamp, image = row
		timestamp = datetime.fromisoformat(timestamp)
		formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
		print(f"{id} | {formatted_time} | {image[:30]}...")
		
db_file = "instance/site.db"
conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
	print_doorbell_log(cursor)
except sqlite3.OperationalError as e:
	print(f"Error: {e}")
	print("The doorbell_log table might not exist or there might be a problem with the database.")
	
conn.close()

print("\nDoorbellLog viewing complete.")
