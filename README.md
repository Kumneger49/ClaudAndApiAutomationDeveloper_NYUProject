# NYU AV Operations Dashboard

A unified web dashboard for NYU Audio-Visual Operations that connects two spreadsheets — AV Equipment Inventory and Staff Shift Schedules — into a single interface with Role-Based Access Control (RBAC) and AI-powered device command generation.

**Live app:** https://kumneger49-claudandapiautomationdeveloper-nyuproject-app-ix4df2.streamlit.app/
**Source code:** https://github.com/Kumneger49/ClaudAndApiAutomationDeveloper_NYUProject

---

## Quick Start (Run Locally in 3 Steps)

```bash
# Clone the repo
git clone https://github.com/Kumneger49/ClaudAndApiAutomationDeveloper_NYUProject.git
cd ClaudAndApiAutomationDeveloper_NYUProject

# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Add your Gemini API key for AI features
cp .env.example .env
# Open .env and replace the placeholder with your key from aistudio.google.com

# 3. Launch the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

> **No API key?** The app works fully without one — the AI Command tab uses a built-in keyword parser as fallback (see [How the AI works](#how-the-ai-works-and-the-fallback)).

---

## How to Test the Roles

Log in with either account on the login screen:

| Role | Username | Password | Access |
|---|---|---|---|
| **Manager** | `manager` | `mgr123` | Equipment + Schedules + Device Control + Audit Log |
| **Technician** | `technician` | `tech123` | Equipment + Schedules only (read-only) |

Logging in as **Technician** shows two read-only tabs. The Device Control and Audit Log tabs are not rendered at all — the restriction is enforced server-side via session state, not just hidden in the UI.

Logging in as **Manager** unlocks the full dashboard including device command generation.

---

## How to Trigger a Device Command (Manager only)

1. Log in as `manager / mgr123`
2. Click the **⚡ Device Control** tab
3. Choose either mode:

**Option A — Form Builder**
- Select a device from the dropdown (e.g. *Epson EB-L1505U — Room 101*)
- Pick a command (e.g. `power_on`)
- Set any parameters (e.g. input source, volume level)
- Click **⚡ Send Command**

**Option B — AI Command**
- Click the **🤖 AI Command (Gemini)** sub-tab
- Type a plain-English instruction, or pick an example:
  - `Turn on the projector in Room 101 and set input to HDMI 1`
  - `Mute the DSP in Auditorium A`
  - `Set volume to 75 on Room 202 DSP`
  - `Power off all projectors`
  - `Recall preset 3 on the Auditorium A camera`
- Click **Generate**

---

## Where to View the Generated JSON Payload

The payload appears immediately below the control panel after every command:

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

You can also:
- **Download** the payload as a `.json` file using the Download button
- **Review the full session history** in the **📋 Audit Log** tab — every command sent, with timestamp, issuing user, target device, and complete JSON

---

## How the AI Works (and the Fallback)

The app calls **Google Gemini 2.0 Flash** to parse natural language into structured JSON. Gemini receives the full device registry as context so it can resolve room names, device types, and valid commands intelligently.

If Gemini is unavailable (no API key, quota exceeded, or network error), the app **silently falls back to a built-in keyword parser** — no error is shown, no broken state. The fallback uses keyword matching and regex to produce an identical JSON structure. The app is fully functional in either mode.

You can tell which path ran by checking the `parsed_by` field in the output:
- `"parsed_by"` absent → Gemini was used
- `"parsed_by": "local_nlp"` → fallback parser was used

---

## Mock Data Sources

Both spreadsheets are included in the repository as CSV files:

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
├── app.py                  # Main Streamlit application
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
