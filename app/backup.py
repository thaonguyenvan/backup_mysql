import os
import time
import datetime
import boto
import boto.s3.connection
from boto.s3.key import Key
from .slack_notify import Slack
from .telegram_notify import Telegram
from .email_notify import EmailNotify
import logging
from utils import common

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename='/var/log/backup.log',level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

class Backup(object):
    def __init__(self, settings):
        self.settings = settings
        self.db_user_name           = settings["mysql"]["user"]
        self.db_password            = settings["mysql"]["password"]
        self.database               = settings["mysql"]["database"]
        self.tables                 = settings["mysql"]["tables"]
        self.output_startw          = settings["backup"]["backup_file_name"]
        self.backup_folder          = settings["backup"]["backup_folder"]
        self.slack_token            = settings["slack"]["token"]
        self.slack_channel          = settings["slack"]["channel"]
        self.telegram_token         = settings["telegram"]["token"]
        self.telegram_channel       = settings["telegram"]["chat_id"]
        self.is_sync                = settings["sync"]["sync"]
        self.is_delete_file         = settings["delete_old_file"]["delete_old_file"]
        self.is_send_notify_telegram   = settings["telegram"]["send_notify"]
        self.is_send_notify_slack   = settings["slack"]["send_notify"]
        self.is_sendmail            = settings["email"]["send_notify"]
        self.backup_type            = settings["mysql"]["backup_type"]
        self.backup_s3              = settings["backup"]["backup_s3"]
        self.s3_endpoint            = settings["backup"]["s3_endpoint"]
        self.s3_access_key          = settings["backup"]["s3_access_key"]
        self.s3_secret_key          = settings["backup"]["s3_secret_key"]
        self.s3_bucket              = settings["backup"]["s3_bucket"]
        self.container              = settings["backup"]["container"]
        self.container_name         = settings["backup"]["container_name"]

        self.notify_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.backup_folder + "/" + self.current_date
        self.backup_dir = self.backup_folder + "/" + self.current_date



    def backup_database(self):
        backup_dir = self.backup_folder + "/" + self.current_date
        create_backup_dir = "mkdir -p "+ backup_dir
        backup_command = self.get_command_backup(backup_dir)

        try:
            os.system(create_backup_dir)
            os.system(backup_command)

            backup_size = common.check_file_size(backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz")
            if self.is_delete_file is True:
                common.remove_old_folder(self.settings)
            if self.is_sync is True:
                common.sync_to_ftp(self.settings)
            if self.is_send_notify_telegram is True:
                telegram_message = common.render_message_telegram(datetime=self.notify_date, file_size=backup_size,
                                                                    file_name=self.output_startw + "_" + self.current_time +".sql.gz" )
                telegram = Telegram(self.telegram_token, self.telegram_channel, telegram_message)
                telegram.send_message()
            if self.is_send_notify_slack is True:
                slack_message = common.render_message_telegram(datetime=self.notify_date, file_size=backup_size,
                                                                    file_name=self.output_startw + "_" + self.current_time +".sql.gz" )
                slack = Slack(self.slack_token , self.slack_channel, slack_message)
                slack.send_message()

            if  self.is_sendmail is True:
                sendmail_message = common.render_message_email(datetime=self.notify_date, file_size=backup_size, file_name=self.output_startw + "_" + self.current_time +".sql.gz")
                sendmail = EmailNotify(self.settings, self.notify_date, sendmail_message)
                sendmail.send_email()

            if self.backup_s3 is True:
                file_name=self.output_startw + "_" + self.current_time +".sql.gz"
                try:
                    conn = boto.connect_s3(
                        aws_access_key_id = self.s3_access_key,
                        aws_secret_access_key = self.s3_secret_key,
                        host = self.s3_endpoint,
                        is_secure=True,               # uncomment if you are not using ssl
                        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
                        )

                    bucket = conn.get_bucket(self.s3_bucket)

                    k = bucket.new_key(file_name)
                    k.set_contents_from_filename(backup_dir + "/" + file_name)
                    # key = bucket.get_key('IMG_4020-1.jpg')
                    # key.get_contents_to_filename('/home/thaonv/test.txt')
                    # key.set_canned_acl('public-read')
                    # url = key.generate_url(0, query_auth=False, force_http=True)

                except Exception as ex:
                    logging.warning("backup " + ex)

        except Exception as ex:
            logging.warning("backup " + ex)


    def get_command_backup(self, backup_dir):
        if self.container is True:
            if self.backup_type == "database":
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + self.database + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " " + self.database + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            if self.backup_type == "table":
                backup_table = (self.tables).strip().replace(",", "")
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + self.database + " " + backup_table + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " " + self.database + " " + backup_table + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            if self.backup_type == "all":
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + "--all-databases" + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "docker exec" + self.container_name + "mysqldump -u" + self.db_user_name + " " + "--all-databases" + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            return backup_command
        else:
            if self.backup_type == "database":
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + self.database + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "mysqldump -u" + self.db_user_name + " " + self.database + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            if self.backup_type == "table":
                backup_table = (self.tables).strip().replace(",", "")
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + self.database + " " + backup_table + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "mysqldump -u" + self.db_user_name + " " + self.database + " " + backup_table + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            if self.backup_type == "all":
                if (self.db_password).strip() != '' and self.db_password is not None:
                    backup_command = "mysqldump -u" + self.db_user_name + " -p" + "'" + self.db_password + "'" + " " + "--all-databases" + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
                else:
                    backup_command = "mysqldump -u" + self.db_user_name + " " + "--all-databases" + " 2>/dev/null | gzip > " + backup_dir + "/"+ self.output_startw + "_" + self.current_time +".sql.gz"
            return backup_command
