# coding: utf-8
#
# Translator Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# CHANGELOG
#
# 2014/05/11 - 2.7 - Fenix - rewrote dictionaty creation as literals
#                          - use the new built-in getCmd function (if available)
#                          - removed threading interface: RCON doesn't support multithreading after all
#                          - keep backward compatibility with B3 v1.9.x
#                          - let transauto use only the default target language: speed up the translation and B3 won't hang on
#                          - general improvements
#                          - added automated tests
# 2015/02/07 - 2.8 - Fenix - new plugin module structure
# 2017/05/31 - 3.0 - GrosBedo & Lotabout - new interface to google via web scraping
#                                                                  - add min_time_between to limit number of requests

__author__ = 'GrosBedo'
__version__ = '3.0'

import b3
import b3.plugin
import b3.events

# translate utility that utilize google translator, support python2 & python3
# Note that the order or arguments in the URL matters.

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

try:
    import urllib2
except:
    import urllib.request as urllib2

import json
import re
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')

from ConfigParser import NoOptionError
#from urllib2 import urlopen
#from urllib2 import Request
#from urllib2 import URLError

try:
    # import the getCmd function
    import b3.functions.getCmd as getCmd
except ImportError:
    # keep backward compatibility
    def getCmd(instance, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(instance, cmd):
            func = getattr(instance, cmd)
            return func
        return None


class TranslatorPlugin(b3.plugin.Plugin):
    
    adminPlugin = None
    cmdPrefix = None

    lastTime = None

    # configuration values
    settings = {
        'default_source_language': 'auto',
        'default_target_language': 'en',
        'display_translator_name': True,
        'translator_name': '^7[^1T^7]',
        'min_sentence_length': 6,
        'min_time_between': 30,
    }

    last_message_said = ''

    # available languages
    languages = {
        'ca': 'Catalan', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English', 'et': 'Estonian',
        'fi': 'Finnish', 'fr': 'French', 'de': 'German', 'el': 'Greek', 'ht': 'Haitian Creole', 'he': 'Hebrew',
        'hi': 'Hindi', 'hu': 'Hungarian', 'id': 'Indonesian', 'it': 'Italian', 'lv': 'Latvian', 'lt': 'Lithuanian',
        'no': 'Norwegian', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian', 'sl': 'Slovenian', 'es': 'Spanish',
        'sv': 'Swedish', 'th': 'Thai', 'tr': 'Turkish', 'uk': 'Ukrainian', 'ru': 'Russian', 'zh': 'Chinese',
    }

    def onLoadConfig(self):
        """
        Load the configuration file
        """
        try:
            value = self.config.get('settings', 'default_source_language')
            if value in self.languages.keys() or value == 'auto':
                self.settings['default_source_language'] = value
                self.debug('loaded default_source_language setting: %s' % self.settings['default_source_language'])
            else:
                self.warning('invalid value speficied in settings/default_source_language (%s), '
                             'using default: %s' % (value, self.settings['default_source_language']))
        except NoOptionError:
            self.warning('could not find settings/default_source_language in config file, '
                         'using default: %s' % self.settings['default_source_language'])

        try:
            value = self.config.get('settings', 'default_target_language')
            if value in self.languages.keys():
                self.settings['default_target_language'] = value
                self.debug('loaded default_target_language setting: %s' % self.settings['default_target_language'])
            else:
                self.warning('invalid value speficied in settings/default_target_language (%s), '
                             'using default: %s' % (value, self.settings['default_target_language']))
        except NoOptionError:
            self.warning('could not find settings/default_target_language in config file, '
                         'using default: %s' % self.settings['default_target_language'])

        try:
            self.settings['display_translator_name'] = self.config.getboolean('settings', 'display_translator_name')
            self.debug('loaded display_translator_name setting: %s' % self.settings['display_translator_name'])
        except NoOptionError:
            self.warning('could not find settings/display_translator_name in config file, '
                         'using default: %s' % self.settings['display_translator_name'])
        except ValueError, e:
            self.error('could not load settings/display_translator_name config value: %s' % e)
            self.debug('using default value (%s) for settings/display_translator_name' %
                       self.settings['display_translator_name'])

        try:
            self.settings['translator_name'] = self.config.get('settings', 'translator_name')
            self.debug('loaded translator_name setting: %s' % self.settings['translator_name'])
        except NoOptionError:
            self.warning('could not find settings/translator_name in config file, '
                         'using default: %s' % self.settings['translator_name'])

        try:
            self.settings['min_sentence_length'] = self.config.getint('settings', 'min_sentence_length')
            self.debug('loaded min_sentence_length setting: %s' % self.settings['min_sentence_length'])
        except NoOptionError:
            self.warning('could not find settings/min_sentence_length in config file, '
                         'using default: %s' % self.settings['min_sentence_length'])
        except ValueError, e:
            self.error('could not load settings/min_sentence_length config value: %s' % e)
            self.debug('using default value (%s) for settings/min_sentence_length' %
                       self.settings['min_sentence_length'])

        try:
            self.settings['min_time_between'] = self.config.getint('settings', 'min_time_between')
            self.debug('loaded min_time_between setting: %s' % self.settings['min_time_between'])
        except NoOptionError:
            self.warning('could not find settings/min_time_between in config file, '
                         'using default: %s' % self.settings['min_time_between'])
        except ValueError, e:
            self.error('could not load settings/min_time_between config value: %s' % e)
            self.debug('using default value (%s) for settings/min_time_between' %
                       self.settings['min_time_between'])

    def onStartup(self):
        """
        Initialize plugin settings
        """
        self.adminPlugin = self.console.getPlugin('admin')
        if not self.adminPlugin:    
            self.error('could not start without admin plugin')
            return False
        
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2: 
                    cmd, alias = sp

                func = getCmd(self, cmd)
                if func: 
                    self.adminPlugin.registerCommand(self, cmd, level, func, alias)

        try:
            # register the events needed
            self.registerEvent(self.console.getEventID('EVT_CLIENT_SAY'), self.onSay)
            self.registerEvent(self.console.getEventID('EVT_CLIENT_TEAM_SAY'), self.onSay)
        except TypeError:
            # keep backwards compatibility
            self.registerEvent(self.console.getEventID('EVT_CLIENT_SAY'))
            self.registerEvent(self.console.getEventID('EVT_CLIENT_TEAM_SAY'))

        try:
            # B3 > 1.10dev
            self.cmdPrefix = (self.adminPlugin.cmdPrefix,
                              self.adminPlugin.cmdPrefixLoud,
                              self.adminPlugin.cmdPrefixBig,
                              self.adminPlugin.cmdPrefixPrivate)
        except AttributeError:
            # B3 1.9.x
            self.cmdPrefix = (self.adminPlugin.cmdPrefix,
                              self.adminPlugin.cmdPrefixLoud,
                              self.adminPlugin.cmdPrefixBig)

        # notice plugin startup
        self.debug('plugin started')
        
    ####################################################################################################################
    ##                                                                                                                ##
    ##   EVENTS                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def format_json(self, result, max_entries=5):
        if max_entries is None:
            max_entries = 999999

        ret = []
        for sentence in result['sentences']:
            ret.append(sentence['orig'] + ': ' + sentence['trans'])
            ret.append('')

        # format pos
        if 'dict' in result:
            for pos in result['dict']:
                ret.append(pos['pos'])
                for entry in pos['entry'][:max_entries]:
                    ret.append(entry['word'] + ': ' + ', '.join(entry['reverse_translation']))
                ret.append('')

        return '\n'.join(ret)

    def translate(self, text, from_lang="auto", to_lang="en-EN"):
        """translate text, return the result as json"""
        self.debug('attempting to translate message -> %s : %s' % (to_lang, text))

        url = 'https://translate.googleapis.com/translate_a/single?'

        params = []
        params.append('client=gtx')
        params.append('sl=' + from_lang)
        params.append('tl=' + to_lang)
        params.append('hl=en-US')
        params.append('dt=t')
        params.append('dt=bd')
        params.append('dj=1')
        params.append('source=input')
        params.append(urlencode({'q': text}))
        url += '&'.join(params)

        request = urllib2.Request(url)
        browser = "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0"
        request.add_header('User-Agent', browser)
        response = urllib2.urlopen(request)
        rtn = json.loads(response.read().decode('utf8'))
        self.verbose('translation done and received, sanitizing...')

        # formatting the string
        msg = self.format_json(rtn)
        msg = self.str_sanitize(msg)
        if not msg:
            self.debug('could not translate message (%s): empty string returned' % text)
            return None

        # print as verbose not to spam too many log lines in debug configuration
        self.verbose('message translated [ source <%s> : %s | result <%s> : %s ]' % (from_lang, text, to_lang, msg))
        return msg

    def voice(self, text, lang='en'):
        """return the sound of an word, in mp3 bytes"""
        url = 'https://translate.googleapis.com/translate_tts?'

        params = []
        params.append('client=gtx')
        params.append('ie=UTF-8')
        params.append('tl=' + lang)
        params.append(urlencode({'q': text}))
        url += '&'.join(params)
        request = urllib2.Request(url)
        browser = "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0"
        request.add_header('User-Agent', browser)
        response = urllib2.urlopen(request)
        return response.read()

    def onEvent(self, event):
        """
        Old event dispatch system
        """
        if event.type == self.console.getEventID('EVT_CLIENT_SAY') or \
            event.type == self.console.getEventID('EVT_CLIENT_TEAM_SAY'):
            self.onSay(event)

    def onSay(self, event):
        """
        Handle EVT_CLIENT_SAY and EVT_CLIENT_SAY_TEAM
        """
        client = event.client
        message = event.data.strip()

        # if not enough length
        if len(message) < self.settings['min_sentence_length']:
            return

        # check if we are not spamming requests
        curTime = time.time()
        if self.lastTime and curTime - self.lastTime <= self.settings['min_time_between']:
            return
        else:
            # update last time with current time
            self.lastTime = curTime

        # if it's not a B3 command
        if message[0] not in self.cmdPrefix:

            # save for future use
            self.last_message_said = message

            # we have now to send a translation to all the
            # clients that enabled the automatic translation
            collection = []
            for c in self.console.clients.getList():
                if c != client and c.isvar(self, 'transauto'):
                    collection.append(c)

            if not collection:
                # no one has transauto enabled
                return

            translation = self.translate(message, to_lang=self.settings['default_target_language'])
            if not translation:
                # we didn't managed to get a valid translation
                # no need to spam the chat of everyone with a silly message
                return

            for c in collection:
                # send the translation to all the clients
                self.send_translation(c, translation)

    ####################################################################################################################
    ##                                                                                                                ##
    ##   OTHER METHODS                                                                                                ##
    ##                                                                                                                ##
    ####################################################################################################################

    @staticmethod
    def to_byte_string(s):
        """
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given.
        """
        return s if isinstance(s, str) else s.encode('utf-8')

    @staticmethod
    def str_sanitize(s):
        """
        Sanitize the given string.
        Will remove color codes, XML tags and substitute
        unprintable characters with their alphabetical representation.
        """
        return re.sub('\^[0-9]', '', re.sub(r'<[^>]*>', '', s)).replace('ß', 'ss').replace('ü', 'ue').\
               replace('ö', 'oe').replace('ä', 'ae').replace('à', 'a').replace('è', 'e').replace('é', 'e').\
               replace('ì', 'i').replace('ò', 'o').replace('ù', 'u').replace('ç', 'c').replace('€', 'euro').\
               replace('$', 'dollar').replace('£', 'pound').replace('%', 'pc').replace('"', "''").strip()

    ####################################################################################################################
    ##                                                                                                                ##
    ##   TRANSLATION METHODS                                                                                          ##
    ##                                                                                                                ##
    ####################################################################################################################

    def send_translation(self, client, message, cmd=None):
        """
        Send a translated message to a client
        """
        # prepend translator name if specified
        if self.settings['display_translator_name']:
            message = '%s %s' % (self.settings['translator_name'], message)

        if not cmd:
            client.message(message)
            return

        cmd.sayLoudOrPM(client, message)

    ####################################################################################################################
    ##                                                                                                                ##
    ##   COMMANDS                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def cmd_translate(self, data, client, cmd=None):
        """
        [<source>]*[<target>] <message> - translate a message
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help translate')
            return

        src = self.settings['default_source_language']
        tar = self.settings['default_target_language']

        if '*' in data:

            # language codes specified for this translation
            r = re.compile(r'''^(?P<source>\w*)[*]?(?P<target>\w*)\s*(?P<message>.+)$''')
            m = r.match(data)
            if not m:
                client.message('^7invalid data, try ^3!^7help translate')
                return

            source = m.group('source').strip()
            target = m.group('target').strip()

            if source and source != 'auto':
                if source not in self.languages:
                    self.verbose('invalid source language (%s) specified in !translate command: unable to translate' % source)
                    client.message('^7invalid ^1source ^7language specified, try ^3!^7translang')
                    return
                # use the given source language code
                src = source

            if target:
                if target not in self.languages:
                    self.verbose('invalid target language (%s) specified in !translate command: unable to translate' % target)
                    client.message('^7invalid ^1target ^7language specified, try ^3!^7translang')
                    return
                # use the given target language code
                tar = target

            # get the real message to be translated
            data = m.group('message')

        translation = self.translate(data, src, tar)
        if not translation:
            client.message('^7unable to translate')
            return

        # send the translation to the given client
        self.send_translation(client, translation, cmd)

    def cmd_translast(self, data, client, cmd=None):
        """
        [<target>] - translate the last available sentence from the chat
        """
        if not self.last_message_said:
            client.message('^7unable to translate')
            return

        # set default target language
        tar = self.settings['default_target_language']

        if data:
            if data not in self.languages:
                self.verbose('invalid target language (%s) specified in !translast command: unable to translate' % data)
                client.message('^7Invalid ^1target ^7language specified, try ^3!^7translang')
                return

            # use the provided language code
            tar = data

        message = self.translate(self.last_message_said, to_lang=tar)
        if not message:
            client.message('^7unable to translate')
            return

        # send the translation to the given client
        self.send_translation(client, message, cmd)
    
    def cmd_transauto(self, data, client, cmd=None):
        """
        <on|off> - turn on/off the automatic translation
        """
        if not data: 
            client.message('^7missing data, try ^3!^7help transauto')
            return

        data = data.lower()
        if data not in ('on', 'off'):
            client.message('invalid data, try ^3!^7help transauto')
            return

        if data == 'on':
            client.setvar(self, 'transauto', True)
            client.message('^7Transauto: ^2ON')
        elif data == 'off':
            client.delvar(self, 'transauto')
            client.message('^7Transauto: ^1OFF')

    def cmd_translang(self, data, client, cmd=None):
        """
        Display the list of available language codes
        """
        codes = []
        for k, v in self.languages.items():
            codes.append('^2%s^7:%s' % (k, v))

        cmd.sayLoudOrPM(client, '^7Languages: %s' % ', '.join(codes))