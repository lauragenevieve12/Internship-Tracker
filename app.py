import re
from datetime import date, datetime
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Internship Tracker", page_icon="🎓", layout="wide")

STATUSES = ["To apply", "Applied", "Interview", "Rejected", "Offer"]
STATUS_EMOJI = {
    "To apply": "📝",
    "Applied": "📨",
    "Interview": "🎤",
    "Offer": "🎉",
    "Rejected": "❌",
}
STATUS_COLORS = {
    "To apply": "📝",
    "Applied": "📨",
    "Interview": "🎤",
    "Offer": "🎉",
    "Rejected": "❌",
}

# ---------- Connection ----------
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = get_supabase()
except Exception as exc:
    st.error("Impossible de se connecter à Supabase. Vérifie les secrets de l'application Streamlit.")
    st.caption(f"Détail technique : {exc}")
    st.stop()


def load_applications():
    response = supabase.table("applications").select("*").order("created_at", desc=True).execute()
    data = response.data or []
    df = pd.DataFrame(data)
    expected = ["id", "company", "position", "application_date", "status", "follow_up_date", "notes", "created_at"]
    for col in expected:
        if col not in df.columns:
            df[col] = None
    if not df.empty:
        for col in ["application_date", "follow_up_date"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def display_date(value):
    if value is None or pd.isna(value):
        return "—"
    try:
        return pd.to_datetime(value).strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def safe_text(value):
    return "" if value is None or pd.isna(value) else str(value)


def add_application(company, position, application_date, status, follow_up_date, notes):
    payload = {
        "company": company.strip(),
        "position": position.strip(),
        "application_date": application_date.isoformat(),
        "status": status,
        "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
        "notes": notes.strip() or None,
    }
    supabase.table("applications").insert(payload).execute()


def update_application(app_id, company, position, application_date, status, follow_up_date, notes):
    payload = {
        "company": company.strip(),
        "position": position.strip(),
        "application_date": application_date.isoformat(),
        "status": status,
        "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
        "notes": notes.strip() or None,
    }
    supabase.table("applications").update(payload).eq("id", app_id).execute()


def delete_application(app_id):
    supabase.table("applications").delete().eq("id", app_id).execute()


def response_stats(df):
    total = len(df)
    # A response means the company has moved the application beyond "Applied"/"To apply".
    responded = int(df["status"].isin(["Interview", "Offer", "Rejected"]).sum()) if total else 0
