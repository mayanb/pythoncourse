"""Download and parse posts from thelayoff.com."""

import requests
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


THELAYOFF_PATH = Path('../../data/thelayoff')


def download_posts(company):
    """Download all HTML files of posts for a single company, stopping when a 404 is hit."""
    for page in range(1, 1_000):
        # check whether the file has already been downloaded
        THELAYOFF_PATH.mkdir(parents=True, exist_ok=True)
        html_path = THELAYOFF_PATH / f'{company}_{page:04}.html'
        if html_path.exists():
            print(f"Already saved page {page}.")
            continue

        # if not, download it and see if this is the last page
        html = requests.get(f'https://www.thelayoff.com/{company}?page={page}').text
        if '404 Not Found' in html:
            break
        html_path.write_text(html, encoding='utf-8')
        print(f"Saved page {page}.")


def plot_posts(company):
    """Plot a time series of posts for a single company based on timestamps from downloaded HTML post data."""

    # get all datetimes from the posts
    datetimes = []
    for html_path in sorted(THELAYOFF_PATH.glob(f'{company}_*.html')):
        soup = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')
        for post in soup.find_all('span', {'class': 'post-timeago'}):
            datetimes.append(pd.to_datetime(post.get('data-datetime')))

    # save a plot
    df = pd.DataFrame({'datetime': datetimes})
    df['date'] = df['datetime'].dt.date
    axis = df.groupby('date').count().plot(rot=45, legend=False)
    figure = axis.get_figure()
    figure.savefig(f'../../output/thelayoff_{company}_posts.pdf')


if __name__ == '__main__':
    download_posts('general-motors')
    plot_posts('general-motors')
