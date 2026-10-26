
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Internship Tracker",
    page_icon="💼",
    layout="wide"
)

STATUSES = ["To apply", "Applied", "Interview", "Rejected", "Offer"]

STATUS_LABELS = {
    "To apply": "⚪ To apply",
    "Applied": "🔵 Applied",
    "Interview": "🟣 Interview",
    "Rejected": "🔴 Rejected",
    "Offer": "🟢 Offer"
}


def connect_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def to_date(value):
    """Convert a database date into a Python date."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def load_applications(db):
    result = (
        db.table("applications")
        .select("*")
        .order("application_date", desc=True)
        .execute()
    )
    return result.data or []


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

try:
    supabase = connect_db()
    applications = load_applications(supabase)
except Exception as e:
    st.error(
        "Could not connect to Supabase. "
        "Please check your app secrets and database settings."
    )
    st.stop()


if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.main {
    background-color: #f7f8fc;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e6e8ef;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: white;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("💼 Internship Tracker")
st.caption("All your applications, organized in one place.")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

today = date.today()

total = len(applications)
to_apply = sum(a["status"] == "To apply" for a in applications)
sent = sum(a["status"] == "Applied" for a in applications)
interviews = sum(a["status"] == "Interview" for a in applications)
offers = sum(a["status"] == "Offer" for a in applications)
rejected = sum(a["status"] == "Rejected" for a in applications)

st.subheader("📊 Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Total applications", total)
c2.metric("Applications sent", sent)
c3.metric("Interviews", interviews)

c4, c5, c6 = st.columns(3)
c4.metric("Offers", offers)
c5.metric("Rejected", rejected)
c6.metric("To apply", to_apply)


# --------------------------------------------------
# FOLLOW-UP REMINDERS
# --------------------------------------------------

due_today = []
overdue = []

for app in applications:
    follow_up = to_date(app.get("follow_up_date"))

    if not follow_up:
        continue

    if app["status"] in ["Rejected", "Offer"]:
        continue

    if follow_up < today:
        overdue.append(app)
    elif follow_up == today:
        due_today.append(app)

st.divider()
st.subheader("🔔 Follow-up reminders")

if overdue:
    st.error(f"{len(overdue)} follow-up(s) overdue")
    for app in overdue:
        st.write(
            f"**{app['company']}** — {app['position']} "
            f"(due {app['follow_up_date']})"
        )

if due_today:
    st.warning(f"{len(due_today)} follow-up(s) due today")
    for app in due_today:
        st.write(f"**{app['company']}** — {app['position']}")

if not overdue and not due_today:
    st.success("No follow-ups due today or overdue.")


# --------------------------------------------------
# ADD APPLICATION
# --------------------------------------------------

st.divider()
st.subheader("➕ Add an application")

with st.form("application_form", clear_on_submit=True):
    company = st.text_input("Company name")
    position = st.text_input("Position")
    application_date = st.date_input(
        "Application date",
        value=today
    )
    status = st.selectbox("Status", STATUSES)
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
            except Exception as e:
                st.error(f"Could not save the application: {e}")
        else:
            st.warning("Please enter the company name and position.")


# --------------------------------------------------
# SEARCH AND FILTER
# --------------------------------------------------

st.divider()
st.subheader("📋 My applications")

col1, col2 = st.columns(2)

with col1:
    search = st.text_input(
        "🔎 Search by company or position"
    )

with col2:
    status_filter = st.selectbox(
        "Filter by status",
        ["All"] + STATUSES
    )

filtered = applications.copy()

if search:
    filtered = [
        a for a in filtered
        if search.lower() in a.get("company", "").lower()
        or search.lower() in a.get("position", "").lower()
    ]

if status_filter != "All":
    filtered = [
        a for a in filtered
        if a.get("status") == status_filter
    ]


# --------------------------------------------------
# CSV EXPORT
# --------------------------------------------------

if applications:
    export_rows = []

    for a in applications:
        export_rows.append({
            "Company": a.get("company", ""),
            "Position": a.get("position", ""),
            "Application date": a.get("application_date", ""),
            "Status": a.get("status", ""),
            "Follow-up date": a.get("follow_up_date") or "",
            "Notes": a.get("notes") or ""
        })

    csv_data = pd.DataFrame(export_rows).to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 Export all applications to CSV",
        data=csv_data,
        file_name="internship_applications.csv",
        mime="text/csv"
    )


# --------------------------------------------------
# EDIT, DISPLAY AND DELETE
# --------------------------------------------------

if filtered:
    for app in filtered:
        app_id = app["id"]

        with st.container(border=True):
            left, right = st.columns([4, 1])

            with left:
                st.subheader(app.get("company", ""))
                st.write(f"**Position:** {app.get('position', '')}")
                st.write(
                    f"**Application date:** "
                    f"{app.get('application_date', '')}"
                )
                st.write(
                    f"**Status:** "
                    f"{STATUS_LABELS.get(app.get('status'), app.get('status'))}"
                )
                st.write(
                    f"**Follow-up:** "
                    f"{app.get('follow_up_date') or 'Not set'}"
                )
                st.write(f"**Notes:** {app.get('notes') or '-'}")

            with right:
                if st.button(
                    "✏️ Edit",
                    key=f"edit_{app_id}",
                    use_container_width=True
                ):
                    st.session_state.editing_id = app_id
                    st.session_state.confirm_delete_id = None
                    st.rerun()

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{app_id}",
                    use_container_width=True
                ):
                    st.session_state.confirm_delete_id = app_id
                    st.session_state.editing_id = None
                    st.rerun()

            # EDIT FORM
            if st.session_state.editing_id == app_id:
                st.markdown("#### Edit application")

                with st.form(f"edit_form_{app_id}"):
                    edited_company = st.text_input(
                        "Company name",
                        value=app.get("company", "")
                    )
                    edited_position = st.text_input(
                        "Position",
                        value=app.get("position", "")
                    )
                    edited_date = st.date_input(
                        "Application date",
                        value=to_date(app.get("application_date")) or today
                    )
                    current_status = app.get("status", "To apply")
                    status_index = (
                        STATUSES.index(current_status)
                        if current_status in STATUSES else 0
                    )
                    edited_status = st.selectbox(
                        "Status",
                        STATUSES,
                        index=status_index
                    )
                    edited_follow_up = st.date_input(
                        "Follow-up date (optional)",
                        value=to_date(app.get("follow_up_date"))
                    )
                    edited_notes = st.text_area(
                        "Notes",
                        value=app.get("notes") or ""
                    )

                    save_edit = st.form_submit_button("Save changes")
                    cancel_edit = st.form_submit_button("Cancel")

                    if save_edit:
                        if edited_company.strip() and edited_position.strip():
                            updated_application = {
                                "company": edited_company.strip(),
                                "position": edited_position.strip(),
                                "application_date": edited_date.isoformat(),
                                "status": edited_status,
                                "follow_up_date": (
                                    edited_follow_up.isoformat()
                                    if edited_follow_up else None
                                ),
                                "notes": edited_notes.strip()
                            }

                            try:
                                supabase.table("applications").update(
                                    updated_application
                                ).eq("id", app_id).execute()

                                st.session_state.editing_id = None
                                st.success("Application updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not update the application: {e}")
                        else:
                            st.warning(
                                "Please enter the company name and position."
                            )

                    if cancel_edit:
                        st.session_state.editing_id = None
                        st.rerun()

            # DELETE CONFIRMATION
            if st.session_state.confirm_delete_id == app_id:
                st.warning(
                    f"Are you sure you want to delete "
                    f"{app.get('company', 'this application')}?"
                )

                yes_col, no_col = st.columns(2)

                with yes_col:
                    if st.button(
                        "Yes, delete",
                        key=f"yes_delete_{app_id}",
                        type="primary"
                    ):
                        try:
                            supabase.table("applications").delete().eq(
                                "id", app_id
                            ).execute()

                            st.session_state.confirm_delete_id = None
                            st.success("Application deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not delete the application: {e}")

                with no_col:
                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{app_id}"
                    ):
                        st.session_state.confirm_delete_id = None
                        st.rerun()

else:
    st.info("No applications found. Add one above or change your filters.")

st.caption("Your applications are stored in your Supabase database.")
