"""Re-do the prior analysis with a SQLite database."""

import sqlite3
from pathlib import Path

import pandas as pd


def main():
    """Run all the parts of this task."""

    # delete the database file if it already exists
    db_path = Path('../../data/db.sqlite')
    db_path.unlink(missing_ok=True)

    # create the database and query it to plot hour distributions
    with sqlite3.connect(db_path) as connection:
        create_database(connection)
        run_queries(connection)
        plot_distributions(connection)

    # query the database with Ibis instead
    plot_distributions_with_ibis(db_path)


def create_database(connection):
    """Create tables for orders, delivery, and clicks."""
    cursor = connection.cursor()

    # create an orders table, dropping some duplicate rows to satisfy the primary key constraint
    print("Creating orders table ...")
    cursor.execute('''
        CREATE TABLE JD_order_data (
            order_ID TEXT NOT NULL CHECK(LENGTH(order_ID) = 10),
            sku_ID TEXT NOT NULL CHECK(LENGTH(sku_ID) = 10),
            user_ID TEXT NOT NULL CHECK(LENGTH(user_ID) = 10),
            order_time DATETIME NOT NULL,
            quantity INT NOT NULL,
            final_unit_price REAL NOT NULL,
            PRIMARY KEY (order_ID, sku_ID)
        )
    ''')
    orders = pd.read_csv('../../data/JD_order_data.csv', low_memory=False)
    orders = orders[['order_ID', 'sku_ID', 'user_ID', 'order_time', 'quantity', 'final_unit_price']]
    orders = orders.groupby(['order_ID', 'sku_ID'], as_index=False).first()
    orders.to_sql('JD_order_data', connection, index=False, if_exists='append')
    cursor.execute('CREATE INDEX orders_user_index ON JD_order_data (user_ID)')

    # create a delivery table
    print("Creating delivery table ...")
    cursor.execute('''
        CREATE TABLE JD_delivery_data (
            order_ID TEXT NOT NULL CHECK(LENGTH(order_ID) = 10),
            package_ID TEXT NOT NULL CHECK(LENGTH(package_ID) = 10),
            ship_out_time DATETIME NOT NULL,
            PRIMARY KEY (order_ID, package_ID),
            FOREIGN KEY (order_ID) REFERENCES JD_order_data (order_ID)
        )
    ''')
    delivery = pd.read_csv('../../data/JD_delivery_data.csv', parse_dates=['ship_out_time'])
    delivery = delivery[['order_ID', 'package_ID', 'ship_out_time']]
    delivery.to_sql('JD_delivery_data', connection, index=False, if_exists='append')

    # create a clicks table
    print("Creating clicks table ...")
    cursor.execute('''
        CREATE TABLE JD_click_data (
            user_ID TEXT NOT NULL CHECK(LENGTH(user_ID) = 10),
            sku_ID TEXT NOT NULL CHECK(LENGTH(sku_ID) = 10),
            request_time DATETIME NOT NULL,
            FOREIGN KEY (user_ID) REFERENCES JD_order_data (user_ID),
            FOREIGN KEY (sku_ID) REFERENCES JD_order_data (sku_ID)
        )
    ''')
    clicks = pd.read_csv('../../data/JD_click_data.csv', parse_dates=['request_time'])
    clicks = clicks[clicks['user_ID'] != '-']
    clicks = clicks[['user_ID', 'sku_ID', 'request_time']]
    clicks.to_sql('JD_click_data', connection, index=False, if_exists='append')
    cursor.execute('CREATE INDEX clicks_user_index ON JD_click_data (user_ID)')
    cursor.execute('CREATE INDEX clicks_sku_index ON JD_click_data (sku_ID)')

    # create a user table
    print("Creating users table ...")
    cursor.execute('''
        CREATE TABLE JD_user_data (
            user_ID TEXT NOT NULL CHECK(LENGTH(user_ID) = 10),
            plus INT NOT NULL CHECK(plus IN (0, 1)),
            PRIMARY KEY (user_ID)
        )
    ''')
    users = pd.read_csv('../../data/JD_user_data.csv', low_memory=False)
    users = users[['user_ID', 'plus']]
    users = users.groupby(['user_ID'], as_index=False).first()
    users.to_sql('JD_user_data', connection, index=False, if_exists='append')
    cursor.execute('CREATE INDEX users_user_index ON JD_user_data (user_ID)')


def run_queries(connection):
    """Query the database to get users by demographic and average order value by demographic"""

    # run an SQL query that returns the average number of clicks made by plus vs non-plus users
    print("Getting the number of plus vs non-plus users ...")
    query = '''
        SELECT COUNT(*) num_users
        FROM JD_user_data
        GROUP BY plus 
    '''
    plus_v_nonplus_users = pd.read_sql_query(query, connection)
    print(plus_v_nonplus_users)

    # run an SQL query that gets the value of each order and prints the 5 most expensive orders
    print("Getting the order values")
    query = '''
        SELECT
            SUM(t.sku_price) order_value, 
            user_ID, 
            order_ID
        FROM (
            SELECT 
                quantity * final_unit_price AS sku_price, 
                order_ID, 
                user_ID
            FROM JD_order_data
        ) AS t
        GROUP BY order_ID
        ORDER BY order_value DESC
        LIMIT 5
    '''
    order_values = pd.read_sql_query(query, connection)
    print(order_values)

    # run an SQL query that gets the average order value for plus v nonplus users
    print("Getting the average order value for plus v nonplus users...")
    query = '''
        SELECT AVG(t2.order_value) AS 'average_order_value'
        FROM (
            SELECT
                SUM(t1.sku_price) order_value, 
                order_ID, 
                user_ID
            FROM (
                SELECT 
                    quantity * final_unit_price AS sku_price, 
                    order_ID, 
                    user_ID
                FROM JD_order_data
            ) AS t1
            GROUP BY order_ID
        ) AS t2
        INNER JOIN JD_user_data u ON u.user_ID = t2.user_ID
        GROUP BY plus
    '''
    plus_v_nonplus_ordervals = pd.read_sql_query(query, connection)
    print(plus_v_nonplus_ordervals)


def plot_distributions(connection):
    """Query the database to obtain the distribution of hours between different events for plotting."""

    # obtain the distribution of hours from click to order
    print("Computing the distribution of hours from click to order ...")
    query = '''
        SELECT
            ROUND((JULIANDAY(o.order_time) - JULIANDAY(c.request_time)) * 24) hours,
            COUNT(*) `Click to order`
        FROM JD_click_data c
        INNER JOIN JD_order_data o ON c.sku_ID = o.sku_ID AND c.user_ID = o.user_ID
        INNER JOIN JD_delivery_data d ON o.order_ID = d.order_ID
        WHERE hours BETWEEN 0 AND 24
        GROUP BY hours
    '''
    click_to_order = pd.read_sql_query(query, connection)

    # obtain the distribution of hours from click to ship
    print("Computing the distribution of hours from click to ship ...")
    query = '''
        SELECT
            ROUND((JULIANDAY(d.ship_out_time) - JULIANDAY(c.request_time)) * 24) hours,
            COUNT(*) `Click to ship`
        FROM JD_click_data c
        INNER JOIN JD_order_data o ON c.sku_ID = o.sku_ID AND c.user_ID = o.user_ID
        INNER JOIN JD_delivery_data d ON o.order_ID = d.order_ID
        WHERE hours BETWEEN 0 AND 24
        GROUP BY hours
    '''
    click_to_ship = pd.read_sql_query(query, connection)

    # plot the hour distributions
    print("Plotting the distributions ...")
    axis = click_to_order.set_index('hours').plot()
    click_to_ship.set_index('hours').plot(ax=axis)
    figure = axis.get_figure()
    figure.savefig('../../output/jd_hour_distribution_sql.pdf')


def plot_distributions_with_ibis(db_path):
    """Build and execute the same queries with Ibis to replicate the same plot."""
    import ibis
    client = ibis.sqlite.connect(str(db_path))

    # merge the tables
    clicks = client.table('JD_click_data')
    orders = client.table('JD_order_data')
    delivery = client.table('JD_delivery_data')
    join = clicks.inner_join(orders, [
        clicks['sku_ID'] == orders['sku_ID'],
        clicks['user_ID'] == orders['user_ID'],
    ])
    join = join.inner_join(delivery, orders['order_ID'] == delivery['order_ID'])

    # compute hours from click to ordering and shipping
    click_to_order_seconds = orders['order_time'].epoch_seconds() - clicks['request_time'].epoch_seconds()
    click_to_ship_seconds = delivery['ship_out_time'].epoch_seconds() - clicks['request_time'].epoch_seconds()
    click_to_order_hours = join[(click_to_order_seconds / 3600).round().name('hours')]
    click_to_ship_hours = join[(click_to_ship_seconds / 3600).round().name('hours')]

    # only keep hours within the first day
    click_to_order_hours = click_to_order_hours[click_to_order_hours['hours'].between(0, 24)]
    click_to_ship_hours = click_to_ship_hours[click_to_ship_hours['hours'].between(0, 24)]

    # compute the distribution of these hours
    click_to_order = click_to_order_hours.groupby('hours').aggregate([
        click_to_order_hours.count().name("Click to order"),
    ])
    click_to_ship = click_to_ship_hours.groupby('hours').aggregate([
        click_to_ship_hours.count().name("Click to ship"),
    ])

    # execute the queries and plot the data
    click_to_order_data = click_to_order.execute()
    click_to_ship_data = click_to_ship.execute()
    axis = click_to_order_data.set_index('hours').plot()
    click_to_ship_data.set_index('hours').plot(ax=axis)
    figure = axis.get_figure()
    figure.savefig('../../output/jd_hour_distribution_ibis.pdf')


if __name__ == '__main__':
    main()
