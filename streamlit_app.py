
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from db import (
    init_db, get_accounts, add_account, get_categories, add_category,
    add_transaction, get_transactions, get_budgets, add_budget,
    get_goals, add_goal, update_goal_saved, get_investments, add_investment,
    get_loans, add_loan, calculate_net_worth, export_transactions_csv
)
from utils import guess_category_from_text, today_str, parse_date


init_db()

st.set_page_config(page_title="VERA — Personal Finance Manager", layout="wide",
                   initial_sidebar_state="expanded")

# sidebar
st.sidebar.title("VERA")
menu = st.sidebar.radio("Navigate", [
    "Dashboard", "Transactions", "Add Transaction", "Budgets", "Goals",
    "Accounts", "Investments & Loans", "Reports", "Import/Export", "Settings"
])


def load_transactions_df(filters=None, limit=1000):
    rows = get_transactions(limit=limit, filters=filters)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df

#dashboard
if menu == "Dashboard":
    st.header("Welcome to VERA - Your Financial Dashboard")
    st.markdown("Quick snapshot of your finances")

    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        st.subheader("Net Worth")
        nw = calculate_net_worth()
        st.metric("Net worth", f"₹{nw:,.2f}")
    with col2:
        st.subheader("Accounts")
        accounts = get_accounts()
        total_bal = sum([a["balance"] for a in accounts])
        st.metric("Total balance (accounts)", f"₹{total_bal:,.2f}", delta=None)
    with col3:
        st.subheader("Goals")
        goals = get_goals()
        if goals:
            progress = sum([g["saved_amount"] for g in goals]) / (sum([g["target_amount"] for g in goals]) or 1) * 100
        else:
            progress = 0
        st.metric("Goals funded", f"{progress:.0f}%")

    st.markdown("---")

    st.subheader("Spending this month")
    from_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    dfm = load_transactions_df(filters={"start_date": from_date})
    if not dfm.empty:
        exp_df = dfm[dfm["type"]=="expense"].groupby("category")["amount"].sum().reset_index()
        chart = alt.Chart(exp_df).mark_bar().encode(
            x=alt.X("amount:Q", title="Amount"),
            y=alt.Y("category:N", sort='-x', title="Category"),
            tooltip=["category","amount"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No transactions found for this month.")

    st.subheader("Recent transactions")
    df_recent = load_transactions_df(limit=10)
    if not df_recent.empty:
        st.dataframe(df_recent[["date","type","amount","category","account","description"]])
    else:
        st.write("No transactions yet. Add your first transaction from 'Add Transaction'.")

#transactions 
elif menu == "Transactions":
    st.header("Transactions")
    st.write("View and filter your transactions.")
    start_date = st.date_input("Start date", value=pd.to_datetime(today_str()).replace(day=1))
    end_date = st.date_input("End date", value=pd.to_datetime(today_str()))
    ttype = st.selectbox("Type", options=["All","income","expense","transfer"])
    filters = {"start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d")}
    if ttype != "All":
        filters["type"] = ttype
    df = load_transactions_df(filters=filters, limit=1000)
    if not df.empty:
        st.dataframe(df[["date","type","amount","category","account","target_account","description"]])
        # category breakdown
        st.markdown("### Category breakdown")
        cat_df = df[df["type"]=="expense"].groupby("category")["amount"].sum().reset_index()
        if not cat_df.empty:
            pie = alt.Chart(cat_df).mark_arc().encode(
                theta=alt.Theta(field="amount", type="quantitative"),
                color=alt.Color(field="category", type="nominal"),
                tooltip=["category","amount"]
            )
            st.altair_chart(pie, use_container_width=True)
        # Time series
        st.markdown("### Time series")
        ts = df.groupby(pd.Grouper(key="date", freq="D")).sum().reset_index()
        if not ts.empty:
            line = alt.Chart(ts).mark_line(point=True).encode(
                x="date:T",
                y="amount:Q",
                tooltip=["date","amount"]
            ).properties(height=250)
            st.altair_chart(line, use_container_width=True)
    else:
        st.info("No transactions found for the selected range.")

# add transactions
elif menu == "Add Transaction":
    st.header("Add Transaction")
    st.write("Log income, expense or transfer.")
    accounts = get_accounts()
    categories = get_categories()
    col1, col2 = st.columns(2)
    with col1:
        t_type = st.selectbox("Type", ["expense","income","transfer"])
        date = st.date_input("Date", value=pd.to_datetime(today_str()))
        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, format="%.2f")
        account = st.selectbox("Account", [f'{a["id"]}: {a["name"]} (₹{a["balance"]:,.2f})' for a in accounts])
    with col2:
        desc = st.text_input("Description")
        if t_type != "transfer":
            cat = st.selectbox("Category", [f'{c["id"]}: {c["name"]}' for c in categories])
        else:
            cat = None
        target_acc = None
        if t_type == "transfer":
            target_acc = st.selectbox("Target account", [f'{a["id"]}: {a["name"]} (₹{a["balance"]:,.2f})' for a in accounts])
        recurring = st.selectbox("Recurring", ["None", "monthly", "weekly"])

    if st.button("Add"):
        # parse ids
        account_id = int(account.split(":")[0])
        target_account_id = None
        if target_acc:
            target_account_id = int(target_acc.split(":")[0])
        category_id = None
        if cat:
            category_id = int(cat.split(":")[0])
        
        
        add_transaction(date.strftime("%Y-%m-%d"), float(amount), t_type, category_id, account_id,
                        description=desc, target_account_id=target_account_id,
                        recurring_rule=(recurring if recurring!="None" else None))
        st.success("Transaction added.")

# budgets
elif menu == "Budgets":
    st.header("Budgets")
    categories = get_categories()
    with st.expander("Create new budget"):
        cat = st.selectbox("Category for budget", [f'{c["id"]}: {c["name"]}' for c in categories])
        amount = st.number_input("Budget amount (period)", min_value=0.0, value=1000.0)
        period = st.selectbox("Period", ["monthly","weekly"])
        if st.button("Save budget"):
            add_budget(int(cat.split(":")[0]), float(amount), period)
            st.success("Budget saved.")

    st.write("Your budgets")
    budgets = get_budgets()
    if budgets:
        df = pd.DataFrame(budgets)
        # compute spent per category this period
        now = pd.to_datetime(today_str())
        month_start = now.replace(day=1).strftime("%Y-%m-%d")
        trans = pd.DataFrame(get_transactions(limit=10000, filters={"start_date": month_start}))
        rows = []
        for b in budgets:
            spent = 0.0
            if not trans.empty:
                spent = trans[(trans["category_id"]==b["category_id"]) & (trans["type"]=="expense")]["amount"].sum()
            rows.append({
                "category": b["category"],
                "budget": b["amount"],
                "spent": spent,
                "remaining": b["amount"] - spent,
                "period": b["period"]
            })
        st.dataframe(pd.DataFrame(rows))
        # budget progress bars
        for r in rows:
            st.write(f"**{r['category']}** — Spent ₹{r['spent']:,.2f} / ₹{r['budget']:,.2f}")
            st.progress(min(max(r['spent']/ (r['budget'] or 1), 0.0), 1.0))
    else:
        st.info("No budgets yet.")

# goals
elif menu == "Goals":
    st.header("Goals")
    with st.expander("Create a goal"):
        name = st.text_input("Goal name")
        target_amount = st.number_input("Target amount (₹)", min_value=0.0, value=10000.0)
        target_date = st.date_input("Target date", value=pd.to_datetime(today_str()))
        if st.button("Create goal"):
            add_goal(name, float(target_amount), target_date.strftime("%Y-%m-%d"))
            st.success("Goal created.")

    goals = get_goals()
    if goals:
        for g in goals:
            st.write(f"### {g['name']}")
            st.write(f"Target: ₹{g['target_amount']:,.2f} | Saved: ₹{g['saved_amount']:,.2f}")
            pct = (g['saved_amount'] / (g['target_amount'] or 1)) * 100
            st.progress(min(max(pct/100,0),1))
            col1, col2 = st.columns(2)
            with col1:
                add_amt = st.number_input(f"Add to {g['name']}", min_value=0.0, value=0.0, key=f"add_{g['id']}")
            with col2:
                if st.button(f"Add funds to {g['name']}", key=f"btn_{g['id']}"):
                    if add_amt > 0:
                        update_goal_saved(g['id'], float(add_amt))
                        st.success("Added to goal.")
    else:
        st.info("No goals.")

# accounts
elif menu == "Accounts":
    st.header("Accounts")
    with st.expander("Add account"):
        name = st.text_input("Account name")
        type_ = st.selectbox("Type", ["bank","cash","credit"])
        balance = st.number_input("Opening balance (₹)", value=0.0)
        if st.button("Create account"):
            add_account(name, type_, float(balance))
            st.success("Account created.")
    accounts = get_accounts()
    df = pd.DataFrame(accounts)
    if not df.empty:
        st.dataframe(df[["id","name","type","balance","currency","created_at"]])
    else:
        st.write("No accounts.")

# investments and loans
elif menu == "Investments & Loans":
    st.header("Investments & Loans")
    st.subheader("Investments")
    with st.expander("Add investment"):
        name = st.text_input("Investment name", key="inv_name")
        amt = st.number_input("Amount", min_value=0.0, key="inv_amt")
        itype = st.selectbox("Type", ["mutual fund","stock","savings"], key="inv_type")
        if st.button("Add investment"):
            add_investment(name, float(amt), itype)
            st.success("Investment added.")
    investments = get_investments()
    if investments:
        st.dataframe(pd.DataFrame(investments))
    else:
        st.write("No investments yet.")

    st.subheader("Loans")
    with st.expander("Add loan"):
        lname = st.text_input("Loan name", key="loan_name")
        principal = st.number_input("Principal", min_value=0.0, key="loan_pr")
        balance = st.number_input("Balance", min_value=0.0, key="loan_bal")
        rate = st.number_input("Interest rate (annual %)", min_value=0.0, key="loan_rate")
        monthly = st.number_input("Monthly payment", min_value=0.0, key="loan_monthly")
        if st.button("Add loan"):
            add_loan(lname, float(principal), float(balance), float(rate), float(monthly))
            st.success("Loan added.")
    loans = get_loans()
    if loans:
        st.dataframe(pd.DataFrame(loans))
    else:
        st.write("No loans yet.")

# reports
elif menu == "Reports":
    st.header("Reports & Insights")
    st.markdown("Visual reports to help you understand patterns.")
    # last 6 months spend per month
    df = load_transactions_df(limit=10000)
    if df.empty:
        st.info("No transactions to show reports.")
    else:
        # monthly totals
        df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
        monthly = df.groupby(['month','type'])['amount'].sum().reset_index()
        chart = alt.Chart(monthly).mark_bar().encode(
            x="month:T",
            y="amount:Q",
            color="type:N",
            tooltip=["month","type","amount"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

        st.markdown("### Top merchants / categories (expenses)")
        cat = df[df['type']=="expense"].groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False).head(10)
        st.table(cat)

        st.markdown("### Simple insights")
        # insights
        insights = []
        total_income = df[df['type']=="income"]['amount'].sum()
        total_expense = df[df['type']=="expense"]['amount'].sum()
        if total_expense > total_income:
            insights.append("Your expenses exceed your income. Consider reviewing budgets or cutting discretionary spend.")
        else:
            insights.append("Your income covers your expenses — good job. Consider increasing investments or accelerating goals.")
        # biggest category
        if not cat.empty:
            top_cat = cat.iloc[0]
            insights.append(f"You're spending most on **{top_cat['category']}** — ₹{top_cat['amount']:,.2f}.")
        for insight in insights:
            st.info(insight)

# import/export
elif menu == "Import/Export":
    st.header("Import & Export")
    st.write("Export transactions to CSV")
    if st.button("Export transactions to CSV"):
        path = "vera_transactions_export.csv"
        export_transactions_csv(path)
        st.success(f"Exported to `{path}`. (file saved in app folder)")

    st.markdown("---")
    st.write("Import CSV (expecting columns: date,amount,type,category,account,description)")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("Preview:")
        st.dataframe(df.head())
        if st.button("Import transactions from CSV"):
            # importer
            accounts = get_accounts()
            categories = get_categories()
            name_to_acc = {a["name"]: a["id"] for a in accounts}
            name_to_cat = {c["name"]: c["id"] for c in categories}
            count = 0
            for _, row in df.iterrows():
                date = parse_date(row.get("date") or row.get("Date"))
                amt = float(row.get("amount") or row.get("Amount") or 0)
                ttype = row.get("type") or row.get("Type") or "expense"
                cat_name = row.get("category") or row.get("Category") or None
                acc_name = row.get("account") or row.get("Account") or None
                desc = row.get("description") or row.get("Description") or ""
                if acc_name and acc_name in name_to_acc:
                    acc_id = name_to_acc[acc_name]
                else:
                    acc_id = accounts[0]["id"]
                if cat_name and cat_name in name_to_cat:
                    cat_id = name_to_cat[cat_name]
                else:
                    cat_id = guess_category_from_text(desc, categories)
                add_transaction(date, amt, ttype, cat_id, acc_id, description=desc)
                count += 1
            st.success(f"Imported {count} transactions.")

# settings
elif menu == "Settings":
    st.header("Settings & Category management")
    st.write("Categories")
    categories = get_categories()
    st.dataframe(pd.DataFrame(categories))
    with st.expander("Add category"):
        cname = st.text_input("Category name")
        if st.button("Add category"):
            add_category(cname)
            st.success("Category added.")
    st.markdown("Database file: `vera.db` stored in app folder.")

# Helper functions used in import
def parse_date(s):
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except:
        return today_str()