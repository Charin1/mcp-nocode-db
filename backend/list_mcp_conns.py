import sqlite3
import yaml
import os

def get_db_path():
    return "mcp_nocode_db.db"

def list_mcp_connections():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, url, connection_type, user_id FROM mcp_connections")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No MCP connections found.")
        else:
            print("Found MCP Connections:")
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, URL: {row[2]}, Type: {row[3]}, User: {row[4]}")
                
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    list_mcp_connections()
