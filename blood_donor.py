# ============================================================
#  BLOOD DONOR FINDER
#  Front end : Tkinter        Back end : SQLite database
#  Run       : python3 blood_donor.py
# ============================================================

import os                                        # to find the folder this file is in
import sqlite3                                   # built-in database
import tkinter as tk                             # the GUI library
from tkinter import ttk, messagebox              # nicer widgets + popup boxes
from datetime import date, datetime, timedelta   # to work with donation dates

# ---------------- Settings ----------------
BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

# patient's blood group -> donor groups the patient can safely RECEIVE from
CAN_RECEIVE_FROM = {
    "O-":  ["O-"],
    "O+":  ["O-", "O+"],
    "A-":  ["O-", "A-"],
    "A+":  ["O-", "O+", "A-", "A+"],
    "B-":  ["O-", "B-"],
    "B+":  ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],   # can receive from everyone
}

# days a donor must wait after donating before they can donate again
GAP_DAYS = {"Male": 90, "Female": 120}

# colours used in the app
RED = "#b91c1c"           # header and main buttons
LIGHT_RED = "#fee2e2"     # compatible cells in the chart
GREEN_ROW = "#dcfce7"     # donors who can donate now
GREY_ROW = "#f3f4f6"      # donors who must wait
WHITE = "#ffffff"
TEXT = "#1f2937"          # dark grey text
MUTED = "#6b7280"         # light grey text
LINE_GREY = "#e5e7eb"     # map lines that are not lit up

# ---------------- Back end: database ----------------
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donors.db")
conn = sqlite3.connect(DB_FILE)                  # open (or create) the database file
cursor = conn.cursor()                           # cursor runs SQL commands

cursor.execute("""
    CREATE TABLE IF NOT EXISTS donors (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT,
        age           INTEGER,
        gender        TEXT,
        blood_group   TEXT,
        phone         TEXT,
        city          TEXT,
        last_donation TEXT          -- date as YYYY-MM-DD, or '' if never donated
    )
""")
conn.commit()

# sample donors so the app is not empty the first time: (..., days since last donation)
SAMPLE_DONORS = [
    ("Arun Kumar", 25, "Male", "O+", "9876543210", "Chennai", 120),
    ("Priya Sharma", 22, "Female", "A+", "9876543211", "Chennai", 30),
    ("Rahul Verma", 30, "Male", "B+", "9876543212", "Bangalore", None),
    ("Meena Iyer", 28, "Female", "O-", "9876543213", "Chennai", 200),
    ("Karthik Raja", 35, "Male", "AB+", "9876543214", "Coimbatore", 45),
    ("Sneha Reddy", 24, "Female", "B-", "9876543215", "Hyderabad", None),
    ("Vikram Singh", 40, "Male", "A-", "9876543216", "Chennai", 95),
    ("Divya Nair", 27, "Female", "AB-", "9876543217", "Kochi", 150),
    ("Suresh Babu", 45, "Male", "O+", "9876543218", "Chennai", 60),
    ("Anjali Gupta", 21, "Female", "O+", "9876543219", "Bangalore", 100),
    ("Mohammed Irfan", 33, "Male", "B+", "9876543220", "Chennai", 10),
    ("Lakshmi Devi", 38, "Female", "A+", "9876543221", "Madurai", 130),
]


def add_sample_donors():
    """Fill the database with sample donors, but only if it is empty."""
    cursor.execute("SELECT COUNT(*) FROM donors")
    if cursor.fetchone()[0] > 0:
        return
    for name, age, gender, group, phone, city, days_ago in SAMPLE_DONORS:
        if days_ago is None:
            last = ""                                                    # never donated
        else:
            last = (date.today() - timedelta(days=days_ago)).isoformat()  # e.g. "2026-07-20"
        cursor.execute("INSERT INTO donors (name, age, gender, blood_group, phone, city, last_donation) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?)", (name, age, gender, group, phone, city, last))
    conn.commit()


# ---------------- Logic ----------------

def days_left(gender, last_donation):
    """How many more days this donor must wait. 0 means they can donate today."""
    if last_donation == "":
        return 0                                                     # never donated -> can donate
    days_passed = (date.today() - date.fromisoformat(last_donation)).days
    return max(0, GAP_DAYS[gender] - days_passed)


def register_donor():
    """Check the form, then save the new donor in the database."""
    name = name_entry.get().strip()
    age_text = age_entry.get().strip()
    phone = phone_entry.get().strip()
    city = city_entry.get().strip().title()       # "chennai" -> "Chennai"
    last_text = last_entry.get().strip()

    if name == "" or city == "":
        messagebox.showerror("Missing details", "Please fill in the name and city.")
        return
    if not age_text.isdigit() or not 18 <= int(age_text) <= 65:
        messagebox.showerror("Wrong age", "A donor must be between 18 and 65 years old.")
        return
    if not (phone.isdigit() and len(phone) == 10):
        messagebox.showerror("Wrong phone", "The phone number must have exactly 10 digits.")
        return

    last_donation = ""                            # blank = never donated
    if last_text != "":
        try:
            last_day = datetime.strptime(last_text, "%d-%m-%Y").date()
        except ValueError:
            messagebox.showerror("Wrong date", "Enter the date as DD-MM-YYYY, for example 05-08-2026.")
            return
        if last_day > date.today():
            messagebox.showerror("Wrong date", "The last donation date can't be in the future.")
            return
        last_donation = last_day.isoformat()

    cursor.execute("INSERT INTO donors (name, age, gender, blood_group, phone, city, last_donation) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (name, int(age_text), gender_var.get(), group_box.get(), phone, city, last_donation))
    conn.commit()
    messagebox.showinfo("Registered", f"{name} ({group_box.get()}) is now a registered donor. Thank you!")
    clear_form()
    refresh_all()


def clear_form():
    """Empty every box in the registration form."""
    for entry in (name_entry, age_entry, phone_entry, city_entry, last_entry):
        entry.delete(0, tk.END)
    gender_var.set("Male")
    group_box.current(0)


def search_donors(event=None):
    """Show every donor whose blood the patient can receive, best first."""
    need = need_var.get()
    city = city_search.get().strip()
    groups = CAN_RECEIVE_FROM[need]                       # e.g. A+ -> ["O-", "O+", "A-", "A+"]
    marks = ", ".join("?" * len(groups))                  # "?, ?, ?, ?" for the SQL query

    sql = f"SELECT id, name, blood_group, gender, city, phone, last_donation FROM donors WHERE blood_group IN ({marks})"
    values = list(groups)
    if city != "":                                        # optional city filter
        sql += " AND city LIKE ?"
        values.append(f"%{city}%")
    cursor.execute(sql, values)
    donors = cursor.fetchall()
    donors.sort(key=lambda d: days_left(d[3], d[6]))      # donors who can give now come first

    results.delete(*results.get_children())               # clear the old table rows
    ready = 0
    for donor_id, name, group, gender, place, phone, last in donors:
        wait = days_left(gender, last)
        if wait == 0:
            status, tag = "✓ Can donate now", "ready"
            ready += 1
        else:
            status, tag = f"Wait {wait} more days", "wait"
        last_shown = "Never" if last == "" else date.fromisoformat(last).strftime("%d-%m-%Y")
        results.insert("", tk.END, iid=donor_id, values=(name, group, place, phone, last_shown, status), tags=(tag,))

    result_label.config(text=f"{ready} of {len(donors)} compatible donors can give blood today to a patient who needs {need}.   "
                             f"Compatible groups: {', '.join(groups)}")
    highlight_chart(need)
    light_map("patient", need)                            # keep the donation map in step


def selected_donor():
    """Return the id of the donor picked in the table, or None."""
    picked = results.selection()
    if not picked:
        messagebox.showwarning("No donor selected", "Click a donor in the table first.")
        return None
    return picked[0]


def record_donation():
    """Save today's date as the selected donor's last donation."""
    donor_id = selected_donor()
    if donor_id is None:
        return
    cursor.execute("SELECT name, gender, last_donation FROM donors WHERE id = ?", (donor_id,))
    name, gender, last = cursor.fetchone()
    wait = days_left(gender, last)
    if wait > 0:
        messagebox.showerror("Too soon", f"{name} must wait {wait} more days before donating again.")
        return
    if messagebox.askyesno("Record donation", f"Did {name} donate blood today?"):
        cursor.execute("UPDATE donors SET last_donation = ? WHERE id = ?", (date.today().isoformat(), donor_id))
        conn.commit()
        refresh_all()


def delete_donor():
    """Remove the selected donor from the database."""
    donor_id = selected_donor()
    if donor_id is None:
        return
    cursor.execute("SELECT name FROM donors WHERE id = ?", (donor_id,))
    name = cursor.fetchone()[0]
    if messagebox.askyesno("Delete donor", f"Remove {name} from the donor list?"):
        cursor.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
        conn.commit()
        refresh_all()


def show_donor_card(event=None):
    """Double-click a donor in the table to see all their details on a card."""
    picked = results.selection()
    if not picked:
        return
    cursor.execute("SELECT name, age, gender, blood_group, phone, city, last_donation FROM donors WHERE id = ?",
                   (picked[0],))
    name, age, gender, group, phone, city, last = cursor.fetchone()
    wait = days_left(gender, last)
    colour = RED if wait == 0 else MUTED                  # red top = can donate, grey top = must wait

    card = tk.Toplevel(root)
    card.title(name)
    card.configure(bg=WHITE)
    card.resizable(False, False); card.transient(root)    # transient = card always stays on top of the main window
    top = tk.Frame(card, bg=colour, padx=25, pady=15)
    top.pack(fill=tk.X)
    tk.Label(top, text=group, bg=colour, fg=WHITE, font=("Arial", 32, "bold")).pack(side=tk.LEFT)
    tk.Label(top, text=name, bg=colour, fg=WHITE, font=("Arial", 18, "bold")).pack(side=tk.LEFT, padx=18)

    helps = [p for p in BLOOD_GROUPS if group in CAN_RECEIVE_FROM[p]]       # patient groups this donor can help
    details = [("Age", f"{age} years"), ("Gender", gender), ("Phone", phone), ("City", city),
               ("Last donated", "Never" if last == "" else date.fromisoformat(last).strftime("%d-%m-%Y")),
               ("Can give to", ", ".join(helps))]
    for title, value in details:
        row = tk.Frame(card, bg=WHITE)
        row.pack(fill=tk.X, padx=25, pady=4)
        tk.Label(row, text=title, bg=WHITE, fg=MUTED, font=("Arial", 13), width=12, anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=value, bg=WHITE, fg=TEXT, font=("Arial", 13, "bold"), wraplength=260,
                 justify="left").pack(side=tk.LEFT)

    status = "✓ Can donate today" if wait == 0 else f"Must wait {wait} more days"
    tk.Label(card, text=status, bg=WHITE, fg="#16a34a" if wait == 0 else MUTED,
             font=("Arial", 15, "bold")).pack(pady=(12, 6))
    ttk.Button(card, text="Close", style="Plain.TButton", command=card.destroy).pack(pady=(0, 18))
    card.geometry(f"+{root.winfo_rootx() + 380}+{root.winfo_rooty() + 120}"); card.lift(); card.focus_force()   # middle of app, in front

# ---------------- Drawing functions ----------------

def draw_group_chart():
    """Bar chart: how many donors there are in each blood group."""
    bar_chart.delete("all")
    cursor.execute("SELECT blood_group, COUNT(*) FROM donors GROUP BY blood_group")
    counts = dict(cursor.fetchall())                      # e.g. {"O+": 3, "A+": 2}
    biggest = max(counts.values(), default=1)
    for i, group in enumerate(BLOOD_GROUPS):
        count = counts.get(group, 0)
        x = 35 + i * 50                                   # left edge of this bar
        height = 170 * count / biggest                    # tallest bar is 170 pixels
        bar_chart.create_rectangle(x, 220 - height, x + 32, 220, fill=RED, outline="")
        bar_chart.create_text(x + 16, 212 - height, text=str(count), fill=TEXT, font=("Arial", 11, "bold"))
        bar_chart.create_text(x + 16, 238, text=group, fill=TEXT, font=("Arial", 11, "bold"))


def highlight_chart(need):
    """Colour the compatibility chart for the chosen patient group."""
    for (donor, patient), cell in chart_cells.items():
        ok = donor in CAN_RECEIVE_FROM[patient]
        if ok and patient == need:
            cell.config(bg=RED, fg=WHITE)                 # donors for THIS patient
        elif ok:
            cell.config(bg=LIGHT_RED, fg=RED)             # compatible, other patient
        else:
            cell.config(bg=GREY_ROW, fg=MUTED)            # not compatible
    chart_note.config(text=f"Dark red column: blood groups that can be given to a patient who needs {need}.")


def light_map(side, group):
    """Light up one group on the donation map and every group it is linked to."""
    if side == "patient":
        partners = CAN_RECEIVE_FROM[group]                             # donors this patient can take
        pairs = [(donor, group) for donor in partners]
        map_note.config(text=f"Patient group {group} can receive from {len(partners)} group(s): {', '.join(partners)}")
    else:
        partners = [p for p in BLOOD_GROUPS if group in CAN_RECEIVE_FROM[p]]   # patients this donor can help
        pairs = [(group, patient) for patient in partners]
        map_note.config(text=f"Donor group {group} can give to {len(partners)} group(s): {', '.join(partners)}")

    for pair, line in map_lines.items():
        if pair in pairs:
            blood_map.itemconfig(line, fill=RED, width=3)
            blood_map.tag_raise(line)                                  # bring red lines to the front
        else:
            blood_map.itemconfig(line, fill=LINE_GREY, width=1)
    for (s, g), (circle, label) in map_circles.items():
        lit = (s == side and g == group) or (s != side and g in partners)
        blood_map.itemconfig(circle, fill=RED if lit else GREY_ROW)
        blood_map.itemconfig(label, fill=WHITE if lit else TEXT)
    blood_map.tag_raise("circle")                                      # circles always sit on top of lines


def map_clicked(side, group):
    """Runs when a circle on the donation map is clicked."""
    if side == "patient":
        need_var.set(group)                     # the Find Donors and Chart tabs follow the map
        search_donors()                         # this also lights up the map
    else:
        light_map("donor", group)


def refresh_all():
    """Update the numbers, the bar chart and the search results."""
    cursor.execute("SELECT gender, last_donation FROM donors")
    donors = cursor.fetchall()
    ready = sum(1 for gender, last in donors if days_left(gender, last) == 0)
    stats_label.config(text=f"Registered donors: {len(donors)}     Can donate today: {ready}")
    draw_group_chart()
    search_donors()


# ---------------- Splash screen ----------------

def show_splash():
    """A loading screen with a growing bar, shown for about 2 seconds at start-up."""
    root.withdraw()                                       # hide the main window for now
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)                         # no title bar or close button
    w, h = 460, 280
    x = (splash.winfo_screenwidth() - w) // 2             # centre it on the screen
    y = (splash.winfo_screenheight() - h) // 3
    splash.geometry(f"{w}x{h}+{x}+{y}")

    screen = tk.Canvas(splash, width=w, height=h, bg=RED, highlightthickness=0)
    screen.pack()
    screen.create_text(w // 2, 75, text="🩸", font=("Arial", 48))
    screen.create_text(w // 2, 145, text="BLOOD DONOR FINDER", fill=WHITE, font=("Arial", 24, "bold"))
    status = screen.create_text(w // 2, 185, text="Loading donors...", fill=LIGHT_RED, font=("Arial", 12))
    screen.create_rectangle(80, 215, 380, 227, outline=WHITE)                # empty bar
    bar = screen.create_rectangle(80, 215, 80, 227, fill=WHITE, outline="")  # the part that grows

    def grow(step=0):
        screen.coords(bar, 80, 215, 80 + step * 15, 227)                    # 20 steps x 15 px = 300 px
        if step == 10:
            screen.itemconfig(status, text="Checking blood groups...")
        if step < 20:
            splash.after(90, grow, step + 1)                                 # call itself again in 90 ms
        else:
            splash.destroy()
            root.deiconify()                                                 # show the main window
    grow()


# ---------------- Front end: building the window ----------------
add_sample_donors()

root = tk.Tk()
root.title("Blood Donor Finder")
root.geometry("1060x700")
root.configure(bg=WHITE)

style = ttk.Style()
style.theme_use("clam")                           # "clam" theme lets us colour the widgets
style.configure("Red.TButton", background=RED, foreground=WHITE, font=("Arial", 12, "bold"), padding=8)
style.map("Red.TButton", background=[("active", "#991b1b")])
style.configure("Plain.TButton", font=("Arial", 12), padding=8)
style.configure("TNotebook", background=WHITE)
style.configure("TNotebook.Tab", font=("Arial", 13, "bold"), padding=(18, 8))
style.map("TNotebook.Tab", background=[("selected", LIGHT_RED)], foreground=[("selected", RED)])
style.configure("Treeview", font=("Arial", 12), rowheight=30)
style.configure("Treeview.Heading", font=("Arial", 12, "bold"))

# ----- red header bar -----
header = tk.Frame(root, bg=RED, padx=20, pady=12)
header.pack(fill=tk.X)
tk.Label(header, text="🩸 BLOOD DONOR FINDER", bg=RED, fg=WHITE, font=("Arial", 24, "bold")).pack(side=tk.LEFT)
stats_label = tk.Label(header, text="", bg=RED, fg=WHITE, font=("Arial", 13))
stats_label.pack(side=tk.RIGHT)

tabs = ttk.Notebook(root)
tabs.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

# ===== Tab 1: register a donor =====
register_tab = tk.Frame(tabs, bg=WHITE, padx=25, pady=20)
tabs.add(register_tab, text="Register Donor")

form = tk.Frame(register_tab, bg=WHITE)
form.pack(side=tk.LEFT, anchor="n")


def form_label(text, row):
    """A label on the left side of the form."""
    tk.Label(form, text=text, bg=WHITE, fg=TEXT, font=("Arial", 13)).grid(row=row, column=0, sticky="w", pady=7)


def form_entry(row):
    """A white text box on the right side of the form."""
    entry = tk.Entry(form, font=("Arial", 13), width=24, bg=WHITE, fg=TEXT, insertbackground=TEXT,
                     relief="flat", highlightthickness=1, highlightbackground="#d1d5db", highlightcolor=RED)
    entry.grid(row=row, column=1, sticky="w", pady=7, padx=(15, 0), ipady=3)
    return entry


form_label("Full name", 0)
name_entry = form_entry(0)
form_label("Age", 1)
age_entry = form_entry(1)

form_label("Gender", 2)
gender_var = tk.StringVar(value="Male")
gender_row = tk.Frame(form, bg=WHITE)
gender_row.grid(row=2, column=1, sticky="w", padx=(15, 0))
for option in ("Male", "Female"):
    tk.Radiobutton(gender_row, text=option, variable=gender_var, value=option, bg=WHITE, fg=TEXT,
                   font=("Arial", 13)).pack(side=tk.LEFT, padx=(0, 15))

form_label("Blood group", 3)
group_box = ttk.Combobox(form, values=BLOOD_GROUPS, state="readonly", font=("Arial", 13), width=22)
group_box.current(0)
group_box.grid(row=3, column=1, sticky="w", pady=7, padx=(15, 0))

form_label("Phone (10 digits)", 4)
phone_entry = form_entry(4)
form_label("City", 5)
city_entry = form_entry(5)
form_label("Last donation", 6)
last_entry = form_entry(6)
tk.Label(form, text="DD-MM-YYYY  ·  leave empty if you have never donated", bg=WHITE, fg=MUTED,
         font=("Arial", 11)).grid(row=7, column=1, sticky="w", padx=(15, 0))

buttons = tk.Frame(form, bg=WHITE)
buttons.grid(row=8, column=0, columnspan=2, sticky="w", pady=(20, 0))
ttk.Button(buttons, text="Register Donor", style="Red.TButton", command=register_donor).pack(side=tk.LEFT)
ttk.Button(buttons, text="Clear", style="Plain.TButton", command=clear_form).pack(side=tk.LEFT, padx=10)

# bar chart on the right of the form
chart_box = tk.Frame(register_tab, bg=WHITE)
chart_box.pack(side=tk.RIGHT, anchor="n")
tk.Label(chart_box, text="Donors by blood group", bg=WHITE, fg=TEXT, font=("Arial", 14, "bold")).pack(anchor="w")
bar_chart = tk.Canvas(chart_box, width=440, height=260, bg=WHITE, highlightthickness=0)
bar_chart.pack(pady=(10, 0))

# ===== Tab 2: find donors =====
find_tab = tk.Frame(tabs, bg=WHITE, padx=20, pady=15)
tabs.add(find_tab, text="Find Donors")

search_bar = tk.Frame(find_tab, bg=WHITE)
search_bar.pack(fill=tk.X)
tk.Label(search_bar, text="Patient needs", bg=WHITE, fg=TEXT, font=("Arial", 13, "bold")).pack(side=tk.LEFT)
need_var = tk.StringVar(value="A+")
need_box = ttk.Combobox(search_bar, textvariable=need_var, values=BLOOD_GROUPS, state="readonly",
                        font=("Arial", 13), width=6)
need_box.pack(side=tk.LEFT, padx=(8, 25))
need_box.bind("<<ComboboxSelected>>", search_donors)
tk.Label(search_bar, text="City (optional)", bg=WHITE, fg=TEXT, font=("Arial", 13)).pack(side=tk.LEFT)
city_search = tk.Entry(search_bar, font=("Arial", 13), width=16, bg=WHITE, fg=TEXT, insertbackground=TEXT,
                       relief="flat", highlightthickness=1, highlightbackground="#d1d5db", highlightcolor=RED)
city_search.pack(side=tk.LEFT, padx=8, ipady=3)
city_search.bind("<KeyRelease>", search_donors)        # live search: runs after every key you type
ttk.Button(search_bar, text="Search", style="Red.TButton", command=search_donors).pack(side=tk.LEFT, padx=8)

result_label = tk.Label(find_tab, text="", bg=WHITE, fg=RED, font=("Arial", 12, "bold"), anchor="w")
result_label.pack(fill=tk.X, pady=(12, 6))

columns = ("Name", "Group", "City", "Phone", "Last donated", "Status")
results = ttk.Treeview(find_tab, columns=columns, show="headings", height=11)
for col, width in zip(columns, (190, 80, 130, 140, 130, 190)):
    results.heading(col, text=col)
    results.column(col, width=width, anchor="center")
results.tag_configure("ready", background=GREEN_ROW)                  # green row = can donate
results.tag_configure("wait", background=GREY_ROW, foreground=MUTED)  # grey row = must wait
results.pack(fill=tk.BOTH, expand=True)
results.bind("<Double-1>", show_donor_card)                          # double-click a row -> donor card

actions = tk.Frame(find_tab, bg=WHITE)
actions.pack(fill=tk.X, pady=(12, 0))
ttk.Button(actions, text="Record Donation Today", style="Red.TButton", command=record_donation).pack(side=tk.LEFT)
ttk.Button(actions, text="Delete Donor", style="Plain.TButton", command=delete_donor).pack(side=tk.LEFT, padx=10)
ttk.Button(actions, text="Donor Card", style="Plain.TButton", command=show_donor_card).pack(side=tk.LEFT)  # same as double-click
tk.Label(actions, text="Double-click a donor for details  ·  Green = can donate  ·  Grey = must wait", bg=WHITE, fg=MUTED, font=("Arial", 11)).pack(side=tk.RIGHT)

# ===== Tab 3: compatibility chart =====
chart_tab = tk.Frame(tabs, bg=WHITE, padx=25, pady=15)
tabs.add(chart_tab, text="Compatibility Chart")

top = tk.Frame(chart_tab, bg=WHITE)
top.pack(fill=tk.X)
tk.Label(top, text="Who can give blood to whom?", bg=WHITE, fg=TEXT, font=("Arial", 15, "bold")).pack(side=tk.LEFT)
chart_need = ttk.Combobox(top, textvariable=need_var, values=BLOOD_GROUPS, state="readonly",
                          font=("Arial", 13), width=6)
chart_need.pack(side=tk.RIGHT)
chart_need.bind("<<ComboboxSelected>>", search_donors)
tk.Label(top, text="Patient group", bg=WHITE, fg=TEXT, font=("Arial", 13)).pack(side=tk.RIGHT, padx=8)

chart_note = tk.Label(chart_tab, text="", bg=WHITE, fg=RED, font=("Arial", 12, "bold"), anchor="w")
chart_note.pack(fill=tk.X, pady=(8, 10))

grid = tk.Frame(chart_tab, bg=WHITE)
grid.pack()
tk.Label(grid, text="Donor ↓   Patient →", bg=WHITE, fg=MUTED, font=("Arial", 11)).grid(row=0, column=0, padx=6)
chart_cells = {}                                  # (donor group, patient group) -> its Label
for c, patient in enumerate(BLOOD_GROUPS, start=1):
    tk.Label(grid, text=patient, bg=WHITE, fg=TEXT, font=("Arial", 13, "bold")).grid(row=0, column=c, pady=4)
for r, donor in enumerate(BLOOD_GROUPS, start=1):
    tk.Label(grid, text=donor, bg=WHITE, fg=TEXT, font=("Arial", 13, "bold")).grid(row=r, column=0, padx=6)
    for c, patient in enumerate(BLOOD_GROUPS, start=1):
        mark = "✓" if donor in CAN_RECEIVE_FROM[patient] else "✗"
        cell = tk.Label(grid, text=mark, width=6, height=2, font=("Arial", 13, "bold"))
        cell.grid(row=r, column=c, padx=2, pady=2)
        chart_cells[(donor, patient)] = cell

# ===== Tab 4: donation map =====
map_tab = tk.Frame(tabs, bg=WHITE, padx=25, pady=15)
tabs.add(map_tab, text="Donation Map")
map_note = tk.Label(map_tab, text="", bg=WHITE, fg=RED, font=("Arial", 13, "bold"), anchor="w")
map_note.pack(fill=tk.X)
tk.Label(map_tab, text="Click any circle: a patient group shows who can give to it, a donor group shows who it can help.",
         bg=WHITE, fg=MUTED, font=("Arial", 11), anchor="w").pack(fill=tk.X)

blood_map = tk.Canvas(map_tab, width=900, height=440, bg=WHITE, highlightthickness=0)
blood_map.pack(pady=(8, 0))
DONOR_X, PATIENT_X = 230, 670                     # x position of the two columns of circles
blood_map.create_text(DONOR_X, 14, text="DONOR", fill=MUTED, font=("Arial", 12, "bold"))
blood_map.create_text(PATIENT_X, 14, text="PATIENT", fill=MUTED, font=("Arial", 12, "bold"))


def map_y(i):
    """y position of the i-th blood group on the map."""
    return 50 + i * 52


# 1) a line for every safe donor -> patient pair (drawn first, so it sits under the circles)
map_lines = {}                                    # (donor group, patient group) -> line id
for d, donor in enumerate(BLOOD_GROUPS):
    for p, patient in enumerate(BLOOD_GROUPS):
        if donor in CAN_RECEIVE_FROM[patient]:
            map_lines[(donor, patient)] = blood_map.create_line(DONOR_X + 22, map_y(d), PATIENT_X - 22, map_y(p),
                                                                fill=LINE_GREY, width=1)

# 2) a clickable circle for every group, in both columns
map_circles = {}                                  # ("donor" or "patient", group) -> (circle id, text id)
for side, x in (("donor", DONOR_X), ("patient", PATIENT_X)):
    for i, group in enumerate(BLOOD_GROUPS):
        y = map_y(i)
        circle = blood_map.create_oval(x - 22, y - 22, x + 22, y + 22, fill=GREY_ROW, outline=RED, width=2, tags="circle")
        label = blood_map.create_text(x, y, text=group, fill=TEXT, font=("Arial", 12, "bold"), tags="circle")
        for item in (circle, label):
            blood_map.tag_bind(item, "<Button-1>", lambda e, s=side, g=group: map_clicked(s, g))
        map_circles[(side, group)] = (circle, label)

refresh_all()                                     # fill in numbers, chart and table
show_splash()                                     # loading screen first, then the main window
root.mainloop()                                   # start the app and wait for clicks
conn.close()                                      # close the database when the window closes
