"""Call functions in R using rpy2"""

from rpy2.robjects import pandas2ri, Formula
from rpy2.robjects.packages import importr

pandas2ri.activate()
stats = importr('stats')
base = importr('base')
fixest = importr('fixest')

from pythoncourse.day3.task1_regressions import get_order_vs_delivery_data


def run_rpy2_regressions():
    """Run regressions on the orders vs. delivery data with R."""
    df = get_order_vs_delivery_data()

    model1 = stats.lm(Formula('delivery_time ~ order_time_of_day'), data=df)
    print(base.summary(model1).rx2('coefficients')[:, 0])

    model2 = fixest.feols(Formula('delivery_time ~ order_time_of_day'), data=df)
    print(base.summary(model2).rx2('coefficients'))

    df['order_dow'] = df['order_time'].dt.day_name()
    model3 = fixest.feols(Formula('delivery_time ~ order_time_of_day | order_dow'), data=df)
    print(base.summary(model3).rx2('coefficients'))

    df['order_dom'] = df['order_time'].dt.day
    model4 = fixest.feols(Formula('delivery_time ~ order_time_of_day | order_dom'), data=df)
    print(base.summary(model4).rx2('coefficients'))


if __name__ == '__main__':
    run_rpy2_regressions()
