# -*- coding: utf-8 -*-
"""
Push a file to a remote server via SCP.
"""

import os
cd=os.getcwd()
import sys
import paramiko
from scp import SCPClient
import yaml
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

#%% Inputs
if len(sys.argv)==1:
    source_config=os.path.join(cd,'configs','config_kestrel.yaml')
else:
    source_config=sys.argv[1]

#%% Initialization
#config
with open(source_config, 'r') as fid:
    config = yaml.safe_load(fid)

#logger
os.makedirs(os.path.join(cd,config['log_dir']),exist_ok=True)
logfile=os.path.join(cd,config['log_dir'],datetime.strftime(datetime.now(), '%Y%m%d.%H%M%S'))+'_scp_push.log'

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#SSH connection
ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(config['host'], port=config['port'], username=config['username'], password=config['password'])

#%% Main
remote_path=f"{config['destination']}/{os.path.basename(config['filename'])}"
logging.info(f"Uploading {config['filename']} -> {config['host']}:{remote_path}")

with SCPClient(ssh.get_transport()) as scp:
    scp.put(config['filename'], remote_path=config['destination'])

logging.info("Upload completed successfully.")

#terminate
ssh.close()
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
