"""Run and plot basic OLS models using statsmodels on order time and delivery data"""

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def main():
    """Run the parts of this task."""
    df = get_order_vs_delivery_data()
    plot_order_vs_delivery_data(df)
    run_basic_regression(df)
    run_regression_discontinuity(df)


def get_order_vs_delivery_data():
    """Create a dataframe merging the order and delivery data. Generate variables for order time of day and delivery
    duration.
    """

    # select only orders (not each SKU inside) that are supposed to be delivered by the same or next day
    orders = pd.read_csv('../../data/JD_order_data.csv', parse_dates=['order_time'])
    orders = orders[orders['promise'] == '1']
    orders = orders.drop_duplicates(subset=['order_ID', 'order_time'])

    # merge in delivery
    delivery = pd.read_csv('../../data/JD_delivery_data.csv', parse_dates=['ship_out_time', 'arr_time'])
    df = orders.merge(delivery, on='order_ID')

    # keep only the last delivery for each order
    df['delivery_time'] = df.apply(lambda x: (x.arr_time - x.order_time).total_seconds() / 3600, axis=1)
    df.sort_values('delivery_time').drop_duplicates('order_ID', keep='last')

    # keep only orders that arrived within 72 hours
    df = df[(df['delivery_time'] <= 72) & (df['delivery_time'] > 0)]

    # compute the time of the day the order was placed
    df['order_time_of_day'] = df.apply(lambda x: x.order_time.hour + x.order_time.minute / 60, axis=1)
    return df


def plot_order_vs_delivery_data(df):
    """Plot delivery time vs order time of day."""
    axis = df.plot(x='order_time_of_day', y='delivery_time', style='o', alpha=0.03, legend=None)
    axis.set_xlabel('Order Time of Day')
    axis.set_ylabel('Delivery Time (hours)')
    figure = axis.get_figure()
    figure.savefig(f'../../output/delivery_duration_v_ordertime.png')


def run_basic_regression(df):
    """Run a basic linear regression on delivery time vs order time of day without the formula API."""
    Y = df['delivery_time']
    X = sm.add_constant(df['order_time_of_day'])
    model = sm.OLS(Y, X).fit()
    print(model.summary())


def run_regression_discontinuity(df):
    """Estimate a regression discontinuity OLS model and plot the model fit on your scatterplot."""

    # estimate a regression discontinuity model
    model = smf.ols(formula='delivery_time ~ I(order_time_of_day - 11) * I(order_time_of_day >= 11)', data=df).fit()
    print(model.summary())

    # store the fitted values
    df = df.copy()
    df['OLS_model'] = model.fittedvalues

    # plot the data and the fitted values
    axis1 = df.plot(kind='scatter', x='order_time_of_day', y='delivery_time', style='o', alpha=0.03, label="Data")
    axis2 = df.plot(kind='scatter', x='order_time_of_day', y='OLS_model', color='g', ax=axis1, label="OLS Model")
    axis2.set_xlabel('Order Time of Day')
    axis2.set_ylabel('Delivery Time (hours)')
    figure = axis2.get_figure()
    figure.savefig(f'../../output/regression_discontinuity_plot.png')


if __name__ == '__main__':
    main()
