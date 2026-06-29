import streamlit as st
import sqlite3
import re
import os
from PIL import Image

def init_auth_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.]+@[a-zA-Z.]+\.[a-zA-Z]+$"
    return re.match(pattern, email) is not None

def create_user(username, name, email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)", (username, name, email, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def show_auth_page():
    
    if "auth_db_initialized" not in st.session_state:
        init_auth_db()
        st.session_state.auth_db_initialized = True
    
    st.markdown("""
    <style>
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #f1f1f1 !important;
        border-radius: 5px 5px 0px 0px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.5, 3, 1.5])
    
    with col2:
        with st.container(border=True):
            
            spacer1, logo_col, text_col, spacer2 = st.columns([0.5, 1, 3, 0.5], vertical_alignment="center")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            logo_path = os.path.join(current_dir, "company.png")
            text_path = os.path.join(current_dir, "company text .png")
            
            with logo_col:
                try:
                    if os.path.exists(logo_path):
                        img_logo = Image.open(logo_path)
                        st.image(img_logo, use_container_width=True)
                    else:
                        st.error("Logo file missing")
                except Exception as e:
                    pass
                    
            with text_col:
                try:
                    if os.path.exists(text_path):
                        img_text = Image.open(text_path)
                        st.image(img_text, use_container_width=True)
                    else:
                        st.error("Text file missing")
                except Exception as e:
                    st.markdown("<h2 style='text-align: left; color: #222; margin-bottom: 0px;'>Pararobo CRM</h2>", unsafe_allow_html=True)
                
            st.markdown("<p style='text-align: center; color: #666; font-size: 14px; margin-top: -10px;'>Login to manage your dashboard</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            tab1, tab2 = st.tabs(["Login Here", "Register New Account"])
            
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                # AUTOCOMPLETE WARNING FIX
                log_email = st.text_input("Email ID", key="log_email", placeholder="e.g. john@gmail.com", autocomplete="email")
                log_pass = st.text_input("Password", type="password", key="log_pass", placeholder="Enter your password", autocomplete="current-password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Login", use_container_width=True, type="primary"):
                    if log_email and log_pass:
                        if not is_valid_email(log_email):
                            st.error("Invalid Email Format! Please enter a valid email (e.g., abcd@gmail.com)")
                        else:
                            user = verify_user(log_email, log_pass)
                            if user:
                                st.session_state['logged_in'] = True
                                st.session_state['current_user_name'] = user[1] 
                                st.success(f"Welcome back, {user[1]}! Redirecting to Dashboard...")
                                st.rerun()
                            else:
                                st.error("Invalid Email ID or Password!")
                    else:
                        st.warning("⚠️ Please enter both email and password.")
                        
            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                reg_name = st.text_input("Full Name", key="reg_name", placeholder="e.g. John Doe", autocomplete="name")
                reg_user = st.text_input("Choose Username", key="reg_user", placeholder="johndoe123", autocomplete="username")
                reg_email = st.text_input("Email ID", key="reg_email", placeholder="e.g. john@gmail.com", autocomplete="email")
                reg_pass = st.text_input("Create Password", type="password", key="reg_pass", placeholder="Make it strong!", autocomplete="new-password")
                reg_confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm_pass", placeholder="Re-enter your password", autocomplete="new-password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Create Account", use_container_width=True, type="primary"):
                    if reg_name and reg_email and reg_user and reg_pass and reg_confirm_pass:
                        if not is_valid_email(reg_email):
                            st.error("Invalid Email Format! Please enter a valid email (e.g., abcd@gmail.com)")
                        elif reg_pass == reg_confirm_pass:
                            if create_user(reg_user, reg_name, reg_email, reg_pass):
                                st.success("Account created successfully! Please switch to the Login tab.")
                            else:
                                st.error("⚠️ Username or Email already exists! Please choose a different one.")
                        else:
                            st.error("Passwords do not match! Please check and try again.")
                    else:
                        st.warning("⚠️ Please fill all the fields to register.")