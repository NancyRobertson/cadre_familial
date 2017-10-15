#!/usr/bin/python
#
# Cadre Familial
# Un script qui ajoute a un dossier dropbox les images trouvees dans 
# une boite aux lettres IMAP.
#
# Family Frame
# A script to populate a dropbox folder with attachments from an imap mailbox
#
# Copyright Nancy Robertson, 2016.
#
# Includes public domain work from RKI July 2013
# Ref: http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/
#
#
# NR 2017/10/13 Get dropbox app key and secret from environment
# NR 2017/10/13 Require dropbox token to be passed in as param
#
import sys
import imaplib
import getpass
import email
import email.header
import datetime
import os
import dropbox
import argparse
import shutil
import redis

# Get your app key and secret from the Dropbox developer website
app_key = os.environ['CRON_DROP_KEY']
app_secret = os.environ['CRON_DROP_SECRET']

parser = argparse.ArgumentParser(
    description='Lis les messages et uploade les fichiers attaches a dropbox.')
parser.add_argument('--version', '-V', action='version', version='%(prog)s 0.1')
parser.add_argument('--dbx_token', '-t', action='store', 
    help='the access_token for a known dropbox account.')
parser.add_argument('--dbx_folder', '-f', action='store', 
    default='/slideshow',
    help='the folder to store the attachments in the dropbox account.')
parser.add_argument('--email_account', '-e', action='store', 
    help='where to read the messages from')
parser.add_argument('--password', '-p', action='store', 
    help='the password for the email account')
parser.add_argument('--email_mailbox','-m', action='store',
    default='INBOX',
    help='the mailbox to process.')
parser.add_argument('--email_all', '-a', action='store_const', 
    dest='email_search',
    const='ALL',
    default='(UNSEEN)',
    help='process all messages in specified mail folder rather than just the unseen ones.')
parser.add_argument('--local_folder','-l', action='store', 
    default='cadre_attach',
    help='the local folder to store attachments.')
parser.add_argument('--cleanup_local_folder','-c', action='store_true', 
    help='delete the local folder and attachments on termination.')
parser.add_argument('--local_only', '-o', action='store_true',
    help='do not upload the pictures to dropbox')
parser.add_argument('--no_metadata', '-M', action='store_true',
    help='do not store metadata in redis')
parser.add_argument('--verbose', '-v', action='count',
    help='increase verbosity')
parser.add_argument('--email_max', '-x', type=int,
    help='the maximum number of messages to process in this run.')
parser.add_argument('--email_search_expr', action='store', 
    dest='email_search',
    help='specify IMAP search expression for the messages to process.')

args = parser.parse_args()

if not args.password:
    args.password= getpass.getpass('Password ('+args.email_account+'): ')
    #args.password= getpass.getpass('Password :')

def exists(path):
    try:
        dbx.files_get_metadata(path)
        return True
    except:
        return False


def process_part(part, redis_connection, message_id) :
    if part.get_content_maintype() == 'multipart':
        return False
    if part.get('Content-Disposition') is None:
        return False

    filename = part.get_filename()
    if filename is None:
        print "Attachment has no filename"
        return False

    att_path = os.path.join(args.local_folder, filename)
    if args.verbose >= 2:
        print '\tfilename: %s' % (filename)

    if not os.path.isfile(att_path) :
        fp = open(att_path, 'wb')
        fp.write(part.get_payload(decode=True))
        fp.close()

    if not args.no_metadata:
        redis_connection.sadd( "message_attach:"+message_id, filename)
    if not args.local_only:
        if not exists(os.path.join(args.dbx_folder,filename)) :
            if args.verbose >= 1:
                print 'uploading: ', filename
            f = open(os.path.join(args.local_folder, filename), 'rb')
            response = dbx.files_upload(f.read(),os.path.join(args.dbx_folder,filename))
            if args.verbose >= 1:
                print "uploaded: ", response
        else :
            return False

    return True


def process_message(num, msg) :
    # extract header Subject field
    decode = email.header.decode_header(msg['Subject'])[0]
    subject = unicode("")
    if decode[1]:
            subject = unicode(decode[0],decode[1])
    else:
            subject = unicode(decode[0])
            
    # extract header From field
    decode = email.header.decode_header(msg['From'])[0]
    from_h = unicode("")
    if decode[1]:
            from_h = unicode(decode[0],decode[1])
    else:
            from_h = unicode(decode[0])
            
    # extract header Message-ID field
    decode = email.header.decode_header(msg['Message-ID'])[0]
    message_id = unicode("")
    if decode[1]:
            message_id = unicode(decode[0],decode[1])
    else:
            message_id = unicode(decode[0])
            
    # extract header To field
    decode = email.header.decode_header(msg['To'])[0]
    header_to = unicode("")
    if decode[1]:
            header_to = unicode(decode[0],decode[1])
    else:
            header_to = unicode(decode[0])
            
    if args.verbose >= 1:
        print 'Message %s (%s): %s  from %s' % (num, message_id, subject, from_h)
    # Now convert to local date-time
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(
            email.utils.mktime_tz(date_tuple))
        if args.verbose >= 1:
            print "Local Date:", local_date.strftime("%a, %d %b %Y %H:%M:%S")
    if not args.no_metadata:
        redis_connection = redis.StrictRedis("redis")
        redis_connection.hmset( "message:"+message_id, {'From':from_h, 'Subject':subject, 'Date': local_date.strftime("%a, %d %b %Y %H:%M:%S"), 'To': header_to})
    
    if msg.get_content_maintype() != 'multipart':
            return
    count_parts = 0;
    for part in msg.walk():
        if process_part(part, redis_connection, message_id):
            count_parts += 1
    if args.verbose >= 1:
        print 'Has %d attachments' % (count_parts)

    return


def process_mailbox(M):
    """
    Do something with emails messages in the folder.
    For the sake of this example, print some headers.
    """

    rv, data = M.search(None, args.email_search)
    if rv != 'OK':
        print "No messages found!"
        return

    messages_processed = 0
    for num in data[0].split():
        if args.verbose >= 1:
            print ""
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print "ERROR getting message", num
            return

        msg = email.message_from_string(data[0][1])
        process_message(num, msg)
        messages_processed += 1
        if args.email_max > 0 and messages_processed >= args.email_max:
            print "Maximum number of messages (%d) reached. Exiting." % (messages_processed)
            return
    return


if args.verbose >= 2:
    print "Verbosity level: %d " % (args.verbose)


M = imaplib.IMAP4_SSL('imap.gmail.com')

# Ensure the local_folder exists
if not os.path.isdir(args.local_folder):
    os.mkdir(args.local_folder)

try:
    rv, data = M.login(args.email_account, args.password)
except imaplib.IMAP4.error:
    type, value, traceback = sys.exc_info()
    print "LOGIN FAILED!!! "
    print('Error value %s' % (value))
    print traceback
    sys.exit(1)

if args.verbose >= 1:
    print rv, data

rv, data = M.select(args.email_mailbox)
if rv == 'OK':
    if args.verbose >= 1:
        print "Processing mailbox %s\n" % args.email_mailbox
    if not args.local_only:
        dbx = dropbox.Dropbox(args.dbx_token)

    process_mailbox(M)
    M.close()
    if args.cleanup_local_folder:
        shutil.rmtree(args.local_folder)
else:
    print "ERROR: Unable to open mailbox ", rv

M.logout()


