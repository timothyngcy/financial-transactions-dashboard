# Financial Transaction Dashboard

## Dashboard Information

### Sidebar
Users are able to filter the dataset using the following fields:
- Date
- Category
- Merchant
- Payment Method
- Account Type
- Transaction Type

### Overview Tab
This tab provides a general overview of the dataset and allows users to interact with various charts:
- **Transactions over time:** displayed in a line chart.
- **Transactions by day of the week:** visualised in a combo bar-line chart.
- **Spending in the top 5 categories:** shown in a stacked bar chart, grouped by payment method, account type, or transaction type.
- **Distribution of transaction amounts:** presented in a histogram.

### Potential Anomalies Tab
This tab highlights potential anomalies and outliers in the transactions, including:
- **High transaction amounts:** flagged when a transaction exceeds the expected trend (best-fit line).
- **Number of transactions VS total transaction amount:** visualised in a heatmap to identify unusual patterns.
- **Observed transactions VS Benford’s Law:** compared in an overlay bar chart to detect irregularities in first-digit distributions.

## Dependencies
All the required packages are listed in the `requirements.txt` file.

To install them, run:
```
pip install -r requirements.txt
```

## Viewing the Dashboard
To view the dashboard, you have 2 options:

1. **Locally**
   
   Open a terminal in the project directory and run:
   ```
   streamlit run app.py
   ```

2. **Hosted**
   
   Go to the following link: https://financial-transactions-dashboard-kqd8hkwfdjesnmqb8zhhrs.streamlit.app/
