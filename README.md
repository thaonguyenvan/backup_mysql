Backup mysql script use python3

# Requirement
- Ubuntu / CentOS
- python 3
- git 
- crontab
- rsync (optional)

# Feature

- Backup mysql database.
- Backup all database.
- Backup table(s).
- Send notify to Telegram, Slack, Email.
- Auto sync to FTP server (require install rsync and ssh less between 2 servers).
- Remove old file and folder in **x** day.

# How to (Example with CentOS 7)

### 1. Install requirement packages

```
yum groupinstall "Development Tools" -y
yum install git -y
```

### 2. Install python 3.6

```
yum install https://centos7.iuscommunity.org/ius-release.rpm -y
yum install python-devel -y
yum install python36-devel -y
yum install python36 -y

yum install python-pip -y
yum install python36u-pip -y
pip3.6 install virtualenv
```

### 3. Clone this Repo

```
cd /opt/
git clone https://github.com/huytm/backup_mysql.git
```

### 4. Create virtual environmet and install required python lib

```
cd /opt/backup_mysql
virtualenv env
source env/bin/activate
pip install -r requirement.txt
```

### 5. Edit setting file with your purpose

> Some example you can fint at here: [Example](https://github.com/huytm/backup_mysql/blob/master/example/example.md)

Edit file setting at  `/opt/backup_mysql/settings/settings.json`.

```json
{
    "mysql": {
        "user": "MYSQL_USER",
        "password": "MYSQL_PASSWORD",
        "backup_type": "table", 
        "database": "MYSQL_DATABASES",
        "tables": "table1, table2, table3"
    },
    "backup": {
        "backup_s3": false,
        "backup_folder": "/your/backup/folder",
        "backup_file_name": "your_back_up_file_name",
        "s3_endpoint":"s3.cloud365.vn",
        "s3_access_key":"ACCESS_KEY",
        "s3_secret_key":"SECRET_KEY",
        "s3_bucket":"your_bucket_name"
    },
    "delete_old_file": {
        "delete_old_file": true,
        "remove_days": 10
    },
    "sync": {
        "sync": false,
        "ftp_server": "10.10.10.10",
        "remote_sync_path": "/backup/folder/in/ftp/server"
    },
    "telegram": {
        "send_notify": true,
        "token": "your_telegram_token",
        "chat_id": "your_telegram_chat_id"
    },
    "slack": {
        "send_notify": true,
        "token": "your_slack_token",
        "channel": "your_slack_channel"
    },
    "email": {
        "send_notify": true,
        "smtp_server": "your_smtp_server",
        "smtp_user": "your_user_email@your_smtp_server",
        "smtp_password": "your_email_password",
        "smtp_from": "This is sender <your_user_email@your_smtp_server>",
        "smtp_TLS": true,
        "smtp_port": 587,
        "email_subject": "Test backup report {}",
        "receiver_email": "to_email"
    }
}
```

(Note)

**a. backup_type - The type of backup (kiểu backup) include:**

- all : `Backup all database.`

- database : `Backup 1 database.`

- table : `Backup table(s).`

**b. Extended feature:**

- "container": true / false
    ```
    MySQL is running on container or not. If settings is true, you must specify other information about container name of running MySQL/MariaDB.
    ```

- "backup_s3": true / false
    ```
    Backup to s3 or not. If settings is true, you must specify some other information about s3 access and secret key.
    ```

- "sync": true / false 

    ```
    sync backup folder with ftp server or not. If setting is true, 2 servers must installed rsync and SSH less.
    ```

- "send_notify": true / false 

    ```
    Slack (Telegram, email) notify or not
    ```

- "delete_old_file": true / false

    ```
    Delete old file and folder in "remove_days" days or not.
    ```


### 6. Add script to crontab

```
crontab -e
```

Add the following line, notice the path of `env` and `run_backup.py` file


```
0 */2 * * * source /opt/backup_mysql/env/bin/activate && python /opt/backup_mysql/run_backup.py
```

