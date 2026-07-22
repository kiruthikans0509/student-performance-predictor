import streamlit as st
import requests

API_URL = "https://student-performance-predictor-fm00.onrender.com/predict"

# App title
st.title("Student Performance Predictor")
st.write("Enter your details to predict your grade, pass/fail status and performance level.")

# Input fields
st.subheader("Student Details")

hours_studied = st.slider("Hours Studied Per Day", min_value=1, max_value=9, value=5)
previous_scores = st.slider("Previous Scores", min_value=40, max_value=99, value=70)
extracurricular = st.selectbox("Extracurricular Activities", ["Yes", "No"])
sleep_hours = st.slider("Sleep Hours Per Day", min_value=4, max_value=9, value=7)
sample_papers = st.slider("Sample Question Papers Practiced", min_value=0, max_value=9, value=3)

# Predict button
if st.button("Predict Performance"):

    payload = {
        "hours_studied": hours_studied,
        "previous_scores": previous_scores,
        "extracurricular": extracurricular,
        "sleep_hours": sleep_hours,
        "sample_papers": sample_papers
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()

        st.subheader("Prediction Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Grade", result["output"]["grade"])

        with col2:
            if result["output"]["pass_fail"] == "Pass":
                st.success("Pass")
            else:
                st.error("Fail")
                
        with col3:
            st.metric("Performance Level", result["output"]["performance_level"])
        

        

        
    else:
        st.error(f"API Error {response.status_code}: {response.text}")