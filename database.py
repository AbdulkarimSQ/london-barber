import sqlite3

def get_db():
    db = sqlite3.connect("barber.db")
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            duration INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            service_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (service_id) REFERENCES services(id)
        );

        CREATE TABLE IF NOT EXISTS working_hours (
            day TEXT PRIMARY KEY,
            open_time TEXT NOT NULL,
            close_time TEXT NOT NULL,
            slot_duration INTEGER NOT NULL DEFAULT 30
        );
    """)

    if db.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO services (name, price, duration) VALUES (?, ?, ?)",
            [
                ("Haircut", 25, 30),
                ("Beard Trim", 13, 30),
                ("Haircut + Beard", 30, 45),
                ("Kids Cut", 20, 30),
                ("Hair Wash + Style", 20, 30),
            ],
        )

    db.executemany(
        "INSERT OR IGNORE INTO working_hours (day, open_time, close_time, slot_duration) VALUES (?, ?, ?, ?)",
        [(day, "10:00", "22:00", 30) for day in
         ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")],
    )

    db.commit()
    db.close()
