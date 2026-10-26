
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Internship Tracker",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Internship Tracker")
st.write("Manage your internship applications in one place.")

if "applications" not in st.session_state:
    st.session_state.applications = []

st.subheader("Add a new application")

with st.form("application_form"):
    company = st.text_input("Company name")
    position = st.text_input("Position")
    application_date = st.date_input("Application date")
    status = st.selectbox(
        "Status",
        ["To apply", "Applied", "Interview", "Rejected", "Offer"]
    )

    submitted = st.form_submit_button("Add application")

    if submitted:
        if company.strip() and position.strip():
            st.session_state.applications.append({
                "Company": company,
                "Position": position,
                "Application date": application_date,
                "Status": status
            })
            st.success("Application added!")
        else:
            st.error("Please enter the company name and position.")

st.subheader("My applications")

if st.session_state.applications:
    df = pd.DataFrame(st.session_state.applications)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No applications added yet. Start by filling in the form above.")
