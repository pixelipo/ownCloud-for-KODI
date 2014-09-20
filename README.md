XBMC-ownCloud
=============

An ownCloud Video/Music add-on for XBMC

A video add-on for XBMC that enables playback of video and music files stored in a ownCloud account.

- tested with ownCloud 6
- public test servers (where I have tested)
	- https - my.owndrive.com; cloudu.de
	- http - owncloud.arvixe.com

Session handling has been generalized to work on multiple server platforms, but may not work on your ownCloud installation.

Your username and password are the ones you use to log into your ownDrive account.

The domain is the domain or IP that you use to get to your ownDrive account (it can be a domain like my.owndrive.com, a subomain like mysub.owncloud.arvixe.com, or even an IP address)
- do not prefix the domain with any protocol (no http://, etc) and don't tail it with anything (no /location/)

Supports [Tested on]:
All XBMC 12 and 12.2 including Linux, Windows, OS X, Android, Pivos, iOS (including ATV2)

*Note for Raspberry Pi users*: Due to a bug in libcurl with HTTPS streams, playback of content on these devices may not work.  I have tested on various Raspberry Pi distributions and have personally witnessed about a 90% failure rate for playback of videos over HTTPS.  HTTP is unaffected.  "Disk Cache", when implemented, will bypass this problem.  It is not implemente at this time.

Getting Started:
1) download the .zip file
2) transfer the .zip file to XBMC
3) in Video Add-on, select Install from .zip

Before starting the add-on for the first time, either "Configure" or right click and select "Add-on Settings".  Enter your fully-qualified Username (including @gmail.com or @domain) and Password.

Features and limitations:
- will index videos, music and folders in your ownCloud account
- no pictures at this time

How to use:
- starting the plugin via video or audio add-ons will display a directory containing all video files within the ownCloud account or those that are shared to that account
- click on the video or music file to playback

Calling this plugin using STRM files or other plugins:

See https://github.com/ddurdle/XBMC-ownCloud/wiki/-Add-on-API


FAQ:

1) Is there support for multiple accounts?
Not at this time

2) Does thie add-on support Pictures or other filetypes?
Music and video files are supported; pictures/images or anyother file type is not.


Roadmap to future releases:

See https://github.com/ddurdle/XBMC-ownCloud/wiki/Roadmap

