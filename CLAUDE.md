# ftp_transfer

Lightweight automation tool for bidirectional SFTP file synchronization. Supports push (local → remote) and pull (remote → local) workflows with local caching, size guards, and automatic cleanup.

## Structure

```
ftp_transfer/
├── sftp_push.py          # Upload local files to remote SFTP
├── sftp_pull.py          # Download remote files to local storage
├── configs/              # YAML configuration files (excluded from git)
│   ├── config.yaml
│   └── config_windcube_rtd.yaml
├── data/                 # Local data storage
└── log/                  # Timestamped log files
```

## Running

```bash
python sftp_push.py                          # uses configs/config.yaml
python sftp_pull.py                          # uses configs/config_windcube_rtd.yaml
python sftp_pull.py configs/other.yaml       # custom config
```

No installation required. Scripts are run directly.

## Configuration

YAML files in `configs/` (excluded from git via `.gitignore`). Key fields:

| Field | Description |
|---|---|
| `host`, `username`, `password`, `port` | SFTP credentials |
| `remote_dir` | Remote path on server |
| `push_dir` | Local source directory for push |
| `pull_dir` | Local destination directory for pull |
| `log_dir` | Directory for log files |
| `time_delete` | Days after which transferred local files are deleted |
| `max_size` | Max file size in bytes to upload (default 200 MB) |
| `max_age` | Max file age in days to be eligible for upload (push only) |
| `filename_filters` | List of substrings; filename must contain at least one to be uploaded (push only, empty = no filter) |

## Key Logic

**Push (`sftp_push.py`):**
- Reads `local_file_list.txt` from the remote to know which files were already uploaded (idempotency).
- Skips files exceeding `max_size`, older than `max_age`, or whose filename matches none of `filename_filters`.
- Verifies size match between local and remote after upload to detect incomplete transfers.
- Deletes local files older than `time_delete` days after successful upload.
- Updates `local_file_list.txt` on remote at the end of each run.

**Pull (`sftp_pull.py`):**
- Downloads all files from a flat remote directory (no recursion).
- Deletes remote files after download.
- Writes a `local_file_list.txt` (filename + size pairs) and uploads it back to the server.

## Dependencies

No lock file. Key third-party packages:

- `paramiko` — SSH/SFTP client
- `pyyaml` — YAML config parsing
- `numpy` — used in file tracking logic

## Conventions

- No classes — purely functional, procedural scripts.
- Logs written to `log/` as `YYYYMMDD.HHMMSS_ftp_{push|pull}.log`.
- Config is injected at the top of each script run; `sftp_pull.py` accepts an optional CLI argument for the config path.
