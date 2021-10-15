import requests
from urllib.parse import urlparse
# from utils import ConfigData, global_const as gc


def monitor_url(wloc):
    # https://stackoverflow.com/questions/1949318/checking-if-a-website-is-up-via-python
    # url = "http://slapp07.mssm.edu:81/api/sampleinfo/stats"  # "https://api.github.com"

    response_details = {
        'status': 0,
        'html_status_code': 0,
        'desc': 'Not defined',
        'json_validation': 'not performed'
    }

    try:
        # response = requests.head(wloc['url'])
        response = requests.get (wloc['url'])
    except Exception as e:
        # response was completed with an error, prepare a response from function
        response_details['status'] = 0
        response_details['html_status_code'] = 'Not Defined'
        response_details['desc'] = str(e)
    else:
        if response.status_code == 200:
            # if status_code == 200, check if the json response needs to be validated
            if 'validate_json_response' in wloc:
                val_conditions = wloc['validate_json_response']
            else:
                val_conditions = None
            if val_conditions:
                # json response is required to be validated
                json_response = response.json()  # get json response
                # valid_cnt = 0
                for val_cond in val_conditions:  # loop through all validation conditions
                    # valid_cnt += 1
                    # if conditions are set, perform validation on those, otherwise skip these
                    if val_cond['param_name'] and val_cond['param_value']:
                        # if parameter name and expected value are provided proceed here
                        # validate the json response parameter
                        if val_cond['param_name'] in json_response:
                            # if required parameter name is present in the json response
                            if not json_response[val_cond['param_name']] == val_cond['param_value']:
                                # validation of the json parameter has failed, prepare a response from function
                                response_details['status'] = 2
                                response_details['html_status_code'] = response.status_code
                                response_details['json_validation'] = 'failed'
                                response_details['desc'] = 'Json validation failed for parameter "{}". Expected value ' \
                                                           'was "{}", while "{}" was received.'\
                                    .format(val_cond['param_name'],
                                            val_cond['param_value'],
                                            json_response[val_cond['param_name']])
                                break  # exit json validation loop due to a recorded failure
                        else:
                            # if required parameter name is not present in the json response
                            response_details['status'] = 2
                            response_details['html_status_code'] = response.status_code
                            response_details['json_validation'] = 'failed'
                            response_details['desc'] = 'Expected to exist json validation parameter "{}" was not ' \
                                                       'found in the received json response. The following are ' \
                                                       'parameters present in the json response: {}' \
                                .format(val_cond['param_name'], json_response.keys())
                            break  # exit json validation loop due to a recorded failure

                if response_details['json_validation'] != 'failed':
                    # validation of the json response conditions was completed without errors, prepare a response
                    response_details['status'] = 1
                    response_details['html_status_code'] = response.status_code
                    response_details['desc'] = 'OK'
                    response_details['json_validation'] = 'OK'
            else:
                # no validation of json response is required, prepare a response from function
                response_details['status'] = 1
                response_details['html_status_code'] = response.status_code
                response_details['desc'] = 'OK'
                response_details['json_validation'] = 'not required'
        else:
            # website returned some error code, prepare a response from function
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
