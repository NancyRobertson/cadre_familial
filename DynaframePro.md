* Install latest dynaframePro image from [Geektoolkit's post on Patreon](https://www.patreon.com/Geektoolkit/posts) on raspberry Pi (min RAM 2GB)
* Setup WIFI
  * Connect phone to WIFI SSID DynaFramePro XXX
  * Select Home SSID
  * Enter password
* Make frame horizontal
  * Browse to IP of frame
  * Choose Settings page from hamburger menu
  * In Other Settings, set Rotation to 0°
* Change user pi's default password from `dynaframe` to something more secure
* Reading gmail...
  * Ref: http://frostyx.cz/posts/synchronize-your-2fa-gmail-with-mbsync
  * `sudo apt-get install isync`
  * create .mbsyncrc file
```
IMAPStore gmail-remote
Host imap.gmail.com
SSLType IMAPS
AuthMechs LOGIN
User n****n.estarling2@gmail.com
Pass ****

MaildirStore gmail-local
Path ~/Mail/gmail/
Inbox ~/Mail/gmail/INBOX
Subfolders Verbatim


Channel gmail
Master :gmail-remote:
Slave :gmail-local:
Create Both
Expunge Both
Patterns * !"[Gmail]/All Mail" !"[Gmail]/Important" !"[Gmail]/Starred" !"[Gmail]/Bin"
SyncState *

```
  * `mkdir -p ~/Mail/gmail/INBOX`
  * `mbsync gmail`

* Extract attachments
  * Ref: https://manpages.debian.org/testing/maildir-utils/mu-easy.1.en.html
  * Ref: https://manpages.debian.org/testing/maildir-utils/mu-extract.1.en.html
  * Ref: https://unix.stackexchange.com/questions/649525/how-to-view-an-email-message-file-located-in-a-maildir-from-the-command-line
  * Install maildir-utils (whichever version is available as a package for raspbian it is 1.0)
    * `sudo apt-get install maildir-utils`
  * After reading mail, index it
    * `mu index --maildir=~/Mail`
  * extract attachments from all messages
    * `mkdir -p ~/Pictures/Estarling`
    * `mu find  flag:attach --skip-dups --fields="l" --exec='mu extract --save-attachments --target-dir=~/Pictures/Estarling --overwrite'`

# DynaframePro Extra Doc
## Included
* Swap in September 2022 release
  * https://pimylifeup.com/raspberry-pi-swap-file/

## Install on existing PI
Extract it based on distributed image...

Copy the Dynaframe folder, copy it to your image, sudo bash deps.sh and then sudo chmod +x Dynaframe and you should be able to launch it on your custom image
