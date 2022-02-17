"""Do some basic analysis with the orders data."""

import pandas as pd


def main():
    """Compute and print the mean number of SKUs purchased per user, info of the most expensive order, and the most orders placed by a user."""
    df = pd.read_csv('../../data/JD_order_data.csv')

    mean_purchases = df.groupby('user_ID').size().mean()
    print(f"Mean SKUs purchased per user: {mean_purchases}")

    df['cost'] = df['final_unit_price'] * df['quantity']
    orders = df.groupby('order_ID')['cost'].sum()
    most_expensive = df[df['order_ID'] == orders.index[orders.argmax()]]
    print(f"Most expensive order:\n{most_expensive.to_string()}")
    
    max_purchases = df.groupby('user_ID').agg({'order_ID': 'nunique'})['order_ID'].max()
    print(f"Most orders placed by a user: {max_purchases}")


if __name__ == '__main__':
    main()
