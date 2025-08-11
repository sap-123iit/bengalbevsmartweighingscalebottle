import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import os

# Color constants
BACKGROUND_COLOR = "#f0f3f7"  # Light gray background
PRIMARY_COLOR = "#0984e3"     # Blue for buttons
TEXT_COLOR = "#2d3436"        # Dark gray text color

class LicensePrompt:
    DB_PATH = r"E:\bengalbevsmartweighingscalebottle\scale.db"

    def __init__(self):
        self.root = tk.Tk()
        self.create_database()
        self.create_style()
        self.prompt_for_license_key()
        self.root.mainloop()

    def create_database(self):
        db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
        os.makedirs(db_dir, exist_ok=True)
        full_db_path = os.path.join(db_dir, self.DB_PATH)

        self.conn = sqlite3.connect(full_db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS license_keys
            (id INTEGER PRIMARY KEY, license_key TEXT, expiry_date TEXT)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_license_key
            (id INTEGER PRIMARY KEY, license_key TEXT)
        """)
        self.conn.commit()

    def create_style(self):
        style = ttk.Style()
        style.configure("TButton",
                        background=PRIMARY_COLOR,
                        foreground="white",  # White text for readability
                        padding=10,
                        font=('Helvetica', 10, 'bold'))
        style.map("TButton",
                  background=[("active", "#0052cc")],  # Slightly darker blue when active
                  foreground=[("active", "white")])  # White text when active

    def prompt_for_license_key(self):
        self.root.title("License Key Required")
        self.root.geometry("450x250")
        self.root.configure(bg=BACKGROUND_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.on_license_window_close)
        self.root.resizable(False, False)

        main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        title_label = tk.Label(main_frame, text="License Key Required", 
                            font=("Helvetica", 16, "bold"), 
                            bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
        title_label.pack(pady=(0, 10))
        message_label = tk.Label(main_frame, 
                                text="Your license has expired or is invalid. Please enter a new license key to continue:",
                                font=("Helvetica", 11), 
                                bg=BACKGROUND_COLOR, fg=TEXT_COLOR,
                                wraplength=400, justify="center")
        message_label.pack(pady=(0, 20))
        entry_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        entry_frame.pack(pady=(0, 20))
        tk.Label(entry_frame, text="License Key:", font=("Helvetica", 10), 
                bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        self.license_entry = tk.Entry(entry_frame, width=40, font=("Helvetica", 12),
                                    relief="solid", bd=1)
        self.license_entry.pack(pady=(5, 0))
        self.license_entry.focus_set()
        button_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        button_frame.pack()
        submit_btn = ttk.Button(button_frame, text="Submit", 
                            command=self.verify_and_update_license)
        submit_btn.pack(side="left", padx=(0, 10))
        cancel_btn = ttk.Button(button_frame, text="Cancel", 
                            command=self.on_license_window_close)
        cancel_btn.pack(side="left")
        self.root.bind('<Return>', lambda event: self.verify_and_update_license())

    def verify_and_update_license(self):
        entered_key = self.license_entry.get().strip()
        
        if not entered_key:
            messagebox.showerror("Invalid License Key", "License key cannot be empty.")
            return

        if len(entered_key) < 10:
            messagebox.showerror("Invalid License Key", 
                               "License key must be at least 10 characters long.")
            return

        try:
            # Update the current_license_key table
            self.cursor.execute("DELETE FROM current_license_key")
            self.cursor.execute("INSERT INTO current_license_key (license_key) VALUES (?)",
                               (entered_key,))
            self.conn.commit()
            
            messagebox.showinfo("License Key Updated", 
                              "License key updated successfully!")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update license key: {str(e)}")

    def on_license_window_close(self):
        result = messagebox.askyesno("Exit Application", 
                                   "Without a valid license key, the application cannot continue.\n\n" +
                                   "Do you want to exit the application?")
        if result:
            self.root.destroy()

if __name__ == "__main__":
    app = LicensePrompt()