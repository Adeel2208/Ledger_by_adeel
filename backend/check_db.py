import sqlite3

conn = sqlite3.connect('vcbrain.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Count records
try:
    cursor.execute("SELECT COUNT(*) FROM founders")
    print("Founders:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM applications")
    print("Applications:", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM signals")
    print("Signals:", cursor.fetchone()[0])
except Exception as e:
    print(f"Error: {e}")

conn.close()
