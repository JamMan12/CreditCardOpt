import streamlit as st
import pandas as pd
from src.models.schemas import UserPreferences, CategorySpend
from src.data.loader import ALL_CARDS, POINT_VALUATIONS
from src.optimizer.engine import CreditCardOptimizer

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardOptimizer – Find Your Perfect Wallet",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Hero / Header */
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #8892b0;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* Card Tiles */
    .card-tile {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(102, 126, 234, 0.25);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
    }
    .card-name {
        font-size: 1.2rem;
        font-weight: 700;
        color: #e6f1ff;
        margin-bottom: 0.3rem;
    }
    .card-issuer {
        font-size: 0.85rem;
        color: #8892b0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-detail {
        font-size: 0.9rem;
        color: #a8b2d1;
        margin-top: 0.15rem;
    }
    .card-badge {
        display: inline-block;
        background: rgba(102, 126, 234, 0.15);
        color: #667eea;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-top: 0.5rem;
    }
    .card-badge.green {
        background: rgba(100, 255, 218, 0.1);
        color: #64ffda;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        text-align: center;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #8892b0;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e6f1ff;
    }
    .metric-value.positive { color: #64ffda; }
    .metric-value.negative { color: #ff6b6b; }

    /* Allocation Table */
    .alloc-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ccd6f6;
        margin-bottom: 0.8rem;
        margin-top: 1.5rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a1a 0%, #111127 100%);
        border-right: 1px solid rgba(102, 126, 234, 0.15);
    }
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: #ccd6f6 !important;
    }
    .sidebar-section-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #667eea;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid rgba(102, 126, 234, 0.2);
    }

    /* Divider */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102,126,234,0.3), transparent);
        margin: 1.5rem 0;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Sidebar: User Inputs ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💳 Your Profile")
    st.markdown('<p style="color:#8892b0; font-size: 0.85rem;">Tell us about your spending so we can find the optimal credit card wallet for you.</p>', unsafe_allow_html=True)

    # Spending Categories
    st.markdown('<div class="sidebar-section-title">Monthly Spending</div>', unsafe_allow_html=True)

    CATEGORIES = [
        ("dining", "🍽️ Dining", 400),
        ("grocery", "🛒 Grocery", 500),
        ("gas", "⛽ Gas", 150),
        ("travel", "✈️ Travel", 200),
        ("transit", "🚇 Transit", 100),
        ("streaming", "📺 Streaming", 30),
        ("recurring", "🔁 Recurring Bills", 200),
        ("other", "💡 Everything Else", 500),
    ]

    monthly_spend = {}
    for cat_key, cat_label, default_val in CATEGORIES:
        monthly_spend[cat_key] = st.number_input(
            cat_label,
            min_value=0,
            max_value=10000,
            value=default_val,
            step=25,
            key=f"spend_{cat_key}",
        )

    # Constraints
    st.markdown('<div class="sidebar-section-title">Constraints</div>', unsafe_allow_html=True)

    max_annual_fee = st.slider(
        "💰 Max Total Annual Fee",
        min_value=0,
        max_value=1000,
        value=300,
        step=25,
        help="Maximum combined annual fees you're willing to pay across all cards.",
    )

    max_cards = st.slider(
        "🃏 Max Cards in Wallet",
        min_value=1,
        max_value=5,
        value=2,
        help="Maximum number of credit cards you want to carry.",
    )

    # Required Perks
    st.markdown('<div class="sidebar-section-title">Required Perks</div>', unsafe_allow_html=True)
    require_no_fx = st.checkbox("🌍 No Foreign Transaction Fees", value=False)
    require_lounge = st.checkbox("🛋️ Airport Lounge Access", value=False)

    st.markdown("---")
    optimize_btn = st.button("🚀 Optimize My Wallet", type="primary", use_container_width=True)


# ─── Main Content ───────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">CardOptimizer</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Mathematically optimal credit card recommendations powered by OR-Tools optimization.</p>', unsafe_allow_html=True)

if optimize_btn or "result" in st.session_state:
    # Build preferences
    category_spends = [
        CategorySpend(category=key, monthly_amount=val)
        for key, val in monthly_spend.items()
        if val > 0
    ]

    prefs = UserPreferences(
        monthly_spend=category_spends,
        max_annual_fee=max_annual_fee,
        max_cards=max_cards,
        require_no_fx_fee=require_no_fx,
        require_lounge_access=require_lounge,
    )

    # Run optimizer
    optimizer = CreditCardOptimizer(cards=ALL_CARDS, user_prefs=prefs)
    result = optimizer.optimize()
    st.session_state["result"] = result

    if result is None:
        st.error("😔 **No feasible solution found.** Try loosening your constraints (increase fee budget, allow more cards, or relax perk requirements).")
    else:
        # ── Value Summary Metrics ────────────────────────────────────────────
        net_yr1 = result.total_rewards_value + result.total_welcome_bonus_value - result.total_annual_fees
        net_yr2 = result.total_rewards_value - result.total_annual_fees

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Year 1 Net Value</div>
                <div class="metric-value positive">${net_yr1:,.2f}</div>
            </div>""", unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Year 2+ Net Value</div>
                <div class="metric-value positive">${net_yr2:,.2f}</div>
            </div>""", unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Annual Fees</div>
                <div class="metric-value negative">${result.total_annual_fees:,.2f}</div>
            </div>""", unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Welcome Bonuses</div>
                <div class="metric-value positive">${result.total_welcome_bonus_value:,.2f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # ── Selected Cards ───────────────────────────────────────────────────
        st.markdown("### 🏆 Your Optimal Wallet")

        cols = st.columns(len(result.selected_cards))
        for i, card in enumerate(result.selected_cards):
            with cols[i]:
                badges = ""
                if card.has_no_fx_fee:
                    badges += '<span class="card-badge green">No FX Fee</span>'
                if card.has_lounge_access:
                    badges += '<span class="card-badge green">Lounge</span>'
                badges += f'<span class="card-badge">{card.network}</span>'
                badges += f'<span class="card-badge">{card.point_system.replace("_", " ").title()}</span>'

                wb_val = card.welcome_bonus_points * POINT_VALUATIONS.get(card.point_system, 1.0) / 100
                fee_display = f"${card.effective_first_year_fee:,.0f} yr 1 / ${card.annual_fee:,.0f} yr 2+"

                st.markdown(f"""
                <div class="card-tile">
                    <div class="card-issuer">{card.issuer}</div>
                    <div class="card-name">{card.name}</div>
                    <div class="card-detail">📋 Fee: {fee_display}</div>
                    <div class="card-detail">🎁 Welcome Bonus: {card.welcome_bonus_points:,} pts (${wb_val:,.0f})</div>
                    {badges}
                </div>""", unsafe_allow_html=True)

        # ── Spend Allocation ─────────────────────────────────────────────────
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📊 Spend Allocation")
        st.markdown('<p style="color:#8892b0; font-size:0.9rem;">Which card to use for each spending category to maximize your rewards.</p>', unsafe_allow_html=True)

        # Build a table
        alloc_rows = []
        cat_labels = {key: label for key, label, _ in CATEGORIES}
        for cat, allocations in result.spend_allocations.items():
            for card_id, amount in allocations:
                card = next((c for c in result.selected_cards if c.id == card_id), None)
                if card and amount > 0:
                    earn_rate = card.earning_rates.get(cat, card.earning_rates.get("other", 1.0))
                    cpp = POINT_VALUATIONS.get(card.point_system, 1.0)
                    value = amount * earn_rate * cpp / 100
                    alloc_rows.append({
                        "Category": cat_labels.get(cat, cat.title()),
                        "Card": card.name,
                        "Annual Spend": f"${amount:,.0f}",
                        "Earn Rate": f"{earn_rate}x",
                        "Points Earned": f"{int(amount * earn_rate):,}",
                        "Est. Value": f"${value:,.2f}",
                    })

        if alloc_rows:
            df = pd.DataFrame(alloc_rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn(width="medium"),
                    "Card": st.column_config.TextColumn(width="large"),
                    "Annual Spend": st.column_config.TextColumn(width="small"),
                    "Earn Rate": st.column_config.TextColumn(width="small"),
                    "Points Earned": st.column_config.TextColumn(width="small"),
                    "Est. Value": st.column_config.TextColumn(width="small"),
                },
            )

        # ── Value Breakdown Chart ────────────────────────────────────────────
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📈 Value Breakdown")

        chart_data = pd.DataFrame({
            "Component": ["Spend Rewards", "Welcome Bonuses", "Annual Fees"],
            "Value ($)": [
                result.total_rewards_value,
                result.total_welcome_bonus_value,
                -result.total_annual_fees,
            ]
        })
        st.bar_chart(chart_data, x="Component", y="Value ($)", use_container_width=True)

        # ── Point Valuations Reference ───────────────────────────────────────
        with st.expander("ℹ️ Point Valuations Used"):
            val_rows = [{"Program": k.replace("_", " ").title(), "Valuation": f"{v}¢ per point"} for k, v in POINT_VALUATIONS.items()]
            st.table(pd.DataFrame(val_rows))

else:
    # Landing state
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
        <h3 style="color: #ccd6f6; font-weight: 600;">Set Your Spending Profile</h3>
        <p style="color: #8892b0; max-width: 500px; margin: 0 auto;">
            Use the sidebar to enter your monthly spending, set your fee budget and constraints,
            then hit <strong style="color: #667eea;">Optimize My Wallet</strong> to find the mathematically
            optimal combination of credit cards.
        </p>
    </div>
    """, unsafe_allow_html=True)
