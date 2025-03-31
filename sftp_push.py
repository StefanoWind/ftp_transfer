# -*- coding: utf-8 -*-
"""
Created on Fri Mar 28 16:03:34 2025

@author: sletizia
"""

import os
cd=os.getcwd()
import paramiko
import yaml
import numpy as np
import time
import logging
from datetime import datetime

#%% Inputs
source_config=os.path.join(cd,'configs','config.yaml')

#%% Functions

def upload_directory(sftp, local_path, remote_path,skip_file,skip_size):
    """
    Recursively upload a local directory to a remote SFTP server.
    """
    for root, _, files in os.walk(local_path):

        # Create remote directories if they don't exist
        try:
            sftp.stat(remote_path)  # Check if exists
        except FileNotFoundError:
            sftp.mkdir(remote_path)

        # Upload all files in the directory
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace("\\", "/")
            if os.path.basename(remote_file)!='local_file_list.txt':
                if np.sum(os.path.basename(local_file)==skip_file)==0:#file was never transfered
                    try:
                        remote_size=sftp.stat(remote_file).st_size
                    except FileNotFoundError:#file does not exist on SFTP server
                        logging.info(f"Uploading {os.path.basename(local_file)} -> {remote_file}")
                        sftp.put(local_file, remote_file)
                        continue
                    if remote_size!=os.path.getsize(local_file):#file does exists on SFTP server, but size is not matching
                        logging.info(f"Re-uploading {os.path.basename(local_file)} -> {remote_file}. Size not matching.")
                        sftp.put(local_file, remote_file)
                    else:#file exists on SFTP server and size matches
                        logging.info(f"{os.path.basename(local_file)} already exists on SFTP server.")
                else:
                    file_id=np.where(os.path.basename(local_file)==skip_file)[0][0]
                    if os.path.getsize(local_file)!=skip_size[file_id]:#file was transfered to final location, but incompletely
                        logging.info(f"Re-uploading {os.path.basename(local_file)} -> {remote_file}. Size not matching.")
                        sftp.put(local_file, remote_file)
                    else:#file was already sent to final location
                        logging.info(f"{os.path.basename(local_file)} already exists on final location.")
                        file_age= (time.time()-os.path.getmtime(local_file))/(3600*24)
                        if file_age>config['time_delete']:#file can be deleted
                            logging.info(f"Deleting {os.path.basename(local_file)} because it is {str(np.round(file_age,1))} days old.")
                            os.remove(local_file)
            
#%% Initialization
#config
with open(source_config, 'r') as fid:
    config = yaml.safe_load(fid)

# Establish SSH transport
transport = paramiko.Transport((config['host'], config['port']))
transport.connect(username=config['username'], password=config['password'])
sftp = paramiko.SFTPClient.from_transport(transport)

#setup logger
os.makedirs(os.path.join(cd,config['log_dir']),exist_ok=True)
logfile=os.path.join(cd,config['log_dir'],datetime.strftime(datetime.now(), '%Y%m%d.%H%M%S'))+'_ftp_push.log'

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
 
#%% Main

#pull file list
try:
    sftp.get(os.path.join(config['remote_dir'],'local_file_list.txt'),  os.path.join(config['push_dir'],'local_file_list.txt'))
    with open(os.path.join(config['push_dir'],'local_file_list.txt'),'r') as fid:
        skip=np.array(fid.read().split('\n'))
        l=np.array([len(s) for s in skip])
        skip=skip[l>0]
    skip_file=np.array([s.split(',')[0] for s in skip])
    skip_size=np.array([int(s.split(',')[1]) for s in skip])
except FileNotFoundError:
    logging.info('No local file list found')
    skip_file=np.array([])
    skip_size=np.array([])

#push local files
upload_directory(sftp, config['push_dir'], config['remote_dir'],skip_file,skip_size)
logging.info("Upload completed successfully.")

#terminate
sftp.close()
transport.close()
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)