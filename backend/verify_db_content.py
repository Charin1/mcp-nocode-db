
import sqlite3
import json

DATABASE_PATH = "./mcp_nocode_db.db"

def check_last_message():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get the most recent message
        cursor.execute("SELECT id, query, results FROM chat_messages ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            msg_id, query, results = row
            print(f"Message ID: {msg_id}")
            print(f"Query: {query}")
            print(f"Results type: {type(results)}")
            
            if results:
                print("Results found in DB!")
                try:
                    parsed = json.loads(results)
                    # print(f"Parsed results keys: {parsed.keys()}") # might be list or dict
                    preview = str(parsed)[:200]
                    print(f"Content Preview: {preview}")
                except Exception as e:
                    print(f"Error parsing results JSON: {e}")
                    print(f"Raw content: {results}")
            else:
                print("Results field is EMPTY/NULL.")
        else:
            print("No messages found.")
            
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    check_last_message()
