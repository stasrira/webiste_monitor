import os
from pathlib import Path
from utils import global_const as gc
import re


def get_project_root():
    # Returns project root folder.
    return Path(__file__).parent.parent


def file_exists(fn):
    try:
        with open(fn, "r"):
            return 1
    except IOError:
        return 0


def is_excel(file_path):
    ext = Path(file_path).suffix
    if 'xls' in ext:
        return True
    else:
        return False


def identify_delimeter_by_file_extension(file_path):
    ext = Path(file_path).suffix
    out_value = None

    if ext == 'csv':
        out_value = ','
    elif ext == 'tab':
        out_value = '   '
    elif 'xls' in ext:
        out_value = None
    else:
        out_value = ','

    return out_value


def start_external_process_async(exec_path):
    from subprocess import Popen
    process = Popen(exec_path, shell=True)
    return process


def check_external_process(process):
    pr_out = process.poll()
    if pr_out is None:
        status = 'running'
        message = ''
    else:
        status = 'stopped'
        message = pr_out
    out = {'status': status, 'message': message}
    return out

# get list of directories or files based on the given location and mask
def get_file_system_items_global(dir_cur, item_type='dir',
                                 match_pattern=None,
                                 recursive = None, get_names_only = None):
    import glob

    # base_loc = self.data_loc / dir_cur
    if match_pattern is None:
        match_pattern = '*'
    if get_names_only is None:
        get_names_only = False

    items = []

    # if recursive was not provided, set it to True
    if recursive is None:
        recursive = True
        match_pattern = '**/' + match_pattern

    # search_pattern = str(Path(str(dir_cur) + '/**/' + match_pattern))
    search_pattern = str(Path(str(dir_cur) + '/' + match_pattern))  # '/**/SampleManifests'
    items_cur = glob.glob(search_pattern, recursive=recursive)

    if item_type == 'dir':
        items_clean = [fn for fn in items_cur if Path.is_dir(Path(fn))]
    elif item_type == 'file':
        items_clean = [fn for fn in items_cur if not Path.is_dir(Path(fn))]

    else:
        items_clean = None
    items.extend(items_clean)

    if get_names_only:
        # remove path from the file names and keep only names
        items = [os.path.basename(item) for item in items]

    return items

def move_file_to_processed(file_path, processed_dir_path, log_obj, error_obj):
    if not os.path.exists(processed_dir_path):
        # if Processed folder does not exist in the current study folder, create it
        log_obj.info('Creating directory for processed files "{}"'.format(processed_dir_path))
        os.mkdir(processed_dir_path)

    file_name = Path(file_path).name
    file_name_new = file_name
    file_name_new_path = Path(processed_dir_path) / file_name_new
    cnt = 0
    #check if file with the same name was already saved in "processed" dir
    while os.path.exists(file_name_new_path):
        # if file exists, identify a new name, so the new file won't overwrite the existing one
        if cnt >= gc.PROCESSED_FOLDER_MAX_FILE_COPIES:
            file_name_new_path = None
            break
        cnt += 1
        file_name_new = '{}({}){}'.format(os.path.splitext(file_name)[0], cnt, os.path.splitext(file_name)[1])
        file_name_new_path = Path(processed_dir_path) / file_name_new

    if not file_name_new_path is None:
        # new file name was successfully identified
        # move the file to the processed dir under the identified new name
        os.rename(file_path, file_name_new_path)
        log_obj.info('Processed file "{}" was moved to "{}" under {} name: "{}".'
                     .format(str(file_path), str(processed_dir_path)
                          ,('the same' if cnt == 0 else 'the new')
                          ,file_name_new_path))
    else:
        # new file name was not identified
        _str = 'Processed file "{}" cannot be moved to "{}" because {} copies of this file already exist in this ' \
               'folder that exceeds the allowed application limit of copies for the same file.'\
            .format(file_path, processed_dir_path, cnt + 1)
        log_obj.error (_str)
        error_obj.add_error(_str)
        pass

def prepare_status_email(datasetfile_loc_objs, db_access):
    msg_out = []
    nbsp = 3
    dsf_loc_cnt = 0
    dsf_loc_processed = []
    dsf_loc_disqualified = []
    dsf_loc_no_files = []
    datasetfile_loc_objs_grouped = []
    disqualified_reasons = {}
    # loop through all dataset file locations and group them based on the disqualification and processed files
    for dsf_loc in datasetfile_loc_objs:
        if dsf_loc.disqualified:
            dsf_loc_disqualified.append(dsf_loc)
        else:
            if dsf_loc.dataset_files:
                dsf_loc_processed.append(dsf_loc)
            else:
                dsf_loc_no_files.append(dsf_loc)
    # recollect all dataset file locations in a single list using a specific order of the groups
    datasetfile_loc_objs_grouped.extend(dsf_loc_processed)
    datasetfile_loc_objs_grouped.extend(dsf_loc_disqualified)
    datasetfile_loc_objs_grouped.extend(dsf_loc_no_files)

    # loop through the list of grouped dataset file locations and prepare a status email
    for dsf_loc in datasetfile_loc_objs_grouped:
        email_msg = ''
        dsf_loc_cnt += 1
        email_msg = '<b>Data file location (#{}):</b><br/>{}' \
            .format(dsf_loc_cnt, '&nbsp;' * nbsp + str(dsf_loc.location_path))
        email_msg = email_msg + '<br/>Dataset type: <b>{}</b> (id = {})' \
            .format(db_access.get_dataset_type_name(dsf_loc.dataset_type_id) if dsf_loc.dataset_type_id else 'manifest (used as default)',
                    str(dsf_loc.dataset_type_id) if dsf_loc.dataset_type_id else 'ND')
        email_msg = email_msg + '<br/>{}Disqualified:{} {}{}</font>'. \
            format(
            '<b>' if dsf_loc.disqualified else '',
            '</b>' if dsf_loc.disqualified else '',
            '<font color = "red">' if dsf_loc.disqualified else '<font color = "green">',
            dsf_loc.disqualified)
        if dsf_loc.disqualified and dsf_loc.disqualified_reasons:
            email_msg = email_msg + '<br/><font color = "red">Disqualification Reasons:</font>'
            for ds_reason in dsf_loc.disqualified_reasons:
                email_msg = email_msg + '<br/>{}'.format('&nbsp;' * nbsp + str(ds_reason))
                ds_reason_to_report = ds_reason
                if 'Expected to exist config file' in ds_reason:
                    matches = re.findall(r'\"(.+?)\"', ds_reason)
                    for match in matches:
                        ds_reason_to_report = ds_reason_to_report.replace(str(match), '').\
                            replace('""', '[<i>note: the path was omitted</i>]')

                if ds_reason_to_report in disqualified_reasons.keys():
                    disqualified_reasons[ds_reason_to_report] +=1
                else:
                    disqualified_reasons[ds_reason_to_report] = 1

        if not dsf_loc.disqualified and dsf_loc.dataset_files:
            email_msg = email_msg + '<br/>Number of processed data files: {}.'.format(len(dsf_loc.dataset_files))
            email_msg = email_msg + '<br/>Data files:'
            file_cnt = 0
            for mnf_file in dsf_loc.dataset_files:
                file_cnt += 1
                email_msg = email_msg + '<br/>{}- <i><b>File (#{}):</b> {}</i>'.format(
                    '&nbsp;' * nbsp, file_cnt, str(mnf_file.datasetfile_path))
                email_msg = email_msg + '<br/>{}Processed: {}{}</font>' \
                    .format('&nbsp;' * nbsp,
                            '<font color="green">' if mnf_file.processed else '<font color="red">',
                            str(mnf_file.processed))
                if mnf_file.submitted_datasetfile_rows:
                    email_msg = email_msg + '<br/>{}Processed rows summary:'.format('&nbsp;' * nbsp)
                for row_status in mnf_file.submitted_datasetfile_rows:
                    email_msg = email_msg + '<br/>{}- Status: <font color = "{}">{}</font>: {} rows ' \
                        .format('&nbsp;' * nbsp,
                                'green' if row_status == 'OK' else 'red',
                                row_status,
                                len(mnf_file.submitted_datasetfile_rows[row_status]))
                    if not row_status == 'OK':
                        email_msg = email_msg + '<br/>{}Details:'.format('&nbsp;' * nbsp)
                        for item in mnf_file.submitted_datasetfile_rows[row_status]:
                            email_msg = email_msg + '<br/>{}{} --> {}' \
                                .format('&nbsp;' * nbsp, str(item[0]), str(item[1]['description']))
                            # print(str(item[0]))
                            # print(str(item[1]['description']))
                    # print(row_status)
                    # print(mnf_file.submitted_datasetfile_rows[row_status])
                if mnf_file.error.exist():
                    email_msg = email_msg + '<br/>{}<font color = "red">Errors reported:</font>'.format('&nbsp;' * nbsp)
                    for err in mnf_file.error.get_errors_to_str()['errors']:
                        email_msg = email_msg + '<br/>{}->{}'.format('&nbsp;' * nbsp, err)
        else:
            email_msg = email_msg + '<br/><font color="blue">No dataset files processed in this location.</font>'

        msg_out.append(email_msg)

    return msg_out, disqualified_reasons
