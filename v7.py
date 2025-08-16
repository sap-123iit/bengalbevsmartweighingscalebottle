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

from PIL import Image, ImageTk
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

# Coca‑Cola theme
BACKGROUND_COLOR = "#FAFAFA"
PRIMARY_COLOR    = "#E41E2B"
SECONDARY_COLOR  = "#C0161F"
ACCENT_COLOR     = "#FFFFFF"
TEXT_COLOR       = "#2B2B2B"
SUBTEXT_COLOR    = "#555555"

LICENSE_PROMPT_PATH = r"e:/bengalbevsmartweighingscalebottle-main/license_prompt.py"


class SmartWeighingScale:
    DB_PATH = r"E:\bengalbevsmartweighingscalebottle-main\scale.db"

    def __init__(self, master):
        self.master = master
        self.create_database()
        self.check_license()

    # ---------------- License flow ----------------
    def check_license(self):
        try:
            self.cursor.execute("SELECT license_key FROM current_license_key ORDER BY id DESC LIMIT 1")
            cur = self.cursor.fetchone()
            if not cur:
                return self.run_license_program()

            key = cur[0]
            self.cursor.execute("SELECT expiry_date FROM license_keys WHERE license_key=?", (key,))
            row = self.cursor.fetchone()
            if not row:
                return self.run_license_program()

            expiry = datetime.strptime(row[0], "%Y-%m-%d").date()
            if datetime.now().date() <= expiry:
                self.create_style()
                self.app = Flask(__name__)
                self.setup_flask_routes()
                threading.Thread(target=self.app.run, kwargs={"host": "0.0.0.0", "port": 5000}, daemon=True).start()
                self.create_main_window()
            else:
                self.run_license_program()
        except Exception:
            self.run_license_program()

    def run_license_program(self):
        try:
            subprocess.run(["python", LICENSE_PROMPT_PATH], check=True)
            self.check_license()
        except subprocess.CalledProcessError:
            self.master.destroy()

    # ---------------- Database ----------------
    def create_database(self):
        db_dir = os.path.join(os.path.expanduser("~"), ".smart_weighing_scale")
        os.makedirs(db_dir, exist_ok=True)
        full_db_path = os.path.join(db_dir, self.DB_PATH)

        self.conn = sqlite3.connect(full_db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS records
                               (timestamp TEXT, weight REAL, category TEXT, remark TEXT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS categories
                               (name TEXT PRIMARY KEY, lower_limit REAL, upper_limit REAL)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS license_keys
                               (id INTEGER PRIMARY KEY, license_key TEXT, expiry_date TEXT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS current_license_key
                               (id INTEGER PRIMARY KEY, license_key TEXT)""")

        # Seed categories
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany(
                "INSERT INTO categories (name, lower_limit, upper_limit) VALUES (?, ?, ?)",
                [
                    ("Bottle category 1", 220.0, 260.0),
                    ("Bottle category 2", 220.0, 260.0),
                    ("Bottle category 3", 220.0, 260.0),
                ]
            )

        # Seed licenses
        self.cursor.execute("SELECT COUNT(*) FROM license_keys")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany(
                "INSERT INTO license_keys (license_key, expiry_date) VALUES (?, ?)",
                [
                    ("LICENSE_KEY_BEFORE_AUG_2025", "2025-08-02"),
                    ("LICENSE_KEY_AFTER_AUG_2025", "2099-12-31"),
                ]
            )
        self.cursor.execute("SELECT COUNT(*) FROM current_license_key")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO current_license_key (license_key) VALUES (?)",
                                ("LICENSE_KEY_BEFORE_AUG_2025",))
        self.conn.commit()

    # ---------------- Style ----------------
    def create_style(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure("TNotebook", background=BACKGROUND_COLOR, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=ACCENT_COLOR,
            foreground=TEXT_COLOR,
            padding=[12, 6],
            font=("Helvetica", 11, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PRIMARY_COLOR)],
            foreground=[("selected", "white")]
        )

        style.configure("TButton", background=PRIMARY_COLOR, foreground="white",
                        padding=10, font=("Helvetica", 10, "bold"))
        style.map("TButton", background=[("active", SECONDARY_COLOR)],
                  foreground=[("active", "white")])

        style.configure("TCombobox", fieldbackground="white", background="white", padding=5)

        style.configure("Treeview", background="white", fieldbackground="white",
                        rowheight=26, font=("Helvetica", 10))
        style.configure("Treeview.Heading", background=PRIMARY_COLOR, foreground="white",
                        font=("Helvetica", 11, "bold"))

    # ---------------- Branding ----------------
    def load_brand_images(self):
        # Keep references on self AND on label widgets to prevent garbage collection.
        self.logo_img = None
        self.be_mark_img = None
        try:
            img = Image.open("coca_logo.png").convert("RGBA")
            self.logo_img = ImageTk.PhotoImage(img.resize((160, 60), Image.LANCZOS))
        except Exception:
            self.logo_img = None
        try:
            mark = Image.open("bengal_beverages.png").convert("RGBA")
            self.be_mark_img = ImageTk.PhotoImage(mark.resize((42, 42), Image.LANCZOS))
        except Exception:
            self.be_mark_img = None

    def build_gradient_bg(self, width=900, height=120, start="#E41E2B", end="#B90E18"):
        img = Image.new("RGB", (width, height), start)
        r1, g1, b1 = Image.new("RGB", (1, 1), start).getpixel((0, 0))
        r2, g2, b2 = Image.new("RGB", (1, 1), end).getpixel((0, 0))
        px = img.load()
        for x in range(width):
            t = x / max(1, width - 1)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            for y in range(height):
                px[x, y] = (r, g, b)
        return ImageTk.PhotoImage(img)

    # ---------------- Main window ----------------
    def create_main_window(self):
        self.master.title("SMART WEIGHING SCALE — Coca‑Cola Edition")
        self.master.geometry("1024x720")
        self.master.configure(bg=BACKGROUND_COLOR)

        self.load_brand_images()

        root = tk.Frame(self.master, bg=BACKGROUND_COLOR)
        root.pack(fill="both", expand=True)

        # Header
        header_h = 120
        header = tk.Canvas(root, height=header_h, highlightthickness=0, bd=0, bg=PRIMARY_COLOR)
        header.pack(fill="x", side="top")
        self.header_bg = self.build_gradient_bg(width=2000, height=header_h)
        header.create_image(0, 0, image=self.header_bg, anchor="nw")
        if self.logo_img:
            header_logo = header.create_image(20, header_h // 2, image=self.logo_img, anchor="w")
            # keep a reference on the canvas to avoid GC
            header.logo_ref = self.logo_img
        header.create_text(200, 45, anchor="w", text="Smart Weighing Scale",
                           font=("Helvetica", 20, "bold"), fill=ACCENT_COLOR)
        header.create_text(200, 82, anchor="w", text="Quality Check for Bottles",
                           font=("Helvetica", 11), fill="#FFE9EA")

        # Content
        content = tk.Frame(root, bg=BACKGROUND_COLOR)
        content.pack(fill="both", expand=True)

        notebook = ttk.Notebook(content)
        notebook.pack(expand=True, fill="both", padx=18, pady=18)

        self.tab_main = tk.Frame(notebook, bg=BACKGROUND_COLOR)
        self.tab_settings = tk.Frame(notebook, bg=BACKGROUND_COLOR)
        self.tab_records = tk.Frame(notebook, bg=BACKGROUND_COLOR)

        notebook.add(self.tab_main, text="Main")
        notebook.add(self.tab_settings, text="Settings")
        notebook.add(self.tab_records, text="Records")

        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_records_tab()

        # Footer with Bengal Beverages logo (persistent reference on label)
        footer = tk.Frame(root, bg=ACCENT_COLOR, height=52)
        footer.pack(fill="x", side="bottom")
        ttk.Separator(footer, orient="horizontal").pack(fill="x", side="top")
        inner = tk.Frame(footer, bg=ACCENT_COLOR)
        inner.pack(fill="both", expand=True)
        if self.be_mark_img:
            lbl = tk.Label(inner, image=self.be_mark_img, bg=ACCENT_COLOR)
            lbl.image = self.be_mark_img  # preserve reference
            lbl.pack(side="left", padx=10)
        tk.Label(inner, text="Bengal Beverages Private Limited", bg=ACCENT_COLOR,
                 fg=SUBTEXT_COLOR, font=("Helvetica", 10)).pack(side="left")

    # ---------------- Tabs ----------------
    def setup_main_tab(self):
        TITLE_FONT = ("Helvetica", 21, "bold")
        WEIGHT_FONT = ("Helvetica", 26, "bold")
        RESULT_FONT = ("Helvetica", 16, "bold")
        DROPDOWN_FONT = ("Helvetica", 12)

        main_frame = tk.Frame(self.tab_main, bg=BACKGROUND_COLOR)
        main_frame.pack(expand=True, fill="both", padx=24, pady=20)
        main_frame.columnconfigure(0, weight=1)

        card = tk.Frame(main_frame, bg=ACCENT_COLOR)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        tk.Frame(card, bg=PRIMARY_COLOR, height=4).grid(row=0, column=0, sticky="ew")

        tk.Label(card, text="Weight Reading", bg=ACCENT_COLOR, fg=TEXT_COLOR, font=TITLE_FONT)\
            .grid(row=1, column=0, pady=(18, 12))

        self.weight_var = tk.StringVar(value="0.0000 g")
        tk.Label(card, textvariable=self.weight_var, font=WEIGHT_FONT,
                 bg="white", fg=TEXT_COLOR, relief="solid", bd=1, width=18)\
            .grid(row=2, column=0, pady=12, padx=18, sticky="n")

        self.result_label = tk.Label(card, text="", font=RESULT_FONT, width=14, height=2,
                                     bg=BACKGROUND_COLOR, fg="white")
        self.result_label.grid(row=3, column=0, pady=12)

        form = tk.Frame(card, bg=ACCENT_COLOR)
        form.grid(row=4, column=0, pady=(8, 22))
        tk.Label(form, text="Bottle category:", bg=ACCENT_COLOR, fg=SUBTEXT_COLOR,
                 font=("Helvetica", 11)).pack(side="left", padx=(0, 10))
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            form, textvariable=self.category_var, values=self.get_categories(),
            state="readonly", font=DROPDOWN_FONT, width=28
        )
        self.category_dropdown.pack(side="left")
        vals = self.category_dropdown["values"]
        if vals:
            self.category_var.set(vals[0])

    def setup_settings_tab(self):
        tk.Label(self.tab_settings, text="Bottle Categories", font=("Helvetica", 20, "bold"),
                 bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(pady=20)

        self.cat_tree = ttk.Treeview(
            self.tab_settings, columns=("Category Name", "Lower Limit", "Upper Limit"), show="headings"
        )
        for col in self.cat_tree["columns"]:
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=200)
        self.cat_tree.pack(padx=30, pady=10, fill="both")

        self.refresh_category_tree()
        ttk.Button(self.tab_settings, text="Upload Excel to Add Category", command=self.upload_excel).pack(pady=10)

    def setup_records_tab(self):
        tk.Label(self.tab_records, text="Records",
                 font=("Helvetica", 20, "bold"),
                 foreground=TEXT_COLOR,
                 background=BACKGROUND_COLOR).pack(pady=(20, 30), anchor="w", padx=80)

        date_frame = ttk.Frame(self.tab_records)
        date_frame.pack(fill="x", padx=80)

        tk.Label(date_frame, text="From", font=("Helvetica", 10), fg=TEXT_COLOR,
                 bg=BACKGROUND_COLOR).grid(row=0, column=0, padx=(0, 10))
        self.from_date = DateEntry(date_frame, width=12, background=PRIMARY_COLOR,
                                   foreground="white", borderwidth=0, font=("Helvetica", 10))
        self.from_date.grid(row=0, column=1, padx=(0, 5))
        self.from_time_hour = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.from_time_hour.grid(row=0, column=2); self.from_time_hour.insert(0, "00")
        tk.Label(date_frame, text=":", font=("Helvetica", 10), bg=BACKGROUND_COLOR).grid(row=0, column=3)
        self.from_time_minute = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.from_time_minute.grid(row=0, column=4); self.from_time_minute.insert(0, "00")
        tk.Label(date_frame, text=":", font=("Helvetica", 10), bg=BACKGROUND_COLOR).grid(row=0, column=5)
        self.from_time_second = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.from_time_second.grid(row=0, column=6, padx=(0, 50)); self.from_time_second.insert(0, "00")

        tk.Label(date_frame, text="To", font=("Helvetica", 10), fg=TEXT_COLOR,
                 bg=BACKGROUND_COLOR).grid(row=0, column=7, padx=(0, 10))
        self.to_date = DateEntry(date_frame, width=12, background=PRIMARY_COLOR,
                                 foreground="white", borderwidth=0, font=("Helvetica", 10))
        self.to_date.grid(row=0, column=8, padx=(0, 5))
        self.to_time_hour = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.to_time_hour.grid(row=0, column=9); self.to_time_hour.insert(0, "23")
        tk.Label(date_frame, text=":", font=("Helvetica", 10), bg=BACKGROUND_COLOR).grid(row=0, column=10)
        self.to_time_minute = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.to_time_minute.grid(row=0, column=11); self.to_time_minute.insert(0, "59")
        tk.Label(date_frame, text=":", font=("Helvetica", 10), bg=BACKGROUND_COLOR).grid(row=0, column=12)
        self.to_time_second = ttk.Entry(date_frame, width=3, font=("Helvetica", 10)); self.to_time_second.grid(row=0, column=13); self.to_time_second.insert(0, "59")

        columns = ("Timestamp", "Captured value (kg)", "Bottle category", "Remark")
        self.records_tree = ttk.Treeview(self.tab_records, columns=columns, show="headings", height=12)

        for col in columns:
            self.records_tree.heading(col, text=col)
        self.records_tree.column("Timestamp", width=260)
        self.records_tree.column("Captured value (kg)", width=180)
        self.records_tree.column("Bottle category", width=220)
        self.records_tree.column("Remark", width=120)

        self.records_tree.tag_configure('oddrow', background='#F8F9FA')
        self.records_tree.tag_configure('evenrow', background='#FFFFFF')
        self.records_tree.pack(pady=(20, 18), padx=80, fill="both")

        # Three action buttons
        button_frame = ttk.Frame(self.tab_records)
        button_frame.pack(pady=8)
        ttk.Button(button_frame, text="Show records", command=self.show_records).grid(row=0, column=0, padx=15)
        ttk.Button(button_frame, text="Export to Excel", command=self.export_to_excel).grid(row=0, column=1, padx=15)
        ttk.Button(button_frame, text="Export to PDF", command=self.export_to_pdf).grid(row=0, column=2, padx=15)

    # ---------------- Helpers ----------------
    def get_categories(self):
        self.cursor.execute("SELECT name FROM categories")
        return [r[0] for r in self.cursor.fetchall()]

    def refresh_category_tree(self):
        for i in self.cat_tree.get_children():
            self.cat_tree.delete(i)
        self.cursor.execute("SELECT name, lower_limit, upper_limit FROM categories")
        for row in self.cursor.fetchall():
            self.cat_tree.insert("", tk.END, values=row)

    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            expected = ["Category", "Lower Limit", "Upper Limit"]
            if not all(c in df.columns for c in expected):
                messagebox.showerror("Error", "Missing columns in Excel file")
                return
            for _, r in df.iterrows():
                self.cursor.execute(
                    "INSERT OR REPLACE INTO categories (name, lower_limit, upper_limit) VALUES (?, ?, ?)",
                    (str(r["Category"]), float(r["Lower Limit"]), float(r["Upper Limit"]))
                )
            self.conn.commit()
            messagebox.showinfo("Success", "Categories updated successfully")
            self.refresh_category_tree()
            self.category_dropdown["values"] = self.get_categories()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- Live reading ----------------
    def display_remote_weight(self, weight, remark):
        self.weight_var.set(f"{weight:.4f} g")
        bg = "#28A745" if remark == "Pass" else PRIMARY_COLOR
        self.result_label.config(text=remark, bg=bg, fg="white")

    def setup_flask_routes(self):
        SCALE = self

        @self.app.route('/send_weight', methods=['GET'])
        def receive_weight():
            try:
                weight = float(request.args.get('weight'))
                category = SCALE.category_var.get()
                if not category:
                    return jsonify({"result": "fail", "error": "No category selected"}), 400

                SCALE.cursor.execute("SELECT lower_limit, upper_limit FROM categories WHERE name=?", (category,))
                limits = SCALE.cursor.fetchone()
                if not limits:
                    return jsonify({"result": "fail", "error": "Category not found"}), 400

                lo, hi = limits
                remark = "Pass" if lo <= weight <= hi else "Fail"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                SCALE.cursor.execute(
                    "INSERT INTO records (timestamp, weight, category, remark) VALUES (?, ?, ?, ?)",
                    (timestamp, weight, category, remark)
                )
                SCALE.conn.commit()

                SCALE.master.after(0, SCALE.display_remote_weight, weight, remark)
                return jsonify({"result": remark.lower()})
            except Exception as ex:
                return jsonify({"result": "fail", "error": str(ex)}), 400

    # ---------------- Records actions ----------------
    def _range_strings(self):
        from_dt = f"{self.from_date.get_date().strftime('%Y-%m-%d')} {self.from_time_hour.get()}:{self.from_time_minute.get()}:{self.from_time_second.get()}"
        to_dt   = f"{self.to_date.get_date().strftime('%Y-%m-%d')} {self.to_time_hour.get()}:{self.to_time_minute.get()}:{self.to_time_second.get()}"
        return from_dt, to_dt

    def _fetch_records(self, from_dt, to_dt):
        self.cursor.execute("""
            SELECT timestamp, weight, category, remark FROM records
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (from_dt, to_dt))
        return self.cursor.fetchall()

    def show_records(self):
        self.records_tree.delete(*self.records_tree.get_children())
        from_dt, to_dt = self._range_strings()
        rows = self._fetch_records(from_dt, to_dt)
        for i, row in enumerate(rows):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.records_tree.insert("", tk.END, values=row, tags=(tag,))

    def export_to_excel(self):
        from_dt, to_dt = self._range_strings()
        data = self._fetch_records(from_dt, to_dt)
        if not data:
            messagebox.showinfo("Info", "No data to export")
            return

        df = pd.DataFrame(data, columns=["Timestamp", "Captured value (kg)", "Bottle category", "Remark"])

        # Summary
        self.cursor.execute("""
            SELECT remark, COUNT(*) FROM records
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY remark
        """, (from_dt, to_dt))
        summary = {"Pass": 0, "Fail": 0}
        for remark, count in self.cursor.fetchall():
            summary[remark] = count

        summary_rows = [
            ["", "", "Summary", ""],
            ["", "", "Number of Pass", summary.get("Pass", 0)],
            ["", "", "Number of Fail", summary.get("Fail", 0)],
        ]
        out_df = pd.concat([df, pd.DataFrame(summary_rows, columns=df.columns)], ignore_index=True)

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        try:
            out_df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", "Data exported successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_to_pdf(self):
        from_dt, to_dt = self._range_strings()
        rows = self._fetch_records(from_dt, to_dt)
        if not rows:
            messagebox.showinfo("Info", "No data to export")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                filetypes=[("PDF files", "*.pdf")])
        if not out_path:
            return

        try:
            self._render_pdf(out_path, rows, from_dt, to_dt)
            messagebox.showinfo("Success", "PDF exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {e}")

    # ---------------- PDF rendering ----------------
    def _render_pdf(self, filepath, rows, from_dt, to_dt):
        page_w, page_h = A4
        margin_l = 15*mm
        margin_r = 15*mm
        margin_b = 18*mm

        header_h = 22*mm
        row_h = 8.5*mm
        max_rows_per_page = 20

        cols = [
            ("Timestamp", 0.34),
            ("Captured value (kg)", 0.20),
            ("Bottle category", 0.26),
            ("Remark", 0.20),
        ]
        table_w = page_w - margin_l - margin_r

        c = canvas.Canvas(filepath, pagesize=A4)

        try:
            coca_reader = ImageReader("coca_logo.png")
        except Exception:
            coca_reader = None
        try:
            bengal_reader = ImageReader("bengal_beverages.png")
        except Exception:
            bengal_reader = None

        def draw_header():
            c.setFillColor(colors.HexColor(PRIMARY_COLOR))
            c.rect(0, page_h - header_h, page_w, header_h, fill=1, stroke=0)

            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(margin_l, page_h - header_h + 12*mm, "Smart Weighing Scale — Report")
            c.setFont("Helvetica", 9)
            c.drawString(margin_l, page_h - header_h + 8*mm, f"From: {from_dt}   To: {to_dt}")
            c.drawString(margin_l, page_h - header_h + 4*mm, datetime.now().strftime("Generated: %Y-%m-%d %H:%M:%S"))

            if coca_reader:
                c.drawImage(coca_reader, page_w - margin_r - 35*mm, page_h - header_h + 5*mm,
                            width=35*mm, height=12*mm, mask='auto')
            if bengal_reader:
                c.drawImage(bengal_reader, page_w - margin_r - 50*mm, page_h - header_h + 5*mm,
                            width=12*mm, height=12*mm, mask='auto')

        def draw_table_header(y):
            c.setFillColor(colors.HexColor(PRIMARY_COLOR))
            c.rect(margin_l, y - row_h, table_w, row_h, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            x = margin_l
            for title, frac in cols:
                w = table_w * frac
                c.drawString(x + 2.5*mm, y - row_h + 2.8*mm, title)
                x += w

        def draw_row(y, row, odd):
            bg = colors.HexColor("#FFF5F6") if odd else colors.white
            c.setFillColor(bg)
            c.rect(margin_l, y - row_h, table_w, row_h, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            x = margin_l
            data = [str(row[0]), f"{row[1]:.4f}", str(row[2]), str(row[3])]
            for (title, frac), idx in zip(cols, range(len(cols))):
                w = table_w * frac
                c.drawString(x + 2.5*mm, y - row_h + 2.8*mm, data[idx])
                x += w

        total = len(rows)
        pages = (total + max_rows_per_page - 1) // max_rows_per_page

        idx = 0
        for p in range(pages):
            draw_header()
            y = page_h - header_h - 10*mm
            draw_table_header(y)
            y_start = y - 2

            for r in range(max_rows_per_page):
                if idx >= total:
                    break
                y_row = y_start - r*row_h
                draw_row(y_row, rows[idx], odd=bool(idx % 2))
                idx += 1

            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor(SUBTEXT_COLOR))
            c.drawRightString(page_w - margin_r, margin_b/2, f"Page {p+1}/{pages}")
            c.showPage()

        c.save()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartWeighingScale(root)
    root.mainloop()