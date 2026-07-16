# -*- coding: utf-8 -*-
"""
Pull data form SFPT server
"""

import os
cd=os.getcwd()
import sys
import stat
import paramiko
import yaml
import glob
import logging
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

#%% Inputs
if len(sys.argv)==1:
    source_config=os.path.join(cd,'configs','config_windcube_rtd.yaml')
else:
    source_config=sys.argv[1]

#%% Functions
def download_all_files(sftp, remote_path, local_path, remove_remote, min_age):
    """
    Download all files from a single remote directory to a local directory.
    """
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    for attr in sorted(sftp.listdir_attr(remote_path), key=lambda a: a.filename):
        filename = attr.filename
        remote_file = f"{remote_path}/{filename}"
        local_file = os.path.join(local_path, filename)

        if stat.S_ISDIR(attr.st_mode):
            logging.warning(f"Skipping {remote_file}: subdirectories are not supported.")
            continue

        file_age=(time.time()-attr.st_mtime)/(3600*24)
        if file_age<min_age:
            logging.info(f"Skipping {remote_file}: below minimum age for transfer.")
            continue

        try:
            logging.info(f"Downloading {remote_file} -> {local_file}")
            sftp.get(remote_file, local_file)
            if remove_remote:
                sftp.remove(remote_file)
                logging.info(f"Removed {remote_file}")
        except Exception as e:
            logging.error(f"Failed to download/remove {remote_file}: {e}")


#%% Initialization
#config
with open(source_config, 'r') as fid:
    config = yaml.safe_load(fid)

# Establish SSH transport
transport = paramiko.Transport((config['host'], config['port']))
transport.connect(username=config['username'], password=config['password'])
sftp = paramiko.SFTPClient.from_transport(transport)

#logger
os.makedirs(os.path.join(cd,config['log_dir']),exist_ok=True)
logfile=os.path.join(cd,config['log_dir'],datetime.strftime(datetime.now(), '%Y%m%d.%H%M%S'))+'_ftp_pull.log'

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
 

#%% Main

#get remote files
download_all_files(sftp,config['remote_dir'], config['pull_dir'],config['remove_remote'],config['min_age'])
logging.info("Download completed successfully.")

#scan local file
local_files=glob.glob(os.path.join(config['pull_dir'],'*'))
with open(os.path.join(config['pull_dir'],'local_file_list.txt'),'w') as fid:
    for f in local_files:
        if os.path.basename(f)!='local_file_list.txt':
            fid.write(f'{os.path.basename(f)}, {os.path.getsize(f)} \n')
            
#send local file list to FTP server
sftp.put(os.path.join(config['pull_dir'],'local_file_list.txt'), os.path.join(config['remote_dir'],'local_file_list.txt'))
logging.info(f"Sent local file list containing {len(local_files)} items.")

#terminate
sftp.close()
transport.close()
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)