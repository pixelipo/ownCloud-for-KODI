'''
    owncloud XBMC Plugin
    Copyright (C) 2013 dmdsoftware

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

import os
import re
import urllib, urllib2
import cookielib


import xbmc, xbmcaddon, xbmcgui, xbmcplugin

# global variables
PLUGIN_NAME = 'plugin.video.owncloud'
PLUGIN_URL = 'plugin://'+PLUGIN_NAME+'/'
ADDON = xbmcaddon.Addon(id=PLUGIN_NAME)


# helper methods
def log(msg, err=False):
    if err:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(ADDON.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)


#
#
#
class owncloud7:


    MEDIA_TYPE_MUSIC = 1
    MEDIA_TYPE_VIDEO = 2
    MEDIA_TYPE_FOLDER = 0

    CACHE_TYPE_MEMORY = 0
    CACHE_TYPE_DISK = 1
    CACHE_TYPE_AJAX = 2

    ##
    # initialize (setting 1) username, 2) password, 3) authorization token, 4) user agent string
    ##
    def __init__(self, user, password, protocol, domain, auth, session, user_agent):
        self.user = user
        self.password = password
        self.user_agent = user_agent
        self.protocol = protocol
        self.domain = domain
        self.cookiejar = cookielib.CookieJar()
        self.auth = auth
        self.session = session

        return


    ##
    # perform login
    ##
    def login(self):

        self.auth = ''
        self.session = ''

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        # default User-Agent ('Python-urllib/2.6') will *not* work
        opener.addheaders = [('User-Agent', self.user_agent)]

        url = self.protocol + self.domain +'/'

        try:
            response = opener.open(url)

        except urllib2.URLError, e:
            log(str(e), True)
            return
        response_data = response.read()
        response.close()

        requestToken = None
        #owncloud7
        for r in re.finditer('name=\"(requesttoken)\" value\=\"([^\"]+)\"',
                             response_data, re.DOTALL):
            requestTokenType,requestToken = r.groups()

        url = self.protocol + self.domain + '/index.php'


        values = {
                  'password' : self.password,
                  'user' : self.user,
                  'remember_login' : 1,
                  'requesttoken' : requestToken,
                  'timezone-offset' : -4,
        }

        log('logging in')

        # try login
        try:
            response = opener.open(url,urllib.urlencode(values))

        except urllib2.URLError, e:
            if e.code == 403:
                #login denied
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30017))
            log(str(e), True)
            return
        response_data = response.read()
        response.close()


        loginResult = 0
        #validate successful login
        for r in re.finditer('(data-user)\=\"([^\"]+)\"',
                             response_data, re.DOTALL):
            loginType,loginResult = r.groups()

        if (loginResult == 0 or loginResult != self.user):
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30017))
            log('login failed', True)
            return

        for cookie in self.cookiejar:
            for r in re.finditer(' ([^\=]+)\=([^\s]+)\s',
                        str(cookie), re.DOTALL):
                cookieType,cookieValue = r.groups()
                if cookieType == 'oc_token':
                    self.auth = cookieValue
                elif cookieType != 'oc_remember_login' and cookieType != 'oc_username':
                    self.session = cookieType + '=' + cookieValue


        return


    ##
    # return the appropriate "headers" for owncloud requests that include 1) user agent, 2) authorization cookie
    #   returns: list containing the header
    ##
    def getHeadersList(self):
        if (self.auth != '' or self.session != 0):
            return [('User-Agent', self.user_agent), ('Cookie', self.session+'; oc_username='+self.user+'; oc_token='+self.auth+'; oc_remember_login=1')]
        else:
            return [('User-Agent', self.user_agent )]

    ##
    # return the appropriate "headers" for owncloud requests that include 1) user agent, 2) authorization cookie
    #   returns: URL-encoded header string
    ##
    def getHeadersEncoded(self):
        if (self.auth != '' or self.session != 0):
            return urllib.urlencode({ 'User-Agent' : self.user_agent, 'Cookie' : self.session+'; oc_username='+self.user+'; oc_token='+self.auth+'; oc_remember_login=1' })
        else:
            return urllib.urlencode({ 'User-Agent' : self.user_agent })

    ##
    # retrieve a list of videos, using playback type stream
    #   parameters: prompt for video quality (optional), cache type (optional)
    #   returns: list of videos
    ##
    def getVideosList(self, folderName='', cacheType=CACHE_TYPE_MEMORY):

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        opener.addheaders = self.getHeadersList()

        url = self.protocol + self.domain +'/index.php/apps/files/ajax/list.php?'+ urllib.urlencode({'dir' : folderName})+'&sort=name&sortdirection=asc'

        # if action fails, validate login
        try:
            response = opener.open(url)
        except urllib2.URLError, e:
            log(str(e), True)
            return
        response_data = response.read()
        response.close()

        loginResult = 0
        #validate successful login
        for r in re.finditer('(data-user)\=\"([^\"]+)\" data-requesttoken="([^\"]+)"',
                             response_data, re.DOTALL):
            loginType,loginResult,requestToken = r.groups()

        if (loginResult == 0 or loginResult != self.user):
            self.login()
            try:
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
                opener.addheaders = self.getHeadersList()
                response = opener.open(url)
                response_data = response.read()
                response.close()
            except urllib2.URLError, e:
              log(str(e), True)
              return
        videos = {}
        # parsing page for files
        for r in re.finditer('\[\{.*?\}\]' ,response_data, re.DOTALL):
          entry = r.group()

          for s in re.finditer('\{.*?\}' ,entry, re.DOTALL):
            item = s.group()

            for q in re.finditer('\"id\"\:\"([^\"]+)\".*?\"name\"\:\"([^\"]+)\".*?\"mimetype\"\:\"([^\/]+)\/.*?\"type\"\:\"([^\"]+)\"' ,item, re.DOTALL):
                fileID,fileName,fileType,contentType = q.groups()

            # Undo any urlencoding before displaying the files (should also make the folders accessible)
            fileName = urllib.unquote(fileName)

            log('found video %s %s' % (fileID, fileName))

            if fileType == 'video\\':
                fileType = self.MEDIA_TYPE_VIDEO
            elif fileType == 'audio\\':
                fileType = self.MEDIA_TYPE_MUSIC

            if contentType == 'dir':
                videos[fileName] = {'url':  'plugin://plugin.video.owncloud?mode=folder&directory=' + urllib.quote_plus(folderName+'/'+fileName), 'mediaType': self.MEDIA_TYPE_FOLDER}
            elif cacheType == self.CACHE_TYPE_MEMORY:
                videos[fileName] = {'url': self.protocol + self.domain +'/index.php/apps/files/download/'+urllib.quote_plus(folderName)+ '/'+fileName + '|' + self.getHeadersEncoded(), 'mediaType': fileType}
            elif cacheType == self.CACHE_TYPE_AJAX:
                videos[fileName] = {'url': self.protocol + self.domain +'/index.php/apps/files/ajax/download.php?'+ urllib.urlencode({'dir' : folderName})+'&files='+fileName + '|' + self.getHeadersEncoded(), 'mediaType': fileType}

        return videos



    ##
    # retrieve a video link
    #   parameters: title of video, whether to prompt for quality/format (optional), cache type (optional)
    #   returns: list of URLs for the video or single URL of video (if not prompting for quality)
    ##
    def getVideoLink(self,filename,directory,cacheType=0):

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        # default User-Agent ('Python-urllib/2.6') will *not* work
        opener.addheaders = [('User-Agent', self.user_agent)]

        params = urllib.urlencode({'files': filename, 'dir': directory})
        url = self.protocol + self.domain +'/index.php/apps/files/ajax/download.php?'+params

        return url + '|' + self.getHeadersEncoded()




