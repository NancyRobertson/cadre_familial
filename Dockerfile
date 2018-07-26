# NR 2017/10/12 Add chmod for cadre_familial.py
# NR 2017/10/12 Add package tzdata
# NR 2017/10/13 Pass credentials as environment variables

FROM ubuntu:latest

# Install dependencies
RUN apt-get update -y
RUN apt-get install cron
RUN apt-get install python -y
RUN apt-get install python-pip -y
RUN pip install dropbox
RUN pip install redis

# will be using the timezone from the host via a volume to match redis:alpine behavior
RUN rm /etc/localtime

# Workaround for pam security issue
# Ref: https://stackoverflow.com/questions/43323754/cannot-make-remove-an-entry-for-the-specified-session-cron
RUN sed -i '/session    required     pam_loginuid.so/c\#session    required   pam_loginuid.so' /etc/pam.d/cron

# Add python scripts
ADD cadre_familial.py /usr/local/bin/cadre_familial.py
ADD src/backup_rdb.py /usr/local/bin/backup_rdb.py
RUN chmod a+x /usr/local/bin/*.py

RUN (crontab -l ; echo "* * * * * . /usr/local/etc/cadre_familial.env; echo "Hello \$CRON2_ACCOUNT"  > /proc/1/fd/1 2>/proc/1/fd/2") | crontab
RUN (crontab -l ; echo "0,15,30,45 * * * * . /usr/local/etc/cadre_familial.env; date > /proc/1/fd/1 2>/proc/1/fd/2 ; /usr/local/bin/cadre_familial.py -v --local_folder e_tmp --cleanup_local_folder --email_account \${CRON1_ACCOUNT} --password \${CRON1_PASSWORD} --dbx_token \$CRON_DBX_TOKEN > /proc/1/fd/1 2>/proc/1/fd/2") | crontab
RUN (crontab -l ; echo "*/7 * * * * . /usr/local/etc/cadre_familial.env; date > /proc/1/fd/1 2>/proc/1/fd/2; /usr/local/bin/cadre_familial.py -v --local_folder c_tmp --cleanup_local_folder --email_account \$CRON2_ACCOUNT --password \$CRON2_PASSWORD --dbx_token \$CRON_DBX_TOKEN > /proc/1/fd/1 2>/proc/1/fd/2") | crontab
RUN (crontab -l ; echo "*/3 * * * * . /usr/local/etc/cadre_familial.env; date > /proc/1/fd/1 2>/proc/1/fd/2; /usr/local/bin/cadre_familial.py -v --local_folder c3_tmp --cleanup_local_folder --email_account \$CRON3_ACCOUNT --password \$CRON3_PASSWORD --dbx_token \$CRON_DBX_TOKEN3 > /proc/1/fd/1 2>/proc/1/fd/2") | crontab
RUN (crontab -l ; echo "27,57 * * * * . /usr/local/etc/cadre_familial.env; date > /proc/1/fd/1 2>/proc/1/fd/2 ; /usr/local/bin/backup_rdb.py -v --dbx_token \$CRON_DBX_TOKEN > /proc/1/fd/1 2>/proc/1/fd/2") | crontab

# Run the command on container startup
CMD printenv | sed 's/^\(.*\)$/export \1/g'| grep -E "^export CRON">/usr/local/etc/cadre_familial.env; cron -f
