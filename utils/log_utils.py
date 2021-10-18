import os
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter


def setup_logger_common(lg_name, lg_level, log_path, filename, time_rotating_details = None):
    os.makedirs(log_path, exist_ok=True)
    log_file = log_path / filename  # (filename + '_' + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.log')

    if not lg_name and len(lg_name) == 0:
        lg_name = __name__

    mlog = logging.getLogger(lg_name)

    try:
        lev = eval('logging.' + lg_level)
    except Exception:
        lev = logging.INFO

    mlog.setLevel(lev)

    if time_rotating_details \
            and 'when' in time_rotating_details \
            and 'interval' in time_rotating_details \
            and 'backupCount' in time_rotating_details:
        # create a handler with assigned time rotation
        handler = TimedRotatingFileHandler(filename=log_file,
                                           when = time_rotating_details['when'],
                                           interval= time_rotating_details['interval'],
                                           backupCount=time_rotating_details['backupCount'],
                                           encoding='utf-8',
                                           delay=False)
    else:
        # create a handler without time rotation settings
        handler = logging.FileHandler(log_file)

    # set logging level
    handler.setLevel(lev)  # logging.DEBUG

    # create a logging format
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the file handler to the logger
    mlog.addHandler(handler)

    out = {'logger': mlog, 'handler': handler}

    return out


def deactivate_logger_common(logger, handler):
    logger.removeHandler(handler)
