from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from database import get_db, init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def admin():
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        return f.read()

# Initialize database on startup
init_db()

class ServiceCreate(BaseModel):
    name: str
    price: float
    duration: int

@app.post("/services", status_code=201)
def create_service(service: ServiceCreate):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO services (name, price, duration) VALUES (?, ?, ?)",
        (service.name, service.price, service.duration)
    )
    db.commit()
    service_id = cursor.lastrowid
    db.close()
    return {"id": service_id, "name": service.name, "price": service.price, "duration": service.duration}

@app.get("/services")
def get_services():
    db = get_db()
    services = [dict(row) for row in db.execute("SELECT * FROM services").fetchall()]
    db.close()
    return services

@app.get("/services/{service_id}")
def get_service(service_id: int):
    db = get_db()
    service = db.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    db.close()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return dict(service)

@app.put("/services/{service_id}")
def update_service(service_id: int, service: ServiceCreate):
    db = get_db()
    existing = db.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    if not existing:
        db.close()
        raise HTTPException(status_code=404, detail="Service not found")

    db.execute(
        "UPDATE services SET name = ?, price = ?, duration = ? WHERE id = ?",
        (service.name, service.price, service.duration, service_id)
    )
    db.commit()
    db.close()
    updated = {"id": service_id, **service.model_dump()}
    return {"message": "Service updated successfully", "service": updated}

@app.delete("/services/{service_id}")
def delete_service(service_id: int):
    db = get_db()
    service = db.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    if not service:
        db.close()
        raise HTTPException(status_code=404, detail="Service not found")
    db.execute("DELETE FROM services WHERE id = ?", (service_id,))
    db.commit()
    db.close()
    return {"message": "Service deleted successfully"}

class BookingCreate(BaseModel):
    customer_name: str
    customer_phone: str
    service_id: int
    date: str
    time: str

@app.post("/bookings", status_code=201)
def create_booking(booking: BookingCreate):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO bookings (customer_name, customer_phone, service_id, date, time) VALUES (?, ?, ?, ?, ?)",
        (booking.customer_name, booking.customer_phone, booking.service_id, booking.date, booking.time)
    )
    db.commit()
    booking_id = cursor.lastrowid
    db.close()
    return {
        "id": booking_id,
        "customer_name": booking.customer_name,
        "customer_phone": booking.customer_phone,
        "service_id": booking.service_id,
        "date": booking.date,
        "time": booking.time,
    }

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):
    db = get_db()
    booking = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    db.close()
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with id {booking_id} not found")
    return dict(booking)

@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int):
    db = get_db()
    booking = db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not booking:
        db.close()
        raise HTTPException(status_code=404, detail=f"Booking with id {booking_id} not found")
    db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    db.commit()
    db.close()
    return {"message": "Booking deleted successfully", "booking": dict(booking)}

@app.get("/bookings")
def list_bookings():
    db = get_db()
    bookings = [dict(row) for row in db.execute("SELECT * FROM bookings").fetchall()]
    db.close()
    return bookings

# ══════ Working Hours Model ══════

class WorkingHours(BaseModel):
    day: str
    open_time: str
    close_time: str
    slot_duration: int

# ══════ Working Hours Endpoints ══════
@app.post("/working-hours", status_code=201)
def set_working_hours(hours: WorkingHours):
    db = get_db()
    db.execute(
        """INSERT INTO working_hours (day, open_time, close_time, slot_duration)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(day) DO UPDATE SET
               open_time = excluded.open_time,
               close_time = excluded.close_time,
               slot_duration = excluded.slot_duration""",
        (hours.day, hours.open_time, hours.close_time, hours.slot_duration)
    )
    db.commit()
    db.close()
    return {
        "message": f"working hours set for {hours.day}",
        "hours": {
            "day": hours.day,
            "open_time": hours.open_time,
            "close_time": hours.close_time,
            "slot_duration": hours.slot_duration,
        },
    }

@app.get("/working-hours")
def get_working_hours():
    db = get_db()
    rows = [dict(row) for row in db.execute("SELECT * FROM working_hours").fetchall()]
    db.close()
    return rows

@app.get("/available-hours")
def get_available_hours(date: str, day: str):
    db = get_db()
    hours = db.execute("SELECT * FROM working_hours WHERE day = ?", (day,)).fetchone()
    if not hours:
        db.close()
        raise HTTPException(status_code=404, detail=f"No working hours set for {day}")

    start_hour, start_min = map(int, hours["open_time"].split(":"))
    end_hour, end_min = map(int, hours["close_time"].split(":"))
    duration = hours["slot_duration"]

    start_total = start_hour * 60 + start_min
    end_total = end_hour * 60 + end_min

    all_slots = []
    current = start_total
    while current + duration <= end_total:
        h, m = divmod(current, 60)
        all_slots.append(f"{h:02d}:{m:02d}")
        current += duration

    booked_times = [
        row["time"] for row in db.execute(
            "SELECT time FROM bookings WHERE date = ?", (date,)
        ).fetchall()
    ]
    db.close()
    available = [s for s in all_slots if s not in booked_times]

    return {"date": date, "day": day, "available_slots": available}
