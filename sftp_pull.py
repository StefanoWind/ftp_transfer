# -*- coding: utf-8 -*-
"""
Pull data form SFPT server
"""

import os
cd=os.getcwd()
import paramiko
import yaml
import glob
import logging
from datetime import datetime

#%% Inputs
source_config=os.path.join(cd,'configs','config.yaml')

#%% Functions
def download_all_files(sftp, remote_path, local_path):
    """
    Download all files from a single remote directory to a local directory.
    """
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    for filename in sftp.listdir(remote_path):
        remote_file = f"{remote_path}/{filename}"
        local_file = os.path.join(local_path, filename)

        logging.info(f"Downloading {remote_file} -> {local_file}")
        sftp.get(remote_file, local_file)
        sftp.remove(remote_file) 


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
download_all_files(sftp,config['remote_dir'], config['pull_dir'])
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