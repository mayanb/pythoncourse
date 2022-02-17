"""Analyze a larger merge of the retail dataset to demonstrate chunking analysis."""

import pandas as pd
import numpy as np


def main():
    """Merge the retail datasets and collect distributions of times chunk-by-chunk for plotting."""

    # collect click-to-order and shipping hours, working chunk-by-chunk
    click_to_order = []
    click_to_ship = []
    orders = pd.read_csv('../../data/JD_order_data.csv', parse_dates=['order_time'])
    delivery = pd.read_csv('../../data/JD_delivery_data.csv', parse_dates=['ship_out_time'])
    for clicks in pd.read_csv('../../data/JD_click_data.csv', parse_dates=['request_time'], chunksize=1_000_000):
        df = clicks.merge(orders, on=['sku_ID', 'user_ID']).merge(delivery, on='order_ID')
        df['click_to_order'] = np.round((df['order_time'] - df['request_time']).dt.total_seconds() / 3600)
        df['click_to_ship'] = np.round((df['ship_out_time'] - df['request_time']).dt.total_seconds() / 3600)
        click_to_order.append(df.loc[df['click_to_order'].between(0, 24), 'click_to_order'].value_counts())
        click_to_ship.append(df.loc[df['click_to_ship'].between(0, 24), 'click_to_ship'].value_counts())

    # plot the hour distributions
    axis = pd.concat(click_to_order).to_frame("Click to order").groupby(level=0).sum().plot()
    pd.concat(click_to_ship).to_frame("Click to ship").groupby(level=0).sum().plot(ax=axis)
    figure = axis.get_figure()
    figure.savefig('../../output/jd_hour_distribution.pdf')


if __name__ == '__main__':
    main()
