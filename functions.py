import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Convert dates in DataFrame into datetime format and renames 'amount' to 'outflow'
    # expects a panda DataFrame
    # returns a panda DataFrame with date column converted to datetime format
@st.cache_data(show_spinner=False)
def read_and_clean_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df = df.copy()

    df["Date"] = pd.to_datetime(df["date"])
    df["Outflow"] = df["amount"]

    return df

## SIDEBAR FUNCTIONS ##

def filter_dates(df, date_range):
    # if no date range selected or if it does not contain 2 dates, return original df
    if not date_range or len(date_range) != 2:
        return df
    
    # extracts the start and end dates from the date_range tuple
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

    # make end inclusive (covers entire end day)
    end = end + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    date_range_filter = (df["Date"] >= start) & (df["Date"] <= end)

    return df.loc[date_range_filter].copy()

def filter_category(df, categories):
    # if no categories selected, return original df
    if not categories:
        return df

    category_filter = df["category"].isin(categories)
    
    return df.loc[category_filter].copy()

def filter_payment(df, payment_methods):
    # if no payment_methods selected, return original df
    if not payment_methods:
        return df

    payment_methods_filter = df["payment_method"].isin(payment_methods)
    
    return df.loc[payment_methods_filter].copy()

def filter_account(df, account_types):
    # if no account_types selected, return original df
    if not account_types:
        return df

    account_types_filter = df["account_type"].isin(account_types)
    
    return df.loc[account_types_filter].copy()

## OVERVIEW TAB FUNCTIONS ##

# Resample the time series data based on the specified frequency and aggregate the amounts
    # expects a panda DataFrame and a frequency string (D, W, M)
    # returns a panda Series with the resampled time series data
def outflow_over_time(df: pd.DataFrame, 
                      freq: str) -> pd.Series:
    df = df.copy()
    series = df.set_index("Date")["Outflow"].resample(freq).sum()
    out = series.reset_index()

    return out

# CAN REMOVE ABOVE and take the comments

# Appends a horizontal line for mean on the line chart
    # expects a panda DataFrame, x and y column names as strings, and a title string
    # returns a plotly Figure object with the line chart and mean horizontal line
def line_with_mean(df: pd.DataFrame, 
                   x: str,
                   y: str, 
                   freq: str) -> go.Figure:
    df_copy = df.copy()
    aggregated_df = df_copy.set_index(x)[y].resample(freq).sum().reset_index()

    freq_labels = {"D": "Daily", "W": "Weekly", "ME": "Monthly"}
    freq_label = freq_labels.get(freq, freq)
    
    fig = px.line(aggregated_df,
                  x=x,
                  y=y,
                  title=f"{freq_label} Transactions")

    mean_val = aggregated_df[y].mean()

    fig.add_hline(
        y=mean_val,
        line_dash="dot",
        line_color="#E54E04",
        annotation_text=f"{freq_label} Mean Amount = {mean_val:.2f}",
        annotation_position="top right", 
        annotation_font_size=20,
        annotation_font_color="#E54E04"
    )

    return fig

def transactions_by_days(df):
    df_copy = df.copy()
    df_copy['Day'] = df_copy['Date'].dt.day_name()

    WEEKDAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    df_copy['Day'] = pd.Categorical(df_copy['Day'], 
                                    categories=WEEKDAY_ORDER, 
                                    ordered=True)
    
    avg_transaction_df = df_copy.groupby('Day', as_index=False, observed=False)["Outflow"].mean().sort_values('Day')
    num_transaction_df = df_copy.groupby('Day', as_index=False, observed=False)["Outflow"].count().sort_values('Day')

    # highlight the highest transactions
    highest_avg = avg_transaction_df["Outflow"].max()
    highest_num = num_transaction_df["Outflow"].max()
    
    # there may be multiple days with the same average number of transactions
    highest_avg_days = avg_transaction_df.loc[avg_transaction_df["Outflow"] == highest_avg, "Day"].tolist()
    highest_num_days = num_transaction_df.loc[num_transaction_df["Outflow"] == highest_num, "Day"].tolist()

    fig = go.Figure()

    # bar chart for average transaction amount
    fig.add_trace(go.Bar(
        x=avg_transaction_df["Day"],
        y=avg_transaction_df["Outflow"],
        name="Average Transaction Amount",
        marker_color=['darkblue' if day in highest_avg_days else 'lightblue' for day in avg_transaction_df["Day"]],
        text=avg_transaction_df["Outflow"].round(2),
        textposition='auto'
    ))

    # line chart for number of transactions
    fig.add_trace(go.Scatter(
        x=num_transaction_df["Day"],
        y=num_transaction_df["Outflow"],
        mode='lines+markers',
        name="Number of Transactions",
        line=dict(color='#E54E07', width=3),
        marker=dict(size=8, symbol="circle")
    ))

    # highlight the days with the highest number of transactions
    for day in highest_num_days:
        fig.add_trace(go.Scatter(
            x=[day],
            y=[highest_num],
            mode='markers+text',
            name="Highest number of transactions",
            marker=dict(color='#E54E04', size=8, symbol="circle"),
            text=[f'{highest_num}'],
            textfont=dict(size=16, color="#E54E04"),
            textposition='top center',
            showlegend=False
        ))
    
    fig.update_layout(
        yaxis_title="Amount ($) / Number of Transactions",
        margin=dict(t=60, b=60),
        template="plotly_white",
        showlegend=True
    )

    return fig

def stacked_bar_chart(df, x, y, color, title, x_label=None, y_label=None):
    df_copy = df.copy()

    first_agg = (
        df_copy
        .groupby([x], as_index=False, observed=False)
        .agg({y:'sum'})
        .sort_values(by=y, ascending=False)
        .head(5)
    )

    top_5_x = first_agg[x]

    df_only_top_5_x = df_copy[df_copy[x].isin(top_5_x)].copy()

    category_order = first_agg[x].tolist()[::-1]
    
    df_only_top_5_x[x] = pd.Categorical(
        df_only_top_5_x[x],
        categories=category_order,
        ordered=True
    )

    aggregated_df = (
        df_only_top_5_x
        .groupby([x, color], as_index=False, observed=False)
        .agg({y:'sum'})
    )
    
    fig = px.bar(
        aggregated_df,
        x=y,
        y=x,
        color=color,
        orientation="h",
    )
    
    fig.update_layout(
        title=title,
        barmode="stack",
        xaxis_title=x_label if x_label else y,
        yaxis_title=y_label if y_label else x,
        template="plotly_white"
    )
    
    return fig

# histogram?

## ANOMALIES TAB FUNCTIONS ##