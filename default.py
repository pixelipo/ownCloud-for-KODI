'''
    owncloud XBMC Plugin
    Copyright (C) 2013-2014 ddurdle

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

from resources.lib import owncloud
#from resources.lib import gPlayer
#from resources.lib import tvWindow
from resources.lib import cloudservice
from resources.lib import folder
from resources.lib import file
from resources.lib import mediaurl
from resources.lib import package



import sys
import urllib
import cgi
import re

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# global variables
PLUGIN_NAME = 'owncloud'



#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addMediaFile(service, media):

    listitem = xbmcgui.ListItem(media.title, iconImage=media.thumbnail,
                                thumbnailImage=media.thumbnail)
    if media.type == media.AUDIO:
        infolabels = decode_dict({ 'title' : media.title })
        listitem.setInfo('Music', infolabels)
    else:
        infolabels = decode_dict({ 'title' : media.title , 'plot' : media.plot })
        listitem.setInfo('Video', infolabels)

    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', media.fanart)
    cm=[]
    url = service.getPlaybackCall(media)
    cleanURL = re.sub('---', '', url)
    cleanURL = re.sub('&', '---', cleanURL)
    cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&title='+media.title+'&streamurl='+cleanURL+')', ))
    cm.append(( addon.getLocalizedString(30046), 'XBMC.PlayMedia('+url+'&quality=SD&stream=1', ))
    cm.append(( addon.getLocalizedString(30047), 'XBMC.PlayMedia('+url+'&quality=HD&stream=1)', ))
    cm.append(( addon.getLocalizedString(30048), 'XBMC.PlayMedia('+url+'&stream=0)', ))
    cm.append(( addon.getLocalizedString(30032), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=download&title='+media.title+'&filename='+media.id+')', ))

#    listitem.addContextMenuItems( commands )
    if cm:
        listitem.addContextMenuItems(cm, False)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=0)

#***phase out
def addVideo(url, infolabels, label, img='', fanart='', total_items=0,
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'], url))
    listitem = xbmcgui.ListItem(label, iconImage=img,
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=total_items)
#***phase out
def addMusic(url, infolabels, label, img='', fanart='', total_items=0,
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
    log('adding video: %s - %s' % (infolabels['title'], url))
    listitem = xbmcgui.ListItem(label, iconImage=img,
                                thumbnailImage=img)
    listitem.setInfo('music', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=total_items)

#***phase out
#def addDirectory(url, title, img='', fanart='', total_items=0):
#    log('adding dir: %s - %s' % (title, url))
#    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
#    if not fanart:
#        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
#    listitem.setProperty('fanart_image', fanart)
#    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
#                                isFolder=True, totalItems=total_items)

def addDirectory(service, folder):
    listitem = xbmcgui.ListItem(decode(folder.title), iconImage='', thumbnailImage='')
    fanart = addon.getAddonInfo('path') + '/fanart.jpg'

    if folder.id != '':
        cm=[]
        cm.append(( addon.getLocalizedString(30042), 'XBMC.RunPlugin('+PLUGIN_URL+'?mode=buildstrm&title='+folder.title+'&instanceName='+str(service.instanceName)+'&folderID='+str(folder.id)+')', ))
        listitem.addContextMenuItems(cm, False)
    listitem.setProperty('fanart_image', fanart)
    xbmcplugin.addDirectoryItem(plugin_handle, service.getDirectoryCall(folder), listitem,
                                isFolder=True, totalItems=0)

def addMenu(url,title):
    listitem = xbmcgui.ListItem(decode(title), iconImage='', thumbnailImage='')
    fanart = addon.getAddonInfo('path') + '/fanart.jpg'

    listitem.setProperty('fanart_image', fanart)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=0)


#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data


def numberOfAccounts(accountType):

    count = 1
    max_count = int(addon.getSetting(accountType+'_numaccounts'))
    actualCount = 0
    while True:
        try:
            if addon.getSetting(accountType+str(count)+'_username') != '':
                actualCount = actualCount + 1
        except:
            break
        if count == max_count:
            break
        count = count + 1
    return actualCount


#global variables
PLUGIN_URL = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.owncloud')

#debugging
try:

    remote_debugger = addon.getSetting('remote_debugger')
    remote_debugger_host = addon.getSetting('remote_debugger_host')

    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    log(addon.getLocalizedString(30016), True)
    sys.exit(1)
except :
    pass


# retrieve settings
user_agent = addon.getSetting('user_agent')


mode = plugin_queries['mode']

# make mode case-insensitive
mode = mode.lower()


log('plugin url: ' + PLUGIN_URL)
log('plugin queries: ' + str(plugin_queries))
log('plugin handle: ' + str(plugin_handle))

if mode == 'main':
    addMenu(PLUGIN_URL+'?mode=options','<<'+addon.getLocalizedString(30043)+'>>')


#dump a list of videos available to play
if mode == 'main' or mode == 'folder':

    cacheType = int(addon.getSetting('playback_type'))

    folderName=''

    if (mode == 'folder'):
        folderName = plugin_queries['directory']
    else:
        pass

    instanceName = ''
    try:
        instanceName = plugin_queries['instance']
    except:
        pass

    numberOfAccounts = numberOfAccounts(PLUGIN_NAME)

    # show list of services
    if numberOfAccounts > 1 and instanceName == '':
        count = 1
        max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
        while True:
            instanceName = PLUGIN_NAME+str(count)
            try:
                username = addon.getSetting(instanceName+'_username')
                if username != '':
                    addMenu(PLUGIN_URL+'?mode=main&instance='+instanceName,username)
            except:
                break
            if count == max_count:
                break
            count = count + 1

    else:
        # show index of accounts
        if instanceName == '' and numberOfAccounts == 1:

                count = 1
                max_count = int(addon.getSetting(PLUGIN_NAME+'_numaccounts'))
                while True:
                    instanceName = PLUGIN_NAME+str(count)
                    try:
                        username = addon.getSetting(instanceName+'_username')
                        if username != '':

                            # you need to have at least a username&password set or an authorization token
#                            if ((username == '' or password == '') and auth_token == ''):
#                                xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
#                                log(addon.getLocalizedString(30015), True)
#                                xbmcplugin.endOfDirectory(plugin_handle)

                            #let's log in
                            oc = owncloud.owncloud(PLUGIN_URL,addon,instanceName, user_agent)

                    except:
                        break

                    if count == max_count:
                        break
                    count = count + 1

        # no accounts defined
        elif numberOfAccounts == 0:

            #legacy account conversion
            try:
                username = addon.getSetting('username')

                if username != '':
                    addon.setSetting(PLUGIN_NAME+'1_username', username)
                    addon.setSetting(PLUGIN_NAME+'1_password', addon.getSetting('password'))
                    addon.setSetting(PLUGIN_NAME+'1_domain', addon.getSetting('domain'))
                    addon.setSetting(PLUGIN_NAME+'1_protocol', addon.getSetting('protocol'))
                    addon.setSetting(PLUGIN_NAME+'1_version', addon.getSetting('version'))
                    addon.setSetting(PLUGIN_NAME+'1_auth_token', addon.getSetting('auth_token'))
                    addon.setSetting(PLUGIN_NAME+'1_auth_session', addon.getSetting('auth_session'))
                    addon.setSetting('username', '')
                    addon.setSetting('password', '')
                    addon.setSetting('protocol', '')
                    addon.setSetting('domain', '')
                    addon.setSetting('version', '')
                    addon.setSetting('auth_token', '')
                    addon.setSetting('auth_session', '')
            except :
                    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30015))
                    log(addon.getLocalizedString(30015), True)
                    xbmcplugin.endOfDirectory(plugin_handle)

            #let's log in
            oc = owncloud.owncloud(PLUGIN_URL,addon,instanceName, user_agent)


        # show entries of a single account (such as folder)
        elif instanceName != '':

            oc = owncloud.owncloud(PLUGIN_URL,addon,instanceName, user_agent)



        mediaItems = oc.getMediaList(folderName,0)

        if mediaItems:
            for item in mediaItems:

                try:
                    if item.file == 0:
                        addDirectory(oc, item.folder)
                    else:
                        addMediaFile(oc, item.file)
                except:
                        addMediaFile(oc, item.file)

        oc.updateAuthorization(addon)


#play a video given its exact-title
elif mode == 'video' or mode == 'audio':
    filename = plugin_queries['filename']
    try:
        directory = plugin_queries['directory']
        cacheType = addon.getSetting('playback_type')
    except:
        directory = ''
        cacheType = 0

    if cacheType == '0':
      videoURL = owncloud.getVideoLink(filename,directory)
    else:
      videoURL = owncloud.getVideoLink(filename,directory,cacheType)

    item = xbmcgui.ListItem(path=videoURL)
    log('play url: ' + videoURL)
    item.setInfo( type="Video", infoLabels={ "Title": filename , "Plot" : filename } )
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

if mode == 'options' or mode == 'buildstrm' or mode == 'clearauth':
    addMenu(PLUGIN_URL+'?mode=clearauth','<<'+addon.getLocalizedString(30018)+'>>')
    addMenu(PLUGIN_URL+'?mode=buildstrm','<<'+addon.getLocalizedString(30025)+'>>')



xbmcplugin.endOfDirectory(plugin_handle)

