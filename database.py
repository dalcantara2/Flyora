"""
database.py
-----------
Handles all direct database interactions for Flyora:
  - get_db()    : opens a connection to the SQLite database
  - init_db()   : creates the tables if they do not already exist
  - seed_db()   : inserts the starter flight data (only if the table is empty)

This module is imported by app.py at startup so the database is always
ready before the first request is served.
"""

import os
import sqlite3
from config import DATABASE_PATH, DATABASE_DIR


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db():
    """
    Opens and returns a new SQLite connection to the Flyora database.

    - row_factory = sqlite3.Row lets us access columns by name (row["price"])
      instead of by index (row[4]), which makes templates much easier to read.
    - The caller is responsible for closing the connection.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def init_db():
    """
    Creates the 'flights' and 'bookings' tables if they do not already exist,
    then runs any pending column migrations.

    Safe to call every time the app starts — IF NOT EXISTS means it will
    never overwrite data that is already there.
    """

    # Make sure the database/ directory exists before SQLite tries to create
    # the .db file inside it.
    os.makedirs(DATABASE_DIR, exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # flights table
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number    TEXT    NOT NULL,
            airline          TEXT    NOT NULL,
            origin_city      TEXT    NOT NULL,
            destination_city TEXT    NOT NULL,
            departure_date   TEXT    NOT NULL,
            departure_time   TEXT    NOT NULL,
            arrival_time     TEXT    NOT NULL,
            duration_minutes INTEGER NOT NULL,
            price            REAL    NOT NULL,
            seats_available  INTEGER NOT NULL,
            aircraft_type    TEXT    NOT NULL
        )
    """)

    # ------------------------------------------------------------------
    # bookings table
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_reference  TEXT    NOT NULL UNIQUE,
            flight_id          INTEGER NOT NULL,
            passenger_name     TEXT    NOT NULL,
            passenger_email    TEXT    NOT NULL,
            passenger_phone    TEXT    NOT NULL,
            seat_preference    TEXT    NOT NULL DEFAULT 'No preference',
            num_passengers     INTEGER NOT NULL DEFAULT 1,
            total_price        REAL    NOT NULL,
            booked_at          TEXT    NOT NULL,
            trip_purpose       TEXT    NOT NULL,
            FOREIGN KEY (flight_id) REFERENCES flights (id)
        )
    """)

    conn.commit()

    # ------------------------------------------------------------------
    # Safe column migration: add selected_seat if it does not exist yet.
    # SQLite does not support ALTER TABLE ... ADD COLUMN IF NOT EXISTS,
    # so we attempt the ALTER and silently ignore the error if the column
    # is already present.
    # ------------------------------------------------------------------
    try:
        cursor.execute(
            "ALTER TABLE bookings ADD COLUMN selected_seat TEXT NOT NULL DEFAULT ''"
        )
        conn.commit()
        print("[Flyora] Migration: added 'selected_seat' column to bookings.")
    except sqlite3.OperationalError:
        pass  # Column already exists — nothing to do

    conn.close()
    print("[Flyora] Database tables are ready.")


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_db():
    """
    Inserts starter flight data into the flights table.

    The guard at the top checks whether any rows already exist.
    If the table has data, this function exits immediately — so restarting
    the app or redeploying will never create duplicate flights.

    Flights cover a realistic mix of:
      - Domestic and international routes
      - Short-haul (< 3 h) and long-haul (> 6 h) durations
      - Economy and premium price points
      - Multiple airlines and aircraft types
      - Dates spread across several months
    """

    conn = get_db()
    cursor = conn.cursor()

    # --- Seed guard: do nothing if flights already exist ---
    cursor.execute("SELECT COUNT(*) FROM flights")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"[Flyora] Seed skipped — {count} flights already in database.")
        conn.close()
        return

    # ------------------------------------------------------------------
    # 16 seed flights — all dates in August / September 2026
    #
    # Routes included:
    #   New York    → Los Angeles   (SK101)  Aug 12
    #   Los Angeles → New York      (SK102)  Aug 15
    #   New York    → Miami         (SK103)  Aug 18  ← required route
    #   Miami       → New York      (SK104)  Aug 20  ← required route
    #   Atlanta     → Miami         (SK105)  Aug 22  ← required route
    #   Atlanta     → New York      (SK106)  Aug 25  ← required route
    #   Chicago     → Miami         (SK203)  Aug 14
    #   Miami       → Chicago       (SK204)  Aug 28
    #   Houston     → Denver        (SK305)  Aug 30
    #   Denver      → Houston       (SK306)  Sep 02
    #   Seattle     → San Francisco (SK407)  Sep 05
    #   New York    → London        (SK501)  Sep 08  ← required route
    #   London      → New York      (SK502)  Sep 12
    #   Los Angeles → Tokyo         (SK601)  Sep 15  ← required route
    #   Tokyo       → Los Angeles   (SK602)  Sep 20
    #   Chicago     → Paris         (SK701)  Sep 25
    #
    # Columns: flight_number, airline, origin_city, destination_city,
    #          departure_date, departure_time, arrival_time,
    #          duration_minutes, price, seats_available, aircraft_type
    # ------------------------------------------------------------------
    flights = [
        # --- Domestic US — core routes ---
        ("SK101", "Flyora Air",      "New York",    "Los Angeles",   "2026-08-12", "07:00", "10:30", 210,  189.99, 42, "Boeing 737"),
        ("SK102", "Flyora Air",      "Los Angeles", "New York",      "2026-08-15", "08:30", "17:00", 270,  199.99, 38, "Boeing 737"),
        ("SK103", "Flyora Air",      "New York",    "Miami",         "2026-08-18", "09:00", "12:15", 195,  139.99, 50, "Airbus A320"),
        ("SK104", "Flyora Air",      "Miami",       "New York",      "2026-08-20", "14:30", "17:45", 195,  144.99, 48, "Airbus A320"),
        ("SK105", "BlueSky Express", "Atlanta",     "Miami",         "2026-08-22", "06:30", "08:15",  105,  89.99, 65, "Boeing 737 MAX"),
        ("SK106", "BlueSky Express", "Atlanta",     "New York",      "2026-08-25", "07:45", "10:00",  135, 109.99, 60, "Boeing 737 MAX"),
        ("SK203", "Flyora Air",      "Chicago",     "Miami",         "2026-08-14", "06:00", "09:45", 225,  159.99, 55, "Airbus A320"),
        ("SK204", "Flyora Air",      "Miami",       "Chicago",       "2026-08-28", "14:00", "17:30", 210,  149.99, 60, "Airbus A320"),

        # --- Domestic US — additional routes ---
        ("SK305", "BlueSky Express", "Houston",     "Denver",        "2026-08-30", "09:15", "11:00", 105,   99.99, 70, "Boeing 737 MAX"),
        ("SK306", "BlueSky Express", "Denver",      "Houston",       "2026-09-02", "13:00", "16:45", 105,   94.99, 68, "Boeing 737 MAX"),
        ("SK407", "Flyora Air",      "Seattle",     "San Francisco", "2026-09-05", "07:30", "09:15", 105,   79.99, 80, "Embraer E175"),

        # --- International routes ---
        ("SK501", "Flyora Air",      "New York",    "London",        "2026-09-08", "21:00", "09:00", 420,  549.99, 24, "Boeing 777"),
        ("SK502", "Flyora Air",      "London",      "New York",      "2026-09-12", "10:30", "13:00", 450,  579.99, 20, "Boeing 777"),
        ("SK601", "BlueSky Express", "Los Angeles", "Tokyo",         "2026-09-15", "11:00", "15:30", 630,  749.99, 18, "Boeing 787 Dreamliner"),
        ("SK602", "BlueSky Express", "Tokyo",       "Los Angeles",   "2026-09-20", "17:00", "10:00", 600,  729.99, 22, "Boeing 787 Dreamliner"),
        ("SK701", "Flyora Air",      "Chicago",     "Paris",         "2026-09-25", "18:30", "08:30", 480,  619.99, 30, "Airbus A330"),
    ]

    cursor.executemany("""
        INSERT INTO flights (
            flight_number, airline, origin_city, destination_city,
            departure_date, departure_time, arrival_time,
            duration_minutes, price, seats_available, aircraft_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, flights)

    conn.commit()
    conn.close()
    print(f"[Flyora] Database seeded with {len(flights)} flights.")


# ---------------------------------------------------------------------------
# Airport / city alias map  (added in search refinement)
# ---------------------------------------------------------------------------

# Maps common IATA codes and informal names to the canonical city name stored
# in the database.  Keys are stored lowercase so the lookup is case-insensitive.
CITY_ALIASES = {
    # New York
    "nyc": "New York",
    "jfk": "New York",
    "lga": "New York",
    "ewr": "New York",
    "new york city": "New York",
    # Los Angeles
    "lax": "Los Angeles",
    "la":  "Los Angeles",
    # Miami
    "mia": "Miami",
    # Chicago
    "ord": "Chicago",
    "mdw": "Chicago",
    "chi": "Chicago",
    # Houston
    "iah": "Houston",
    "hou": "Houston",
    # Denver
    "den": "Denver",
    # Seattle
    "sea": "Seattle",
    # San Francisco
    "sfo": "San Francisco",
    "sf":  "San Francisco",
    # London
    "lhr": "London",
    "lgw": "London",
    "lon": "London",
    # Tokyo
    "nrt": "Tokyo",
    "hnd": "Tokyo",
    "tyo": "Tokyo",
    # Paris
    "cdg": "Paris",
    "ory": "Paris",
}


def resolve_city(name):
    """
    Resolves a user-entered city name or airport code to its canonical form.

    - Checks the alias map first (case-insensitive).
    - Falls back to title-casing the raw input so "new york" becomes "New York".

    Parameters
    ----------
    name : str  — raw input from the search form

    Returns
    -------
    str  — canonical city name ready to match against the database
    """
    cleaned = name.strip().lower()
    return CITY_ALIASES.get(cleaned, name.strip().title())


# ---------------------------------------------------------------------------
# Flight queries  (updated in search refinement)
# ---------------------------------------------------------------------------

def search_flights(origin, destination, date):
    """
    Smart two-pass flight search.

    Pass 1 — Exact date match
        Returns all available flights on the requested route AND date.

    Pass 2 — Next available (only if Pass 1 returns nothing)
        If the route exists but has no flight on the exact date, returns
        the next available flights on that route departing ON OR AFTER
        the requested date, sorted closest-first.

        Past dates are never suggested. If there are no future flights on
        the route the function returns an empty list so the template shows
        the normal "no flights found" state.

    Airport aliases (NYC, JFK, LAX, LHR, etc.) are resolved to their
    canonical city names before querying.

    Parameters
    ----------
    origin      : str  — departure city / airport code entered by the user
    destination : str  — destination city / airport code entered by the user
    date        : str  — departure date in YYYY-MM-DD format

    Returns
    -------
    dict with keys:
        "flights"        : list of sqlite3.Row  — the result rows
        "is_alternative" : bool  — True when showing alternatives, not exact hits
        "alt_date"       : str or None  — the actual date of the alternatives
    """
    # Resolve aliases to canonical city names
    origin_resolved      = resolve_city(origin)
    destination_resolved = resolve_city(destination)

    conn   = get_db()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # Pass 1: exact date + route match
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT *
        FROM   flights
        WHERE  LOWER(TRIM(origin_city))      = LOWER(?)
        AND    LOWER(TRIM(destination_city)) = LOWER(?)
        AND    departure_date                = ?
        AND    seats_available               > 0
        ORDER  BY departure_time ASC
    """, (origin_resolved, destination_resolved, date))

    exact_flights = cursor.fetchall()

    if exact_flights:
        conn.close()
        return {
            "flights":        exact_flights,
            "is_alternative": False,
            "alt_date":       None,
        }

    # ------------------------------------------------------------------
    # Pass 2: same route, next available date on or after requested date.
    # Past dates are never shown — if nothing exists in the future the
    # caller receives an empty list and renders the no-results state.
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT *
        FROM   flights
        WHERE  LOWER(TRIM(origin_city))      = LOWER(?)
        AND    LOWER(TRIM(destination_city)) = LOWER(?)
        AND    departure_date               >  ?
        AND    seats_available               > 0
        ORDER  BY departure_date ASC, departure_time ASC
        LIMIT  5
    """, (origin_resolved, destination_resolved, date))

    future_flights = cursor.fetchall()
    conn.close()

    if future_flights:
        return {
            "flights":        future_flights,
            "is_alternative": True,
            "alt_date":       future_flights[0]["departure_date"],
        }

    # Route does not exist, or no future flights remain on it
    return {
        "flights":        [],
        "is_alternative": False,
        "alt_date":       None,
    }


def get_flight_by_id(flight_id):
    """
    Returns a single flight row by its primary key, or None if not found.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = cursor.fetchone()
    conn.close()
    return flight


def get_booked_seats(flight_id):
    """
    Returns a set of seat labels (e.g. {'2A', '5C', '7F'}) that have already
    been booked on the given flight.

    Used by both the booking form (to mark seats occupied in the map) and by
    create_booking() (to enforce the uniqueness constraint server-side).

    Only considers bookings where selected_seat is not empty, so old rows
    that pre-date the seat-map feature are safely ignored.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT selected_seat
        FROM   bookings
        WHERE  flight_id    = ?
        AND    selected_seat != ''
    """, (flight_id,))
    seats = {row["selected_seat"] for row in cursor.fetchall()}
    conn.close()
    return seats


# ---------------------------------------------------------------------------
# Booking functions  (added in Phase 2)
# ---------------------------------------------------------------------------

def generate_booking_reference():
    """
    Generates a unique booking reference in the format FLY-NNNN-XX.

    Example: FLY-4821-QR

    The format is:
      FLY   — Flyora brand prefix
      NNNN  — 4-digit random number (1000–9999)
      XX    — 2 random uppercase letters

    If the generated reference already exists in the database (extremely
    unlikely), the function retries up to 10 times before raising an error.
    """
    import random
    import string

    conn = get_db()
    cursor = conn.cursor()

    for _ in range(10):
        digits  = str(random.randint(1000, 9999))
        letters = "".join(random.choices(string.ascii_uppercase, k=2))
        ref     = f"FLY-{digits}-{letters}"

        # Check the reference is not already in use
        cursor.execute(
            "SELECT id FROM bookings WHERE booking_reference = ?", (ref,)
        )
        if cursor.fetchone() is None:
            conn.close()
            return ref

    conn.close()
    raise RuntimeError("Could not generate a unique booking reference after 10 attempts.")


def create_booking(flight_id, passenger_name, passenger_email,
                   passenger_phone, selected_seat, trip_purpose):
    """
    Saves a new booking and decrements the flight's available seat count.

    Parameters
    ----------
    flight_id        : int
    passenger_name   : str
    passenger_email  : str
    passenger_phone  : str
    selected_seat    : str  — e.g. "4A" — the seat chosen on the map
    trip_purpose     : str  — "Business" / "Leisure" / "Family"

    Returns
    -------
    str   — the booking reference on success
    None  — if the flight has no seats left or the seat is already taken
    "SEAT_TAKEN" — if that exact seat is already booked on this flight
    """
    from datetime import datetime, timezone

    conn = get_db()
    cursor = conn.cursor()

    try:
        # --- Check seat availability and confirm flight exists ---
        cursor.execute(
            "SELECT price, seats_available FROM flights WHERE id = ?",
            (flight_id,)
        )
        flight = cursor.fetchone()
        if flight is None:
            return None
        if flight["seats_available"] < 1:
            return None

        # --- Check the specific seat is not already taken ---
        if selected_seat:
            cursor.execute("""
                SELECT id FROM bookings
                WHERE  flight_id    = ?
                AND    selected_seat = ?
            """, (flight_id, selected_seat))
            if cursor.fetchone() is not None:
                conn.close()
                return "SEAT_TAKEN"

        # --- Total price is always for 1 passenger ---
        total_price = round(flight["price"], 2)

        # --- Generate reference ---
        booking_ref = generate_booking_reference()

        # --- Insert booking (num_passengers locked to 1, seat_preference
        #     kept for DB compatibility but derived from selected_seat) ---
        booked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Derive a seat-preference label from the seat letter for legacy compat
        seat_letter = selected_seat[-1].upper() if selected_seat else ""
        if seat_letter in ("A", "F"):
            seat_preference = "Window"
        elif seat_letter in ("C", "D"):
            seat_preference = "Aisle"
        elif seat_letter in ("B", "E"):
            seat_preference = "Middle"
        else:
            seat_preference = "No preference"

        cursor.execute("""
            INSERT INTO bookings (
                booking_reference, flight_id,
                passenger_name, passenger_email, passenger_phone,
                seat_preference, num_passengers, total_price,
                booked_at, trip_purpose, selected_seat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_ref, flight_id,
            passenger_name, passenger_email, passenger_phone,
            seat_preference, 1, total_price,
            booked_at, trip_purpose, selected_seat
        ))

        # --- Decrement available seats ---
        cursor.execute("""
            UPDATE flights SET seats_available = seats_available - 1
            WHERE id = ?
        """, (flight_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()
    return booking_ref


def get_booking_by_reference(booking_reference):
    """
    Returns a single booking row joined with its flight details.

    Used by both the confirmation page (Phase 2) and the lookup route (Phase 4).

    Returns a sqlite3.Row with columns from both tables, or None if not found.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            b.booking_reference,
            b.passenger_name,
            b.passenger_email,
            b.passenger_phone,
            b.seat_preference,
            b.num_passengers,
            b.total_price,
            b.booked_at,
            b.trip_purpose,
            b.selected_seat,
            f.flight_number,
            f.airline,
            f.origin_city,
            f.destination_city,
            f.departure_date,
            f.departure_time,
            f.arrival_time,
            f.duration_minutes,
            f.aircraft_type,
            f.price  AS price_per_person
        FROM   bookings b
        JOIN   flights  f ON b.flight_id = f.id
        WHERE  b.booking_reference = ?
    """, (booking_reference,))

    booking = cursor.fetchone()
    conn.close()
    return booking
