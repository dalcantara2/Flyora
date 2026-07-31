"""
checklist.py
------------
Smart Travel Assistant — generates a personalized travel checklist after booking.

This module is a stub for Phase 1. The full rule engine will be implemented
in Phase 3. For now the function signature and category structure are defined
so app.py and the confirmation template can import it without errors.
"""


def generate_checklist(trip_purpose, destination_city, duration_minutes):
    """
    Returns a personalized travel checklist as a dictionary of categories.

    Parameters
    ----------
    trip_purpose      : str  — "Business", "Leisure", or "Family"
    destination_city  : str  — e.g. "London", "Tokyo"
    duration_minutes  : int  — total flight duration in minutes

    Returns
    -------
    dict  — keys are category names (str), values are lists of item strings.
            Example:
            {
                "Documents":        ["Passport", "Boarding pass"],
                "Health & Comfort":  ["Neck pillow", "Earplugs"],
            }

    Phase 3 will expand this with destination-aware and purpose-aware rules.
    For now it returns a minimal placeholder so the confirmation page renders.
    """

    # ------------------------------------------------------------------
    # Phase 1 placeholder — always returns the same base checklist.
    # Phase 3 will replace this body with the full rule engine.
    # ------------------------------------------------------------------
    checklist = {
        "Documents": [
            "Valid passport or government-issued ID",
            "Boarding pass (printed or mobile)",
            "Booking confirmation (reference number)",
            "Travel insurance documents",
        ],
        "Essentials": [
            "Phone charger and power bank",
            "Headphones or earbuds",
            "Wallet with local currency or travel card",
            "Medications and prescriptions",
        ],
        "Health & Comfort": [
            "Reusable water bottle",
            "Hand sanitizer and face mask",
            "Snacks for the journey",
        ],
    }

    return checklist
