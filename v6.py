import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from tkcalendar import DateEntry
import threading
import os
from flask import Flask, request, jsonify
import subprocess

# Color constants
BACKGROUND_COLOR = "#f0f3f7"  # Light gray background used in main window
PRIMARY_COLOR = "#0984e3"     # Blue used for buttons and headings
SECONDARY_COLOR = "#74b9ff"   # Lighter blue used for active states
TEXT_COLOR = "#2d3436"        # Dark gray text color

class SmartWeighingScale:
    DB_PATH = r"E:\bengalbevsmartweighingscalebottle\scale.db"  # Define as class attribute #mention the database path

    def __init__(self, master):
        self.master = master
        self.create_database()
        self.check_license()

    def check_license(self):
        try:
            # Fetch the current license key
            self.cursor.execute("SELECT license_key FROM current_license_key ORDER BY id DESC LIMIT 1")
            current_result = self.cursor.fetchone()
            if not current_result:
                self.run_license_program()
                return

            current_license_key = current_result[0]
            
            # Check if the current license key exists in license_keys and get its expiry date
            self.cursor.execute("SELECT expiry_date FROM license_keys WHERE license_key = ?", (current_license_key,))
            license_result = self.cursor.fetchone()
            
            if license_result:
                expiry_date_str = license_result[0]
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                    current_date = datetime.now().date()
                    if current_date <= expiry_date:
                        # Valid license, proceed with UI and Flask
                        self.create_style()
                        self.app = Flask(__name__)
                        self.setup_flask_routes()
                        flask_thread = threading.Thread(target=self.app.run, kwargs={"host": "0.0.0.0", "port": 5000}, daemon=True)
                        flask_thread.start()
                        self.create_main_window()
                    else:
                        # Expired license, run license prompt
                        self.run_license_program()
                except Exception:
                    # Invalid date format or other error, run license prompt
                    self.run_license_program()
            else:
                # Current license key not found in license_keys, run license prompt
                self.run_license_program()
        except Exception:
            # Database error or other issue, run license prompt
            self.run_license_program()

    def run_license_program(self):
        try:
            subprocess.run(["python", r"e:/bengalbevsmartweighingscalebottle/license_prompt.py"], check=True)
            # After license prompt completes, recheck license
            self.check_license()
        except subprocess.CalledProcessError:
            # If license prompt fails or is closed, exit the application
            self.master.destroy()

    def create_database(self):
        # Ensure the directory for the database exists
        db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
        os.makedirs(db_dir, exist_ok=True)
        full_db_path = os.path.join(db_dir, self.DB_PATH)

        self.conn = sqlite3.connect(full_db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS records
            (timestamp TEXT, weight REAL, category TEXT, remark TEXT)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories
            (name TEXT PRIMARY KEY, lower_limit REAL, upper_limit REAL)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS license_keys
            (id INTEGER PRIMARY KEY, license_key TEXT, expiry_date TEXT)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_license_key
            (id INTEGER PRIMARY KEY, license_key TEXT)
        """)

        # Insert initial categories if table is empty
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany("""
                INSERT INTO categories (name, lower_limit, upper_limit)
                VALUES (?, ?, ?)
            """, [
                ("Bottle category 1", 220.0, 260.0),
                ("Bottle category 2", 220.0, 260.0),
                ("Bottle category 3", 220.0, 260.0)
            ])

        # Insert initial license keys if table is empty
        self.cursor.execute("SELECT COUNT(*) FROM license_keys")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany("INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                                   [("LICENSE_KEY_BEFORE_AUG_2025", "2025-08-02"),
                                    ("LICENSE_KEY_AFTER_AUG_2025", "2099-12-31")])

        # Insert initial current license key if table is empty
        self.cursor.execute("SELECT COUNT(*) FROM current_license_key")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO current_license_key (license_key) VALUES (?)",
                               ("LICENSE_KEY_BEFORE_AUG_2025",))
        self.conn.commit()

    def create_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BACKGROUND_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", background="#dfe6e9", foreground=TEXT_COLOR, padding=[10, 5], font=('Helvetica', 11, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", SECONDARY_COLOR)])

        style.configure("TButton",
                        background=PRIMARY_COLOR,
                        foreground="white",
                        padding=10,
                        font=('Helvetica', 10, 'bold'))
        style.map("TButton",
                  background=[("active", SECONDARY_COLOR)])

        style.configure("TCombobox",
                        fieldbackground="white",
                        background="white",
                        padding=5)

        style.configure("Treeview",
                        background="white",
                        fieldbackground="white",
                        rowheight=25,
                        font=('Helvetica', 10))

        style.configure("Treeview.Heading",
                        background=PRIMARY_COLOR,
                        foreground="white",
                        font=('Helvetica', 11, 'bold'))

    def create_main_window(self):
        self.master.title("SMART WEIGHING SCALE FOR CHECKING BOTTLES")
        self.master.geometry("900x600")
        self.master.configure(bg=BACKGROUND_COLOR)

        notebook = ttk.Notebook(self.master)
        notebook.pack(expand=True, fill="both")

        self.tab_main = tk.Frame(notebook, bg=BACKGROUND_COLOR)
        self.tab_settings = tk.Frame(notebook, bg=BACKGROUND_COLOR)
        self.tab_records = tk.Frame(notebook, bg=BACKGROUND_COLOR)

        notebook.add(self.tab_main, text="Main")
        notebook.add(self.tab_settings, text="Settings")
        notebook.add(self.tab_records, text="Records")

        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_records_tab()

    def setup_main_tab(self):
        """Set up the main tab interface for the Smart Weighing Scale application."""
        # Constants for styling
        TITLE_FONT = ("Helvetica", 20, "bold")
        WEIGHT_FONT = ("Helvetica", 24, "bold")
        RESULT_FONT = ("Helvetica", 16, "bold")
        DROPDOWN_FONT = ("Helvetica", 12)
        PADDING_Y = 10
        PADDING_X = 20
        WEIGHT_LABEL_WIDTH = 15
        RESULT_LABEL_WIDTH = 12
        RESULT_LABEL_HEIGHT = 2

        # Create a main frame to hold all widgets with grid layout
        main_frame = tk.Frame(self.tab_main, bg=BACKGROUND_COLOR)
        main_frame.pack(expand=True, fill="both", padx=PADDING_X, pady=PADDING_Y)

        # Title label
        title_label = tk.Label(
            main_frame,
            text="Weight Reading",
            font=TITLE_FONT,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        title_label.grid(row=0, column=0, pady=PADDING_Y, sticky="ew")

        # Weight display label
        self.weight_var = tk.StringVar(value="0.0000 g")
        weight_label = tk.Label(
            main_frame,
            textvariable=self.weight_var,
            font=WEIGHT_FONT,
            bg="white",
            fg=TEXT_COLOR,
            relief="solid",
            bd=2,
            width=WEIGHT_LABEL_WIDTH
        )
        weight_label.grid(row=1, column=0, pady=PADDING_Y, sticky="ew")

        # Result label (Pass/Fail)
        self.result_label = tk.Label(
            main_frame,
            text="",
            font=RESULT_FONT,
            width=RESULT_LABEL_WIDTH,
            height=RESULT_LABEL_HEIGHT
        )
        self.result_label.grid(row=2, column=0, pady=PADDING_Y, sticky="ew")

        # Category selection dropdown
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.category_var,
            values=self.get_categories(),
            state="readonly",
            font=DROPDOWN_FONT
        )
        self.category_dropdown.grid(row=3, column=0, pady=PADDING_Y, sticky="ew")
        
        # Set default category if available
        if self.category_dropdown['values']:
            self.category_var.set(self.category_dropdown['values'][0])

        # Configure grid column to center widgets
        main_frame.columnconfigure(0, weight=1)

    def setup_settings_tab(self):
        tk.Label(self.tab_settings, text="Bottle Categories", font=("Helvetica", 20, "bold"), bg=BACKGROUND_COLOR).pack(pady=20)

        self.cat_tree = ttk.Treeview(self.tab_settings, columns=("Category Name", "Lower Limit", "Upper Limit"), show="headings")
        for col in self.cat_tree["columns"]:
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=200)
        self.cat_tree.pack(padx=30, pady=10, fill="both")
        self.refresh_category_tree()

        ttk.Button(self.tab_settings, text="Upload Excel to Add Category", command=self.upload_excel).pack(pady=10)

    def setup_records_tab(self):
        tk.Label(self.tab_records, text="Records",
                 font=('Helvetica', 20, 'bold'),
                 foreground=TEXT_COLOR,
                 background=BACKGROUND_COLOR).pack(pady=(20, 30), anchor="w", padx=80)

        date_frame = ttk.Frame(self.tab_records)
        date_frame.pack(fill="x", padx=80)

        from_label = tk.Label(date_frame, text="From",
                             font=('Helvetica', 10),
                             foreground=TEXT_COLOR,
                             background=BACKGROUND_COLOR)
        from_label.grid(row=0, column=0, padx=(0, 10))

        self.from_date = DateEntry(date_frame, width=12,
                                  background=PRIMARY_COLOR,
                                  foreground='white',
                                  borderwidth=0,
                                  font=("Helvetica", 10))
        self.from_date.grid(row=0, column=1, padx=(0, 5))

        self.from_time_hour = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.from_time_hour.grid(row=0, column=2)
        self.from_time_hour.insert(0, "00")

        tk.Label(date_frame, text=":", font=("Helvetica", 10), background=BACKGROUND_COLOR).grid(row=0, column=3)

        self.from_time_minute = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.from_time_minute.grid(row=0, column=4)
        self.from_time_minute.insert(0, "00")

        tk.Label(date_frame, text=":", font=("Helvetica", 10), background=BACKGROUND_COLOR).grid(row=0, column=5)

        self.from_time_second = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.from_time_second.grid(row=0, column=6, padx=(0, 50))
        self.from_time_second.insert(0, "00")

        to_label = tk.Label(date_frame, text="To",
                           font=('Helvetica', 10),
                           foreground=TEXT_COLOR,
                           background=BACKGROUND_COLOR)
        to_label.grid(row=0, column=7, padx=(0, 10))

        self.to_date = DateEntry(date_frame, width=12,
                                background=PRIMARY_COLOR,
                                foreground='white',
                                borderwidth=0,
                                font=("Helvetica", 10))
        self.to_date.grid(row=0, column=8, padx=(0, 5))

        self.to_time_hour = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.to_time_hour.grid(row=0, column=9)
        self.to_time_hour.insert(0, "23")

        tk.Label(date_frame, text=":", font=("Helvetica", 10), background=BACKGROUND_COLOR).grid(row=0, column=10)

        self.to_time_minute = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.to_time_minute.grid(row=0, column=11)
        self.to_time_minute.insert(0, "59")

        tk.Label(date_frame, text=":", font=("Helvetica", 10), background=BACKGROUND_COLOR).grid(row=0, column=12)

        self.to_time_second = ttk.Entry(date_frame, width=3, font=("Helvetica", 10))
        self.to_time_second.grid(row=0, column=13)
        self.to_time_second.insert(0, "59")

        columns = ("Timestamp", "Captured value (kg)", "Bottle category", "Remark")
        self.records_tree = ttk.Treeview(self.tab_records, columns=columns, show="headings", height=10)

        style = ttk.Style()
        style.configure('Treeview',
                        background='white',
                        fieldbackground='white',
                        foreground=TEXT_COLOR,
                        font=('Helvetica', 10),
                        rowheight=25)
        style.configure('Treeview.Heading',
                        font=('Helvetica', 11, 'bold'),
                        background=PRIMARY_COLOR,
                        foreground='white',
                        relief='flat',
                        padding=5)
        style.map('Treeview.Heading',
                  background=[('active', SECONDARY_COLOR)],
                  foreground=[('active', 'white')])

        for col in columns:
            self.records_tree.heading(col, text=col)
        self.records_tree.column("Timestamp", width=200)
        self.records_tree.column("Captured value (kg)", width=150)
        self.records_tree.column("Bottle category", width=150)
        self.records_tree.column("Remark", width=100)

        self.records_tree.tag_configure('oddrow', background='#F8F9FA')
        self.records_tree.tag_configure('evenrow', background='#FFFFFF')

        self.records_tree.pack(pady=(20, 30), padx=80, fill="both")

        button_frame = ttk.Frame(self.tab_records)
        button_frame.pack(pady=20)

        show_button = ttk.Button(button_frame, text="Show records",
                                command=self.show_records)
        show_button.grid(row=0, column=0, padx=20)

        export_button = ttk.Button(button_frame, text="Export to excel",
                                  command=self.export_to_excel)
        export_button.grid(row=0, column=1, padx=20)

    def get_categories(self):
        self.cursor.execute("SELECT name FROM categories")
        return [row[0] for row in self.cursor.fetchall()]

    def refresh_category_tree(self):
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        self.cursor.execute("SELECT name, lower_limit, upper_limit FROM categories")
        for row in self.cursor.fetchall():
            self.cat_tree.insert("", tk.END, values=row)

    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df = pd.read_excel(file_path)
                expected = ["Category", "Lower Limit", "Upper Limit"]
                if not all(col in df.columns for col in expected):
                    messagebox.showerror("Error", "Missing columns in Excel file")
                    return
                for _, row in df.iterrows():
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO categories (name, lower_limit, upper_limit)
                        VALUES (?, ?, ?)
                    ''', (row['Category'], row['Lower Limit'], row['Upper Limit']))
                self.conn.commit()
                messagebox.showinfo("Success", "Categories updated successfully")
                self.refresh_category_tree()
                self.category_dropdown['values'] = self.get_categories()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def display_remote_weight(self, weight, remark):
        self.weight_var.set(f"{weight:.4f} g")
        color = "#27ae60" if remark == "Pass" else "#e74c3c"
        self.result_label.config(text=remark, bg=color, fg="white")

    def setup_flask_routes(self):
        SCALE = self

        @self.app.route('/send_weight', methods=['GET'])
        def receive_weight():
            try:
                weight = float(request.args.get('weight'))
                category = SCALE.category_var.get()
                if not category:
                    return jsonify({"result": "fail", "error": "No category selected"}), 400

                SCALE.cursor.execute("SELECT lower_limit, upper_limit FROM categories WHERE name = ?", (category,))
                limits = SCALE.cursor.fetchone()
                if not limits:
                    return jsonify({"result": "fail", "error": "Category not found"}), 400

                lower_limit, upper_limit = limits
                remark = "Pass" if lower_limit <= weight <= upper_limit else "Fail"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                SCALE.cursor.execute('''
                    INSERT INTO records (timestamp, weight, category, remark)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, weight, category, remark))
                SCALE.conn.commit()
                SCALE.master.after(0, SCALE.display_remote_weight, weight, remark)
                return jsonify({"result": remark.lower()})
            except Exception as ex:
                return jsonify({"result": "fail", "error": str(ex)}), 400

    def show_records(self):
        self.records_tree.delete(*self.records_tree.get_children())
        from_date_str = self.from_date.get_date().strftime("%Y-%m-%d")
        from_time_str = f"{self.from_time_hour.get()}:{self.from_time_minute.get()}:{self.from_time_second.get()}"
        from_datetime_str = f"{from_date_str} {from_time_str}"

        to_date_str = self.to_date.get_date().strftime("%Y-%m-%d")
        to_time_str = f"{self.to_time_hour.get()}:{self.to_time_minute.get()}:{self.to_time_second.get()}"
        to_datetime_str = f"{to_date_str} {to_time_str}"

        self.records_tree.after(10, lambda: self._populate_records(from_datetime_str, to_datetime_str))

    def _populate_records(self, from_date, to_date):
        self.cursor.execute("""
            SELECT timestamp, weight, category, remark FROM records
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (from_date, to_date))
        for i, row in enumerate(self.cursor.fetchall()):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.records_tree.insert("", tk.END, values=row, tags=(tag,))

    def export_to_excel(self):
        from_date_str = self.from_date.get_date().strftime("%Y-%m-%d")
        from_time_str = f"{self.from_time_hour.get()}:{self.from_time_minute.get()}:{self.from_time_second.get()}"
        from_datetime_str = f"{from_date_str} {from_time_str}"

        to_date_str = self.to_date.get_date().strftime("%Y-%m-%d")
        to_time_str = f"{self.to_time_hour.get()}:{self.to_time_minute.get()}:{self.to_time_second.get()}"
        to_datetime_str = f"{to_date_str} {to_time_str}"

        # Fetch records
        self.cursor.execute("""
            SELECT timestamp, weight, category, remark FROM records
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (from_datetime_str, to_datetime_str))
        data = self.cursor.fetchall()

        # Fetch Pass/Fail counts
        self.cursor.execute("""
            SELECT remark, COUNT(*) FROM records
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY remark
        """, (from_datetime_str, to_datetime_str))
        summary = {"Pass": 0, "Fail": 0}
        for remark, count in self.cursor.fetchall():
            if remark in summary:
                summary[remark] = count

        if data:
            # Create DataFrame for records
            df = pd.DataFrame(data, columns=["Timestamp", "Captured value (kg)", "Bottle category", "Remark"])
            
            # Create summary DataFrame
            summary_data = [
                ["", "", "Summary", ""],
                ["", "", "Number of Pass", summary["Pass"]],
                ["", "", "Number of Fail", summary["Fail"]]
            ]
            summary_df = pd.DataFrame(summary_data, columns=["Timestamp", "Captured value (kg)", "Bottle category", "Remark"])
            
            # Concatenate records and summary
            df = pd.concat([df, summary_df], ignore_index=True)
            
            # Open file dialog with .xlsx auto-selected
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")]
            )
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", "Data exported successfully")
        else:
            messagebox.showinfo("Info", "No data to export")

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartWeighingScale(root)
    root.mainloop()