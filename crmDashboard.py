# 1. Importing required tools for the application
import streamlit as st
from utils import load_global_css
import time
import urllib.parse
import streamlit.components.v1 as components

# Page configuration must be the first Streamlit command
st.set_page_config(page_title="CRM Dashboard", layout="wide", initial_sidebar_state="expanded")

# Load custom global CSS styles (Dark Theme)
load_global_css()

# Importing the other page modules
import employeeDetail
import internDetail
import projectDetail
import taskDetail
import leadDetail
import clientDetail
import quotationAndProposal

# Get the current page from the URL (default is Dashboard)
current_page = st.query_params.get("page", "Dashboard")

# Function to change pages smoothly from the sidebar
def navigate(page_name):
    st.query_params["page"] = page_name
    st.session_state['collapse_sidebar'] = True 

# ==========================================
# AUTO-COLLAPSE SIDEBAR SCRIPT
# ==========================================
# This script automatically closes the left sidebar to give more screen space
if st.session_state.get('collapse_sidebar', False):
    unique_id = int(time.time() * 1000) 
    
    components.html(
        f"""
        <div id="sidebar_trigger_{unique_id}"></div>
        <script>
        setTimeout(function() {{
            const doc = window.parent.document;
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            
            // STEP 1: Close all open drop-downs (expanders) in the sidebar
            if (sidebar) {{
                const openExpanders = sidebar.querySelectorAll('details[open] summary');
                for (let i = 0; i < openExpanders.length; i++) {{
                    openExpanders[i].click(); 
                }}
            }}

            // STEP 2: Wait 150ms and then click the collapse button
            setTimeout(function() {{
                const buttons = doc.querySelectorAll('button');
                let clicked = false;
                
                for (let i = 0; i < buttons.length; i++) {{
                    let aria = buttons[i].getAttribute('aria-label');
                    let title = buttons[i].getAttribute('title');
                    
                    if (aria === 'Collapse sidebar' || title === 'Collapse sidebar' || aria === 'Close' || title === 'Close') {{
                        buttons[i].click();
                        clicked = true;
                        break;
                    }}
                }}
                
                if (!clicked && sidebar) {{
                    const firstBtn = sidebar.querySelector('button');
                    if (firstBtn) {{
                        firstBtn.click();
                    }}
                }}
            }}, 150); 
            
        }}, 50); 
        </script>
        """,
        height=0, width=0
    )
    st.session_state['collapse_sidebar'] = False

# ==========================================
# KPI CARD CREATION FUNCTION (NEW LOGIC)
# ==========================================
# This function creates a beautifully styled KPI card that acts as a direct link!
# The invisible button is completely removed.
def create_clickable_kpi_card(title, value, delta, is_negative=False):
    delta_color = "#ff4b4b" if is_negative else "#39FF14" 
    
    # Safely format the title for the URL link
    safe_title = urllib.parse.quote(title)
    
    # HTML and CSS to create the card and make the entire card clickable
    html_code = f"""
    <style>
    /* Styling the link tag to remove default text underlines */
    .kpi-link {{
        text-decoration: none !important;
        display: block;
    }}
    
    /* Styling the actual card box (Default State) */
    .kpi-box {{
        cursor: pointer;
        padding: 20px;
        border-radius: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }}
    
    /* Adding a premium hover effect when the mouse goes over the card */
    .kpi-box:hover {{
        transform: translateY(-5px);
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid #3498db;
        box-shadow: 0px 8px 15px rgba(0, 0, 0, 0.3);
    }}
    </style>
    
    <a href="?page={safe_title}" target="_self" class="kpi-link">
        <div class="kpi-box">
            <p style="margin: 0; font-size: 16px; font-weight: bold; color: #a1a1aa;">{title}</p>
            <h2 style="margin: 5px 0; font-size: 32px; color: #ffffff;">{value}</h2>
            <p style="margin: 0; font-size: 16px; font-weight: bold; color: {delta_color};">{delta}</p>
        </div>
    </a>
    """
    
    # Render the interactive HTML card on the screen
    st.markdown(html_code, unsafe_allow_html=True)
    
    # NOTE: The invisible button code has been permanently deleted!

# ==========================================
# SIDEBAR MENU NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h2>Menu</h2>", unsafe_allow_html=True)
    
    if st.button("📊 Dashboard", use_container_width=True):
        navigate("Dashboard")
        st.rerun()
        
    with st.expander("🧑‍💼 Employees Detail"):
        if st.button("View Employees", use_container_width=True):
            navigate("Employees Detail")
            st.rerun()
       
    with st.expander("🧑‍🎓 Interns Detail"):
        if st.button("View Intern", use_container_width=True):
            navigate("Intern Detail")
            st.rerun()
                    
    with st.expander("📂 Project Detail"):
        if st.button("View Projects", use_container_width=True):
            navigate("Project Detail")
            st.rerun()
            
    with st.expander("📝 Task"):
        if st.button("View Tasks", use_container_width=True):
            navigate("Task")
            st.rerun()
            
    with st.expander("🎯 Leads"):
        if st.button("View Leads", use_container_width=True):
            navigate("Lead Detail")
            st.rerun()
            
    with st.expander("🤝 Client Management"):
        if st.button("View Clients", use_container_width=True):
            navigate("Client Detail")
            st.rerun()

    with st.expander("📄 Quotation & Proposal"):
        if st.button("View Proposals", use_container_width=True):
            navigate("Quotation and Proposal")
            st.rerun()

    st.markdown("---")
    
    # Logout functionality clears memory and reloads the app
    if st.button("🚪 Logout", use_container_width=True, type="primary"):
        st.session_state['logged_in'] = False
        st.session_state.pop('current_user_name', None)
        st.query_params.clear()
        st.rerun()

# List of KPI pages for routing
kpi_pages = [
    "Total Leads", "Qualified Leads", "Active Clients", 
    "Revenue This Month", "Pending Payments", "Ongoing Projects", 
    "Team Utilization %", "Open Support Tickets", "Interns Active", 
    "Proposal Conversion Rate"
]

# ==========================================
# PAGE ROUTING (Renders the selected page)
# ==========================================
if current_page == "Dashboard":

    # Dashboard Header with Logos
    spacer_left, logo_col, text_col, spacer_right = st.columns([2.5, 1, 4, 2.5], vertical_alignment="center")
    
    with logo_col:
        st.image("pararobo.png", width=500)
    with text_col:
        st.image("pararobo text .png", width=500)

    # Welcome message with the user's name if logged in
    welcome_name = st.session_state.get('current_user_name', '')
    if welcome_name:
        st.markdown(f"<h3 style='text-align: left; margin-top: 15px;'>👋 Welcome, {welcome_name}! | 📊 CRM Dashboard</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='text-align: left; margin-top: 15px;'>📊 CRM Dashboard</h3>", unsafe_allow_html=True)
        
    st.markdown("---")

    # Rendering Top Row KPI Cards
    row1_cols = st.columns(5)
    with row1_cols[0]:
        create_clickable_kpi_card("Total Leads", "1,245", "↑ 12%")
    with row1_cols[1]:
        create_clickable_kpi_card("Qualified Leads", "842", "↑ 5%")
    with row1_cols[2]:
        create_clickable_kpi_card("Active Clients", "150", "↑ 3")
    with row1_cols[3]:
        create_clickable_kpi_card("Revenue This Month", "$45,200", "↑ $2,400")
    with row1_cols[4]:
        create_clickable_kpi_card("Pending Payments", "$8,400", "↓ -$400", is_negative=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Rendering Bottom Row KPI Cards
    row2_cols = st.columns(5)
    with row2_cols[0]:
        create_clickable_kpi_card("Ongoing Projects", "24", "↑ 2")
    with row2_cols[1]:
        create_clickable_kpi_card("Team Utilization %", "85%", "↑ 4%")
    with row2_cols[2]:
        create_clickable_kpi_card("Open Support Tickets", "12", "↓ -3", is_negative=True)
    with row2_cols[3]:
        create_clickable_kpi_card("Interns Active", "5", "↑ 1")
    with row2_cols[4]:
        create_clickable_kpi_card("Proposal Conversion Rate", "68%", "↑ 2.5%")

# Load the respective module based on user selection
elif current_page == "Employees Detail":
    employeeDetail.show_employee_page()

elif current_page == "Intern Detail":
    internDetail.show_intern_page()

elif current_page == "Task":
    taskDetail.show_task_page()

elif current_page == "Project Detail":
    projectDetail.show_project_page()

elif current_page == "Lead Detail":
    leadDetail.show_lead_page()

elif current_page == "Client Detail":
    clientDetail.show_client_page()

elif current_page == "Quotation and Proposal":
    quotationAndProposal.show_proposal_page()

# Placeholder template for all KPI analytical pages
elif current_page in kpi_pages:
    st.markdown(f"<h1>Welcome to {current_page}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<h3>Detailed view and analytics for {current_page} will be displayed here.</h3>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Button to return to the main dashboard
    if st.button("⬅ Back to Dashboard", use_container_width=False):
        navigate("Dashboard")
        st.rerun()