"""Analyze merges of the smaller retail datasets."""

import pandas as pd


def main():
    """Merge users, orders, and delivery data to compute statistics."""
    orders = pd.read_csv('../../data/JD_order_data.csv')
    users = pd.read_csv('../../data/JD_user_data.csv')

    # merge and check coverage
    df = orders.merge(users, how='left', on='user_ID')
    coverage = df['user_level'].notnull().mean()
    print(f"User coverage: {100 * coverage}%.")

    # compute average prices by demographic bin
    for demographic in ['gender', 'age', 'marital_status', 'education']:
        print(df.groupby(demographic)['final_unit_price'].mean().to_string())

    # merge in delivery data and check coverage
    delivery = pd.read_csv('../../data/JD_delivery_data.csv', parse_dates=['ship_out_time', 'arr_time'])
    df = df.merge(delivery, on='order_ID')
    coverage = df['package_ID'].notnull().mean()
    print(f"Delivery coverage: {100 * coverage}%.")

    # count the average number of packages per order
    mean_packages = df.groupby('order_ID').size().mean()
    print(f"Mean packages per order: {mean_packages}.")

    # compute the average shipping time by user city level
    df['hours'] = (df['arr_time'] - df['ship_out_time']).dt.total_seconds() / 3600
    print(df.groupby('city_level')['hours'].mean().to_string())


if __name__ == '__main__':
    main()

