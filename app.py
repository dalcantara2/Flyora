"""
app.py
------
Entry point for the Flyora Flask application.

Routes:
  GET  /                          — Home page with search form
  POST /search                    — Search flights, render results
  GET  /book/<flight_id>          — Show booking form + seat map
  POST /book/<flight_id>          — Validate, save booking, redirect
  GET  /seats/<flight_id>         — JSON: already-booked seats for this flight
  GET  /confirmation/<ref>        — Booking confirmation page
  GET  /lookup                    — Booking lookup form
  POST /lookup                    — Fetch booking by reference
"""

import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import SECRET_KEY, DEBUG
from database import (
    init_db, seed_db,
    search_flights, get_flight_by_id,
    get_booked_seats,
    create_booking, get_booking_by_reference,
    resolve_city,
)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = SECRET_KEY

init_db()
seed_db()


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

def format_duration(minutes):
    """210 → '3h 30m'"""
    return f"{minutes // 60}h {minutes % 60}m"

app.jinja_env.globals["format_duration"] = format_duration


def format_date(date_str):
    """'2026-08-12' → 'August 12, 2026'"""
    from datetime import datetime
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_str

app.jinja_env.filters["format_date"] = format_date


# ---------------------------------------------------------------------------
# Seat-map constants shared between the route and the template
# ---------------------------------------------------------------------------

# Seats blocked for demonstration — spread across several rows so the map
# looks realistically occupied on first load.
DEMO_BLOCKED_SEATS = {
    "1A", "1C", "1D", "1F",
    "2B", "2E",
    "3C", "3D",
    "5A", "5F",
    "6B", "6E",
    "8C", "8D",
    "10A", "10F",
    "11B", "11E",
    "12C", "12D",
}

# Exit row number (1-indexed)
EXIT_ROW = 7


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ── Search ──────────────────────────────────────────────────────────────────

@app.route("/search", methods=["POST"])
def search():
    origin      = request.form.get("origin",      "").strip()
    destination = request.form.get("destination", "").strip()
    date        = request.form.get("date",        "").strip()

    if not origin or not destination or not date:
        flash("Please fill in all three search fields.", "warning")
        return redirect(url_for("index"))

    if origin.lower() == destination.lower():
        flash("Departure and destination cities cannot be the same.", "warning")
        return redirect(url_for("index"))

    origin_display      = resolve_city(origin)
    destination_display = resolve_city(destination)

    results = search_flights(origin, destination, date)

    return render_template(
        "results.html",
        flights        = results["flights"],
        is_alternative = results["is_alternative"],
        alt_date       = results["alt_date"],
        origin         = origin_display,
        destination    = destination_display,
        date           = date,
    )


# ── Booking form (GET) ───────────────────────────────────────────────────────

@app.route("/book/<int:flight_id>", methods=["GET"])
def booking_form(flight_id):
    """
    Renders the booking form with the interactive seat map.

    Passes to the template:
      flight       — the flight row
      booked_seats — JSON array of seat labels already taken (from real bookings
                     PLUS the demo-blocked set), so JS can mark them occupied
      exit_row     — row number of the emergency exit (for labelling)
    """
    flight = get_flight_by_id(flight_id)

    if flight is None:
        flash("Flight not found. Please search again.", "error")
        return redirect(url_for("index"))

    if flight["seats_available"] < 1:
        flash("Sorry, that flight is fully booked. Please choose another.", "warning")
        return redirect(url_for("index"))

    # Merge real bookings with demo-blocked seats
    real_booked  = get_booked_seats(flight_id)
    all_occupied = sorted(real_booked | DEMO_BLOCKED_SEATS)

    return render_template(
        "booking_form.html",
        flight       = flight,
        booked_seats = json.dumps(all_occupied),   # safe JSON for inline JS
        exit_row     = EXIT_ROW,
    )


# ── Seats JSON endpoint ──────────────────────────────────────────────────────

@app.route("/seats/<int:flight_id>")
def seats_json(flight_id):
    """
    Returns the current list of occupied seats for a flight as JSON.

    Used by the seat map to refresh availability without a full page reload.
    Response: { "booked": ["1A", "2C", ...] }
    """
    flight = get_flight_by_id(flight_id)
    if flight is None:
        return jsonify({"error": "Flight not found"}), 404

    real_booked  = get_booked_seats(flight_id)
    all_occupied = sorted(real_booked | DEMO_BLOCKED_SEATS)
    return jsonify({"booked": all_occupied})


# ── Create booking (POST) ────────────────────────────────────────────────────

@app.route("/book/<int:flight_id>", methods=["POST"])
def create_booking_route(flight_id):
    """
    Validates the booking form, saves the booking, and redirects to confirmation.

    Validation:
      - Full name, email, phone are non-empty
      - selected_seat is provided and is a valid seat label (1–12, A–F)
      - selected_seat is not already taken on this flight
      - trip_purpose is one of the allowed values
    """
    flight = get_flight_by_id(flight_id)
    if flight is None:
        flash("Flight not found.", "error")
        return redirect(url_for("index"))

    # Collect form fields
    passenger_name  = request.form.get("passenger_name",  "").strip()
    passenger_email = request.form.get("passenger_email", "").strip()
    passenger_phone = request.form.get("passenger_phone", "").strip()
    selected_seat   = request.form.get("selected_seat",   "").strip().upper()
    trip_purpose    = request.form.get("trip_purpose",    "Leisure")

    # Recompute occupied seats for re-rendering on error
    real_booked  = get_booked_seats(flight_id)
    all_occupied = sorted(real_booked | DEMO_BLOCKED_SEATS)

    # Build valid seat set for server-side validation
    valid_seats = {
        f"{row}{col}"
        for row in range(1, 13)
        for col in ("A", "B", "C", "D", "E", "F")
    }

    errors = []

    if not passenger_name:
        errors.append("Full name is required.")
    if not passenger_email or "@" not in passenger_email:
        errors.append("A valid email address is required.")
    if not passenger_phone:
        errors.append("Phone number is required.")
    if not selected_seat:
        errors.append("Please select a seat from the seat map.")
    elif selected_seat not in valid_seats:
        errors.append("The selected seat is not valid.")
    elif selected_seat in all_occupied:
        errors.append(f"Seat {selected_seat} is already taken. Please choose another.")
    if trip_purpose not in ("Business", "Leisure", "Family"):
        trip_purpose = "Leisure"

    if errors:
        for error in errors:
            flash(error, "error")
        return render_template(
            "booking_form.html",
            flight       = flight,
            booked_seats = json.dumps(all_occupied),
            exit_row     = EXIT_ROW,
        )

    # Attempt to save
    result = create_booking(
        flight_id       = flight_id,
        passenger_name  = passenger_name,
        passenger_email = passenger_email,
        passenger_phone = passenger_phone,
        selected_seat   = selected_seat,
        trip_purpose    = trip_purpose,
    )

    if result is None:
        flash("Booking failed — the flight may have just sold out. Please try again.", "error")
        return redirect(url_for("index"))

    if result == "SEAT_TAKEN":
        flash(
            f"Seat {selected_seat} was just taken by another passenger. "
            "Please select a different seat.",
            "error"
        )
        return render_template(
            "booking_form.html",
            flight       = flight,
            booked_seats = json.dumps(sorted(get_booked_seats(flight_id) | DEMO_BLOCKED_SEATS)),
            exit_row     = EXIT_ROW,
        )

    # PRG redirect — prevents duplicate submissions on browser refresh
    return redirect(url_for("confirmation", ref=result))


# ── Confirmation ─────────────────────────────────────────────────────────────

@app.route("/confirmation/<ref>")
def confirmation(ref):
    booking = get_booking_by_reference(ref)
    if booking is None:
        flash("Booking reference not found.", "error")
        return redirect(url_for("index"))
    return render_template("confirmation.html", booking=booking)


# ── Lookup ───────────────────────────────────────────────────────────────────

@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    if request.method == "POST":
        ref = request.form.get("booking_reference", "").strip().upper()
        if not ref:
            flash("Please enter a booking reference.", "warning")
            return render_template("lookup.html")
        booking = get_booking_by_reference(ref)
        if booking is None:
            flash(
                f"No booking found for reference '{ref}'. Please check and try again.",
                "error"
            )
            return render_template("lookup.html")
        return render_template("confirmation.html", booking=booking)
    return render_template("lookup.html")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", message="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        message="Something went wrong on our end. Please try again."
    ), 500


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=DEBUG)
