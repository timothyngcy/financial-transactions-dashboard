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

# Appends a horizontal line for mean on the line chart
    # expects a panda DataFrame, x and y column names as strings, and a title string
    # returns a plotly Figure object with the line chart and mean horizontal line
def line_with_mean(df: pd.DataFrame, 
                   x: str,
                   y: str, 
                   title: str) -> go.Figure:
    fig = px.line(df, x=x, y=y, title=title)

    mean_val = df[y].mean()

    fig.add_hline(
        y=mean_val,
        line_dash="dot",
        line_color="red",
        annotation_text=f"Mean = {mean_val:.2f}",
        annotation_position="top right", 
        annotation_font_size=20,
        annotation_font_color="red"
    )

    return fig

## ANOMALIES TAB FUNCTIONS ##