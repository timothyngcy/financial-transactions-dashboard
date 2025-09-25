import streamlit as st
import functions as fx
import plotly.express as px

file_path = 'financial_transactions.csv'
df_ft = fx.read_and_clean_data(file_path)
df_copy = df_ft.copy()

st.set_page_config(page_title="Financial Transaction Monitoring Dashboard", layout="wide")
st.title("Financial Transaction Monitoring Dashboard")

# sidebar
with st.sidebar:
    st.header("Filters")

    # date filter
    min_d, max_d = df_copy["Date"].min().date(), df_copy["Date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_d, max_d), # default selection
        min_value=min_d, # earliest allowed date
        max_value=max_d # latest allowed date
    )

    # category filter
    cats = sorted(df_copy["category"].unique())
    sel_cat = st.multiselect("Category", cats, default=cats) 

    # payment filter
    pay_methods = sorted(df_copy["payment_method"].unique())
    sel_pay_method = st.multiselect("Payment Method", pay_methods, default=pay_methods)

    # account type filter
    accs = sorted(df_copy["account_type"].unique())
    sel_acc = st.multiselect("Account Type", accs, default=accs)

filtered_df = fx.filter_dates(df_copy, date_range)
filtered_df = fx.filter_category(filtered_df, sel_cat)
filtered_df = fx.filter_payment(filtered_df, sel_pay_method)
filtered_df = fx.filter_account(filtered_df, sel_acc)

# key metrics
st.subheader("Metrics of All Transactions")
with st.container(height=120, vertical_alignment="center"):
    met1, met2, met3 = st.columns(3)
    met1.metric("Total Transaction Amount", f"${filtered_df['amount'].sum():,.2f}")
    met2.metric("Average Transaction Amount", f"${filtered_df['amount'].mean():,.2f}")
    met3.metric("Number of Transactions", f"{len(filtered_df):,}")

# creation of tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Anomaly Detection", "TEST"])

# tab 1: overview
with tab1:
    # line chart for spending over time
    st.subheader("Outflow Over Time")
    freq = st.radio("Frequency", ["Daily", "Weekly", "Monthly"], horizontal=True)
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
    
    fig = fx.line_with_mean(filtered_df,
                            "Date",
                            "Outflow",
                            freq_map[freq])

    st.plotly_chart(fig)

    # bar/line chart for transactions by day of the week
    st.subheader("Transactions by Day of the Week")
    daily_transactions= fx.transactions_by_days(filtered_df)
    st.plotly_chart(daily_transactions, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = fx.stacked_bar_chart(
            filtered_df,
            x="category",
            y="Outflow",
            color="payment_method",
            title="Top 8 Spending Categories",
            x_label="Total Outflow ($)",
            y_label="Category"
        )

        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = fx.stacked_bar_chart(
            filtered_df,
            x="category",
            y="Outflow",
            color="account_type",
            title="Top 8 Spending Categories",
            x_label="Total Outflow ($)",
            y_label="Category"
        )

        st.plotly_chart(fig, use_container_width=True)


# tab 2: anomaly detection
with tab2:
    st.subheader("Potential Anomalies")
    st.caption("Note: Anomalies are detected across the full dataset (filters not applied).") 