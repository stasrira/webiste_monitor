import requests
from urllib.parse import urlparse


def monitor_url(url):
    # https://stackoverflow.com/questions/1949318/checking-if-a-website-is-up-via-python
    # url = "http://slapp07.mssm.edu:81/api/sampleinfo/stats"  # "https://api.github.com"

    response_details = {
        'status': 0,
        'html_status_code': 0,
        'desc': 'Not defined'
    }

    try:
        response = requests.head(url)
    except Exception as e:
        # print('NOT OK: {}'.format(str(e)))
        response_details['status'] = 0
        response_details['html_status_code'] = 500
        response_details['desc'] = str(e)
    else:
        if response.status_code == 200:
            # print("OK")
            response_details['status'] = 1
            response_details['html_status_code'] = response.status_code
            response_details['desc'] = 'OK'
        else:
            # print('NOT OK: HTTP response code {}'.format(response.status_code))
            response_details['status'] = 0
            response_details['html_status_code'] = response.status_code
            response_details['desc'] = 'NOT OK'

    return response_details

def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
