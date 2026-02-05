#!/usr/bin/env python3
"""
Test script to verify database connectivity
"""
import mysql.connector as mysql
from app.config import settings

def test_db_connection():
    try:
        print("Testing database connection...")
        print(f"Host: {settings.db_host}")
        print(f"User: {settings.db_user}")
        print(f"Database: {settings.db_name}")
        
        conn = mysql.connect(
            host=settings.db_host,
            user=settings.db_user,
            password=settings.db_pass,
            database=settings.db_name,
            connection_timeout=5,
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print(f"MySQL version: {version[0]}")
        
        # Test schema introspection
        from app.schema import get_schema_summary
        schema = get_schema_summary()
        print(f"Schema summary: {schema}")
        
        cursor.close()
        conn.close()
        print("Database connection test: SUCCESS")
        return True
        
    except Exception as e:
        print(f"Database connection test: FAILED - {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()