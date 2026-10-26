
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

st.set_page_config(
    page_title="Internship Tracker",
    page_icon="💼",
    layout="wide"
)

# Connect to Supabase
@st.cache_resource
def connect_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = connect_db()
    result = supabase.table("applications").select("*").order(
        "application_date", desc=True
    ).execute()
    applications = result.data
except Exception as e:
    st.error("Database connection failed. Check your Supabase secrets.")
    st.stop()

# Modern design
st.markdown("""
<style>
.main {background-color: #f7f8fc;}
div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e6e8ef;
}
</style>
""", unsafe_allow_html=True)

st.title("💼 Internship Tracker")
st.caption("All your applications, organized in one place.")

# Dashboard
total = len(applications)
interviews = sum(a["status"] == "Interview" for a in applications)
offers = sum(a["status"] == "Offer" for a in applications)
pending = sum(a["status"] in ["To apply", "Applied"] for a in applications)

st.subheader("📊 Dashboard")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total applications", total)
c2.metric("Interviews", interviews)
c3.metric("Offers", offers)
c4.metric("Pending", pending)

st.divider()

# Add application
st.subheader("➕ Add an application")

with st.form("application_form", clear_on_submit=True):
    company = st.text_input("Company name")
    position = st.text_input("Position")
    application_date = st.date_input("Application date", value=date.today())
    status = st.selectbox(
        "Status",
        ["To apply", "Applied", "Interview", "Rejected", "Offer"]
    )
    follow_up_date = st.date_input(
        "Follow-up date (optional)",
        value=None
    )
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Save application")

    if submitted:
        if company.strip() and position.strip():
            new_application = {
                "company": company.strip(),
                "position": position.strip(),
                "application_date": application_date.isoformat(),
                "status": status,
                "follow_up_date": (
                    follow_up_date.isoformat()
                    if follow_up_date else None
                ),
                "notes": notes.strip()
            }
            try:
                supabase.table("applications").insert(
                    new_application
                ).execute()
                st.success("Application saved permanently!")
                st.rerun()
            except Exception:
                st.error("Could not save. Check your Supabase table permissions.")
        else:
            st.warning("Please enter the company and position.")

st.divider()

# Filters
st.subheader("📋 My applications")

col1, col2 = st.columns(2)
with col1:
    search = st.text_input("🔎 Search by company or position")
with col2:
    status_filter = st.selectbox(
        "Filter by status",
        ["All"] + ["To apply", "Applied", "Interview", "Rejected", "Offer"]
    )

filtered = applications.copy()

if search:
    filtered = [
        a for a in filtered
        if search.lower() in a["company"].lower()
        or search.lower() in a["position"].lower()
    ]

if status_filter != "All":
    filtered = [
        a for a in filtered if a["status"] == status_filter
    ]

# Follow-up reminders
today = date.today()
reminders = [
    a for a in filtered
    if a.get("follow_up_date")
    and a["follow_up_date"] <= today.isoformat()
    and a["status"] not in ["Rejected", "Offer"]
]

if reminders:
    st.warning(f"🔔 {len(reminders)} follow-up reminder(s) due or overdue.")

# Visual statuses
status_icons = {
    "To apply": "⚪ To apply",
    "Applied": "🔵 Applied",
    "Interview": "🟣 Interview",
    "Rejected": "🔴 Rejected",
    "Offer": "🟢 Offer"
}

if filtered:
    for a in filtered:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.subheader(a["company"])
                st.write(f"**Position:** {a['position']}")
                st.write(f"**Application date:** {a['application_date']}")
                st.write(f"**Status:** {status_icons.get(a['status'], a['status'])}")
                st.write(f"**Follow-up:** {a.get('follow_up_date') or '-'}")
                st.write(f"**Notes:** {a.get('notes') or '-'}")

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{a['id']}"):
                    st.session_state[f"confirm_delete_{a['id']}"] = True

            if st.session_state.get(f"confirm_delete_{a['id']}", False):
                st.warning(f"Delete the application for {a['company']}?")
                yes, no = st.columns(2)

                with yes:
                    if st.button("Yes, delete", key=f"yes_{a['id']}"):
                        supabase.table("applications").delete().eq(
                            "id", a["id"]
                        ).execute()
                        st.session_state.pop(f"confirm_delete_{a['id']}", None)
                        st.rerun()

                with no:
                    if st.button("Cancel", key=f"no_{a['id']}"):
                        st.session_state.pop(f"confirm_delete_{a['id']}", None)
                        st.rerun()
else:
    st.info("No applications found. Add one above or change your filters.")

st.caption("Your applications are stored in your Supabase database.")
st.caption("Your applications are stored in your Supabase database.")
