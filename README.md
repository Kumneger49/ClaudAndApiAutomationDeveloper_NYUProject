# NYU AV Operations Dashboard

A unified web dashboard for NYU Audio-Visual Operations that connects two spreadsheets — AV Equipment Inventory and Staff Shift Schedules — into a single interface with Role-Based Access Control (RBAC) and AI-powered device command generation.

---

## Quick Start (Run Locally in 3 Steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Add your Gemini API key for AI features
cp .env.example .env
# Open .env and replace the placeholder with your key from aistudio.google.com

# 3. Launch the app
streamlit run app.py
```

To clone from GitHub first:

```bash
git clone https://github.com/Kumneger49/ClaudAndApiAutomationDeveloper_NYUProject.git
cd ClaudAndApiAutomationDeveloper_NYUProject
```

Open **http://localhost:8501** in your browser. That's it.

> **No API key?** The app works fully without one — the AI Command tab uses a built-in keyword parser as fallback (see details below).

---

## Test Credentials

Log in with either account to explore different access levels:

| Role | Username | Password | What you can do |
|---|---|---|---|
| **Manager** | `manager` | `mgr123` | View data + send device commands + see audit log |
| **Technician** | `technician` | `tech123` | View data only (read-only) |

---

## Features

### All Users
- **Equipment Inventory** — 14 AV devices across 5 rooms, filterable by type, building, and status
- **Staff Schedules** — 13 shifts across 3 days, filterable by date, role, and building

### Manager Only
- **Device Control — Form Builder**: pick a device and command from dropdowns, set parameters, generate a JSON control payload
- **Device Control — AI Command**: type a plain-English command and get a structured JSON payload back
- **Audit Log**: every command sent this session, with full JSON, timestamp, and issuing user

### Role Enforcement
Technicians see only 2 tabs. The Device Control and Audit Log tabs are hidden entirely — not just disabled. This is enforced server-side via Streamlit session state.

---

## How to Use the AI Command Feature

1. Log in as `manager / mgr123`
2. Click the **⚡ Device Control** tab
3. Click the **🤖 AI Command (Gemini)** sub-tab
4. Type a plain-English command or pick one of the examples:
   - `Turn on the projector in Room 101 and set input to HDMI 1`
   - `Mute the DSP in Auditorium A`
   - `Set volume to 75 on Room 202 DSP`
   - `Power off all projectors`
5. Click **Generate** — a JSON payload appears immediately below

### How the AI works (and the fallback)

The app calls **Google Gemini 2.0 Flash** to parse natural language into structured JSON. Gemini is given the full device registry as context so it can resolve room names, device types, and valid commands intelligently.

If Gemini is unavailable (no API key, quota exceeded, or network error), the app **automatically falls back to a built-in keyword parser** — no error shown to the user, no broken state. The fallback uses keyword matching and regex to produce an identical JSON structure. This means the app is fully functional in any environment.

You can tell which path ran by checking the `parsed_by` field in the JSON output:
- `"parsed_by"` absent → Gemini was used
- `"parsed_by": "local_nlp"` → fallback parser was used

---

## Example JSON Payload

```json
{
  "device_id": "PRJ_001",
  "device_type": "Projector",
  "device_name": "Epson EB-L1505U",
  "room": "Room 101",
  "ip_address": "192.168.1.101",
  "command": "power_on",
  "parameters": {
    "input_source": "HDMI_1"
  },
  "issued_by": "manager_system",
  "timestamp": "2026-06-23T10:30:00Z",
  "priority": "normal",
  "ack_required": true
}
```

Every payload is also saved to the **📋 Audit Log** tab and can be downloaded as a `.json` file.

---

## Data Sources

| Source | Description | File |
|---|---|---|
| Spreadsheet A | AV Equipment Inventory — 14 devices across 5 rooms | `data/equipment.csv` |
| Spreadsheet B | Staff Shift Schedules — 13 shifts across 3 days | `data/schedules.csv` |
| Device Registry | Device configs, valid commands, and parameters | `config/devices.json` |

Mock data covers real NYU-style AV hardware: Epson and Christie projectors, QSC and Biamp DSPs, Crestron and Extron switchers, and PTZOptics cameras across Bobst Library, Kimmel Center, and Silver Center.

---

## Project Structure

```
.
├── app.py                  # Main Streamlit application (~890 lines)
├── data/
│   ├── equipment.csv       # AV Equipment Inventory (Spreadsheet A)
│   └── schedules.csv       # Staff Shift Schedules (Spreadsheet B)
├── config/
│   └── devices.json        # Device registry, commands, and valid parameters
├── requirements.txt
├── .env.example            # API key template
└── .env                    # Your API key — never committed
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI framework | Python + Streamlit |
| Data manipulation | Pandas |
| AI (primary) | Google Gemini 2.0 Flash via `google-genai` SDK |
| AI (fallback) | Built-in keyword + regex parser |
| Access control | Session-based RBAC (no backend database needed) |
| Secrets | `python-dotenv` — key stored in `.env`, gitignored |

---

## Getting a Gemini API Key (Optional)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API key** → **Create API key**
3. Copy the key into your `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```

The free tier gives 15 requests/minute — more than enough for testing.
