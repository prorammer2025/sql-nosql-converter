#!/usr/bin/env python3
"""
SQL ↔ NoSQL Converter
A Tkinter desktop app to convert between relational (SQL INSERTs) and document-based (JSON) data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import re
import signal
from typing import List, Dict, Any, Optional

# Import converters — assumes `converter/__init__.py` exists
try:
    from converter.sql_to_nosql import parse_sql_inserts, sql_to_nosql
    from converter.nosql_to_sql import nosql_to_sql
except ImportError as e:
    messagebox.showerror("Import Error", f"Failed to load converter modules:\n{e}\n\n"
                         "Ensure 'converter/__init__.py' and submodules exist.")
    raise SystemExit(1)


class SQLNoSQLConverter:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔁 SQL ↔ NoSQL Converter • Portfolio Tool")
        self.root.geometry("950x620")
        self.root.minsize(800, 500)

        # State
        self.dark_mode = False
        self.converted_data: str = ""
        self.setup_styles()
        self.create_widgets()

        # Bind safe close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self) -> None:
        """Configure UI theme (light/dark)."""
        style = ttk.Style()
        if self.dark_mode:
            style.theme_use('clam')
            bg, fg, btn_bg = '#1e1e1e', '#ffffff', '#3a3a3a'
            style.configure('.', background=bg, foreground=fg)
            style.configure('TFrame', background=bg)
            style.configure('TLabelframe', background=bg, foreground=fg)
            style.configure('TLabelframe.Label', background=bg, foreground=fg)
            style.configure('TButton', background=btn_bg, foreground=fg)
            style.map('TButton', background=[('active', '#505050')])
            self.text_bg, self.text_fg = '#2d2d2d', '#cccccc'
        else:
            style.theme_use('default')
            self.text_bg, self.text_fg = 'white', 'black'

    def create_widgets(self) -> None:
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="📂 Open SQL...", command=self.open_sql_file)
        file_menu.add_command(label="📂 Open JSON...", command=self.open_json_file)
        file_menu.add_command(label="💾 Save Result As...", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.on_closing)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="🌓 Toggle Dark/Light Mode", command=self.toggle_theme)

        # --- Input Section ---
        input_frame = ttk.LabelFrame(self.root, text="📥 Input Data")
        input_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.input_text = tk.Text(
            input_frame, 
            wrap="word", 
            font=("Consolas", 10),
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground=self.text_fg
        )
        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=self.input_text.yview)
        self.input_text.config(yscrollcommand=input_scroll.set)
        self.input_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        input_scroll.pack(side="right", fill="y", pady=5)

        # --- Control Buttons ---
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(ctrl_frame, text="🧪 Load Sample SQL", command=self.load_sample_sql).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="🧪 Load Sample JSON", command=self.load_sample_json).pack(side="left", padx=2)

        ttk.Label(ctrl_frame, text="Group by key:").pack(side="left", padx=(20, 2))
        self.group_key = ttk.Entry(ctrl_frame, width=12)
        self.group_key.pack(side="left", padx=2)
        self.group_key.insert(0, "order_id")

        ttk.Label(ctrl_frame, text="Nest key:").pack(side="left", padx=(10, 2))
        self.nest_key = ttk.Entry(ctrl_frame, width=12)
        self.nest_key.pack(side="left", padx=2)
        self.nest_key.insert(0, "item_id")

        # --- Convert Buttons ---
        conv_frame = ttk.Frame(self.root)
        conv_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            conv_frame, 
            text="➡️ Convert: SQL → NoSQL (JSON)", 
            command=self.convert_sql_to_nosql
        ).pack(side="left", expand=True, fill="x", padx=2)

        ttk.Button(
            conv_frame, 
            text="⬅️ Convert: NoSQL (JSON) → SQL", 
            command=self.convert_nosql_to_sql
        ).pack(side="left", expand=True, fill="x", padx=2)

        # --- Output Section ---
        output_frame = ttk.LabelFrame(self.root, text="📤 Converted Output")
        output_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.output_text = tk.Text(
            output_frame,
            wrap="word",
            font=("Consolas", 10),
            bg=self.text_bg,
            fg=self.text_fg,
            insertbackground=self.text_fg
        )
        out_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.config(yscrollcommand=out_scroll.set)
        self.output_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        out_scroll.pack(side="right", fill="y", pady=5)

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self.setup_styles()
        # Update text widget colors
        self.input_text.config(bg=self.text_bg, fg=self.text_fg, insertbackground=self.text_fg)
        self.output_text.config(bg=self.text_bg, fg=self.text_fg, insertbackground=self.text_fg)

    # ======================
    # DATA LOADING
    # ======================
    def load_sample_sql(self) -> None:
        sample = """-- Sample e-commerce data: orders + items
INSERT INTO orders (order_id, customer_id, order_date, status) VALUES (1, 101, '2025-11-25', 'shipped');
INSERT INTO orders (order_id, customer_id, order_date, status) VALUES (2, 102, '2025-11-26', 'processing');
INSERT INTO order_items (item_id, order_id, product_name, quantity, price) VALUES (1001, 1, 'Wireless Keyboard', 1, 49.99);
INSERT INTO order_items (item_id, order_id, product_name, quantity, price) VALUES (1002, 1, 'USB-C Hub', 2, 29.99);
INSERT INTO order_items (item_id, order_id, product_name, quantity, price) VALUES (1003, 2, 'Mechanical Mouse', 1, 34.50);"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, sample.strip())

    def load_sample_json(self) -> None:
        sample = [
            {
                "order_id": 1,
                "customer_id": 101,
                "order_date": "2025-11-25",
                "status": "shipped",
                "items": [
                    {"item_id": 1001, "product": "Wireless Keyboard", "qty": 1},
                    {"item_id": 1002, "product": "USB-C Hub", "qty": 2}
                ]
            },
            {
                "order_id": 2,
                "customer_id": 102,
                "order_date": "2025-11-26",
                "status": "processing",
                "items": [
                    {"item_id": 1003, "product": "Mechanical Mouse", "qty": 1}
                ]
            }
        ]
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, json.dumps(sample, indent=2))

    def open_sql_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open SQL File",
            filetypes=[("SQL Files", "*.sql"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self._load_file(path)

    def open_json_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, content)
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to read {path}:\n{e}")

    # ======================
    # CONVERSION LOGIC
    # ======================
    def convert_sql_to_nosql(self) -> None:
        raw = self.input_text.get(1.0, tk.END).strip()
        if not raw:
            messagebox.showwarning("⚠️ Input Required", "Please enter SQL INSERT statements.")
            return

        try:
            data = parse_sql_inserts(raw)
            if not data:
                messagebox.showinfo("ℹ️ Info", "No INSERT statements parsed. Try 'Load Sample SQL'.")
                return

            gk = self.group_key.get().strip() or None
            nk = self.nest_key.get().strip() or None

            result = sql_to_nosql(data, group_key=gk, nest_key=nk)
            self.converted_data = json.dumps(result, indent=2, ensure_ascii=False)
            
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, self.converted_data)
            messagebox.showinfo("✅ Success", f"Converted {len(data)} SQL rows → {len(result)} JSON doc(s).")

        except Exception as e:
            messagebox.showerror("❌ Conversion Error", f"SQL → NoSQL failed:\n{type(e).__name__}: {e}")

    def convert_nosql_to_sql(self) -> None:
        raw = self.input_text.get(1.0, tk.END).strip()
        if not raw:
            messagebox.showwarning("⚠️ Input Required", "Please enter JSON data.")
            return

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]  # Normalize single doc to list

            result = nosql_to_sql(data, table_name="converted_data")
            self.converted_data = result

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, self.converted_data)
            messagebox.showinfo("✅ Success", f"Converted {len(data)} JSON doc(s) → SQL statements.")

        except json.JSONDecodeError as e:
            messagebox.showerror("❌ JSON Error", f"Invalid JSON:\nLine {e.lineno}, Col {e.colno}\n{e.msg}")
        except Exception as e:
            messagebox.showerror("❌ Conversion Error", f"NoSQL → SQL failed:\n{type(e).__name__}: {e}")

    # ======================
    # FILE I/O
    # ======================
    def save_result(self) -> None:
        if not self.converted_data.strip():
            messagebox.showwarning("⚠️ No Data", "Nothing to save — run a conversion first.")
            return

        default_ext = ".json" if self.converted_data.strip().startswith("[") or self.converted_data.strip().startswith("{") else ".sql"
        path = filedialog.asksaveasfilename(
            title="Save Converted Data",
            defaultextension=default_ext,
            filetypes=[
                ("JSON Files", "*.json"),
                ("SQL Files", "*.sql"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.converted_data)
                messagebox.showinfo("✅ Saved", f"Data saved to:\n{os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("❌ Save Error", f"Failed to save file:\n{e}")

    # ======================
    # SHUTDOWN SAFETY
    # ======================
    def on_closing(self) -> None:
        """Safely close the application."""
        try:
            # Optional: ask for confirmation
            # if not messagebox.askokcancel("Quit", "Are you sure you want to exit?"):
            #     return
            self.root.quit()  # Stops mainloop
            self.root.destroy()  # Destroys widgets
        except tk.TclError:
            # Window already destroyed (e.g. rapid double-click on [X])
            pass


# ======================
# ENTRY POINT
# ======================
def main() -> None:
    root = tk.Tk()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        root.quit()
    signal.signal(signal.SIGINT, signal_handler)

    # Start app
    app = SQLNoSQLConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()