import pandas as pd
import streamlit as st
import functions as fx

file_path = 'financial_transactions.csv'
df_ft = fx.read_and_clean_data(file_path)
df_copy = df_ft.copy()

st.set_page_config(page_title="Financial Transaction Monitoring Dashboard", layout="wide")
st.title("Financial Transaction Monitoring Dashboard")

## sidebar
with st.sidebar:
    st.header("Filters")

    ### date filter
    min_d, max_d = df_copy["Date"].min().date(), df_copy["Date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_d, max_d), # default selection
        min_value=min_d, # earliest allowed date
        max_value=max_d # latest allowed date
    )

    ### category filter
    cats = sorted(df_copy["category"].unique())
    sel_cat = st.multiselect("Category", cats, default=cats) 

    ### merchant filter
    merch = sorted(df_copy["merchant"].unique())
    sel_merch = st.multiselect("Merchant", merch, default=merch)

    ### payment filter
    pay_methods = sorted(df_copy["payment_method"].unique())
    sel_pay_method = st.multiselect("Payment Method", pay_methods, default=pay_methods)

    ### account type filter
    accs = sorted(df_copy["account_type"].unique())
    sel_acc = st.multiselect("Account Type", accs, default=accs)

    ### transaction type filter
    tran = sorted(df_copy["transaction_type"].unique())
    sel_tran = st.multiselect("Transaction Type", tran, default=tran)

filtered_df = fx.filter_dates(df_copy, date_range)
filtered_df = fx.filter_category(filtered_df, sel_cat)
#filtered_df = fx.filter_merchant(filtered_df, sel_merch)
filtered_df = fx.filter_payment(filtered_df, sel_pay_method)
filtered_df = fx.filter_account(filtered_df, sel_acc)
filtered_df = fx.filter_transaction(filtered_df, sel_tran)

## key metrics
st.subheader("Metrics of All Transactions")
with st.container(height=120, vertical_alignment="center"):
    met1, met2, met3 = st.columns(3)
    met1.metric("Total Transaction Amount", f"${filtered_df['amount'].sum():,.2f}")
    met2.metric("Average Transaction Amount", f"${filtered_df['amount'].mean():,.2f}")
    met3.metric("Number of Transactions", f"{len(filtered_df):,}")

tab1, tab2 = st.tabs(["Overview", "Potential Anomalies"])

## tab 1: overview
with tab1:
    st.subheader("Transactions Over Time")
    freq = st.radio("Frequency of Transaction Overview", ["Daily", "Weekly", "Monthly"], horizontal=True)
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
    
    col1, col2 = st.columns(2)
    
    ### Line chart for spending over time with mean line
    with col1:
        overall_fig = fx.line_with_mean(df=filtered_df,
                                x="Date",
                                y="amount",
                                freq=freq_map[freq])
    
        overall_fig.update_traces(line=dict(color='lightblue'))

        overall_fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Amount ($)",
        )

        st.plotly_chart(overall_fig)
    
    ### Bar + line chart for amount by day of the week
    with col2:
        df_daily = filtered_df.copy()
        df_daily['Day'] = df_daily['Date'].dt.day_name()

        WEEKDAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        df_daily['Day'] = pd.Categorical(df_daily['Day'], 
                                        categories=WEEKDAY_ORDER, 
                                        ordered=True)
        
        avg_transaction_df = df_daily.groupby('Day', as_index=False, observed=False)["amount"].mean().sort_values('Day')
        num_transaction_df = df_daily.groupby('Day', as_index=False, observed=False)["amount"].count().sort_values('Day')

        daily_fig = fx.bar_line_chart(x1=avg_transaction_df["Day"],
                                    y1=avg_transaction_df["amount"].round(2),
                                    name1="Average Transaction Amount",
                                    x2=num_transaction_df["Day"],
                                    y2=num_transaction_df["amount"],
                                    name2="Number of Transactions")
        
        daily_fig.update_layout(
            title="By Day of the Week",
            xaxis_title="Day of the Week",
            yaxis_title="Average Amount ($) / Number of Transactions",
            showlegend=False,
            hovermode="x",
        )

        daily_fig.update_traces(
            selector=dict(type='bar'),
            text=avg_transaction_df["amount"].round(2),
            textposition='auto',
            hovertemplate='Average Amount: $%{y:.2f}<extra></extra>',
            hoverlabel=dict(
                bgcolor='lightblue',
                font_size=12,
                font_color='black'
            )
        )

        daily_fig.update_traces(
            selector=dict(type='scatter'),
            hovertemplate='Number of Transactions: %{y}<extra></extra>',
            hoverlabel=dict(
                bgcolor='#E54E04',
                font_size=12,
                font_color='white'
            )
        )

        st.plotly_chart(daily_fig)

    ### stacked bar chart for spending by category, payment method, account type, etc.
    st.subheader("Spending by Category and Payment Method / Account Type / Transaction Type")

    segment_bar = st.radio("Segment barplot by:",
                           ["Payment Method", "Account Type", "Transaction Type"],
                           horizontal=True)
    
    bar_mapping = {"Payment Method": "payment_method",
                   "Account Type": "account_type",
                   "Transaction Type": "transaction_type"}

    stacked_bar_fig = fx.stacked_bar_chart(
        df=filtered_df,
        x="category",
        y="amount",
        color=bar_mapping[segment_bar]
    )

    stacked_bar_fig.update_layout(
        title="Spending for the Top 5 Categories (by Total Transaction Amount), Grouped By " + segment_bar, 
        legend_title_text=segment_bar,
        barmode="stack",
        xaxis_title="Total Amount ($)",
        yaxis_title="Category"
    )

    st.plotly_chart(stacked_bar_fig)

    ### histogram for distribution of spending
    st.subheader("Distribution of Spending")

    df_hist = filtered_df.copy()

    histo_fig = fx.histogram(
        df=df_hist,
        x="amount"
    )

    histo_fig.update_traces(
        textposition="outside",
        marker=dict(
            color="lightblue",                
            line=dict(width=1, color="black")
        ),
        textfont=dict(size=12, color="black"),
        cliponaxis=False
    )

    histo_fig.update_layout(
        title="Distribution of Transaction Amounts",
        xaxis_title="Total Amount ($)",
        yaxis_title="Frequency"
    )

    st.plotly_chart(histo_fig)

## tab 2: anomaly detection
with tab2:
    ### Scatter plot of Amount against Dates with Line of Best Fit
    st.subheader("Scatter Plot of Amount Against Time with Line of Best Fit")

    df_scatter = filtered_df.copy()
    df_scatter["Date_ordinal"] = df_scatter["Date"].map(pd.Timestamp.toordinal)

    scatter_color = st.radio("Colour scatter plot by:",
                             ["Category", "Merchant", "Payment Method", "Account Type", "Transaction Type"],
                             horizontal=True)
    scatter_mapping = {"Category": "category",
                       "Merchant": "merchant",
                       "Payment Method": "payment_method",
                       "Account Type": "account_type",
                       "Transaction Type": "transaction_type"}
    
    color_col = scatter_mapping[scatter_color]
    
    scatter_fig = fx.scatterplot_with_line(
        x=df_scatter["Date_ordinal"], 
        y=df_scatter["amount"],
        color=df_scatter[color_col]
    )
    
    # update dates to be readable
    monthly_ticks = df_scatter[df_scatter["Date"].dt.is_month_start]
    tickvals = monthly_ticks["Date_ordinal"]
    ticktext = monthly_ticks["Date"].dt.strftime("%b %Y")

    scatter_fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        title_text="Date"
    )
    scatter_fig.update_yaxes(title_text="Total Amount ($)")
    scatter_fig.update_layout(
        title="Spending Against Time, Coloured by " + scatter_color, 
        legend_title_text=scatter_color
    )
    scatter_fig.update_traces(
        hovertemplate="<b>Total Amount:</b> $%{y}"
    )

    st.plotly_chart(scatter_fig)

    st.caption(
        "This scatter plot highlights high-value outliers above the line of best fit. "
        "Use the radio buttons to change the color grouping of the points."
    )

    ### Heatmap of Number of Transactions with Merchants by Week
    # 1. Find the top 10 merchants with the highest total transaction counts for each month
    # 2. Plot the heatmap of these merchants for both the number of transactions and total transaction amounts

    st.subheader("Monthly Heatmap of Transactions and Total Amount by Merchant")

    col1, col2 = st.columns(2)

    # heatmap 1: Heatmap of Number of Transactions by Merchant
    with col1:
        df_heatmap_merchants = filtered_df.copy()
        # create 'Month' column
        df_heatmap_merchants['Month'] = df_heatmap_merchants['Date'].dt.to_period('M').apply(lambda r: r.start_time)
        # count the number of transactions for each month for every merchant
        merchant_transactions_num = df_heatmap_merchants.groupby(['merchant', 'Month']).size().reset_index(name='transaction_count')
        # calculate total number of transactions across all months    
        merchant_transactions_totals = merchant_transactions_num.groupby('merchant')['transaction_count'].sum().sort_values(ascending=False)
        # keep only top 10 merchants
        top_10_merchants = merchant_transactions_totals.head(10).index
        # filter the df to only keep the top 10 merchants
        top_merchant_num_df = merchant_transactions_num[merchant_transactions_num['merchant'].isin(top_10_merchants)]
        # pivot by merchant and month using transaction_counts
        heatmap_data_num = top_merchant_num_df.pivot(index='merchant', columns='Month', values='transaction_count').fillna(0)
        # sort by the order of the top 10 merchants
        heatmap_data_num = heatmap_data_num.loc[top_10_merchants]

        heatmap_merchant_num = fx.heatmap(heatmap_data_num)

        heatmap_merchant_num.update_coloraxes(showscale=False)
        heatmap_merchant_num.update_traces(
            hovertemplate=
                '<b>Merchant:</b> %{y}<br>' +
                '<b>Month of</b> %{x}<br>' +
                '<b>Total Amount:</b> $%{z}<extra></extra>'
        )
        heatmap_merchant_num.update_layout(
            yaxis_title="Merchant",
            title="By Number of Transactions"
        )

        st.plotly_chart(heatmap_merchant_num)
    
    # heatmap 2: Heatmap of Total Transaction Amount by Merchant
    with col2:
        merchant_transactions_total = df_heatmap_merchants.groupby(['merchant', 'Month'])['amount'].sum().reset_index()
        top_merchant_total_df = merchant_transactions_total[merchant_transactions_total['merchant'].isin(top_10_merchants)]
        heatmap_data_total = top_merchant_total_df.pivot(index='merchant', columns='Month', values='amount').fillna(0)
        heatmap_data_total = heatmap_data_total.loc[top_10_merchants]

        heatmap_merchant_total = fx.heatmap(df=heatmap_data_total)

        heatmap_merchant_total.update_coloraxes(showscale=False)
        heatmap_merchant_total.update_traces(
            hovertemplate=
                '<b>Merchant:</b> %{y}<br>' +
                '<b>Month of</b> %{x}<br>' +
                '<b>Total Amount:</b> $%{z}<extra></extra>'
        )
        heatmap_merchant_total.update_layout(
            yaxis_title="",
            title="By Total Transaction Amount"
        )

        st.plotly_chart(heatmap_merchant_total)

    st.caption(
        "**Dark boxes** in the heatmaps indicate high values and **light boxes** indicate low values. \n\n"
        "Interpretation of heatmaps: \n"
        "- **Left heatmap dark / Right heatmap bright**: Indicates high number of transactions (left) but a low total amount (right), suggesting multiple small payments in that period potentially bypassing approval limits. \n"
        "- **Left heatmap bright / Right heatmap dark**: Indicates low number of transactions (left) but a high total amount (right), suggesting there were small large purchases in the month, which may warrant review to ensure proper approval was granted for these transactions."
    )

    ### Benford's Law Bar Chart
    # Benford's Law describes the relative frequency distribution for leading digits of numbers in real-world datasets.
    st.subheader("Bar Chart of Benford's Law")

    st.markdown("""
    Benford’s Law describes the expected frequency of first digits in the real-world: smaller digits appear more often as the leading digit. For example, 1 appears about 30% of the time, while 9 appears under 5%.  

    Source: [Wolfram MathWorld – Benford’s Law](https://mathworld.wolfram.com/BenfordsLaw.html)
                
    Checking this box will include negative values and zeros in the first-digit distribution.
    Although Benford’s Law typically applies to positive numbers, including these values can help explore the overall dataset more thoroughly
    (e.g. if there are negative transaction amouns).
    """)

    include_negatives_zeros = st.checkbox("Include negative and zero amounts?", value=False)

    df_benford = filtered_df.copy()

    digits_without = ["1","2","3","4","5","6","7","8","9"]
    # taken from: https://mathworld.wolfram.com/BenfordsLaw.html
    benford_without = [30.103, 17.6091, 12.4939, 9.691, 7.91812, 6.69468, 5.79919, 5.11525, 4.57575]

    if include_negatives_zeros:
        digits = ["-1", "0"] + digits_without
        benford_values = [0, 0] + benford_without
    else:
        digits = digits_without
        benford_values = benford_without

    neg_count = (df_benford['amount'] < 0).sum() if include_negatives_zeros else 0
    zero_count = ((df_benford['amount'] > 0) & (df_benford['amount'] < 1)).sum() if include_negatives_zeros else 0
    
    df_benford = df_benford[df_benford['amount'] >= 1]
    df_benford['first_digit'] = df_benford['amount'].apply(lambda x: int(str(x)[0]))

    first_digit_counts = df_benford['first_digit'].value_counts().sort_index()
    observed_values = [first_digit_counts.get(i, 0) for i in range(1,10)]
    total_count = sum(observed_values) + neg_count + zero_count

    observed_percentages = [(count / total_count) * 100 for count in observed_values]
    neg_percent = (neg_count / total_count) * 100
    zero_percent = (zero_count / total_count) * 100
    observed_percentages_full = ([neg_percent, zero_percent] + observed_percentages) if include_negatives_zeros else observed_percentages

    benford_values_rounded = [round(val, 2) for val in benford_values]
    observed_percentages_rounded = [round(val, 2) for val in observed_percentages_full]

    benford_fig = fx.dual_bar_chart(
        x1=digits,
        y1=benford_values_rounded,
        name1="Benford's Law",
        x2=digits,
        y2=observed_percentages_rounded,
        name2="Observed"
    )

    benford_fig.update_layout(
        title="Benford's Law vs Observed Data",
        xaxis_title="First Digit of Transaction Amount",
        yaxis_title="Percentage (%)",
        barmode='overlay',
        showlegend=True,
        hovermode="x",
        xaxis=dict(
            dtick=1
        )
    )

    benford_fig.update_traces(
        selector=dict(type='bar', name='Benford\'s Law'),
        hoverlabel=dict(
            bgcolor='skyblue',
            font_color='black',
            font_size=12
        )
    )

    benford_fig.update_traces(
        selector=dict(type='bar', name='Observed'),
        hoverlabel=dict(
            bgcolor='#edc001',
            font_color='black',
            font_size=12
        )
    )

    st.plotly_chart(benford_fig)
    
    st.caption(
        "Note: The digit \"-1\" indicate that the number is a negative number. \n\n"
        "Interpretation of bar chart: \n"
        "- If the chart predominantly shows **green**, this is in line with expected values of the first digit of the amounts.\n"
        "- However, if **yellow** or **blue** dominate, it might indicate a deviation from Benford's Law, suggesting a potential anomaly in the transactional data. \n"
        "- If there are **negative values** in the transaction amounts, it could indicate a refund or potential error."
    )