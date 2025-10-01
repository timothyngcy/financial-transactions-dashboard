import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Convert dates in DataFrame into datetime format
    # expects a panda DataFrame
    # returns a panda DataFrame with date column converted to datetime format
@st.cache_data(show_spinner=False)
def read_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    df = df.copy()

    df["Date"] = pd.to_datetime(df["date"])

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

## GRAPH FUNCTIONS ##

# Returns a plotly figure as a line chart with a horizontal line for mean
    # df = DataFrame to aggregate the data (panda DataFrame)
    # x = column name for x-axis (string)
    # y = column name for y-axis (string)
    # freq = frequency for resampling (string: "D", "W", "ME")
def line_with_mean(df, x, y, freq):
    df_copy = df.copy()
    aggregated_df = df_copy.set_index(x)[y].resample(freq).sum().reset_index()

    freq_labels = {"D": "Daily", "W": "Weekly", "ME": "Monthly"}
    freq_label = freq_labels.get(freq, freq)
    
    fig = px.line(aggregated_df,
                  x=x,
                  y=y,
                  title=f"{freq_label} Transactions"
                  )

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

# Returns a plotly figure as a combined bar and line chart and highlighting the highest values
    # x1 = categorical variable on x-axis for bar chart (list)
    # y1 = numerical variable on y-axis for bar chart (list)
    # name1 = name for bar chart (string)
    # x2 = categorical variable on x-axis for line chart (list)
    # y2 = numerical variable on y-axis for line chart (list)
    # name2 = name for line chart (string)
def bar_line_chart(x1, y1, name1, x2, y2, name2):
    fig = go.Figure()

    max_bar = max(y1)
    # highlight the highest bar(s) on the bar chart
    bar_colors = ['#061e49' if val == max_bar else 'lightblue' for val in y1]

    # barchart
    fig.add_trace(go.Bar(
        x=x1,
        y=y1,
        name=name1,
        marker_color=bar_colors
    ))
    
    # only highest point labeled
    scatter_text = [""] * len(y2)
    max_val = max(y2)
    for i, val in enumerate(y2):
        if val == max_val:
            scatter_text[i] = f"{val}" 

    # line chart
    fig.add_trace(go.Scatter(
        x=x2,
        y=y2,
        mode='lines+markers+text',
        name=name2,
        line=dict(color='#E54E07', width=3),
        marker=dict(size=8, symbol="circle"),
        text=scatter_text,
        textposition='top center',
        textfont=dict(size=16, color="#E54E04")
    ))

    return fig

# Returns a stacked horizontal bar chart, keeping only the top 5 categories by total amount
    # x = categorical variable on y-axis (string)
    # y = numerical variable on x-axis (string)
    # color = categorical variable for color segments (string)
def stacked_bar_chart(df, x, y, color):
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
    
    return fig

# Returns a scatterplot with a linear regression best fit line
    # x = numerical variable on x-axis (list)
    # y = numerical variable on y-axis (list)
    # color = categorical variable for color segments (list)
def scatterplot_with_line(x, y, color=None):
    fig = px.scatter(
        x=x,
        y=y,
        color=color
    )

    # compute regression line
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    best_fit_line = slope * np.array(x) + intercept

    fig.add_trace(go.Scatter(
        x=x,
        y=best_fit_line,
        mode='lines',
        line=dict(color='#E54E04', width=2),
        name='Best Fit Line'
    ))

    return fig

# Returns a histogram plotly figure from a given dataframe
    # df = DataFrame to be visualized as histogram (panda DataFrame)
    # x = column name for x-axis (string)
def histogram(df, x):
    fig = px.histogram(
        df,
        x=x,
        nbins=20,
        text_auto=True
    )

    return fig

# Returns a heatmap figure from a given dataframe
    # df = DataFrame to be visualized as heatmap (panda DataFrame)
def heatmap(df):
    fig = px.imshow(
        df,
        x=df.columns,
        y=df.index,
        text_auto=True,
        color_continuous_scale="Blues"
    )

    return fig

# Returns a bar chart comparing two variables
    # x1 = categorical variable on x-axis for first bar chart (list)
    # y1 = numerical variable on y-axis for first bar chart (list)
    # name1 = name for first bar chart (string)
    # x2 = categorical variable on x-axis for second bar chart (list)
    # y2 = numerical variable on y-axis for second bar chart (list)
    # name2 = name for second bar chart (string)
def dual_bar_chart(x1, y1, name1, x2, y2, name2):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x1,
        y=y1,
        name=name1,
        marker_color='skyblue',
        opacity=0.6
    ))

    fig.add_trace(go.Bar(
        x=x2,
        y=y2,
        name=name2,
        marker_color='#edc001',
        opacity=0.6
    ))

    return fig