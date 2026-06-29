# 1. Importing required tools for the application
import streamlit as st
import pandas as pd
import sqlite3
import base64
import os
import time
import datetime
import re

# ==========================================
# HELPER FUNCTIONS
# ==========================================

# This function checks if the email format is correct
def is_valid_email(email):
    # Copy-paste karne par aage-peeche ke extra spaces automatically hata dega
    email = str(email).strip() 
    # Naya advance pattern jo har tarah ke standard emails (numbers ke sath) accept karega
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

# This function loads platform icons (like WhatsApp, Facebook) from your local folder
def get_image_html(platform_name):
    # Mapping platform names to their respective image files
    platform_map = {
        "LinkedIn": "linkedin.png",
        "WhatsApp": "whatsapp.png",
        "Facebook": "facebook.png",
        "Instagram": "social.png",
        "Email": "email.png",
        "Cold Call": "coldcall.png"
    }
    
    image_name = platform_map.get(platform_name, "default.png")
    
    # If the image exists, convert it to base64 so it can show up in the HTML table
    if os.path.exists(image_name):
        with open(image_name, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return f'<img src="data:image/png;base64,{encoded_string}" width="20" style="vertical-align: middle; margin-right: 8px;"> {platform_name}'
    else:
        # If image is not found, just show the platform text
        return f'{platform_name}'

# ==========================================
# DATABASE SECTION (Handles Data Storage)
# ==========================================

# This function creates an EMPTY database for LIVE usage
def init_lead_db():
    conn = sqlite3.connect("crm_main.db")
    cursor = conn.cursor()
    
    # Create the leads table with all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            lead_name TEXT,
            contact TEXT,
            email TEXT,
            platform TEXT,
            purpose TEXT,
            lead_type TEXT,
            created_at TEXT
        )
    ''')
    
    # DUMMY DATA COMPLETELY REMOVED FOR LIVE DEPLOYMENT
    
    conn.commit()
    conn.close()

# This function fetches all leads from the database to show in the table
def get_all_leads():
    conn = sqlite3.connect("crm_main.db")
    # Order by newest leads first
    query = "SELECT * FROM leads ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# This function securely saves a new lead into the database
def save_new_lead(l_id, name, contact, email, platform, purpose, l_type, created_time):
    conn = sqlite3.connect("crm_main.db")
    cursor = conn.cursor()
    try:
        # Insert the data into the leads table
        cursor.execute('''
            INSERT INTO leads (lead_id, lead_name, contact, email, platform, purpose, lead_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (l_id, name, contact, email, platform, purpose, l_type, created_time))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Fails if duplicate lead ID happens
    finally:
        conn.close()

# ==========================================
# SAFE MEMORY LOGIC (Fixes the Data Loss Bug)
# ==========================================

# This function safely locks the data before moving to the Preview screen
def ld_go_preview():
    p = st.session_state
    
    # Fetch data from the input boxes using safe keys
    name = p.get("ld_name_in", "")
    contact = p.get("ld_contact_in", "")
    platform = p.get("ld_platform_in", "WhatsApp")
    email = p.get("ld_email_in", "").strip() # Strip extra spaces
    l_type = p.get("ld_type_in", "Cold")
    purpose = p.get("ld_purpose_in", "")

    # 1. Check if all required fields are filled
    if name and contact and email and purpose:
        # 2. Check if the email address is valid
        if not is_valid_email(email):
            p.ld_error = "⚠️ Invalid Email Format! Please enter a valid email ID."
        else:
            p.ld_step = "preview"
            p.ld_error = ""
            
            # 3. Save data to a safe dictionary so it does not get deleted on refresh
            p.safe_ld_data = {
                'name': name,
                'contact': contact,
                'email': email,
                'platform': platform,
                'type': l_type,
                'purpose': purpose
            }
    else:
        p.ld_error = "⚠️ Please fill all mandatory fields (*)."

# This function switches the screen back to Edit mode
def ld_go_edit():
    st.session_state.ld_step = "form"

# This function runs automatically when the Platform dropdown is changed
def update_lead_type():
    # If platform is LinkedIn, automatically change lead type to Warm
    if st.session_state.ld_platform_in == "LinkedIn":
        st.session_state.ld_type_in = "Warm"
    else:
        # For all other platforms, set it to Cold by default
        st.session_state.ld_type_in = "Cold"

# This function resets old data when adding a brand new lead
def prepare_new_lead():
    st.session_state.ld_step = "form"
    st.session_state.ld_error = ""
    st.session_state.safe_ld_data = {} 
    
    # Delete old inputs from memory
    keys_to_clear = ["ld_name_in", "ld_contact_in", "ld_email_in", "ld_purpose_in", "ld_platform_in", "ld_type_in"]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]

# ==========================================
# UI DIALOGS & POP-UPS
# ==========================================

# Dialog: Add New Lead Wizard (Form + Preview Mode)
@st.dialog("➕ Add New Lead", width="large")
def add_lead_dialog():
    
    # Check if the step variable is initialized
    if "ld_step" not in st.session_state:
        st.session_state.ld_step = "form"
        
    # Get safely stored drafts (so data returns when clicked on 'Edit Details')
    draft = st.session_state.get("safe_ld_data", {})

    # ------------- STEP 1: FORM UI -------------
    if st.session_state.ld_step == "form":
        st.markdown("<p style='color: #555;'>Enter the new lead details below. Date and time will be recorded automatically.</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Lead Name *", placeholder="e.g. John Doe", value=draft.get('name', ''), key="ld_name_in")
            st.text_input("Contact Number *", placeholder="+91-XXXXXXXXXX", value=draft.get('contact', ''), key="ld_contact_in")
            
            p_opts = ["WhatsApp", "Facebook", "Instagram", "Email", "Cold Call", "LinkedIn"]
            
            # Initialize platform if not set
            if "ld_platform_in" not in st.session_state:
                st.session_state.ld_platform_in = draft.get('platform', "WhatsApp")
                
            # The on_change function updates the Lead Type automatically
            st.selectbox("Source Platform *", p_opts, key="ld_platform_in", on_change=update_lead_type)
            
        with col2:
            st.text_input("Email ID *", placeholder="john@pararobo.com", value=draft.get('email', ''), key="ld_email_in")
            
            t_opts = ["Hot", "Warm", "Cold", "Not Connected"]
            
            # Initialize lead type dynamically if not set
            if "ld_type_in" not in st.session_state:
                if draft.get('type'):
                    st.session_state.ld_type_in = draft['type']
                else:
                    # Apply automatic default logic based on the current platform
                    st.session_state.ld_type_in = "Warm" if st.session_state.ld_platform_in == "LinkedIn" else "Cold"
                    
            st.selectbox("Lead Status Type *", t_opts, key="ld_type_in")
            
        st.text_area("Lead Purpose / Requirement *", placeholder="Briefly describe what the client needs...", value=draft.get('purpose', ''), key="ld_purpose_in")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Display validation errors
        if st.session_state.get("ld_error"):
            st.error(st.session_state.ld_error)
            
        # This button triggers the memory save logic
        st.button("👁️ Generate Preview", type="primary", use_container_width=True, on_click=ld_go_preview)

    # ------------- STEP 2: PREVIEW UI -------------
    elif st.session_state.ld_step == "preview":
        data = st.session_state.safe_ld_data
        
        st.markdown("<h3 style='color: #333;'>👁️ Preview Lead Details</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666;'>Please review the details before saving to the database.</p>", unsafe_allow_html=True)
        
        # Summary Display Box
        with st.container(border=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown(f"**Lead Name:** {data['name']}")
                st.markdown(f"**Email ID:** {data['email']}")
                st.markdown(f"**Contact Number:** {data['contact']}")
            with col_p2:
                st.markdown(f"**Source Platform:** {data['platform']}")
                st.markdown(f"**Lead Status:** {data['type']}")
                
        st.markdown(f"**Purpose / Requirement:** {data['purpose']}")
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action Buttons
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            # Send the user back to the form
            st.button("✏️ Edit Details", use_container_width=True, on_click=ld_go_edit)
            
        with col_b2:
            # Confirm and save to database
            if st.button("✅ Confirm & Save Lead", type="primary", use_container_width=True):
                # Generate unique ID and Date automatically
                l_id = f"LD-{int(time.time())}"
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
                
                status = save_new_lead(
                    l_id, data['name'], data['contact'], data['email'], 
                    data['platform'], data['purpose'], data['type'], current_time
                )
                
                if status:
                    st.success("New lead successfully added!")
                    time.sleep(1)
                    st.rerun() # Refresh dashboard
                else:
                    st.error("⚠️ Error saving lead. Please try again.")
                    st.rerun()

# ==========================================
# MAIN PAGE RENDER (Table & UI)
# ==========================================

# Function to generate an HTML table for displaying the leads
def create_lead_table(df):
    # Check if database is empty - LIVE STATE MESSAGE
    if len(df) == 0:
        return "<br><h4 style='text-align:center; color:#ff4b4b; padding:20px; border: 1px dashed #ff4b4b; border-radius: 8px;'>NO DATA IS BEEN ENTERED</h4>"
        
    html_table = "<style>"
    html_table += ".lead-table { width: 100%; border-collapse: collapse; background-color: #FFFFFF; color: #000000; margin-top: 15px; }"
    html_table += ".lead-table th, .lead-table td { border: 2px solid #000000; padding: 12px; text-align: left; }"
    html_table += ".lead-table th { font-weight: bold; font-size: 16px; background-color: #F8F9FA; }"
    html_table += "</style>"
    html_table += "<table class='lead-table'>"
    html_table += "<thead>"
    html_table += "<tr>"
    html_table += "<th>Lead Name</th>"
    html_table += "<th>Contact</th>"
    html_table += "<th>Email</th>"
    html_table += "<th>Platform</th>"
    html_table += "<th>Purpose</th>"
    html_table += "<th>Lead Type</th>"
    html_table += "</tr>"
    html_table += "</thead>"
    html_table += "<tbody>"
    
    # Loop through data and build rows
    for _, row in df.iterrows():
        # Set colors based on lead status
        lead_color = "#000000"
        if row['lead_type'] == 'Hot':
            lead_color = "#ff0000"
        elif row['lead_type'] == 'Warm':
            lead_color = "#ff9900"
        elif row['lead_type'] == 'Cold':
            lead_color = "#0000EE"
        elif row['lead_type'] == 'Not Connected':
            lead_color = "#888888"

        # Get the HTML for the platform icon
        platform_display = get_image_html(row['platform'])

        html_table += "<tr>"
        html_table += f"<td><strong>{row['lead_name']}</strong></td>"
        html_table += f"<td>{row['contact']}</td>"
        html_table += f"<td>{row['email']}</td>"
        html_table += f"<td>{platform_display}</td>"
        html_table += f"<td>{row['purpose']}</td>"
        html_table += f"<td style='color: {lead_color}; font-weight: bold;'>{row['lead_type']}</td>"
        html_table += "</tr>"
        
    html_table += "</tbody></table>"
    return html_table

# Main function to show the Leads page
def show_lead_page():
    
    # Start the database automatically on startup
    if "lead_db_initialized" not in st.session_state:
        init_lead_db()
        st.session_state.lead_db_initialized = True

    # Header section
    head_col1, head_col2 = st.columns([4, 1], vertical_alignment="center")
    with head_col1:
        st.markdown("<h1 style='color: #000000; margin-bottom: 0px;'>🎯 Leads Detail</h1>", unsafe_allow_html=True)
    with head_col2:
        # Button to open the Add Lead form
        if st.button("➕ Add Lead", type="primary", use_container_width=True):
            prepare_new_lead() # Clean up memory for a fresh form
            add_lead_dialog()  # Open the popup
            
    st.markdown("---")

    # Get data from database and render the table
    df = get_all_leads()
    st.markdown(create_lead_table(df), unsafe_allow_html=True)