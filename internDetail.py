# 1. Importing required tools for the application
import streamlit as st
import pandas as pd
import datetime
import sqlite3
import time
import base64
import re  # Added for email validation
import streamlit.components.v1 as components
from utils import load_global_css

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

# ==========================================
# DATABASE SECTION (Handles Data Storage)
# ==========================================

# Function to create an EMPTY database and table if it doesn't exist
def init_intern_db():
    conn = sqlite3.connect("crm_main.db")
    cursor = conn.cursor()
    
    # Create interns table with all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interns (
            intern_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            contact TEXT,
            role TEXT,
            assigned_project TEXT,
            completed_projects TEXT,
            mentor TEXT,
            duration TEXT,
            status TEXT,
            college TEXT,
            branch TEXT,
            semester TEXT,
            skills TEXT,
            photo_data BLOB,
            interview_process TEXT,
            internship_type TEXT
        )
    ''')
    
    # Safely add new columns if the database is from an older version
    try:
        cursor.execute("ALTER TABLE interns ADD COLUMN photo_data BLOB")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE interns ADD COLUMN interview_process TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE interns ADD COLUMN internship_type TEXT")
    except sqlite3.OperationalError:
        pass
    
    # DUMMY DATA COMPLETELY REMOVED FOR LIVE DEPLOYMENT
    
    conn.commit()
    conn.close()

# Function to auto-move completed projects from 'assigned' to 'completed' list
def sync_intern_projects():
    try:
        conn_proj = sqlite3.connect("crm_main.db")
        cursor_proj = conn_proj.cursor()
        cursor_proj.execute("SELECT project_name FROM projects WHERE status = 'Completed'")
        completed_projects = [row[0] for row in cursor_proj.fetchall()]
        conn_proj.close()

        if not completed_projects:
            return

        conn_int = sqlite3.connect("crm_main.db")
        cursor_int = conn_int.cursor()
        cursor_int.execute("SELECT intern_id, assigned_project, completed_projects FROM interns WHERE assigned_project != '-' AND assigned_project IS NOT NULL")
        interns = cursor_int.fetchall()

        updates = []
        for i_id, assigned, comp in interns:
            if assigned in completed_projects:
                new_comp = assigned if comp in ["-", "", None] else f"{comp}, {assigned}"
                new_assigned = "-" 
                updates.append((new_comp, new_assigned, i_id))

        if updates:
            cursor_int.executemany("UPDATE interns SET completed_projects = ?, assigned_project = ? WHERE intern_id = ?", updates)
            conn_int.commit()
        conn_int.close()
    except Exception:
        pass 

# Function to read all intern data for the dashboard table
def get_all_interns():
    conn = sqlite3.connect("crm_main.db")
    query = """
        SELECT 
            intern_id AS 'Intern ID', name AS 'Name', email AS 'Email', contact AS 'Contact',
            role AS 'Role', assigned_project AS 'Assigned Project', completed_projects AS 'Completed Projects',
            mentor AS 'Mentor', duration AS 'Duration', status AS 'Status', college AS 'College',
            branch AS 'Branch', semester AS 'Semester', skills AS 'Skills', photo_data, 
            interview_process AS 'Interview Process', internship_type AS 'Internship Type'
        FROM interns
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to save a new intern into the database securely
def add_new_intern(i_id, name, email, contact, role, project, comp_proj, mentor, duration, status, college, branch, sem, skills, photo, process, i_type):
    conn = sqlite3.connect("crm_main.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM interns WHERE email = ?", (email,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return "duplicate_email"
        
    try:
        cursor.execute('''
            INSERT INTO interns (intern_id, name, email, contact, role, assigned_project, completed_projects, mentor, duration, status, college, branch, semester, skills, photo_data, interview_process, internship_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (i_id, name, email, contact, role, project, comp_proj, mentor, duration, status, college, branch, sem, skills, photo, process, i_type))
        conn.commit()
        return "success"
    except sqlite3.IntegrityError:
        return "duplicate_id"  
    finally:
        conn.close()

def delete_intern(i_id):
    conn = sqlite3.connect("crm_main.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interns WHERE intern_id = ?", (i_id,))
    conn.commit()
    conn.close()

# ==========================================
# SAFE MEMORY LOGIC (Fixes the Data Loss Bug)
# ==========================================

# This function safely locks the data before moving to the Preview screen
def int_go_preview():
    p = st.session_state
    
    name = p.get("i_name_in", "")
    email = p.get("i_email_in", "").strip() # Strip space before processing
    contact = p.get("i_contact_in", "")
    num = p.get("i_num_in", "")
    process = p.get("i_process_in", "Walk in interview")
    i_type = p.get("i_type_in", "Full time")
    
    if process == "College Through":
        college = p.get("i_college_in", "")
        branch = p.get("i_branch_in", "")
        sem = p.get("i_sem_in", "1st Semester")
        valid_college = bool(college and branch) 
    else:
        college, branch, sem = "-", "-", "-" 
        valid_college = True
        
    role = p.get("i_role_in", "AI/ML Developer")
    skills = p.get("i_skills_in", "")
    project = p.get("i_project_in", "")
    mentor = p.get("i_mentor_in", "Prajatak sir")
    start = p.get("i_start_in", datetime.date.today())
    end = p.get("i_end_in", datetime.date.today())

    if name and email and contact and num and valid_college:
        # Validating Email Format with improved pattern
        if not is_valid_email(email):
            p.int_error = "⚠️ Invalid Email Format! Please enter a valid email ID."
        elif len(num) != 3 or not num.isdigit():
            p.int_error = "⚠️ ID Number must be exactly 3 digits (e.g. 001)."
        elif end < start:
            p.int_error = "⚠️ End Date cannot be before Start Date!"
        else:
            p.int_step = "preview"
            p.int_error = ""
            
            p.safe_int_data = {
                'name': name, 'email': email, 'contact': contact, 'num': num,
                'process': process, 'type': i_type,
                'college': college, 'branch': branch, 'sem': sem, 'role': role,
                'skills': skills, 'project': project, 'mentor': mentor, 
                'start': start, 'end': end
            }
            
            if p.get("i_photo_in") is not None:
                p.int_photo_data = p.i_photo_in.getvalue()
    else:
        p.int_error = "⚠️ Please fill all mandatory fields (*)."

def int_go_edit():
    st.session_state.int_step = "form"

def prepare_new_intern():
    st.session_state.int_step = "form"
    st.session_state.int_error = ""
    st.session_state.int_photo_data = None
    st.session_state.safe_int_data = {} 
    for k in ["i_name_in", "i_contact_in", "i_college_in", "i_branch_in", "i_skills_in", "i_email_in", "i_num_in", "i_project_in", "i_photo_in"]:
        if k in st.session_state: del st.session_state[k]

# ==========================================
# UI DIALOGS & POP-UPS
# ==========================================

@st.dialog("Intern Profile")
def show_intern_profile(intern):
    img_src = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    photo_val = intern.get('photo_data')
    if photo_val is not None and isinstance(photo_val, (bytes, bytearray)) and len(photo_val) > 0:
        b64_img = base64.b64encode(photo_val).decode('utf-8')
        img_src = f"data:image/png;base64,{b64_img}"

    st.markdown(f"""
    <div style='text-align: center;'>
        <img src='{img_src}' width='120' height='120' style='margin-bottom: 10px; border-radius: 50%; object-fit: cover; border: 2px solid #39FF14;'>
        <h3 style='margin: 0px; color: #ffffff;'>{intern['Name']}</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Name:** {intern['Name']}")
        st.markdown(f"**Email:** {intern['Email']}")
        st.markdown(f"**Contact:** {intern['Contact']}")
        st.markdown(f"**Interview Process:** {intern['Interview Process']}")
        st.markdown(f"**Internship Type:** {intern['Internship Type']}")
    with col_b:
        st.markdown(f"**Intern ID:** {intern['Intern ID']}")
        st.markdown(f"**Role:** {intern['Role']}")
        st.markdown(f"**Mentor:** {intern['Mentor']}")
        st.markdown(f"**College:** {intern['College']}")
        st.markdown(f"**Branch/Sem:** {intern['Branch']} ({intern['Semester']})")
        
    st.markdown("---")
    st.markdown(f"**Assigned Project:** {intern['Assigned Project']}")
    st.markdown(f"**Completed Projects:** {intern['Completed Projects']}")
    st.markdown(f"**Skills:** {intern['Skills']}")
    st.markdown(f"**Duration:** {intern['Duration']}")
    
    status_color = "#39FF14" if intern['Status'] in ['Active', 'Completed'] else "#ff9900"
    st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold;'>{intern['Status']}</span>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Close Profile", use_container_width=True, key="close_intern_profile"):
        st.rerun() 
        
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(" Remove Intern (Danger Zone)"):
        st.error("⚠️ Warning: This will permanently delete the intern.")
        st.markdown(f"To confirm, type <span style='font-weight: bold; color: #ffffff;'>{intern['Name']}</span> below:", unsafe_allow_html=True)
        
        confirm_input = st.text_input("Type here to confirm:", key=f"del_{intern['Intern ID']}")
        if st.button(" Permanently Delete", type="primary", use_container_width=True):
            if confirm_input.strip().lower() == intern['Name'].strip().lower():
                delete_intern(intern['Intern ID'])
                st.success("Removed successfully!")
                time.sleep(1.5)  
                st.rerun() 
            else:
                st.warning("⚠️ Type name exactly to delete.")

@st.dialog("➕ Add New Intern", width="large")
def add_intern_dialog():
    if "safe_int_data" not in st.session_state:
        st.session_state.safe_int_data = {}
    draft = st.session_state.safe_int_data

    # ------------- STEP 1: FORM UI -------------
    if st.session_state.int_step == "form":
        st.markdown("<p style='color: #a1a1aa;'>Fill out the form below. Fields marked with * are mandatory.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Full Name *", value=draft.get('name', ''), key="i_name_in")
            st.text_input("Contact Number *", value=draft.get('contact', ''), key="i_contact_in")
            
            process_opts = ["Walk in interview", "College Through"]
            p_idx = process_opts.index(draft.get('process', "Walk in interview")) if draft.get('process') in process_opts else 0
            st.selectbox("Interview Process *", process_opts, index=p_idx, key="i_process_in")
            
        with col2:
            st.text_input("Email ID *", value=draft.get('email', ''), key="i_email_in")
            c_id1, c_id2 = st.columns([1, 3])
            c_id1.text_input("Prefix", value="INT-", disabled=True)
            c_id2.text_input("ID Number (3 digits) *", placeholder="001", value=draft.get('num', ''), key="i_num_in")
            
            type_opts = ["Full time", "Half time"]
            t_idx = type_opts.index(draft.get('type', "Full time")) if draft.get('type') in type_opts else 0
            st.selectbox("Internship Type *", type_opts, index=t_idx, key="i_type_in")

        # Dynamic Section: Only show if "College Through" is selected
        if st.session_state.get("i_process_in", "Walk in interview") == "College Through":
            st.markdown("---")
            st.markdown("<p style='color: #39FF14; font-size: 14px; font-weight: bold;'>College Details</p>", unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            with col3:
                st.text_input("College / University *", value=draft.get('college', ''), key="i_college_in")
                sem_opts = ["1st Semester", "2nd Semester", "3rd Semester", "4th Semester", "5th Semester", "6th Semester", "7th Semester", "8th Semester", "9th Semester"]
                s_idx = sem_opts.index(draft.get('sem', "1st Semester")) if draft.get('sem') in sem_opts else 0
                st.selectbox("Semester *", sem_opts, index=s_idx, key="i_sem_in")
            with col4:
                st.text_input("Branch *", value=draft.get('branch', ''), key="i_branch_in")
                st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown("---")
        
        col5, col6 = st.columns(2)
        with col5:
            role_opts = ["AI/ML Developer", "FullStack Developer", "Word Press Developer", "Frontend Developer", "Backend Developer", "Digital Marketing"]
            r_idx = role_opts.index(draft.get('role', "AI/ML Developer")) if draft.get('role') in role_opts else 0
            st.selectbox("Internship Role *", role_opts, index=r_idx, key="i_role_in")
            
            st.text_input("Skills", value=draft.get('skills', ''), key="i_skills_in")
            st.file_uploader("Upload Photo (Optional)", type=['jpg', 'jpeg', 'png'], key="i_photo_in")
            
        with col6:
            st.text_input("Assigned Project", value=draft.get('project', ''), key="i_project_in")
            
            mentor_opts = ["Prajatak sir", "Vikrant sir", "Shahid sir", "Arya sir"]
            m_idx = mentor_opts.index(draft.get('mentor', "Prajatak sir")) if draft.get('mentor') in mentor_opts else 0
            st.selectbox("Assigned Mentor *", mentor_opts, index=m_idx, key="i_mentor_in")
            
            d_col1, d_col2 = st.columns(2)
            d_col1.date_input("Start Date *", value=draft.get('start', datetime.date.today()), key="i_start_in")
            d_col2.date_input("End Date *", value=draft.get('end', datetime.date.today()), key="i_end_in")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.get("int_error"):
            st.error(st.session_state.int_error)
        st.button("👁️ Preview Details", type="primary", use_container_width=True, on_click=int_go_preview)

    # ------------- STEP 2: PREVIEW UI -------------
    elif st.session_state.int_step == "preview":
        data = st.session_state.safe_int_data
        full_id = f"INT-{data['num']}"
        i_duration_str = f"{data['start'].strftime('%d-%b-%Y')} to {data['end'].strftime('%d-%b-%Y')}"
        
        st.markdown("<h3 style='color: #ffffff;'>👁️ Preview Intern Details</h3>", unsafe_allow_html=True)
        
        photo_bytes = st.session_state.get('int_photo_data')
        if photo_bytes is not None:
            b64_p = base64.b64encode(photo_bytes).decode('utf-8')
            st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{b64_p}' width='100' height='100' style='border-radius: 50%; object-fit: cover; border: 2px solid #39FF14;'></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown(f"**Full Name:** {data['name']}")
                st.markdown(f"**Email ID:** {data['email']}")
                st.markdown(f"**Contact Number:** {data['contact']}")
                st.markdown(f"**Interview Process:** {data['process']}")
                st.markdown(f"**Internship Type:** {data['type']}")
                st.markdown(f"**Intern ID:** <span style='color:#39FF14;'>{full_id}</span>", unsafe_allow_html=True)
                
            with col_p2:
                st.markdown(f"**Role:** {data['role']}")
                st.markdown(f"**Assigned Project:** {data['project'] if data['project'] else '-'}")
                st.markdown(f"**Assigned Mentor:** {data['mentor']}")
                st.markdown(f"**Duration:** {i_duration_str}")
                st.markdown(f"**Skills:** {data['skills'] if data['skills'] else '-'}")
                
        if data['process'] == "College Through":
            st.markdown(f"**College Details:** {data['college']} | Branch: {data['branch']} | Sem: {data['sem']}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.get("int_error"):
            st.error(st.session_state.int_error)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.button("✏️ Edit Details", use_container_width=True, on_click=int_go_edit)
        with col_b2:
            if st.button("✅ Confirm & Save", type="primary", use_container_width=True):
                status = add_new_intern(
                    full_id, data['name'], data['email'], data['contact'], 
                    data['role'], data['project'], "-", data['mentor'], 
                    i_duration_str, "Active", data['college'], data['branch'], 
                    data['sem'], data['skills'], photo_bytes, data['process'], data['type']
                )
                if status == "success":
                    st.success("Added Successfully!")
                    time.sleep(1)
                    st.rerun() 
                elif status == "duplicate_email":
                    st.session_state.int_error = "⚠️ Email already exists!"
                    st.rerun()
                else:
                    st.session_state.int_error = "⚠️ Intern ID already exists! Please click Edit Details."
                    st.rerun()

# ==========================================
# TABLES & LOGS SYSTEM
# ==========================================

def create_task_log_table(df):
    html_table = "<table style='width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px;'><tr>"
    for col in ["Name", "Date", "Day", "Today's Task", "Outcome", "Extra Curriculum"]:
        html_table += f"<th style='padding: 12px;'>{col}</th>"
    html_table += "</tr>"
    for _, row in df.iterrows():
        html_table += f"<tr><td style='padding: 12px;'><strong>{row['Name']}</strong></td><td style='padding: 12px;'>{row['Date']}</td><td style='padding: 12px;'>{row['Day']}</td><td style='padding: 12px;'>{row['Task']}</td><td style='padding: 12px;'>{row['Outcome']}</td><td style='padding: 12px;'>{row['Extra Curriculum']}</td></tr>"
    html_table += "</table>"
    return html_table

def create_attendance_table(df):
    html_table = "<table style='width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px;'><tr>"
    for col in ["Date", "Intern Name", "Check-In Time", "Check-Out Time", "Attendance Status"]:
        html_table += f"<th style='padding: 12px;'>{col}</th>"
    html_table += "</tr>"
    for _, row in df.iterrows():
        status_val = row['Status']
        color = "#39FF14" if status_val == 'Present' else "#ff4b4b" if status_val == 'Absent' else "#3498db" if status_val == 'Working' else "#ff9900"
        html_table += f"<tr><td style='padding: 12px;'>{row['Date']}</td><td style='padding: 12px;'><strong>{row['Intern Name']}</strong></td><td style='padding: 12px;'>{row['Check-In']}</td><td style='padding: 12px;'>{row['Check-Out']}</td><td style='padding: 12px; color: {color}; font-weight: bold;'>{status_val}</td></tr>"
    html_table += "</table>"
    return html_table

# ==========================================
# MAIN PAGE RENDER
# ==========================================
def show_intern_page():
    load_global_css() 
    
    # ======== POWERFUL CSS FOR LEFT ALIGNMENT OF NAMES ========
    st.markdown("""
    <style>
    div[data-testid="stButton"] button[kind="tertiary"] {
        color: #60a5fa !important; 
        padding: 0px !important;
        font-weight: bold !important;
        background-color: transparent !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    div[data-testid="stButton"] button[kind="tertiary"] div[data-testid="stMarkdownContainer"] {
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
    }
    div[data-testid="stButton"] button[kind="tertiary"] p {
        text-align: left !important;
        width: 100% !important;
        margin: 0 !important;
    }
    div[data-testid="stButton"] button[kind="tertiary"]:hover {
        color: #39FF14 !important; 
        text-decoration: underline !important;
    }
    </style>
    """, unsafe_allow_html=True)
    # ==========================================================
    
    if "intern_db_initialized" not in st.session_state:
        init_intern_db()
        st.session_state.intern_db_initialized = True
        
    sync_intern_projects()
    df_interns = get_all_interns()
    intern_names_list = df_interns['Name'].tolist() if not df_interns.empty else ["No Interns Found"]

    if 'att_logs' not in st.session_state: st.session_state.att_logs = []
    if 'task_logs' not in st.session_state: st.session_state.task_logs = []
    if 'camera_active' not in st.session_state: st.session_state.camera_active = False

    head_col1, head_col2 = st.columns([4, 1], vertical_alignment="center")
    with head_col1:
        st.markdown("<h1 style='color: #ffffff; margin-bottom: 0px;'>🎓 Intern Management</h1>", unsafe_allow_html=True)
    with head_col2:
        if st.button("➕ Add Intern", type="primary", use_container_width=True):
            prepare_new_intern() 
            add_intern_dialog()  
            
    st.markdown("---")

    main_tab = st.radio("Navigation Menu:", ["🧑‍🎓 Interns Information", "📝 Intern Log"], horizontal=True, label_visibility="collapsed", key="main_intern_navigation")
    st.markdown("<br>", unsafe_allow_html=True)

    if main_tab == "🧑‍🎓 Interns Information":
        st.markdown("<h3 style='color: #ffffff;'>🧑‍🎓 Current Interns Details</h3>", unsafe_allow_html=True)
        
        # Check if database is empty - LIVE STATE MESSAGE
        if len(df_interns) == 0:
            st.markdown("<br><h4 style='text-align:center; color:#ff4b4b; padding:20px; border: 1px dashed #ff4b4b; border-radius: 8px;'>NO DATA IS BEEN ENTERED</h4>", unsafe_allow_html=True)
        else:
            st.markdown("<hr style='margin: 0px; border-top: 2px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1.5, 1.5, 1.5, 1.5, 1, 1.5, 1])
            with col1: st.markdown("**ID**")
            with col2: st.markdown("**Name**")
            with col3: st.markdown("**Role**")
            with col4: st.markdown("**Process**")
            with col5: st.markdown("**Type**")
            with col6: st.markdown("**Mentor**")
            with col7: st.markdown("**Duration**")
            with col8: st.markdown("**Status**")
            st.markdown("<hr style='margin: 0px; border-top: 2px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
            
            for idx, row in df_interns.iterrows():
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1, 1.5, 1.5, 1.5, 1.5, 1, 1.5, 1], vertical_alignment="center")
                with c1: st.write(row['Intern ID'])
                with c2:
                    if st.button(f"🎓 {row['Name']}", key=f"int_{row['Intern ID']}", use_container_width=True, type="tertiary"):
                        show_intern_profile(row)
                with c3: st.write(row['Role'])
                with c4: st.write(row['Interview Process'])
                with c5: st.write(row['Internship Type'])
                with c6: st.write(row['Mentor'])
                with c7: st.write(row['Duration'])
                with c8:
                    color = "#39FF14" if row['Status'] in ['Active', 'Completed'] else "#ff9900"
                    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{row['Status']}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    elif main_tab == "📝 Intern Log":
        st.markdown("<h3 style='color: #ffffff; margin-bottom: 5px;'>📝 Logs Overview</h3>", unsafe_allow_html=True)
        log_type = st.radio("Select Log View:", ["📅 Attendance Log", "📋 Daily Task Log"], horizontal=True, label_visibility="collapsed", key="log_type_radio")
        st.markdown("<br>", unsafe_allow_html=True)

        if log_type == "📅 Attendance Log":
            with st.container(border=True):
                st.markdown("**📸 Capture Photo & Mark Attendance**")
                col1, col2, col3 = st.columns(3)
                
                with col1: sel_intern = st.selectbox("Select Intern Name", intern_names_list, key="att_name_sel")
                with col2: internship_type = st.selectbox("Internship Type", ["Full-Time Internship", "Part-Time Internship"], key="att_type_sel")
                with col3:
                    if internship_type == "Part-Time Internship": duration = st.selectbox("Duration", ["Full Day"], key="att_dur_pt_sel")
                    else: duration = st.selectbox("Duration", ["Full Day", "Half Day"], key="att_dur_ft_sel")

                col4, col5 = st.columns(2)
                with col4:
                    if internship_type == "Full-Time Internship" and duration == "Half Day":
                        slot = st.selectbox("Slots available", ["10:00 AM to 1:30 PM", "2:00 PM to 6:00 PM"], key="att_slot_sel")
                    else:
                        slot = None
                        st.markdown("<br>", unsafe_allow_html=True)
                with col5: att_action = st.selectbox("Action", ["Check-In", "Check-Out"], key="att_action_sel")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if not st.session_state.camera_active:
                    if st.button(" TURN ON CAMERA TO VERIFY", use_container_width=True, type="primary", key="btn_camera_on"):
                        st.session_state.camera_active = True
                        st.rerun()
                else:
                    if st.button(" Turn Off Camera", use_container_width=True, key="btn_camera_off"):
                        st.session_state.camera_active = False
                        st.rerun()
                        
                photo = st.camera_input("Take a picture for verification", key="att_camera_input") if st.session_state.camera_active else None
                
                if photo:
                    now = datetime.datetime.now()
                    current_time = now.time()
                    is_disabled = False
                    time_msg = ""
                    
                    if internship_type == "Part-Time Internship":
                        checkin_start, checkin_end, checkout_start, checkout_end = datetime.time(10, 50), datetime.time(11, 10), datetime.time(14, 50), datetime.time(15, 30)
                        time_msg_in, time_msg_out = " Check-In is only allowed between 10:50 AM and 11:10 AM for Part-Time.", " Check-Out is only allowed between 02:50 PM and 03:30 PM for Part-Time."
                    elif duration == "Half Day":
                        if slot == "10:00 AM to 1:30 PM":
                            checkin_start, checkin_end, checkout_start, checkout_end = datetime.time(9, 50), datetime.time(10, 10), datetime.time(13, 20), datetime.time(13, 40)
                            time_msg_in, time_msg_out = " Check-In is only allowed between 09:50 AM and 10:10 AM for Slot 1.", " Check-Out is only allowed between 01:20 PM and 01:40 PM for Slot 1."
                        else: 
                            checkin_start, checkin_end, checkout_start, checkout_end = datetime.time(13, 50), datetime.time(14, 10), datetime.time(17, 50), datetime.time(18, 30)
                            time_msg_in, time_msg_out = " Check-In is only allowed between 01:50 PM and 02:10 PM for Slot 2.", " Check-Out is only allowed between 05:50 PM and 06:30 PM for Slot 2."
                    else: 
                        checkin_start, checkin_end, checkout_start, checkout_end = datetime.time(9, 50), datetime.time(10, 10), datetime.time(17, 50), datetime.time(18, 30)
                        time_msg_in, time_msg_out = " Check-In is only allowed between 09:50 AM and 10:10 AM.", " Check-Out is only allowed between 05:50 PM and 06:30 PM."
                    
                    if att_action == "Check-In" and not (checkin_start <= current_time <= checkin_end):
                        is_disabled = True; time_msg = time_msg_in
                    elif att_action == "Check-Out" and not (checkout_start <= current_time <= checkout_end):
                        is_disabled = True; time_msg = time_msg_out
                    
                    if is_disabled: st.warning(time_msg)
                        
                    if st.button(f" Confirm {att_action}", use_container_width=True, disabled=is_disabled, key="btn_confirm_att"):
                        date_str, time_str = now.strftime('%d-%b-%Y'), now.strftime('%I:%M %p')
                        record_found = False
                        for record in st.session_state.att_logs:
                            if record['Date'] == date_str and record['Intern Name'] == sel_intern:
                                record_found = True
                                if att_action == "Check-In": st.warning("You have already Checked-In today!")
                                elif att_action == "Check-Out":
                                    record['Check-Out'] = time_str; record['Status'] = "Present"
                                    st.success(f"Check-Out successful for {sel_intern} at {time_str}")
                                    st.session_state.camera_active = False; st.rerun()
                                break
                        if not record_found:
                            if att_action == "Check-In":
                                st.session_state.att_logs.insert(0, {"Date": date_str, "Intern Name": sel_intern, "Check-In": time_str, "Check-Out": "-", "Status": "Working"})
                                st.success(f"Check-In successful for {sel_intern} at {time_str}")
                                st.session_state.camera_active = False; st.rerun()
                            else: st.warning("Please Check-In first before Checking-Out!")

            st.markdown("<h4 style='color: #ffffff; margin-top: 20px;'>📋 Today's Attendance Records</h4>", unsafe_allow_html=True)
            df_att = pd.DataFrame(st.session_state.att_logs)
            if len(df_att) == 0: st.markdown("<p style='color: #a1a1aa; font-size: 16px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px; text-align: center;'>No attendance records available today.</p>", unsafe_allow_html=True)
            else: st.markdown(create_attendance_table(df_att), unsafe_allow_html=True)

        elif log_type == "📋 Daily Task Log":
            now = datetime.datetime.now()
            today_date, today_day = now.strftime('%d-%b-%Y'), now.strftime('%A')
            
            with st.container(border=True):
                col_name, col_date, col_day = st.columns(3)
                with col_name: intern_name = st.selectbox("Select Name", intern_names_list, key="task_name_sel")
                with col_date: st.text_input("Date", value=today_date, disabled=True, key="task_date_input")
                with col_day: st.text_input("Day", value=today_day, disabled=True, key="task_day_input")
                st.markdown("<span style='font-size:14px; color:#ff4b4b;'>* Mandatory Fields</span>", unsafe_allow_html=True)
                task_input = st.text_area("Today's Tasks *", height=100, key="task_desc_input")
                outcome_input = st.text_area("Outcome *", height=100, key="task_out_input")
                extra_input = st.text_area("Extra Curriculum (Optional)", height=80, key="task_extra_input")
                
                if st.button(" Submit Task Log", use_container_width=True, type="primary", key="btn_submit_task"):
                    if not task_input.strip() or not outcome_input.strip(): st.error("Please fill the mandatory fields before submitting.")
                    else:
                        st.session_state.task_logs.insert(0, {"Name": intern_name, "Date": today_date, "Day": today_day, "Task": task_input, "Outcome": outcome_input, "Extra Curriculum": extra_input if extra_input.strip() else "-"})
                        st.success(f"Task log submitted successfully for {intern_name}!"); st.rerun()

            st.markdown("<h4 style='color: #ffffff; margin-top: 20px;'>📋 Recent Task Logs</h4>", unsafe_allow_html=True)
            df_logs = pd.DataFrame(st.session_state.task_logs)
            if len(df_logs) == 0: st.markdown("<p style='color: #a1a1aa; font-size: 16px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px; text-align: center;'>No daily task logs submitted yet.</p>", unsafe_allow_html=True)
            else: st.markdown(create_task_log_table(df_logs), unsafe_allow_html=True)