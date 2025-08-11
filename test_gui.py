#!/usr/bin/env python3
"""
GUI test for license key dialog
"""
import tkinter as tk
import sqlite3
import os
from datetime import datetime, timedelta

# Simulate expired license by setting a past date
def create_expired_license():
    """Create a database with an expired license key"""
    db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "scale.db")
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS license_keys
        (id INTEGER PRIMARY KEY, license_key TEXT, expiry_date TEXT)
    """)
    
    # Insert expired license key (yesterday)
    expired_date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                  ("EXPIRED_LICENSE_KEY", expired_date))
    conn.commit()
    conn.close()
    
    print(f"Created expired license key with date: {expired_date}")

def test_license_dialog():
    """Test the license key dialog by creating a minimal version"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Create license dialog similar to the main application
    license_window = tk.Toplevel(root)
    license_window.title("License Key Required - TEST")
    license_window.geometry("450x250")
    license_window.configure(bg="#f0f3f7")
    
    # Main frame
    main_frame = tk.Frame(license_window, bg="#f0f3f7")
    main_frame.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Title
    title_label = tk.Label(main_frame, text="License Key Required (TEST)", 
                          font=("Helvetica", 16, "bold"), 
                          bg="#f0f3f7", fg="#2d3436")
    title_label.pack(pady=(0, 10))
    
    # Message
    message_label = tk.Label(main_frame, 
                            text="This is a test of the license key dialog.\nEnter any key with 10+ characters:",
                            font=("Helvetica", 11), 
                            bg="#f0f3f7", fg="#2d3436",
                            wraplength=400, justify="center")
    message_label.pack(pady=(0, 20))
    
    # Entry frame
    entry_frame = tk.Frame(main_frame, bg="#f0f3f7")
    entry_frame.pack(pady=(0, 20))
    
    tk.Label(entry_frame, text="License Key:", font=("Helvetica", 10), 
            bg="#f0f3f7", fg="#2d3436").pack(anchor="w")
    
    license_entry = tk.Entry(entry_frame, width=40, font=("Helvetica", 12),
                           relief="solid", bd=1)
    license_entry.pack(pady=(5, 0))
    license_entry.focus_set()
    
    # Result label
    result_label = tk.Label(main_frame, text="", font=("Helvetica", 10),
                           bg="#f0f3f7", fg="#2d3436")
    result_label.pack(pady=(0, 10))
    
    def validate_key():
        entered_key = license_entry.get().strip()
        if not entered_key:
            result_label.config(text="❌ License key cannot be empty.", fg="red")
        elif len(entered_key) < 10:
            result_label.config(text="❌ License key must be at least 10 characters.", fg="red")
        else:
            result_label.config(text="✅ Valid license key format!", fg="green")
            # In real app, this would update the database
            license_window.after(2000, lambda: license_window.destroy())
    
    def close_test():
        license_window.destroy()
        root.destroy()
    
    # Button frame
    button_frame = tk.Frame(main_frame, bg="#f0f3f7")
    button_frame.pack()
    
    from tkinter import ttk
    submit_btn = ttk.Button(button_frame, text="Test Submit", command=validate_key)
    submit_btn.pack(side="left", padx=(0, 10))
    
    close_btn = ttk.Button(button_frame, text="Close Test", command=close_test)
    close_btn.pack(side="left")
    
    # Bind Enter key
    license_window.bind('<Return>', lambda event: validate_key())
    
    print("License dialog test window created. Try entering different license keys.")
    root.mainloop()

if __name__ == "__main__":
    print("Testing license key GUI components...")
    create_expired_license()
    test_license_dialog()

