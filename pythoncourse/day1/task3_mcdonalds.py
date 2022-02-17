"""Scrape open McDonalds job listings."""

import json

import requests
import pandas as pd


MCDONALDS_URL = 'https://careers.mcdonalds.com/api/jobs'


def count_jobs():
    """Count the number of open McDonalds jobs by experience level and city."""

    # run a generic query -- extra info is added at the end with job counts by category
    response = requests.get(MCDONALDS_URL, params={
        'limit': 1,
        'page': 1,
        'sortBy': 'relevance',
        'descending': False,
        'internal': False,
    })
    data = json.loads(response.text)

    # print job counts
    print(pd.DataFrame(data['filter']['experienceLevels']['all']).to_string())
    print(pd.DataFrame(data['filter']['locations']['all']).to_string())


def plot_jobs(location):
    """Plot McDonalds jobs by location."""

    # query the first 100 jobs in the location
    response = requests.get(MCDONALDS_URL, params={
        'limit': 100,
        'page': 1,
        'sortBy': 'relevance',
        'descending': False,
        'internal': False,
        'locations': location,
    })
    data = json.loads(response.text)

    # collect coordinates for plotting
    locations = []
    for job in data['jobs']:
        locations.append({
            'longitude': job['data']['longitude'],
            'latitude': job['data']['latitude'],
        })

    # plot the coordinates
    df = pd.DataFrame(locations)
    axis = df.plot.scatter(x='longitude', y='latitude')
    figure = axis.get_figure()
    figure.savefig(f'../../output/mcdonalds_{location}_posts.pdf')


if __name__ == '__main__':
    count_jobs()
    plot_jobs('New York,New York,United States')
