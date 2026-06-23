import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from google import genai

APP_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(APP_DIR, ".env"), override=True)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NYU AV Operations Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Gemini setup ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
gemini_client = None
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_AVAILABLE = False

if GEMINI_API_KEY and GEMINI_API_KEY != "paste_your_new_api_key_here":
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception:
        pass

# ── User registry (in production this would be a database) ───────────────────
USERS = {
    "manager": {
        "password": "mgr123",
        "role": "Manager",
        "name": "Ricardo Rivera",
        "email": "rr63@nyu.edu",
    },
    "technician": {
        "password": "tech123",
        "role": "Technician",
        "name": "John Carter",
        "email": "jc@nyu.edu",
    },
    "technician2": {
        "password": "tech456",
        "role": "Technician",
        "name": "Sarah Lee",
        "email": "sl@nyu.edu",
    },
    "manager2": {
        "password": "mgr456",
        "role": "Manager",
        "name": "Omar Clavijo",
        "email": "oc560@nyu.edu",
    },
}

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_equipment():
    return pd.read_csv("data/equipment.csv")

@st.cache_data
def load_schedules():
    return pd.read_csv("data/schedules.csv")

@st.cache_data
def load_device_config():
    with open("config/devices.json") as f:
        return json.load(f)

# ── Session state init ────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "command_log" not in st.session_state:
    st.session_state.command_log = []
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; color: #e0e0e0; }

    /* Login card */
    .login-card {
        background: #1a1d27;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 2.5rem;
        max-width: 420px;
        margin: 4rem auto;
    }

    /* Role badge */
    .badge-manager {
        background: #1a3a5c;
        color: #63b3ed;
        border: 1px solid #2b6cb0;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 13px;
        font-weight: 600;
    }
    .badge-technician {
        background: #1a3a2c;
        color: #68d391;
        border: 1px solid #276749;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Status pills */
    .status-online { color: #68d391; font-weight: 600; }
    .status-offline { color: #fc8181; font-weight: 600; }
    .status-maintenance { color: #f6ad55; font-weight: 600; }

    /* Device control panel */
    .control-panel {
        background: #1a1d27;
        border: 1px solid #2b6cb0;
        border-radius: 10px;
        padding: 1.5rem;
    }

    /* JSON payload box */
    .json-box {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #7ee787;
        white-space: pre;
        overflow-x: auto;
    }

    /* Log entry */
    .log-entry {
        background: #161b22;
        border-left: 3px solid #2b6cb0;
        border-radius: 4px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 13px;
    }

    /* Metric cards */
    .metric-card {
        background: #1a1d27;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }

    /* Section header */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #90cdf4;
        border-bottom: 1px solid #2d3748;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        background: transparent;
        border: none;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ════════════════════════════════════════════════════════════════════════════
def show_login():
    _, col2, _ = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 3rem 0 1rem 0;'>
            <div style='font-size: 3rem;'>🎬</div>
            <h1 style='color:#e2e8f0; font-size:1.8rem; margin:0.5rem 0 0.2rem 0;'>
                NYU AV Operations
            </h1>
            <p style='color:#718096; font-size:0.9rem; margin-bottom:2rem;'>
                Audio-Visual Management Dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "username": username,
                        **USERS[username]
                    }
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.markdown("""
        <div style='background:#161b22; border:1px solid #2d3748; border-radius:8px;
                    padding:1rem; margin-top:1.5rem;'>
            <p style='color:#718096; font-size:0.8rem; margin:0 0 0.5rem 0; font-weight:600;'>
                TEST CREDENTIALS
            </p>
            <p style='color:#a0aec0; font-size:0.85rem; margin:0.2rem 0;'>
                👔 <b>Manager:</b> &nbsp; manager / mgr123
            </p>
            <p style='color:#a0aec0; font-size:0.85rem; margin:0.2rem 0;'>
                🔧 <b>Technician:</b> &nbsp; technician / tech123
            </p>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ════════════════════════════════════════════════════════════════════════════
def show_header():
    user = st.session_state.user
    badge_class = "badge-manager" if user["role"] == "Manager" else "badge-technician"
    role_icon = "👔" if user["role"] == "Manager" else "🔧"

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style='padding: 0.8rem 0;'>
            <span style='font-size:1.5rem; font-weight:700; color:#e2e8f0;'>
                🎬 NYU AV Operations Dashboard
            </span>
            <span style='color:#718096; font-size:0.9rem; margin-left:1rem;'>
                Audio-Visual Management System
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='text-align:right; padding:0.8rem 0;'>
            <span style='color:#a0aec0; font-size:0.85rem;'>
                {role_icon} <b style='color:#e2e8f0;'>{user["name"]}</b>
                &nbsp;
                <span class='{badge_class}'>{user["role"]}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Sign Out", key="signout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    st.divider()


# ════════════════════════════════════════════════════════════════════════════
# METRICS ROW
# ════════════════════════════════════════════════════════════════════════════
def show_metrics(equipment_df, schedules_df):
    total = len(equipment_df)
    online = len(equipment_df[equipment_df["status"] == "Online"])
    offline = len(equipment_df[equipment_df["status"] == "Offline"])
    maintenance = len(equipment_df[equipment_df["status"] == "Maintenance"])
    today_shifts = len(schedules_df[schedules_df["shift_date"] == datetime.now().strftime("%Y-%m-%d")])
    commands_sent = len(st.session_state.command_log)

    cols = st.columns(6)
    metrics = [
        ("Total Devices", total, "#90cdf4"),
        ("Online", online, "#68d391"),
        ("Offline", offline, "#fc8181"),
        ("Maintenance", maintenance, "#f6ad55"),
        ("Shifts Today", today_shifts, "#b794f4"),
        ("Commands Sent", commands_sent, "#63b3ed"),
    ]
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:1.8rem; font-weight:700; color:{color};'>{value}</div>
                <div style='font-size:0.75rem; color:#718096; margin-top:0.2rem;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# EQUIPMENT TAB
# ════════════════════════════════════════════════════════════════════════════
def show_equipment(equipment_df):
    st.markdown("<div class='section-header'>📦 AV Equipment Inventory</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.multiselect(
            "Device Type",
            options=sorted(equipment_df["device_type"].unique()),
            default=[],
            placeholder="All types",
            key="eq_type_filter",
        )
    with col2:
        building_filter = st.multiselect(
            "Building",
            options=sorted(equipment_df["building"].unique()),
            default=[],
            placeholder="All buildings",
            key="eq_building_filter",
        )
    with col3:
        status_filter = st.multiselect(
            "Status",
            options=["Online", "Offline", "Maintenance"],
            default=[],
            placeholder="All statuses",
            key="eq_status_filter",
        )

    filtered = equipment_df.copy()
    if type_filter:
        filtered = filtered[filtered["device_type"].isin(type_filter)]
    if building_filter:
        filtered = filtered[filtered["building"].isin(building_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    # Color-coded status column
    def style_status(val):
        colors = {"Online": "#68d391", "Offline": "#fc8181", "Maintenance": "#f6ad55"}
        return f"color: {colors.get(val, 'white')}; font-weight: 600"

    display_df = filtered[[
        "equipment_id", "device_name", "device_type", "room",
        "building", "ip_address", "status", "last_maintenance", "assigned_staff"
    ]].rename(columns={
        "equipment_id": "ID",
        "device_name": "Device",
        "device_type": "Type",
        "room": "Room",
        "building": "Building",
        "ip_address": "IP Address",
        "status": "Status",
        "last_maintenance": "Last Maintenance",
        "assigned_staff": "Assigned Staff",
    })

    styled = display_df.style.map(style_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)
    st.caption(f"Showing {len(filtered)} of {len(equipment_df)} devices")


# ════════════════════════════════════════════════════════════════════════════
# SCHEDULES TAB
# ════════════════════════════════════════════════════════════════════════════
def show_schedules(schedules_df):
    st.markdown("<div class='section-header'>📅 Staff Shift Schedules</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        date_filter = st.selectbox(
            "Date",
            options=["All dates"] + sorted(schedules_df["shift_date"].unique()),
            key="sched_date_filter",
        )
    with col2:
        role_filter = st.multiselect(
            "Staff Role",
            options=sorted(schedules_df["role"].unique()),
            default=[],
            placeholder="All roles",
            key="sched_role_filter",
        )
    with col3:
        building_filter = st.multiselect(
            "Building",
            options=sorted(schedules_df["building"].unique()),
            default=[],
            placeholder="All buildings",
            key="sched_building_filter",
        )

    filtered = schedules_df.copy()
    if date_filter != "All dates":
        filtered = filtered[filtered["shift_date"] == date_filter]
    if role_filter:
        filtered = filtered[filtered["role"].isin(role_filter)]
    if building_filter:
        filtered = filtered[filtered["building"].isin(building_filter)]

    def style_role(val):
        return "color: #63b3ed; font-weight: 600" if val == "Manager" else "color: #68d391"

    display_df = filtered[[
        "shift_id", "staff_name", "role", "shift_date",
        "start_time", "end_time", "room", "building", "notes"
    ]].rename(columns={
        "shift_id": "Shift ID",
        "staff_name": "Staff Name",
        "role": "Role",
        "shift_date": "Date",
        "start_time": "Start",
        "end_time": "End",
        "room": "Room",
        "building": "Building",
        "notes": "Notes",
    })

    styled = display_df.style.map(style_role, subset=["Role"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)
    st.caption(f"Showing {len(filtered)} of {len(schedules_df)} shifts")


# ════════════════════════════════════════════════════════════════════════════
# LOCAL PARSER: Natural language → JSON payload (offline fallback)
# ════════════════════════════════════════════════════════════════════════════
def parse_command_locally(prompt, device_config):
    text = prompt.lower()

    # Map keywords → commands
    command_map = {
        "power on": "power_on", "turn on": "power_on", "switch on": "power_on", "start": "power_on",
        "power off": "power_off", "turn off": "power_off", "switch off": "power_off", "shut down": "power_off",
        "mute": "mute", "silence": "mute",
        "unmute": "unmute", "un-mute": "unmute",
        "freeze": "freeze", "pause": "freeze",
        "unfreeze": "unfreeze", "resume": "unfreeze",
        "volume": "set_volume", "set volume": "set_volume",
        "input": "set_input", "set input": "set_input", "switch input": "set_input", "switch to": "set_input",
        "brightness": "set_brightness", "set brightness": "set_brightness",
        "route": "route_audio", "audio": "route_audio",
        "reset": "reset",
        "status": "get_status",
        "zoom in": "zoom", "zoom out": "zoom",
        "pan left": "pan", "pan right": "pan",
        "tilt up": "tilt", "tilt down": "tilt",
        "preset": "preset_recall",
    }

    # Map device type keywords
    type_map = {
        "projector": "Projector", "proj": "Projector",
        "dsp": "DSP", "audio": "DSP", "sound": "DSP",
        "switcher": "Switcher", "switch": "Switcher",
        "display": "Display", "screen": "Display", "monitor": "Display",
        "camera": "PTZ Camera", "cam": "PTZ Camera", "ptz": "PTZ Camera",
    }

    # Map room/building keywords to device IDs
    room_map = {
        "101": ["PRJ_001", "DSP_001", "SWT_001"],
        "room 101": ["PRJ_001", "DSP_001", "SWT_001"],
        "202": ["PRJ_002", "DSP_002", "SWT_002"],
        "room 202": ["PRJ_002", "DSP_002", "SWT_002"],
        "303": ["PRJ_004", "CAM_002"],
        "room 303": ["PRJ_004", "CAM_002"],
        "auditorium": ["PRJ_003", "DSP_003", "SWT_003", "CAM_001"],
        "auditorium a": ["PRJ_003", "DSP_003", "SWT_003", "CAM_001"],
        "conference": ["DSP_004", "DSP_005"],
        "conference room b": ["DSP_004", "DSP_005"],
        "silver": ["PRJ_004", "DSP_004", "DSP_005", "CAM_002"],
        "bobst": ["PRJ_001", "PRJ_002", "DSP_001", "DSP_002", "SWT_001", "SWT_002"],
        "kimmel": ["PRJ_003", "DSP_003", "SWT_003", "CAM_001"],
    }

    # Detect command
    detected_command = "power_on"
    for keyword, cmd in command_map.items():
        if keyword in text:
            detected_command = cmd
            break

    # Detect input source
    input_source = None
    for src in ["hdmi_1", "hdmi_2", "hdmi 1", "hdmi 2", "displayport", "vga", "hdbaset"]:
        if src in text:
            input_source = src.replace(" ", "_").upper()
            break

    # Detect volume level
    volume_level = None
    vol_match = re.search(r'\b(\d{1,3})\b', text)
    if vol_match and detected_command in ("set_volume", "set_brightness"):
        volume_level = int(vol_match.group(1))

    # Detect target devices — room first, then type
    target_ids = []
    for room_key, ids in room_map.items():
        if room_key in text:
            # Further filter by device type if mentioned
            detected_type = next((t for kw, t in type_map.items() if kw in text), None)
            if detected_type:
                target_ids = [
                    d for d in ids
                    if device_config["devices"].get(d, {}).get("type") == detected_type
                ]
            else:
                target_ids = ids
            break

    # If no room matched, try device type alone
    if not target_ids:
        detected_type = next((t for kw, t in type_map.items() if kw in text), None)
        if detected_type:
            target_ids = [
                k for k, v in device_config["devices"].items()
                if v["type"] == detected_type
            ]

    # Final fallback — all devices
    if not target_ids:
        target_ids = list(device_config["devices"].keys())[:2]

    # Build parameters
    parameters = {}
    if input_source:
        parameters["input_source"] = input_source
    if volume_level is not None:
        parameters["level"] = volume_level
    if detected_command == "zoom":
        parameters["direction"] = "in" if "in" in text else "out"
        parameters["speed"] = 3
    if detected_command in ("pan", "tilt"):
        if detected_command == "pan":
            parameters["direction"] = "right" if "right" in text else "left"
        else:
            parameters["direction"] = "up" if "up" in text else "down"
        parameters["speed"] = 5

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payloads = []
    for dev_id in target_ids:
        dev = device_config["devices"].get(dev_id, {})
        valid_cmds = dev.get("commands", [])
        cmd = detected_command if detected_command in valid_cmds else (valid_cmds[0] if valid_cmds else detected_command)
        payloads.append({
            "device_id": dev_id,
            "device_type": dev.get("type", "unknown"),
            "device_name": dev.get("name", "unknown"),
            "room": dev.get("room", "unknown"),
            "ip_address": dev.get("ip", "unknown"),
            "command": cmd,
            "parameters": parameters,
            "issued_by": "manager_system",
            "timestamp": ts,
            "priority": "normal",
            "ack_required": True,
            "parsed_by": "local_nlp",
        })

    return (payloads[0] if len(payloads) == 1 else payloads), None


# ════════════════════════════════════════════════════════════════════════════
# GEMINI: Natural language → JSON payload
# ════════════════════════════════════════════════════════════════════════════
def generate_payload_with_gemini(prompt, device_config):
    devices_summary = json.dumps(
        {k: {"name": v["name"], "type": v["type"], "room": v["room"], "commands": v["commands"]}
         for k, v in device_config["devices"].items()},
        indent=2
    )

    system_prompt = f"""You are an AV control system assistant for NYU. Your job is to convert natural language commands into JSON control payloads for AV hardware.

Available devices:
{devices_summary}

Rules:
1. Return ONLY valid JSON — no markdown, no explanation, no code blocks.
2. Always include: device_id, device_type, command, parameters (object, can be empty {{}}), issued_by, timestamp (ISO 8601), priority ("normal" or "high"), ack_required (boolean).
3. If multiple devices are referenced, return a JSON array of payloads.
4. Match device names/rooms loosely — "projector in Room 101" maps to PRJ_001.
5. For unknown commands, use the closest valid command for that device type.
6. issued_by should always be "manager_system".
7. timestamp should be: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}

User command: {prompt}"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=system_prompt,
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"Gemini returned invalid JSON: {e}"
    except Exception as e:
        return None, f"Gemini error: {e}"


# ════════════════════════════════════════════════════════════════════════════
# BUILD PAYLOAD MANUALLY
# ════════════════════════════════════════════════════════════════════════════
def build_manual_payload(device_id, command, device_config, extra_params=None):
    device = device_config["devices"].get(device_id, {})

    parameters = {}
    if extra_params:
        parameters.update(extra_params)

    return {
        "device_id": device_id,
        "device_type": device.get("type", "unknown"),
        "device_name": device.get("name", "unknown"),
        "room": device.get("room", "unknown"),
        "ip_address": device.get("ip", "unknown"),
        "command": command,
        "parameters": parameters,
        "issued_by": st.session_state.user["username"],
        "issued_by_name": st.session_state.user["name"],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "priority": "normal",
        "ack_required": True,
        "session_id": f"session_{st.session_state.user['username']}",
    }


# ════════════════════════════════════════════════════════════════════════════
# DEVICE CONTROL TAB (MANAGER ONLY)
# ════════════════════════════════════════════════════════════════════════════
def show_device_control(device_config):
    st.markdown("""
    <div style='background:#1a2744; border:1px solid #2b6cb0; border-radius:8px;
                padding:0.6rem 1rem; margin-bottom:1rem;'>
        ⚡ <b style='color:#63b3ed;'>Manager Access</b>
        <span style='color:#718096; font-size:0.85rem;'>
         — Device control panel. Commands simulate HTTP POST to AV hardware.
        </span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎛️ Form Builder", "🤖 AI Command (Gemini)"])

    # ── Form-based control ──────────────────────────────────────────────────
    with tab1:
        st.markdown("<div class='section-header'>Build a Device Command</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            device_options = {
                f"{v['name']} — {v['room']} ({k})": k
                for k, v in device_config["devices"].items()
            }
            selected_label = st.selectbox("Select Device", options=list(device_options.keys()))
            selected_id = device_options[selected_label]
            selected_device = device_config["devices"][selected_id]

        with col2:
            available_commands = selected_device["commands"]
            selected_command = st.selectbox("Command", options=available_commands)

        # Dynamic parameter inputs
        cmd_params = device_config.get("command_parameters", {}).get(selected_command, {})
        extra_params = {}
        if cmd_params:
            st.markdown("**Command Parameters**")
            param_cols = st.columns(min(len(cmd_params), 3))
            for i, (param, hint) in enumerate(cmd_params.items()):
                with param_cols[i % len(param_cols)]:
                    if isinstance(hint, list):
                        extra_params[param] = st.selectbox(
                            param.replace("_", " ").title(),
                            options=hint,
                            key=f"param_{param}"
                        )
                    else:
                        extra_params[param] = st.text_input(
                            f"{param.replace('_', ' ').title()} ({hint})",
                            key=f"param_{param}"
                        )

        priority = st.radio("Priority", ["normal", "high"], horizontal=True)

        if st.button("⚡ Send Command", type="primary", use_container_width=True):
            payload = build_manual_payload(selected_id, selected_command, device_config, extra_params)
            payload["priority"] = priority
            st.session_state.last_payload = payload
            st.session_state.command_log.append({
                "timestamp": payload["timestamp"],
                "user": payload["issued_by_name"],
                "device": f"{payload['device_name']} ({payload['room']})",
                "command": selected_command,
                "payload": payload,
            })
            st.success(f"Command dispatched to {payload['device_name']} at {payload['ip_address']}")

    # ── Gemini AI control ───────────────────────────────────────────────────
    with tab2:
        if GEMINI_AVAILABLE:
            st.markdown("""
            <div style='background:#0d2137; border:1px solid #2b6cb0; border-radius:6px;
                        padding:0.5rem 1rem; margin-bottom:0.8rem; font-size:0.85rem;'>
                🤖 <b style='color:#63b3ed;'>Gemini Active</b>
                <span style='color:#718096;'> — powered by Google Gemini AI</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#1a1a0d; border:1px solid #744210; border-radius:6px;
                        padding:0.5rem 1rem; margin-bottom:0.8rem; font-size:0.85rem;'>
                ⚡ <b style='color:#f6ad55;'>Local NLP Mode</b>
                <span style='color:#718096;'> — Gemini unavailable; using built-in keyword parser</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='section-header'>Natural Language → JSON Payload</div>", unsafe_allow_html=True)
        st.caption("Describe what you want to do in plain English.")

        examples = [
            "Turn on the projector in Room 101 and set input to HDMI 1",
            "Mute the DSP in Auditorium A",
            "Power off all projectors",
            "Set volume to 75 on Room 202 DSP",
            "Recall preset 3 on the Auditorium A camera",
        ]
        selected_example = st.selectbox(
            "Or pick an example",
            ["— type your own —"] + examples,
            key="ai_example_select",
        )

        nl_command = st.text_area(
            "Your command",
            value="" if selected_example == "— type your own —" else selected_example,
            placeholder="e.g. Turn on the projector in Room 202 and switch input to HDMI 2",
            height=80,
            key="ai_nl_command",
        )

        btn_label = "🤖 Generate with Gemini" if GEMINI_AVAILABLE else "⚡ Generate with Local Parser"
        if st.button(btn_label, type="primary", use_container_width=True):
            if nl_command.strip():
                if GEMINI_AVAILABLE:
                    with st.spinner("Generating payload..."):
                        payload, error = generate_payload_with_gemini(nl_command, device_config)
                    if error:
                        # Silently fall back — quota/network issues shouldn't break the demo
                        payload, error = parse_command_locally(nl_command, device_config)
                else:
                    with st.spinner("Parsing command..."):
                        payload, error = parse_command_locally(nl_command, device_config)

                if error:
                    st.error(error)
                elif payload is not None:
                    st.session_state.last_payload = payload
                    entries = payload if isinstance(payload, list) else [payload]
                    for p in entries:
                        if isinstance(p, dict):
                            p.setdefault("issued_by_name", st.session_state.user["name"])
                            st.session_state.command_log.append({
                                "timestamp": p.get("timestamp", ""),
                                "user": st.session_state.user["name"],
                                "device": p.get("device_id", "unknown"),
                                "command": p.get("command", "unknown"),
                                "payload": p,
                            })
                    st.success(f"Payload generated for {len(entries)} device(s)")
            else:
                st.warning("Please enter a command.")

    # ── Last payload display ────────────────────────────────────────────────
    if st.session_state.last_payload:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📤 Last Generated JSON Payload</div>", unsafe_allow_html=True)
        payload_json = json.dumps(st.session_state.last_payload, indent=2)
        st.markdown(f"<div class='json-box'>{payload_json}</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Payload",
                data=payload_json,
                file_name=f"av_command_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            if st.button("🗑️ Clear Payload", use_container_width=True):
                st.session_state.last_payload = None
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# COMMAND LOG TAB
# ════════════════════════════════════════════════════════════════════════════
def show_command_log():
    st.markdown("<div class='section-header'>📋 Command Audit Log</div>", unsafe_allow_html=True)

    if not st.session_state.command_log:
        st.info("No commands have been sent this session.")
        return

    if st.button("🗑️ Clear Log"):
        st.session_state.command_log = []
        st.rerun()

    for i, entry in enumerate(reversed(st.session_state.command_log)):
        with st.expander(
            f"[{entry['timestamp']}]  {entry['command'].upper()}  →  {entry['device']}  (by {entry['user']})",
            expanded=(i == 0)
        ):
            st.code(json.dumps(entry["payload"], indent=2), language="json")


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.authenticated:
        show_login()
        return

    equipment_df = load_equipment()
    schedules_df = load_schedules()
    device_config = load_device_config()

    show_header()
    show_metrics(equipment_df, schedules_df)

    user_role = st.session_state.user["role"]

    if user_role == "Manager":
        tabs = st.tabs([
            "📦 Equipment Inventory",
            "📅 Staff Schedules",
            "⚡ Device Control",
            "📋 Audit Log",
        ])
        with tabs[0]:
            show_equipment(equipment_df)
        with tabs[1]:
            show_schedules(schedules_df)
        with tabs[2]:
            show_device_control(device_config)
        with tabs[3]:
            show_command_log()
    else:
        # Technician: read-only, no device control tab
        st.markdown("""
        <div style='background:#1a2a1a; border:1px solid #276749; border-radius:8px;
                    padding:0.6rem 1rem; margin-bottom:1rem;'>
            🔧 <b style='color:#68d391;'>Technician View</b>
            <span style='color:#718096; font-size:0.85rem;'>
             — Read-only access. Device control requires Manager role.
            </span>
        </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["📦 Equipment Inventory", "📅 Staff Schedules"])
        with tabs[0]:
            show_equipment(equipment_df)
        with tabs[1]:
            show_schedules(schedules_df)


if __name__ == "__main__":
    main()
