"use strict";

// =============================================================================
// AIRPORT DATA
// Each entry: { code, city, display }
// - code    : IATA code shown to the user and used as the form value
// - city    : canonical city name that resolve_city() maps this code to
// - display : the formatted string shown in the dropdown option
//
// Only airports that appear in seeded routes are included so users never
// select an option that can never produce a result.
// =============================================================================
const AIRPORTS = [
  { code: "ATL", city: "Atlanta",       display: "ATL — Atlanta"        },
  { code: "ORD", city: "Chicago",       display: "ORD — Chicago"        },
  { code: "DEN", city: "Denver",        display: "DEN — Denver"         },
  { code: "IAH", city: "Houston",       display: "IAH — Houston"        },
  { code: "LAX", city: "Los Angeles",   display: "LAX — Los Angeles"    },
  { code: "LHR", city: "London",        display: "LHR — London"         },
  { code: "MIA", city: "Miami",         display: "MIA — Miami"          },
  { code: "JFK", city: "New York",      display: "JFK — New York"       },
  { code: "LGA", city: "New York",      display: "LGA — New York"       },
  { code: "CDG", city: "Paris",         display: "CDG — Paris"          },
  { code: "SFO", city: "San Francisco", display: "SFO — San Francisco"  },
  { code: "SEA", city: "Seattle",       display: "SEA — Seattle"        },
  { code: "HND", city: "Tokyo",         display: "HND — Tokyo"          },
];


// =============================================================================
// AIRPORT COMBOBOX
// A lightweight, accessible autocomplete widget built without any library.
//
// Behaviour:
//   - Typing filters AIRPORTS by code OR city (case-insensitive substring)
//   - Clicking or pressing Enter/Space on an option selects it
//   - Arrow keys move focus through the list
//   - Escape closes the dropdown without selecting
//   - Clicking outside closes the dropdown
//   - The selected IATA code goes into the hidden <input> that the form submits
//   - The same-city guard prevents origin === destination
// =============================================================================

/**
 * Filters the airport list to entries whose code or city contains the query.
 * @param {string} query
 * @returns {Array}
 */
function filterAirports(query) {
  const q = query.trim().toLowerCase();
  if (!q) return AIRPORTS;
  return AIRPORTS.filter(
    (a) =>
      a.code.toLowerCase().includes(q) ||
      a.city.toLowerCase().includes(q)
  );
}

/**
 * Creates and wires up one airport combobox.
 *
 * @param {HTMLInputElement} displayInput  — the visible text field
 * @param {HTMLInputElement} hiddenInput   — the hidden field submitted by the form
 * @param {HTMLUListElement} listbox       — the <ul> dropdown
 * @param {string}           pairHiddenId — id of the OTHER hidden input (for same-city guard)
 */
function initAirportCombobox(displayInput, hiddenInput, listbox, pairHiddenId) {

  let activeIndex = -1; // index of the currently keyboard-focused option

  // ── Open dropdown and render filtered options ──────────────────────────
  function openDropdown(query) {
    const matches = filterAirports(query);
    listbox.innerHTML = "";
    activeIndex = -1;

    if (matches.length === 0) {
      listbox.hidden = true;
      displayInput.setAttribute("aria-expanded", "false");
      return;
    }

    matches.forEach((airport, i) => {
      const li = document.createElement("li");
      li.className = "airport-input__option";
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.setAttribute("data-code", airport.code);
      li.setAttribute("data-city", airport.city);
      li.setAttribute("tabindex", "-1");
      li.id = `${displayInput.id}-option-${i}`;

      // Highlight the matched portion of the display string
      const raw = airport.display;
      const q   = query.trim().toLowerCase();
      if (q) {
        const idx = raw.toLowerCase().indexOf(q);
        if (idx !== -1) {
          li.innerHTML =
            escapeHtml(raw.slice(0, idx)) +
            "<mark>" + escapeHtml(raw.slice(idx, idx + q.length)) + "</mark>" +
            escapeHtml(raw.slice(idx + q.length));
        } else {
          li.textContent = raw;
        }
      } else {
        li.textContent = raw;
      }

      li.addEventListener("mousedown", (e) => {
        // mousedown fires before blur — prevent the blur from closing first
        e.preventDefault();
        selectOption(airport);
      });

      listbox.appendChild(li);
    });

    listbox.hidden = false;
    displayInput.setAttribute("aria-expanded", "true");
  }

  // ── Close dropdown ────────────────────────────────────────────────────
  function closeDropdown() {
    listbox.hidden = true;
    displayInput.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  }

  // ── Select an option ──────────────────────────────────────────────────
  function selectOption(airport) {
    displayInput.value = airport.display;
    hiddenInput.value  = airport.city;  // Submit the canonical city name, not the code
    closeDropdown();
    displayInput.dispatchEvent(new Event("change"));
  }

  // ── Move keyboard focus within the list ───────────────────────────────
  function moveFocus(direction) {
    const options = listbox.querySelectorAll(".airport-input__option");
    if (!options.length) return;

    // Remove highlight from current
    if (activeIndex >= 0) {
      options[activeIndex].classList.remove("airport-input__option--active");
      options[activeIndex].setAttribute("aria-selected", "false");
    }

    activeIndex = activeIndex + direction;
    if (activeIndex < 0)               activeIndex = options.length - 1;
    if (activeIndex >= options.length) activeIndex = 0;

    options[activeIndex].classList.add("airport-input__option--active");
    options[activeIndex].setAttribute("aria-selected", "true");
    displayInput.setAttribute("aria-activedescendant", options[activeIndex].id);
    // Scroll option into view if the list is taller than its container
    options[activeIndex].scrollIntoView({ block: "nearest" });
  }

  // ── Input events ──────────────────────────────────────────────────────
  displayInput.addEventListener("input", () => {
    hiddenInput.value = ""; // Clear selection whenever user types again
    openDropdown(displayInput.value);
    clearSameCityError();
  });

  displayInput.addEventListener("focus", () => {
    openDropdown(displayInput.value);
  });

  displayInput.addEventListener("blur", () => {
    // Small delay so a mousedown on an option fires before we close
    setTimeout(closeDropdown, 150);
  });

  displayInput.addEventListener("keydown", (e) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (listbox.hidden) openDropdown(displayInput.value);
        moveFocus(1);
        break;

      case "ArrowUp":
        e.preventDefault();
        if (listbox.hidden) openDropdown(displayInput.value);
        moveFocus(-1);
        break;

      case "Enter":
      case " ":
        if (!listbox.hidden && activeIndex >= 0) {
          e.preventDefault();
          const active = listbox.querySelector(".airport-input__option--active");
          if (active) {
            selectOption({
              code: active.dataset.code,
              city: active.dataset.city,
              display: active.textContent.replace(/<\/?mark>/g, ""), // Strip highlight tags
            });
          }
        }
        break;

      case "Escape":
        closeDropdown();
        break;

      case "Tab":
        // Accept the highlighted option when tabbing away, if one is focused
        if (!listbox.hidden && activeIndex >= 0) {
          const active = listbox.querySelector(".airport-input__option--active");
          if (active) {
            selectOption({
              code: active.dataset.code,
              city: active.dataset.city,
              display: active.textContent.replace(/<\/?mark>/g, ""), // Strip highlight tags
            });
          }
        }
        break;
    }
  });
}

// =============================================================================
// SAME-CITY GUARD
// Prevents submitting when origin === destination (by resolved city).
// Shows an inline error instead of an alert().
// =============================================================================

function clearSameCityError() {
  const errEl = document.getElementById("search-form-error");
  if (errEl) {
    errEl.hidden = true;
    errEl.textContent = "";
  }
}

function showSameCityError(msg) {
  const errEl = document.getElementById("search-form-error");
  if (errEl) {
    errEl.textContent = msg;
    errEl.hidden = false;
  }
}

/**
 * Returns the resolved city for an IATA code, or the raw value if not found.
 * Mirrors the server-side resolve_city() logic so the client guard is accurate.
 */
function resolveCity(value) {
  const v = value.trim();
  // Now the hidden input contains city names, not codes, so just return as-is
  // (The combobox already stores the canonical city name)
  return v;
}

// =============================================================================
// HTML ESCAPE UTILITY
// Used when injecting user input into innerHTML for match highlighting.
// =============================================================================
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}


// =============================================================================
// DOM-READY INITIALISATION
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {

  // ── Date input: minimum = today ─────────────────────────────────────────
  const today = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach((input) => {
    input.setAttribute("min", today);
  });

  // ── Flash message auto-dismiss ──────────────────────────────────────────
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.5s ease";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 500);
    }, 5000);
  });

  // ── Initialise airport comboboxes ───────────────────────────────────────
  const originDisplay     = document.getElementById("origin-display");
  const originHidden      = document.getElementById("origin");
  const originListbox     = document.getElementById("origin-listbox");

  const destDisplay       = document.getElementById("destination-display");
  const destHidden        = document.getElementById("destination");
  const destListbox       = document.getElementById("destination-listbox");

  if (originDisplay && originHidden && originListbox) {
    initAirportCombobox(originDisplay, originHidden, originListbox, "destination");
  }

  if (destDisplay && destHidden && destListbox) {
    initAirportCombobox(destDisplay, destHidden, destListbox, "origin");
  }

  // ── Search form submit: same-city guard + hidden-field validation ────────
  const searchForm = document.getElementById("search-form");
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      const originVal = originHidden ? originHidden.value.trim() : "";
      const destVal   = destHidden   ? destHidden.value.trim()   : "";

      // Require a selection from the dropdown (hidden fields must be filled)
      if (!originVal) {
        e.preventDefault();
        showSameCityError("Please select a departure airport from the list.");
        originDisplay && originDisplay.focus();
        return;
      }

      if (!destVal) {
        e.preventDefault();
        showSameCityError("Please select a destination airport from the list.");
        destDisplay && destDisplay.focus();
        return;
      }

      // Same-city check using resolved city names
      const originCity = resolveCity(originVal);
      const destCity   = resolveCity(destVal);

      if (originCity.toLowerCase() === destCity.toLowerCase()) {
        e.preventDefault();
        showSameCityError(
          "Departure and destination cannot be the same city. Please choose different airports."
        );
        return;
      }

      clearSameCityError();
    });
  }

  // ── Lookup form validation ───────────────────────────────────────────────
  const lookupForm = document.getElementById("lookup-form");
  if (lookupForm) {
    lookupForm.addEventListener("submit", (e) => {
      const ref = document.getElementById("booking_reference")?.value.trim();
      if (!ref) {
        e.preventDefault();
        alert("Please enter a booking reference.");
      }
    });
  }

});


// =============================================================================
// SEAT MAP
// Renders a 12-row × 6-column (A–F) interactive seat map inside #seat-rows.
//
// Data flow:
//   1. The server embeds the occupied-seat list in data-booked on #seat-rows.
//   2. initSeatMap() reads that list, builds the DOM, and wires click handlers.
//   3. When a user clicks an available seat the hidden #selected_seat input
//      is updated and the summary panel is refreshed.
//   4. The Confirm Booking button stays disabled until a seat is selected.
// =============================================================================

/**
 * Returns a human-readable position label for a seat letter.
 * @param {string} letter  — "A" through "F"
 * @returns {string}
 */
function seatType(letter) {
  const map = { A: "Window", B: "Middle", C: "Aisle",
                D: "Aisle",  E: "Middle", F: "Window" };
  return map[letter] || "";
}

/**
 * Returns a cabin-position label based on row number.
 * @param {number} row  — 1-indexed row number
 * @returns {string}
 */
function cabinZone(row) {
  if (row <= 4)  return "Front Cabin";
  if (row <= 8)  return "Mid Cabin";
  return "Rear Cabin";
}

/**
 * Builds the seat map inside the #seat-rows container and wires all
 * interactivity. Called once from the DOMContentLoaded handler.
 */
function initSeatMap() {
  const container = document.getElementById("seat-rows");
  if (!container) return;   // not on the booking form page

  // Parse server-provided occupied seat list from the data attribute
  let booked;
  try {
    booked = new Set(JSON.parse(container.dataset.booked || "[]"));
  } catch (_) {
    booked = new Set();
  }
  const exitRow     = parseInt(container.dataset.exitRow || "7", 10);
  const hiddenInput = document.getElementById("selected_seat");
  const confirmBtn  = document.getElementById("confirm-btn");
  const promptEl    = document.getElementById("seat-summary-prompt");
  const detailEl    = document.getElementById("seat-summary-detail");
  const badgeEl     = document.getElementById("seat-summary-badge");
  const typeEl      = document.getElementById("seat-summary-type");
  const posEl       = document.getElementById("seat-summary-position");

  let selectedSeat = null;   // tracks the currently selected seat label

  const ROWS = 12;
  const COLS = ["A", "B", "C", "D", "E", "F"];

  // ── Build DOM ─────────────────────────────────────────────────────────
  for (let r = 1; r <= ROWS; r++) {
    // Add cabin section labels
    if (r === 1) {
      const frontLabel = document.createElement("div");
      frontLabel.className = "cabin-section-label";
      frontLabel.textContent = "✈ Front Cabin";
      container.appendChild(frontLabel);
    }
    if (r === 5) {
      const midLabel = document.createElement("div");
      midLabel.className = "cabin-section-label";
      midLabel.textContent = "Mid Cabin";
      container.appendChild(midLabel);
    }
    if (r === 9) {
      const rearLabel = document.createElement("div");
      rearLabel.className = "cabin-section-label";
      rearLabel.textContent = "Rear Cabin";
      container.appendChild(rearLabel);
    }

    const rowEl = document.createElement("div");
    rowEl.className = "seat-row" + (r === exitRow ? " seat-row--exit" : "");
    rowEl.setAttribute("role", "group");
    rowEl.setAttribute("aria-label", `Row ${r}${r === exitRow ? " — Emergency Exit" : ""}`);

    // Row number label
    const numEl = document.createElement("div");
    numEl.className = "seat-row__number";
    numEl.textContent = r;
    numEl.setAttribute("aria-hidden", "true");
    rowEl.appendChild(numEl);

    COLS.forEach((col, idx) => {
      // Insert aisle spacer between C (idx 2) and D (idx 3)
      if (idx === 3) {
        const aisleEl = document.createElement("div");
        aisleEl.className = "seat-row__aisle";
        aisleEl.setAttribute("aria-hidden", "true");
        if (r === exitRow) {
          aisleEl.innerHTML = '<span class="seat-row__exit-marker" title="Emergency Exit">⚠</span>';
        }
        rowEl.appendChild(aisleEl);
      }

      const label     = `${r}${col}`;
      const isBooked  = booked.has(label);

      const seatEl = document.createElement("button");
      seatEl.type      = "button";   // prevent accidental form submission
      seatEl.className = "seat " + (isBooked ? "seat--occupied" : "seat--available");
      seatEl.textContent = col;
      seatEl.setAttribute("aria-label",
        `Seat ${label} — ${seatType(col)}${isBooked ? " — Occupied" : ""}`
      );
      seatEl.dataset.seat = label;

      if (isBooked) {
        seatEl.disabled = true;
        seatEl.setAttribute("aria-disabled", "true");
      } else {
        seatEl.addEventListener("click", () => onSeatClick(label, seatEl));
        seatEl.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSeatClick(label, seatEl);
          }
        });
      }

      rowEl.appendChild(seatEl);
    });

    container.appendChild(rowEl);
  }

  // ── Seat click handler ────────────────────────────────────────────────
  function onSeatClick(label, seatEl) {
    // Deselect previous seat
    if (selectedSeat) {
      const prev = container.querySelector(`.seat[data-seat="${selectedSeat}"]`);
      if (prev) {
        prev.classList.remove("seat--selected");
        prev.classList.add("seat--available");
        prev.setAttribute("aria-pressed", "false");
      }
    }

    // Select new seat (or deselect if clicking the same one)
    if (selectedSeat === label) {
      selectedSeat = null;
      hiddenInput.value = "";
      if (confirmBtn) confirmBtn.disabled = true;
      updateSummary(null);
      return;
    }

    selectedSeat = label;
    seatEl.classList.remove("seat--available");
    seatEl.classList.add("seat--selected");
    seatEl.setAttribute("aria-pressed", "true");

    hiddenInput.value = label;
    if (confirmBtn) confirmBtn.disabled = false;

    const row = parseInt(label.slice(0, -1), 10);
    const col = label.slice(-1);
    updateSummary({ label, type: seatType(col), zone: cabinZone(row) });
  }

  // ── Update summary panel ──────────────────────────────────────────────
  function updateSummary(info) {
    if (!info) {
      promptEl.textContent = "No seat selected";
      if (detailEl)  detailEl.hidden = true;
      return;
    }
    promptEl.textContent  = "";
    badgeEl.textContent   = `Seat ${info.label}`;
    typeEl.textContent    = info.type;
    posEl.textContent     = info.zone;
    if (detailEl) detailEl.hidden = false;
  }
}

// Wire initSeatMap into the existing DOMContentLoaded listener by appending
// a standalone listener (the existing one in the file handles the search form).
document.addEventListener("DOMContentLoaded", initSeatMap);
