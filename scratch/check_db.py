import sqlite3

try:
    conn = sqlite3.connect("authtwin.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, base_url, created_at FROM targets;")
    rows = cursor.fetchall()
    print("TARGETS IN DB:", rows)
    conn.close()
except Exception as e:
    print("DB ERROR:", e)
