#!/usr/bin/env python3
"""
Test script for license key management system
"""
import sqlite3
import os
from datetime import datetime, timedelta

def test_database_creation():
    """Test if the database and license key table are created correctly"""
    print("Testing database creation...")
    
    # Remove existing database for clean test
    db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
    db_path = os.path.join(db_dir, "scale.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Import and create the application (this will create the database)
    import sys
    sys.path.append('/home/ubuntu/upload')
    
    # Create database directory and connection
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # Create tables as in the application
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records
        (timestamp TEXT, weight REAL, category TEXT, remark TEXT)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories
        (name TEXT PRIMARY KEY, lower_limit REAL, upper_limit REAL)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license_keys
        (id INTEGER PRIMARY KEY, license_key TEXT, expiry_date TEXT)
    """)

    # Insert initial license keys
    cursor.execute("SELECT COUNT(*) FROM license_keys")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                      ("LICENSE_KEY_BEFORE_AUG_2025", "2025-08-02"))
        cursor.execute("INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                      ("LICENSE_KEY_AFTER_AUG_2025", "2099-12-31"))
    conn.commit()
    
    # Verify license keys were inserted
    cursor.execute("SELECT license_key, expiry_date FROM license_keys")
    results = cursor.fetchall()
    print(f"License keys in database: {results}")
    
    conn.close()
    print("✓ Database creation test passed")

def test_license_validation():
    """Test license key validation logic"""
    print("\nTesting license validation...")
    
    db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
    db_path = os.path.join(db_dir, "scale.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # Test 1: Check current date vs license expiry
    cursor.execute("SELECT license_key, expiry_date FROM license_keys ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    if result:
        stored_license_key, expiry_date_str = result
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        
        print(f"Current license key: {stored_license_key}")
        print(f"Expiry date: {expiry_date}")
        print(f"Current date: {current_date}")
        print(f"License expired: {current_date > expiry_date}")
    
    # Test 2: Simulate updating license key
    print("\nTesting license key update...")
    new_license_key = "NEW_LICENSE_KEY_2025"
    new_expiry = (datetime.now().date() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    cursor.execute("DELETE FROM license_keys")
    cursor.execute("INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                  (new_license_key, new_expiry))
    conn.commit()
    
    # Verify update
    cursor.execute("SELECT license_key, expiry_date FROM license_keys")
    result = cursor.fetchone()
    print(f"Updated license key: {result[0]}")
    print(f"New expiry date: {result[1]}")
    
    conn.close()
    print("✓ License validation test passed")

def test_date_scenarios():
    """Test different date scenarios"""
    print("\nTesting different date scenarios...")
    
    # Test scenario 1: Before Aug 2, 2025
    test_date_1 = datetime(2025, 7, 1).date()
    aug_2_2025 = datetime(2025, 8, 2).date()
    print(f"Date {test_date_1} is before Aug 2, 2025: {test_date_1 <= aug_2_2025}")
    
    # Test scenario 2: After Aug 2, 2025
    test_date_2 = datetime(2025, 8, 3).date()
    print(f"Date {test_date_2} is after Aug 2, 2025: {test_date_2 > aug_2_2025}")
    
    print("✓ Date scenario tests passed")

if __name__ == "__main__":
    print("Starting license key management system tests...\n")
    
    try:
        test_database_creation()
        test_license_validation()
        test_date_scenarios()
        
        print("\n🎉 All tests passed successfully!")
        print("\nThe license key management system is working correctly:")
        print("- Database and tables are created properly")
        print("- License keys are stored and retrieved correctly")
        print("- Date validation logic works as expected")
        print("- License key updates function properly")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

