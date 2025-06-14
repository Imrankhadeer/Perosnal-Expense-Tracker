import streamlit as st
from main import FamilyExpenseTracker
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from pathlib import Path
from auth import register_user, login_user, update_username, update_password
import pandas as pd

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰")

# Load external CSS
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None

# --- Authentication
if not st.session_state.logged_in:
    st.title("Login / Register")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user_id = login_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with register_tab:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("User registered! Please log in.")
            else:
                st.error("Username already taken")
    st.stop()

# --- Tracker instance
if "expense_tracker" not in st.session_state:
    st.session_state.expense_tracker = FamilyExpenseTracker(user_id=st.session_state.user_id)

expense_tracker = st.session_state.expense_tracker

# Sidebar
st.sidebar.success(f"Logged in as User ID: {st.session_state.user_id}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.expander("⚙️ Profile Settings"):
    new_u = st.text_input("New Username")
    if st.button("Update Username"):
        if update_username(st.session_state.user_id, new_u):
            st.success("Username updated!")
        else:
            st.error("Username already taken")

    new_p = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        update_password(st.session_state.user_id, new_p)
        st.success("Password updated!")

# Main Navigation
st.markdown('<h1 class="main-title">Personal Expense Tracker</h1>', unsafe_allow_html=True)

selected = option_menu(
    menu_title=None,
    options=["Data Entry", "Data Overview", "Data Visualization", "Summary"],
    icons=["pencil-fill", "clipboard2-data", "bar-chart-fill", "calendar"],
    orientation="horizontal"
)


# --- Data Entry
if selected == "Data Entry":
    st.header("Add Account")
    with st.expander("Add Account"):
        member_name = st.text_input("Name").title()
        earning_status = st.checkbox("Earning Status")
        earnings = st.number_input("Earnings", value=1, min_value=1) if earning_status else 0

        if st.button("Add Account") and member_name:
            existing_member = [m for m in expense_tracker.members if m["name"] == member_name]
            if not existing_member:
                expense_tracker.add_member(member_name, earning_status, earnings)
                st.success("Account added successfully!")
            else:
                existing_member[0]["earning"] = earning_status
                existing_member[0]["earnings"] = earnings
                expense_tracker.update_member(member_name, earning_status, earnings)
                st.success("Account updated successfully!")

    st.header("Add Expenses")
    with st.expander("Add Expenses"):
        if not expense_tracker.members:
            st.warning("Please add an Account first.")
        else:
            member_names = [m["name"] for m in expense_tracker.members]
            selected_member = st.selectbox("Account", member_names)
            expense_category = st.selectbox("Category", (
                "Housing", "Food", "Transportation", "Entertainment",
                "Child-Related", "Medical", "Investment", "Miscellaneous"
            ))
            expense_description = st.text_input("Description (optional)").title()
            expense_value = st.number_input("Value", min_value=0)
            expense_date = st.date_input("Date")

            if st.button("Add Expense"):
                expense_tracker.add_expense(
                    selected_member, expense_value, expense_category, expense_description, expense_date
                )
                st.success("Expense added successfully!")

# --- Data Overview
elif selected == "Data Overview":
    if not expense_tracker.members:
        st.info("Start by adding Accounts.")
    else:
        st.header("Accounts")
        name_column, earning_column, earnings_column, action_column = st.columns(4)
        name_column.write("**NAME**")
        earning_column.write("**EARNING STATUS**")
        earnings_column.write("**BALANCE**")
        action_column.write("**ACTION**")

        for i, member in enumerate(expense_tracker.members):
            name_column.write(member["name"])
            earning_column.write("Earning" if member["earning"] else "Not Earning")
            earnings_column.write(member["earnings"])
            if action_column.button("Remove", key=f"remove_{i}"):
                expense_tracker.delete_member(member["name"])
                st.rerun()

    st.header("Expenses")
    if not expense_tracker.expense_list:
        st.info("No expenses added yet.")
    else:
        df = pd.DataFrame([{
            "Index": i,
            "Value": e.value,
            "Category": e.category,
            "Description": e.description,
            "Date": e.date
        } for i, e in enumerate(expense_tracker.expense_list)])

        selected_indices = []
        for i, row in df.iterrows():
            col1, col2 = st.columns([10, 1])

            with col1:
                st.markdown(f"""
                    <div class="expense-card">
                        <div class="expense-row">
                            <div class="expense-value">₹ {row['Value']}</div>
                            <div class="expense-category">{row['Category']}</div>
                            <div class="expense-description">{row['Description'] or '-'}</div>
                            <div class="expense-date">{row['Date']}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.checkbox("", key=f"select_{row['Index']}", label_visibility="collapsed"):
                    selected_indices.append(row["Index"])

        if selected_indices:
            if st.button("🗑️ Delete Selected", help="Delete all selected expenses"):
                for index in sorted(selected_indices, reverse=True):
                    expense_tracker.delete_expense(index)
                st.success(f"Deleted {len(selected_indices)} expense(s).")
                st.rerun()
        else:
            st.markdown("*No expenses selected.*")

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Earnings", f"₹ {expense_tracker.calculate_total_earnings():,.2f}")
        col2.metric("Total Expenses", f"₹ {expense_tracker.calculate_total_expenditure():,.2f}")
        remaining = expense_tracker.calculate_total_earnings() - expense_tracker.calculate_total_expenditure()
        col3.metric("Remaining", f"₹ {remaining:,.2f}", delta_color="inverse")

# --- Data Visualization
elif selected == "Data Visualization":
    expense_data = [(e.category, e.value) for e in expense_tracker.expense_list]
    if expense_data:
        categories = [x[0] for x in expense_data]
        values = [x[1] for x in expense_data]
        total = sum(values)
        percentages = [(v / total) * 100 for v in values]

        colors = plt.get_cmap('Pastel1').colors

        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
        wedges, _, autotexts = ax.pie(
            percentages,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.4, edgecolor='w'),
            textprops=dict(color="black", fontsize=10),
            pctdistance=0.85
        )

        ax.legend(wedges, categories, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        centre_circle = plt.Circle((0, 0), 0.60, fc='white')
        fig.gca().add_artist(centre_circle)
        ax.set_title("Expense Distribution", fontsize=16, fontweight='bold')
        ax.axis('equal')

        st.pyplot(fig, clear_figure=True)
    else:
        st.info("No expenses to visualize. Please add some.")

# --- Summary
# --- Summary
elif selected == "Summary":
    st.header("📊 Monthly Expense Summary")
    summary = expense_tracker.get_monthly_summary()

    if summary:
        df = pd.DataFrame(summary, columns=["Month", "Total Spent"])
        df["Total Spent"] = df["Total Spent"].astype(float)
        df.set_index("Month", inplace=True)

        # Show raw data table
        st.subheader("Expense Table")
        st.dataframe(df)


        # Show suggestions
        st.subheader("💡 Budget Suggestions")

        avg_spent = df["Total Spent"].mean()
        latest_month = df.index[-1]
        latest_value = df["Total Spent"].iloc[-1]

        if latest_value > avg_spent:
            st.warning(f"Your spending in **{latest_month}** was ₹{latest_value:,.2f}, which is above your average of ₹{avg_spent:,.2f}.")
        else:
            st.success(f"Great job! Your spending in **{latest_month}** was below average (₹{latest_value:,.2f} vs ₹{avg_spent:,.2f}).")

        # Top spending categories
        st.subheader("📌 Spending Breakdown")
        cat_totals = {}
        for e in expense_tracker.expense_list:
            cat_totals[e.category] = cat_totals.get(e.category, 0) + e.value
        cat_df = pd.DataFrame.from_dict(cat_totals, orient='index', columns=["Total Spent"]).sort_values(by="Total Spent", ascending=False)
        st.bar_chart(cat_df)

        # Recommendation
        st.subheader("🧠 Smart Saving Tips")
        top_category = cat_df.index[0] if not cat_df.empty else None
        if top_category:
            st.markdown(f"""
                - Your **highest expense category** is **{top_category}**. Consider reviewing this area for possible savings.
                - Set a monthly budget cap for this category.
                - Track smaller daily expenses — they can add up quickly.
                - Use discounts, coupons, and loyalty programs when possible.
            """)
        else:
            st.info("Not enough data to generate suggestions. Add more expenses to get insights.")
    else:
        st.info("No expenses to summarize. Add entries first.")
