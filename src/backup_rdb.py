#!/usr/bin/python
#
# back_rdb
# Un script copie les donnees redis a dropbox
#
# Copyright Nancy Robertson 2017.
#
import sys
import datetime
import os
import dropbox
import argparse
import shutil
import redis

###
# Trigger redis to export its datastore
# And upload it to the dropbox account
def save_and_upload() :
    filename = 'dump.rdb'

    # Ensure the local_folder exists
    if not os.path.isdir(args.local_folder):
        os.mkdir(args.local_folder)

    att_path = os.path.join(args.local_folder, filename)
    if args.verbose >= 1:
        print '\tfilename: %s' % (filename)

    if not args.no_metadata:
        redis_connection = redis.StrictRedis("redis")
        redis_connection.save()
        
    if not args.local_only:
        if args.verbose >= 1:
            print 'uploading: ', filename
    if not args.local_only:
        dbx = dropbox.Dropbox(args.dbx_token)
        f = open(os.path.join(args.local_folder, filename), 'rb')
        response = dbx.files_upload(f.read(),os.path.join(args.dbx_folder,filename))
        if args.verbose >= 1:
            print "uploaded: ", response
        else :
            return False

    return True

##########################################
# Main

# Get your app key and secret from the Dropbox developer website
app_key = os.environ['CRON_DROP_KEY']
app_secret = os.environ['CRON_DROP_SECRET']

parser = argparse.ArgumentParser(
    description='Lis les messages et uploade les fichiers attaches a dropbox.')
parser.add_argument('--version', '-V', action='version', version='%(prog)s 0.1')
parser.add_argument('--dbx_token', '-t', action='store', 
    help='the access_token for a known dropbox account.')
parser.add_argument('--dbx_folder', '-f', action='store', 
    default='/redis_data',
    help='the dropbox folder to store redis file.')
parser.add_argument('--local_folder','-l', action='store', 
    default='/data',
    help='the local folder to store attachments.')
parser.add_argument('--local_only', '-o', action='store_true',
    help='do not upload the pictures to dropbox')
parser.add_argument('--no_metadata', '-M', action='store_true',
    help='do not store metadata in redis')    
parser.add_argument('--verbose', '-v', action='count',
    help='increase verbosity')

args = parser.parse_args()
if args.verbose >= 2:
    print "Verbosity level: %d " % (args.verbose)
save_and_upload()

