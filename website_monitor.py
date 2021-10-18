import os
from os import path
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv
from utils import setup_logger_common, deactivate_logger_common, prepare_and_send_email
from utils import ConfigData
from utils import global_const as gc
from utils import web_utils


basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

# if executed by itself, do the following
if __name__ == '__main__':
    # load main config file and get required values
    m_cfg = ConfigData(gc.CONFIG_FILE_MAIN)
    loc_cfg = ConfigData(gc.CONFIG_FILE_LOCAL)

    # print ('m_cfg = {}'.format(m_cfg.cfg))
    # assign values
    common_logger_name = gc.MAIN_LOG_NAME  # m_cfg.get_value('Logging/main_log_name')

    # get path configuration values
    logging_level = m_cfg.get_value('Logging/main_log_level')
    # get path configuration values and save them to global_const module
    # path to the folder where all application level log files will be stored (one file per run)
    gc.APP_LOG_DIR = m_cfg.get_value('Location/app_logs')

    log_folder_name = gc.APP_LOG_DIR  # gc.LOG_FOLDER_NAME
    prj_wrkdir = os.path.dirname(os.path.abspath(__file__))

    # get current location of the script and create a Log folder
    # if a relative path provided, convert it to the absolute address based on the application working dir
    if not os.path.isabs(log_folder_name):
        logdir = Path(prj_wrkdir) / log_folder_name
    else:
        logdir = Path(log_folder_name)
    # lg_filename = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.log'
    lg_filename = 'website_monitor.log'

    # define structure of the time_rotating_details dictionary
    time_rotating_details = {}
    # check if the log time interval rotation is given in the config file
    when = m_cfg.get_value('Logging/time_rotating/when')
    interval = m_cfg.get_value('Logging/time_rotating/interval')
    backupCount = m_cfg.get_value('Logging/time_rotating/backupCount')
    if when:
        time_rotating_details['when'] = when
    if interval:
        time_rotating_details['interval'] = interval
    if backupCount:
        time_rotating_details['backupCount'] = backupCount

    lg = setup_logger_common(common_logger_name, logging_level, logdir, lg_filename, time_rotating_details)
    mlog = lg['logger']

    mlog.info('Start monitoring websites.')

    try:
        watch_locations = loc_cfg.get_value('Monitor/locations')
        for wloc in watch_locations:
            _str = ''
            mlog.info('Performing monitoring for the following url: {}'.format(wloc['url']))
            if web_utils.is_url (wloc['url']):  # check if the url is valid
                mlog.info('Url ({}) is valid, proceeding to check if it is up.'.format(wloc['url']))

                response_details = web_utils.monitor_url(wloc)  # validate the website location

                if response_details['status'] == 1:
                    # the website is up and running, json validation was OK or not required
                    mlog.info('The website is up and running. Json response validation status: "{}" '
                              .format(response_details['json_validation']))
                elif response_details['status'] == 2:
                    # the website is up and running, but json validation has failed
                    _str = 'The website is up and running, but json response validation has failed. Json response ' \
                           'validation status: "{}", description: {}'\
                        .format(response_details['json_validation'], response_details['desc'])
                    mlog.warning(_str)
                else:
                    # website is not running
                    _str = 'The website is NOT running properly. Returned status code: {}, description: {}.'\
                        .format(response_details['html_status_code'], response_details['desc'])
                    mlog.warning(_str)
            else:
                # provided url is not valid
                _str = 'Url ({}) is not valid; monitoring will not be performed.'.format(wloc['url'])
                mlog.warning(_str)

            if len(_str.strip()) > 0:
                # if some error response was received (_str variable has some value), send an email
                email_body = 'Alert: the following website is down or not properly performing!' \
                             '<br/><b>URL</b>: {}' \
                             '<br/><b>Details</b>:<br/>{}'.format(wloc['url'], _str)
                url_len_show = m_cfg.get_value('Email/url_len_show_in_subject')
                email_subject = 'Website Monitoring Tool - Alert for {}'\
                    .format (wloc['url'][:url_len_show] + ('...' if len(wloc['url']) > url_len_show else ''))
                prepare_and_send_email (email_body, email_subject, m_cfg, wloc, mlog)

    except Exception as ex:
        # report unexpected error to log file
        _str = 'Unexpected Error "{}" occurred during processing file: {}\n{} ' \
            .format(ex, os.path.abspath(__file__), traceback.format_exc())
        mlog.critical(_str)
        raise

    deactivate_logger_common(mlog, mlog.handlers[0])
    sys.exit()

