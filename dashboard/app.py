import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm
import os

# 1. Page Config
st.set_page_config(
    page_title="Onboarding A/B Test Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Theme Toggle State Setup
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# 3. CSS Variables Injection
bg_val = "#09090b" if IS_DARK else "#ffffff"
bg_subtle_val = "#0c0c0f" if IS_DARK else "#f9fafb"
card_val = "#0c0c0f" if IS_DARK else "#ffffff"
border_val = "#1e1e24" if IS_DARK else "#e4e4e7"
text_val = "#fafafa" if IS_DARK else "#09090b"
text_muted_val = "#71717a"
text_dim_val = "#52525b" if IS_DARK else "#a1a1aa"
shadow_val = "none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"
green_val = "#22c55e" if IS_DARK else "#16a34a"
green_muted_val = "rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"
red_val = "#ef4444" if IS_DARK else "#dc2626"
red_muted_val = "rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"
accent_val = "#50E3C2" # Treatment Muted Sea Teal
control_val = "#4A90E2" # Control Cool Slate Blue

css = f"""
<style>
    /* Global Overrides */
    :root {{
        --bg: {bg_val};
        --bg-subtle: {bg_subtle_val};
        --card: {card_val};
        --border: {border_val};
        --text: {text_val};
        --text-muted: {text_muted_val};
        --text-dim: {text_dim_val};
        --shadow: {shadow_val};
        --radius: 12px;
    }}
    
    header[data-testid="stHeader"], [data-testid="stToolbar"], .stDeployButton {{
        display: none !important;
    }}
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }}
    
    .block-container {{
        padding: 1.5rem 2rem 2rem !important;
        max-width: 1400px !important;
    }}
    
    /* Layout Gap spacing */
    [data-testid="stHorizontalBlock"] {{
        gap: 1.25rem !important;
    }}
    
    /* Metric Cards */
    .metric-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.1rem 1.3rem;
        box-shadow: var(--shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .metric-label {{
        font-size: 0.76rem;
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .metric-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text);
        margin: 0.3rem 0;
        letter-spacing: -0.02em;
    }}
    .metric-delta {{
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        width: fit-content;
        gap: 3px;
    }}
    .delta-up {{
        color: {green_val};
        background: {green_muted_val};
    }}
    .delta-down {{
        color: {red_val};
        background: {red_muted_val};
    }}
    .delta-neutral {{
        color: var(--text-muted);
        background: rgba(113,113,122,0.1);
    }}
    
    /* Chart Wrap */
    .chart-wrap {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.25rem;
    }}
    .chart-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text);
    }}
    .chart-subtitle {{
        font-size: 0.72rem;
        color: var(--text-dim);
        margin-bottom: 0.8rem;
    }}
    
    /* Segment Table */
    .data-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.8rem;
    }}
    .data-table th {{
        text-align: left;
        padding: 0.6rem 0.8rem;
        color: var(--text-muted);
        font-weight: 600;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid var(--border);
    }}
    .data-table td {{
        padding: 0.6rem 0.8rem;
        color: var(--text);
        border-bottom: 1px solid { "#1e1e24" if IS_DARK else "#f0f0f2" };
    }}
    .data-table tr:last-child td {{
        border-bottom: none;
    }}
    
    /* Badges */
    .badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
    }}
    .badge-green {{ color: {green_val}; background: {green_muted_val}; }}
    .badge-red {{ color: {red_val}; background: {red_muted_val}; }}
    .badge-blue {{ color: {control_val}; background: rgba(74,144,226,0.12); }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# 4. Helper Visual Components
def metric_card(label, value, delta=None, delta_type="up"):
    if delta_type == "up":
        cls = "delta-up"
        arrow = "↑"
    elif delta_type == "down":
        cls = "delta-down"
        arrow = "↓"
    else:
        cls = "delta-neutral"
        arrow = "•"
        
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# Plotly styling configuration
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="BlinkMacSystemFont, sans-serif", color="#a1a1aa" if IS_DARK else "#71717a", size=11),
    margin=dict(l=40, r=20, t=25, b=30),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
        zerolinecolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
        zerolinecolor="rgba(255,255,255,0.05)" if IS_DARK else "rgba(0,0,0,0.05)",
    ),
)

# 5. Data Loading & Cleaning
@st.cache_data
def load_and_clean_data():
    # Paths relative to execution directory
    demographics_path = "data/raw_user_demographics.csv"
    events_path = "data/raw_user_events.csv"
    
    if not os.path.exists(demographics_path) or not os.path.exists(events_path):
        # Fallback for folder structure
        demographics_path = "../data/raw_user_demographics.csv"
        events_path = "../data/raw_user_events.csv"
        
    df_demo = pd.read_csv(demographics_path)
    df_evt = pd.read_csv(events_path)
    
    # Cleaning
    df_evt = df_evt.drop_duplicates()
    df_demo['signup_date'] = pd.to_datetime(df_demo['signup_date'])
    df_evt['timestamp'] = pd.to_datetime(df_evt['timestamp'])
    
    # Filter anomalies
    df_demo = df_demo[(df_demo['signup_date'] >= '2026-01-01') & (df_demo['signup_date'] <= '2026-03-31')]
    df_evt = df_evt[df_evt['user_id'].isin(df_demo['user_id'])]
    
    # Fill NAs
    df_demo['device'] = df_demo['device'].fillna('Unknown')
    df_demo['country'] = df_demo['country'].fillna('Unknown')
    
    # Fix negative purchase amounts
    df_evt.loc[(df_evt['event_name'] == 'purchase') & (df_evt['event_value'] < 0), 'event_value'] = df_evt['event_value'].abs()
    
    return df_demo, df_evt

try:
    df_demo, df_evt = load_and_clean_data()
except Exception as e:
    st.error(f"Error loading datasets. Verify that generate_data.py has run. Details: {e}")
    st.stop()

# 6. Sidebar / Filter Panels
st.sidebar.markdown("### Experiment Filters")

# Device filter
device_options = ["All"] + list(df_demo['device'].unique())
selected_device = st.sidebar.selectbox("Device Segment", device_options)

# Country filter
country_options = ["All"] + list(df_demo['country'].unique())
selected_country = st.sidebar.selectbox("Country Segment", country_options)

# Apply filters
df_demo_filtered = df_demo.copy()
if selected_device != "All":
    df_demo_filtered = df_demo_filtered[df_demo_filtered['device'] == selected_device]
if selected_country != "All":
    df_demo_filtered = df_demo_filtered[df_demo_filtered['country'] == selected_country]
    
df_evt_filtered = df_evt[df_evt['user_id'].isin(df_demo_filtered['user_id'])].copy()

# A/B users subset
df_ab_users = df_demo_filtered[df_demo_filtered['ab_variant'].isin(['control', 'treatment'])].copy()
df_ab_events = df_evt_filtered[df_evt_filtered['user_id'].isin(df_ab_users['user_id'])].copy()

# 7. Header
head_left, head_right = st.columns([10, 2])
with head_left:
    st.markdown(f"""
    <div style='margin-bottom: 1.5rem;'>
        <h2 style='margin: 0; font-weight: 800; letter-spacing: -0.03em; color: {text_val};'>
            Onboarding A/B Test Dashboard
        </h2>
        <p style='margin: 3px 0 0; font-size: 0.85rem; color: var(--text-muted);'>
            Interactive Experimentation Performance & Funnel Diagnostics
        </p>
    </div>
    """, unsafe_allow_html=True)
with head_right:
    theme_label = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

# 8. Calculations for KPIs
# Totals
totals = df_ab_users.groupby('ab_variant')['user_id'].nunique()
for var in ['control', 'treatment']:
    if var not in totals:
        totals[var] = 0

# Conversions (purchasers)
purchasers = df_ab_events[df_ab_events['event_name'] == 'purchase']['user_id'].unique()
df_ab_users['converted'] = df_ab_users['user_id'].isin(purchasers).astype(int)
conversions = df_ab_users.groupby('ab_variant')['converted'].sum()
for var in ['control', 'treatment']:
    if var not in conversions:
        conversions[var] = 0

# Rates
rates = {
    'control': conversions['control'] / totals['control'] if totals['control'] > 0 else 0,
    'treatment': conversions['treatment'] / totals['treatment'] if totals['treatment'] > 0 else 0,
}

# 7-Day Retention
df_ab_events['days_since_signup'] = (
    df_ab_events['timestamp'] - 
    df_ab_events['user_id'].map(df_ab_users.set_index('user_id')['signup_date'])
).dt.days
retained_day_7 = df_ab_events[df_ab_events['days_since_signup'] == 7]['user_id'].unique()
df_ab_users['retained_day_7'] = df_ab_users['user_id'].isin(retained_day_7).astype(int)
ret_success = df_ab_users.groupby('ab_variant')['retained_day_7'].sum()
for var in ['control', 'treatment']:
    if var not in ret_success:
        ret_success[var] = 0
ret_rates = {
    'control': ret_success['control'] / totals['control'] if totals['control'] > 0 else 0,
    'treatment': ret_success['treatment'] / totals['treatment'] if totals['treatment'] > 0 else 0,
}

# Average Order Value (AOV)
df_purchases = df_ab_events[df_ab_events['event_name'] == 'purchase']
aov_control = df_purchases[df_purchases['user_id'].isin(df_ab_users[df_ab_users['ab_variant'] == 'control']['user_id'])]['event_value'].mean()
aov_treatment = df_purchases[df_purchases['user_id'].isin(df_ab_users[df_ab_users['ab_variant'] == 'treatment']['user_id'])]['event_value'].mean()
aov_control = 0.0 if np.isnan(aov_control) else aov_control
aov_treatment = 0.0 if np.isnan(aov_treatment) else aov_treatment

# Z-test for conversion significance
z_score, p_value, significance = 0.0, 1.0, "No Data"
if totals['control'] > 0 and totals['treatment'] > 0:
    n_c, n_t = totals['control'], totals['treatment']
    p_c, p_t = rates['control'], rates['treatment']
    p_combined = (conversions['control'] + conversions['treatment']) / (n_c + n_t)
    if p_combined > 0 and p_combined < 1:
        se = np.sqrt(p_combined * (1 - p_combined) * (1/n_c + 1/n_t))
        z_score = (p_t - p_c) / se
        p_value = 2 * (1 - norm.cdf(abs(z_score)))
        significance = "SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"

# KPI Layout row
c1, c2, c3, c4 = st.columns(4)
with c1:
    lift = rates['treatment'] - rates['control']
    lift_str = f"{lift:+.1%}"
    metric_card(
        "Conversion Lift", 
        f"{rates['treatment']:.1%}", 
        delta=f"{lift_str} relative to control ({rates['control']:.1%})", 
        delta_type="up" if lift > 0 else "down"
    )
with c2:
    ret_lift = ret_rates['treatment'] - ret_rates['control']
    ret_lift_str = f"{ret_lift:+.1%}"
    metric_card(
        "Day 7 Retention", 
        f"{ret_rates['treatment']:.1%}", 
        delta=f"{ret_lift_str} vs control ({ret_rates['control']:.1%})", 
        delta_type="up" if ret_lift > 0 else "down"
    )
with c3:
    aov_diff = aov_treatment - aov_control
    aov_diff_str = f"${aov_diff:+.2f}"
    metric_card(
        "Average Order Value", 
        f"${aov_treatment:.2f}", 
        delta=f"{aov_diff_str} vs control (${aov_control:.2f})", 
        delta_type="up" if aov_diff >= 0 else "down"
    )
with c4:
    badge_cls = "badge-green" if significance == "SIGNIFICANT" else "badge-red"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Experiment Status</div>
        <div class="metric-value" style="font-size: 1.35rem; margin-top: 0.5rem;">
            <span class="badge {badge_cls}">{significance}</span>
        </div>
        <div class="metric-label" style="font-size: 0.65rem; margin-top: 0.5rem; text-transform: none;">
            Z-score: {z_score:.2f} (p-value: {p_value:.4f})
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

# 9. Main Visualizations Row
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Onboarding Funnel Analysis</div>
        <div class="chart-subtitle">Unique users completing onboarding stages (March A/B cohort)</div>
    """, unsafe_allow_html=True)
    
    # Calculate funnel steps
    funnel_stages = ['sign_up', 'email_verified', 'tutorial_start', 'tutorial_complete', 'purchase']
    fig_funnel = go.Figure()
    
    for var, name, col in zip(['control', 'treatment'], ['Control (Old)', 'Treatment (New)'], [control_val, accent_val]):
        v_users = df_ab_users[df_ab_users['ab_variant'] == var]['user_id']
        t_signups = len(v_users)
        
        stage_counts = [t_signups]
        for stage in funnel_stages[1:]:
            counts = df_ab_events[
                (df_ab_events['user_id'].isin(v_users)) & 
                (df_ab_events['event_name'] == stage)
            ]['user_id'].nunique()
            stage_counts.append(counts)
            
        fig_funnel.add_trace(go.Bar(
            y=funnel_stages[::-1],
            x=stage_counts[::-1],
            orientation='h',
            name=name,
            marker_color=col,
            hovertemplate='%{x} users'
        ))
        
    layout_funnel = PLOT_LAYOUT.copy()
    layout_funnel['margin'] = dict(l=110, r=10, t=10, b=10)
    fig_funnel.update_layout(
        **layout_funnel,
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Daily Retention Curves</div>
        <div class="chart-subtitle">Percent of users returning on specific days since signup</div>
    """, unsafe_allow_html=True)
    
    # Calculate retention curves
    ret_data = []
    for day in range(8):
        for var, col in zip(['control', 'treatment'], [control_val, accent_val]):
            v_users = df_ab_users[df_ab_users['ab_variant'] == var]['user_id']
            t_signups = len(v_users)
            
            active = df_ab_events[
                (df_ab_events['days_since_signup'] == day) & 
                (df_ab_events['user_id'].isin(v_users))
            ]['user_id'].nunique()
            
            rate = active / t_signups if t_signups > 0 else 0
            ret_data.append({'Day': day, 'Variant': var.capitalize(), 'Rate': rate * 100})
            
    df_ret_curves = pd.DataFrame(ret_data)
    
    fig_ret = px.line(
        df_ret_curves, 
        x='Day', 
        y='Rate', 
        color='Variant',
        color_discrete_map={'Control': control_val, 'Treatment': accent_val},
        markers=True
    )
    layout_ret = PLOT_LAYOUT.copy()
    layout_ret['margin'] = dict(l=40, r=20, t=10, b=10)
    fig_ret.update_layout(
        **layout_ret,
        yaxis_title="Percent Active (%)",
        xaxis_title="Days Since Signup",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_ret, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# 10. Bottom Row: Cohort matrix & Segment conversions
col_b_left, col_b_right = st.columns([1.2, 0.8])

with col_b_left:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Weekly Cohort Retention Heatmap</div>
        <div class="chart-subtitle">Historical baseline retention (pre-A/B test cohorts, Jan - Feb)</div>
    """, unsafe_allow_html=True)
    
    df_pre_test = df_demo_filtered[df_demo_filtered['ab_variant'] == 'not_applicable'].copy()
    
    if len(df_pre_test) > 0:
        df_pre_test['cohort_week'] = df_pre_test['signup_date'].dt.to_period('W').astype(str)
        df_pre_events = df_evt_filtered[df_evt_filtered['user_id'].isin(df_pre_test['user_id'])].copy()
        df_pre_events = df_pre_events.merge(df_pre_test[['user_id', 'signup_date', 'cohort_week']], on='user_id')
        df_pre_events['days_since_signup'] = (df_pre_events['timestamp'] - df_pre_events['signup_date']).dt.days
        
        cohorts = df_pre_events.groupby(['cohort_week', 'days_since_signup'])['user_id'].nunique().reset_index()
        cohort_pivot = cohorts.pivot(index='cohort_week', columns='days_since_signup', values='user_id')
        cohort_sizes = cohort_pivot[0]
        retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0).iloc[:, :8]
        
        fig_heat = px.imshow(
            retention_matrix * 100,
            labels=dict(x="Days Since Signup", y="Cohort Week", color="Retention (%)"),
            x=list(range(8)),
            y=list(retention_matrix.index),
            color_continuous_scale="Blues",
            text_auto=".1f"
        )
        layout_heat = PLOT_LAYOUT.copy()
        layout_heat['margin'] = dict(l=80, r=20, t=10, b=10)
        fig_heat.update_layout(
            **layout_heat,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No baseline user records matched this filter combination.")
        
    st.markdown("</div>", unsafe_allow_html=True)

with col_b_right:
    st.markdown("""
    <div class="chart-wrap" style="height: 100%;">
        <div class="chart-title">Device segment Breakdown</div>
        <div class="chart-subtitle">Control vs Treatment Conversion Rate and Lift</div>
    """, unsafe_allow_html=True)
    
    # Calculate conversion metrics by device
    device_breakdown = []
    for dev in df_ab_users['device'].unique():
        dev_users = df_ab_users[df_ab_users['device'] == dev]
        
        # control
        c_users = dev_users[dev_users['ab_variant'] == 'control']
        c_conv = c_users['converted'].mean() if len(c_users) > 0 else 0
        
        # treatment
        t_users = dev_users[dev_users['ab_variant'] == 'treatment']
        t_conv = t_users['converted'].mean() if len(t_users) > 0 else 0
        
        lift_val = t_conv - c_conv
        
        device_breakdown.append({
            'Device': dev,
            'Control Conv.': f"{c_conv:.1%}",
            'Treatment Conv.': f"{t_conv:.1%}",
            'Lift': f"{lift_val:+.1%}",
            'Direction': "badge-green" if lift_val > 0 else ("badge-red" if lift_val < 0 else "badge-blue")
        })
        
    # Render table
    table_rows = ""
    for r in device_breakdown:
        table_rows += f"<tr><td style='font-weight:600;'>{r['Device']}</td><td>{r['Control Conv.']}</td><td>{r['Treatment Conv.']}</td><td><span class='badge {r['Direction']}'>{r['Lift']}</span></td></tr>"
        
    st.markdown(f"""<table class="data-table">
<thead>
<tr>
<th>Device</th>
<th>Control</th>
<th>Treatment</th>
<th>Lift</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
