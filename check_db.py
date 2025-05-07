import sqlite3
import os
from pathlib import Path

# Database file path
DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "data" / "chexam.db"

def check_database():
    """Check the database structure and print table information."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Database found at: {DB_PATH}")
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check each table structure
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Show sample data if available
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                sample = cursor.fetchone()
                print(f"Sample data: {sample}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return False

if __name__ == "__main__":
    check_database()
