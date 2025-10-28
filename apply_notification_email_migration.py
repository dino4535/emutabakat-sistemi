# -*- coding: utf-8 -*-
"""
Email Notification Migration Script
Tarih: 27 Ekim 2025
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )
    
    print("=" * 60)
    print("EMAIL NOTIFICATION MIGRATION")
    print("=" * 60)
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        with open('add_notification_email_column.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        commands = sql_script.split('GO')
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    while cursor.nextset():
                        pass
                    for message in cursor.messages:
                        print(message[1])
                    conn.commit()
                except Exception as e:
                    print(f"[UYARI] {str(e)}")
        
        print("")
        print("=" * 60)
        print("[OK] Migration tamamlandi!")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[HATA] {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()

