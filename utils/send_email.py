from utils import common as cm
from utils import ConfigData
from utils import global_const as gc
import yagmail
import os
import traceback


def send_yagmail(emails_to, subject, message, email_from=None, attachment_path=None, smtp_server=None,
                 smtp_server_port=None):
    root_dir = cm.get_project_root()
    cnf_path = str(root_dir.joinpath(gc.CONFIG_FILE_MAIN))
    m_cfg = ConfigData(cnf_path)
    if not email_from:
        email_from = m_cfg.get_value('Email/default_from_email')
    if not smtp_server:
        smtp_server = os.environ.get('ST_SMTP_SERVER')  # m_cfg.get_value('Email/smtp_server')
    if not smtp_server_port:
        # smtp_server_port = m_cfg.get_value('Email/smtp_server_port')
        if os.environ.get('ST_SMTP_SERVER_PORT').isnumeric():
            smtp_server_port = os.environ.get('ST_SMTP_SERVER_PORT')
        else:
            smtp_server_port = 25  #default value

    # receiver = emails_to  # 'stasrirak.ms@gmail.com, stasrira@yahoo.com, stas.rirak@mssm.edu'
    body = message
    filename = attachment_path  # 'test.png'

    yag = yagmail.SMTP(email_from,
                       host=smtp_server,
                       smtp_skip_login=True,
                       smtp_ssl=False,
                       soft_email_validation=False,
                       port=smtp_server_port)
    yag.send(
        to=emails_to,
        subject=subject,
        contents=body,
        attachments=filename,
    )


def prepare_and_send_email(email_body, email_subject, mcfg, lcfg, mlog = None):

    if mcfg:
        send_to = []
        # collect all email_to addresses that should be used
        # check if default addresses have to be included
        if 'notify_default_recepients' in lcfg and lcfg['notify_default_recepients'] \
                and isinstance(mcfg.get_value('Email/send_to_emails'), list):
            send_to.extend(mcfg.get_value('Email/send_to_emails'))  # get all default addresses.
        # check if additional addresses have to be included
        if 'additional_recepients' in lcfg and lcfg['additional_recepients'] \
                and isinstance(lcfg['additional_recepients'], list):
            send_to.extend(lcfg['additional_recepients'])
        # send notification email
        if send_to:
            try:
                send_yagmail(
                    emails_to=send_to,
                    subject=email_subject,
                    message=email_body
                    # ,attachment_path = email_attchms_study
                )
            except Exception as ex:
                # report unexpected error during sending emails to a log file and continue
                _str = 'Unexpected Error "{}" occurred during an attempt to send an email.\n{}'. \
                    format(ex, traceback.format_exc())
                if mlog:
                    mlog.critical(_str)
        else:
            mlog.critical('No send to addresses were found for sending alert email for {} website'.format(lcfg['url']))

# if executed by itself, do the following
if __name__ == '__main__':
    # send_email ('stasrirak.ms@gmail.com, stasrira@yahoo.com, stas.rirak@mssm.edu',
    # 'Test Email #4.2', 'Body of the test email??.', None, 'test.png')

    send_yagmail('stasrirak.ms@gmail.com, stasrira@yahoo.com, stas.rirak@mssm.edu', 'Test Email #5.4',
                 '<font color ="blue">Body</font> of the <b>test</b> email!!.', None, 'test.png')
