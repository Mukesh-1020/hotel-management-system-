"""
HOTEL MANAGEMENT SYSTEM
Class 12 Computer Science Project
Python + MySQL + Tkinter

Setup:
    pip install mysql-connector-python
    Edit DB_CONFIG below with your MySQL username and password.
    python hotel_management.py

The database and tables are created automatically on first run.
Default login:  admin / admin123
"""

import hashlib
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk, messagebox

import mysql.connector

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
}
DB_NAME = "hotel_db"
HOTEL_NAME = "Grand Palace Hotel"
ROOM_TYPES = ["Single", "Double", "Deluxe", "Suite"]


# ------------------------------------------------------------------
# DATABASE LAYER
# ------------------------------------------------------------------
class Database:
    def __init__(self):
        self.con = mysql.connector.connect(**DB_CONFIG)
        self.cur = self.con.cursor()
        self.cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        self.cur.execute(f"USE {DB_NAME}")
        self.create_tables()

    def create_tables(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(30) PRIMARY KEY,
                password VARCHAR(64) NOT NULL)"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS rooms (
                room_no INT PRIMARY KEY,
                room_type VARCHAR(20) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                status VARCHAR(15) NOT NULL DEFAULT 'Available')"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS customers (
                cust_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(60) NOT NULL,
                phone VARCHAR(15) NOT NULL,
                email VARCHAR(60),
                address VARCHAR(120),
                id_proof VARCHAR(40))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                cust_id INT NOT NULL,
                room_no INT NOT NULL,
                check_in DATE NOT NULL,
                check_out DATE,
                days INT,
                total DECIMAL(10,2),
                status VARCHAR(15) NOT NULL DEFAULT 'Checked-In',
                FOREIGN KEY (cust_id) REFERENCES customers(cust_id),
                FOREIGN KEY (room_no) REFERENCES rooms(room_no))"""
        )
        # default admin
        self.cur.execute("SELECT COUNT(*) FROM users")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute(
                "INSERT INTO users VALUES (%s, %s)",
                ("admin", hash_pw("admin123")),
            )
        # sample rooms
        self.cur.execute("SELECT COUNT(*) FROM rooms")
        if self.cur.fetchone()[0] == 0:
            sample = [
                (101, "Single", 1500), (102, "Single", 1500),
                (201, "Double", 2500), (202, "Double", 2500),
                (301, "Deluxe", 4000), (401, "Suite", 7000),
            ]
            self.cur.executemany(
                "INSERT INTO rooms (room_no, room_type, price) VALUES (%s,%s,%s)",
                sample,
            )
        self.con.commit()

    def query(self, sql, params=()):
        """Run a SELECT and return all rows."""
        self.cur.execute(sql, params)
        return self.cur.fetchall()

    def execute(self, sql, params=()):
        """Run INSERT/UPDATE/DELETE and commit."""
        self.cur.execute(sql, params)
        self.con.commit()
        return self.cur.lastrowid


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def make_tree(parent, columns, widths, height=10):
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return frame, tree


def fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=r)


# ------------------------------------------------------------------
# LOGIN WINDOW
# ------------------------------------------------------------------
class LoginWindow:
    def __init__(self, root, db, on_success):
        self.root, self.db, self.on_success = root, db, on_success
        root.title(f"{HOTEL_NAME} - Login")
        root.geometry("380x300")
        root.resizable(False, False)

        self.frame = ttk.Frame(root, padding=30)
        self.frame.pack(fill="both", expand=True)
        ttk.Label(self.frame, text=HOTEL_NAME, font=("Helvetica", 16, "bold")).pack(pady=(0, 5))
        ttk.Label(self.frame, text="Staff Login").pack(pady=(0, 20))

        ttk.Label(self.frame, text="Username").pack(anchor="w")
        self.user = ttk.Entry(self.frame, width=30)
        self.user.pack(pady=(0, 10))
        ttk.Label(self.frame, text="Password").pack(anchor="w")
        self.pw = ttk.Entry(self.frame, width=30, show="*")
        self.pw.pack(pady=(0, 15))
        ttk.Button(self.frame, text="Login", command=self.login).pack()
        root.bind("<Return>", lambda e: self.login())
        self.user.focus()

    def login(self):
        rows = self.db.query(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (self.user.get().strip(), hash_pw(self.pw.get())),
        )
        if rows:
            self.root.unbind("<Return>")
            self.frame.destroy()
            self.on_success()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")


# ------------------------------------------------------------------
# MAIN APPLICATION
# ------------------------------------------------------------------
class HotelApp:
    def __init__(self, root, db):
        self.root, self.db = root, db
        root.title(f"{HOTEL_NAME} - Management System")
        root.geometry("950x620")
        root.resizable(True, True)

        ttk.Label(root, text=HOTEL_NAME.upper(), font=("Helvetica", 18, "bold")).pack(pady=8)

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab_dash = ttk.Frame(self.nb)
        self.tab_rooms = ttk.Frame(self.nb)
        self.tab_cust = ttk.Frame(self.nb)
        self.tab_in = ttk.Frame(self.nb)
        self.tab_out = ttk.Frame(self.nb)
        self.tab_book = ttk.Frame(self.nb)
        for tab, name in [
            (self.tab_dash, "Dashboard"), (self.tab_rooms, "Rooms"),
            (self.tab_cust, "Customers"), (self.tab_in, "Check-In"),
            (self.tab_out, "Check-Out"), (self.tab_book, "Bookings"),
        ]:
            self.nb.add(tab, text=name)

        self.build_dashboard()
        self.build_rooms()
        self.build_customers()
        self.build_checkin()
        self.build_checkout()
        self.build_bookings()

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())
        self.refresh_all()

    def refresh_all(self):
        self.load_dashboard()
        self.load_rooms()
        self.load_customers()
        self.load_checkin_lists()
        self.load_checkout_list()
        self.load_bookings()

    # ---------------- DASHBOARD ----------------
    def build_dashboard(self):
        self.dash_labels = {}
        grid = ttk.Frame(self.tab_dash, padding=30)
        grid.pack(expand=True)
        items = ["Total Rooms", "Available Rooms", "Occupied Rooms",
                 "Total Customers", "Active Bookings", "Total Revenue (Rs.)"]
        for i, name in enumerate(items):
            box = ttk.LabelFrame(grid, text=name, padding=20)
            box.grid(row=i // 3, column=i % 3, padx=15, pady=15, sticky="nsew")
            lbl = ttk.Label(box, text="0", font=("Helvetica", 22, "bold"))
            lbl.pack()
            self.dash_labels[name] = lbl

    def load_dashboard(self):
        q = self.db.query
        vals = {
            "Total Rooms": q("SELECT COUNT(*) FROM rooms")[0][0],
            "Available Rooms": q("SELECT COUNT(*) FROM rooms WHERE status='Available'")[0][0],
            "Occupied Rooms": q("SELECT COUNT(*) FROM rooms WHERE status='Occupied'")[0][0],
            "Total Customers": q("SELECT COUNT(*) FROM customers")[0][0],
            "Active Bookings": q("SELECT COUNT(*) FROM bookings WHERE status='Checked-In'")[0][0],
            "Total Revenue (Rs.)": q("SELECT IFNULL(SUM(total),0) FROM bookings WHERE status='Checked-Out'")[0][0],
        }
        for k, v in vals.items():
            self.dash_labels[k].config(text=str(v))

    # ---------------- ROOMS ----------------
    def build_rooms(self):
        form = ttk.LabelFrame(self.tab_rooms, text="Room Details", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Room No").grid(row=0, column=0, padx=5, pady=5)
        self.r_no = ttk.Entry(form, width=12)
        self.r_no.grid(row=0, column=1, padx=5)
        ttk.Label(form, text="Type").grid(row=0, column=2, padx=5)
        self.r_type = ttk.Combobox(form, values=ROOM_TYPES, state="readonly", width=12)
        self.r_type.grid(row=0, column=3, padx=5)
        self.r_type.current(0)
        ttk.Label(form, text="Price / Night").grid(row=0, column=4, padx=5)
        self.r_price = ttk.Entry(form, width=12)
        self.r_price.grid(row=0, column=5, padx=5)

        btns = ttk.Frame(form)
        btns.grid(row=1, column=0, columnspan=6, pady=8)
        ttk.Button(btns, text="Add", command=self.add_room).pack(side="left", padx=5)
        ttk.Button(btns, text="Update", command=self.update_room).pack(side="left", padx=5)
        ttk.Button(btns, text="Delete", command=self.delete_room).pack(side="left", padx=5)
        ttk.Button(btns, text="Clear", command=self.clear_room).pack(side="left", padx=5)

        frame, self.room_tree = make_tree(
            self.tab_rooms, ("Room No", "Type", "Price", "Status"), (100, 150, 120, 120), 12
        )
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.room_tree.bind("<<TreeviewSelect>>", self.pick_room)

    def load_rooms(self):
        fill_tree(self.room_tree, self.db.query(
            "SELECT room_no, room_type, price, status FROM rooms ORDER BY room_no"))

    def pick_room(self, _=None):
        sel = self.room_tree.selection()
        if not sel:
            return
        v = self.room_tree.item(sel[0])["values"]
        self.r_no.config(state="normal")
        self.r_no.delete(0, "end"); self.r_no.insert(0, v[0])
        self.r_type.set(v[1])
        self.r_price.delete(0, "end"); self.r_price.insert(0, v[2])

    def clear_room(self):
        self.r_no.config(state="normal")
        self.r_no.delete(0, "end")
        self.r_price.delete(0, "end")
        self.r_type.current(0)

    def add_room(self):
        try:
            no = int(self.r_no.get()); price = float(self.r_price.get())
        except ValueError:
            return messagebox.showerror("Error", "Room number and price must be numbers")
        if price <= 0:
            return messagebox.showerror("Error", "Price must be greater than 0")
        try:
            self.db.execute("INSERT INTO rooms (room_no, room_type, price) VALUES (%s,%s,%s)",
                            (no, self.r_type.get(), price))
        except mysql.connector.IntegrityError:
            return messagebox.showerror("Error", "Room number already exists")
        self.clear_room(); self.refresh_all()

    def update_room(self):
        try:
            no = int(self.r_no.get()); price = float(self.r_price.get())
        except ValueError:
            return messagebox.showerror("Error", "Select a room and enter a valid price")
        self.db.execute("UPDATE rooms SET room_type=%s, price=%s WHERE room_no=%s",
                        (self.r_type.get(), price, no))
        self.refresh_all()

    def delete_room(self):
        try:
            no = int(self.r_no.get())
        except ValueError:
            return messagebox.showerror("Error", "Select a room first")
        row = self.db.query("SELECT status FROM rooms WHERE room_no=%s", (no,))
        if not row:
            return messagebox.showerror("Error", "Room not found")
        if row[0][0] == "Occupied":
            return messagebox.showerror("Error", "Cannot delete an occupied room")
        if self.db.query("SELECT 1 FROM bookings WHERE room_no=%s LIMIT 1", (no,)):
            return messagebox.showerror("Error", "Room has booking history and cannot be deleted")
        if messagebox.askyesno("Confirm", f"Delete room {no}?"):
            self.db.execute("DELETE FROM rooms WHERE room_no=%s", (no,))
            self.clear_room(); self.refresh_all()

    # ---------------- CUSTOMERS ----------------
    def build_customers(self):
        form = ttk.LabelFrame(self.tab_cust, text="Customer Details", padding=10)
        form.pack(fill="x", padx=10, pady=10)
        self.c_id = None
        labels = ["Name", "Phone", "Email", "Address", "ID Proof"]
        self.c_entries = {}
        for i, lab in enumerate(labels):
            r, c = divmod(i, 3)
            ttk.Label(form, text=lab).grid(row=r, column=c * 2, padx=5, pady=5, sticky="e")
            e = ttk.Entry(form, width=24)
            e.grid(row=r, column=c * 2 + 1, padx=5)
            self.c_entries[lab] = e

        btns = ttk.Frame(form)
        btns.grid(row=2, column=0, columnspan=6, pady=8)
        ttk.Button(btns, text="Add", command=self.add_customer).pack(side="left", padx=5)
        ttk.Button(btns, text="Update", command=self.update_customer).pack(side="left", padx=5)
        ttk.Button(btns, text="Delete", command=self.delete_customer).pack(side="left", padx=5)
        ttk.Button(btns, text="Clear", command=self.clear_customer).pack(side="left", padx=5)

        sf = ttk.Frame(self.tab_cust)
        sf.pack(fill="x", padx=10)
        ttk.Label(sf, text="Search (name/phone):").pack(side="left")
        self.c_search = ttk.Entry(sf, width=25)
        self.c_search.pack(side="left", padx=5)
        self.c_search.bind("<KeyRelease>", lambda e: self.load_customers())

        frame, self.cust_tree = make_tree(
            self.tab_cust, ("ID", "Name", "Phone", "Email", "Address", "ID Proof"),
            (50, 150, 110, 160, 200, 120), 10)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.cust_tree.bind("<<TreeviewSelect>>", self.pick_customer)

    def load_customers(self):
        s = f"%{self.c_search.get().strip()}%"
        fill_tree(self.cust_tree, self.db.query(
            "SELECT cust_id, name, phone, email, address, id_proof FROM customers "
            "WHERE name LIKE %s OR phone LIKE %s ORDER BY cust_id", (s, s)))

    def pick_customer(self, _=None):
        sel = self.cust_tree.selection()
        if not sel:
            return
        v = self.cust_tree.item(sel[0])["values"]
        self.c_id = v[0]
        for lab, val in zip(["Name", "Phone", "Email", "Address", "ID Proof"], v[1:]):
            self.c_entries[lab].delete(0, "end")
            self.c_entries[lab].insert(0, val)

    def clear_customer(self):
        self.c_id = None
        for e in self.c_entries.values():
            e.delete(0, "end")

    def customer_data(self):
        d = {k: e.get().strip() for k, e in self.c_entries.items()}
        if not d["Name"] or not d["Phone"]:
            messagebox.showerror("Error", "Name and phone are required")
            return None
        if not d["Phone"].isdigit() or len(d["Phone"]) < 10:
            messagebox.showerror("Error", "Enter a valid phone number (digits only, min 10)")
            return None
        return d

    def add_customer(self):
        d = self.customer_data()
        if not d:
            return
        self.db.execute(
            "INSERT INTO customers (name, phone, email, address, id_proof) VALUES (%s,%s,%s,%s,%s)",
            (d["Name"], d["Phone"], d["Email"], d["Address"], d["ID Proof"]))
        self.clear_customer(); self.refresh_all()

    def update_customer(self):
        if self.c_id is None:
            return messagebox.showerror("Error", "Select a customer first")
        d = self.customer_data()
        if not d:
            return
        self.db.execute(
            "UPDATE customers SET name=%s, phone=%s, email=%s, address=%s, id_proof=%s WHERE cust_id=%s",
            (d["Name"], d["Phone"], d["Email"], d["Address"], d["ID Proof"], self.c_id))
        self.refresh_all()

    def delete_customer(self):
        if self.c_id is None:
            return messagebox.showerror("Error", "Select a customer first")
        if self.db.query("SELECT 1 FROM bookings WHERE cust_id=%s LIMIT 1", (self.c_id,)):
            return messagebox.showerror("Error", "Customer has booking history and cannot be deleted")
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            self.db.execute("DELETE FROM customers WHERE cust_id=%s", (self.c_id,))
            self.clear_customer(); self.refresh_all()

    # ---------------- CHECK-IN ----------------
    def build_checkin(self):
        form = ttk.LabelFrame(self.tab_in, text="New Check-In", padding=20)
        form.pack(padx=20, pady=30)

        ttk.Label(form, text="Customer").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.ci_cust = ttk.Combobox(form, width=40, state="readonly")
        self.ci_cust.grid(row=0, column=1)

        ttk.Label(form, text="Available Room").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ci_room = ttk.Combobox(form, width=40, state="readonly")
        self.ci_room.grid(row=1, column=1)

        ttk.Label(form, text="Check-In Date").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.ci_date = ttk.Entry(form, width=20)
        self.ci_date.grid(row=2, column=1, sticky="w")
        ttk.Label(form, text="(YYYY-MM-DD)").grid(row=2, column=1, sticky="e")

        ttk.Button(form, text="Check In", command=self.do_checkin).grid(row=3, column=0, columnspan=2, pady=15)

    def load_checkin_lists(self):
        custs = self.db.query("SELECT cust_id, name, phone FROM customers ORDER BY name")
        self.ci_cust["values"] = [f"{c[0]} - {c[1]} ({c[2]})" for c in custs]
        rooms = self.db.query(
            "SELECT room_no, room_type, price FROM rooms WHERE status='Available' ORDER BY room_no")
        self.ci_room["values"] = [f"{r[0]} - {r[1]} (Rs.{r[2]}/night)" for r in rooms]
        if not self.ci_date.get():
            self.ci_date.insert(0, date.today().isoformat())

    def do_checkin(self):
        if not self.ci_cust.get() or not self.ci_room.get():
            return messagebox.showerror("Error", "Select a customer and a room")
        try:
            d = datetime.strptime(self.ci_date.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            return messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
        cust_id = int(self.ci_cust.get().split(" - ")[0])
        room_no = int(self.ci_room.get().split(" - ")[0])
        self.db.execute(
            "INSERT INTO bookings (cust_id, room_no, check_in) VALUES (%s,%s,%s)",
            (cust_id, room_no, d))
        self.db.execute("UPDATE rooms SET status='Occupied' WHERE room_no=%s", (room_no,))
        messagebox.showinfo("Success", f"Room {room_no} checked in successfully")
        self.ci_cust.set(""); self.ci_room.set("")
        self.refresh_all()

    # ---------------- CHECK-OUT ----------------
    def build_checkout(self):
        top = ttk.Label(self.tab_out, text="Select a guest and click Check Out to generate the bill")
        top.pack(pady=10)
        frame, self.out_tree = make_tree(
            self.tab_out, ("Booking ID", "Customer", "Room", "Type", "Check-In", "Price/Night"),
            (90, 180, 80, 100, 110, 110), 12)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Button(self.tab_out, text="Check Out & Generate Bill",
                   command=self.do_checkout).pack(pady=10)

    def load_checkout_list(self):
        fill_tree(self.out_tree, self.db.query(
            """SELECT b.booking_id, c.name, b.room_no, r.room_type, b.check_in, r.price
               FROM bookings b JOIN customers c ON b.cust_id=c.cust_id
               JOIN rooms r ON b.room_no=r.room_no
               WHERE b.status='Checked-In' ORDER BY b.booking_id"""))

    def do_checkout(self):
        sel = self.out_tree.selection()
        if not sel:
            return messagebox.showerror("Error", "Select a booking first")
        bid, name, room, rtype, cin, price = self.out_tree.item(sel[0])["values"]
        cin_date = datetime.strptime(str(cin), "%Y-%m-%d").date()
        today = date.today()
        days = max(1, (today - cin_date).days)
        price = float(price)
        subtotal = days * price
        gst = round(subtotal * 0.12, 2)
        total = round(subtotal + gst, 2)

        bill = (
            f"{HOTEL_NAME}\n{'=' * 36}\n"
            f"Booking ID : {bid}\nGuest      : {name}\n"
            f"Room       : {room} ({rtype})\n"
            f"Check-In   : {cin_date}\nCheck-Out  : {today}\n"
            f"Nights     : {days}\nRate/Night : Rs. {price:.2f}\n"
            f"{'-' * 36}\nSubtotal   : Rs. {subtotal:.2f}\n"
            f"GST (12%)  : Rs. {gst:.2f}\n{'-' * 36}\n"
            f"TOTAL      : Rs. {total:.2f}\n{'=' * 36}\nThank you for staying with us!"
        )
        if not messagebox.askyesno("Confirm Check-Out", bill + "\n\nConfirm check-out?"):
            return
        self.db.execute(
            "UPDATE bookings SET check_out=%s, days=%s, total=%s, status='Checked-Out' WHERE booking_id=%s",
            (today, days, total, bid))
        self.db.execute("UPDATE rooms SET status='Available' WHERE room_no=%s", (room,))
        self.show_bill(bill)
        self.refresh_all()

    def show_bill(self, text):
        win = tk.Toplevel(self.root)
        win.title("Bill")
        t = tk.Text(win, width=42, height=18, font=("Courier", 11))
        t.insert("1.0", text)
        t.config(state="disabled")
        t.pack(padx=10, pady=10)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ---------------- BOOKINGS ----------------
    def build_bookings(self):
        sf = ttk.Frame(self.tab_book)
        sf.pack(fill="x", padx=10, pady=10)
        ttk.Label(sf, text="Filter:").pack(side="left")
        self.b_filter = ttk.Combobox(sf, values=["All", "Checked-In", "Checked-Out"],
                                     state="readonly", width=15)
        self.b_filter.current(0)
        self.b_filter.pack(side="left", padx=5)
        self.b_filter.bind("<<ComboboxSelected>>", lambda e: self.load_bookings())

        frame, self.book_tree = make_tree(
            self.tab_book,
            ("ID", "Customer", "Room", "Check-In", "Check-Out", "Days", "Total", "Status"),
            (50, 150, 70, 100, 100, 60, 100, 100), 15)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

    def load_bookings(self):
        f = self.b_filter.get()
        sql = ("SELECT b.booking_id, c.name, b.room_no, b.check_in, b.check_out, "
               "b.days, b.total, b.status FROM bookings b "
               "JOIN customers c ON b.cust_id=c.cust_id ")
        if f == "All":
            rows = self.db.query(sql + "ORDER BY b.booking_id DESC")
        else:
            rows = self.db.query(sql + "WHERE b.status=%s ORDER BY b.booking_id DESC", (f,))
        fill_tree(self.book_tree, rows)


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    root = tk.Tk()
    try:
        db = Database()
    except mysql.connector.Error as err:
        messagebox.showerror(
            "Database Error",
            f"Could not connect to MySQL:\n{err}\n\nCheck DB_CONFIG at the top of the file.")
        return

    def start_app():
        root.geometry("950x620")
        HotelApp(root, db)

    LoginWindow(root, db, start_app)
    root.mainloop()


if __name__ == "__main__":
    main()
