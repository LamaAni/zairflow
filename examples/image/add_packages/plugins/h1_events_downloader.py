import requests
import time
import json
import logging
import boto3
import sys

MAX_RETRIES = 100
RESULT_LIMIT = 10000
BUCKET = 'disambiguation'
BASE_URL = 'https://api.eventdata.crossref.org/v1/events'


logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s', level='INFO')
LOGGER = logging.getLogger(__name__)

BOTO_CLIENT = boto3.client('s3')


def write_to_s3(data, cursor, date, environment):
    key = f'airflow-sources/{environment}/events/{date}/{cursor}.json'
    BOTO_CLIENT.put_object(Body=data, Bucket=BUCKET, Key=key)


def download_page(url):
    tries = 0
    request = ''
    while tries != MAX_RETRIES:
        try:
            request = requests.get(url, timeout=10, verify=False)
        except requests.exceptions.ReadTimeout:
            LOGGER.warning(f"connection timing out, retrying..  ({tries}/{MAX_RETRIES})")
            tries += 1
            pass
        if request and request.status_code == 200:
            LOGGER.info("downloaded page")
            return request.json()
        else:
            time.sleep(2)
            LOGGER.warning(f"connection refused, retrying..     ({tries}/{MAX_RETRIES})")
            tries += 1
    raise requests.exceptions.RetryError(f"Maximum retries ({MAX_RETRIES}) exceeded")


def download_query(url, date, environment):
    page = download_page(url)
    write_to_s3(json.dumps(page), '00000000-0000-0000-0000-000000000000', date, environment)
    cursor = next_cursor(page)
    while cursor:
        LOGGER.info(f"downloading cursor at {cursor}")
        page = download_page(f'{url}&cursor={cursor}')
        write_to_s3(json.dumps(page), cursor, date, environment)
        cursor = next_cursor(page)


def next_cursor(page):
    cursor = ''
    if 'message' in page:
        if 'next-cursor' in page['message']:
            cursor = page['message']['next-cursor']
    return cursor


def download_events_date(date, environment):
    query_url = f'{BASE_URL}?rows={RESULT_LIMIT}&' + \
                f'from-collected-date={date}&' + \
                f'until-collected-date={date}'
    download_query(query_url, date, environment)
