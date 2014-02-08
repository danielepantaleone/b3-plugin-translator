# coding: utf-8
#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = 'Fenix'
__version__ = '2.5'

import b3
import b3.plugin
import b3.events
import thread
import json
import re

from ConfigParser import NoOptionError
from urllib import urlencode
from urllib2 import urlopen
from urllib2 import Request
from urllib2 import URLError


class TranslatorPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None

    # configuration values
    _settings = dict(default_source_language='auto',
                     default_target_language='en',
                     display_translator_name=True,
                     translator_name='^7[^1T^7]',
                     min_sentence_length=6,
                     microsoft_client_id=None,
                     microsoft_client_secret=None)

    _last_message_said = ''

    # available languages
    _languages = dict(ca='Catalan', cs='Czech', da='Danish', nl='Dutch', en='English', et='Estonian', fi='Finnish',
                      fr='French', de='German', el='Greek', ht='Haitian Creole', he='Hebrew', hi='Hindi',
                      hu='Hungarian', id='Indonesian', it='Italian', lv='Latvian', lt='Lithuanian', no='Norwegian',
                      pl='Polish', pt='Portuguese', ro='Romanian', sl='Slovenian', es='Spanish', sv='Swedish',
                      th='Thai', tr='Turkish', uk='Ukrainian')

    def onLoadConfig(self):
        """\
        Load the configuration file
        """
        try:
            value = self.config.get('settings', 'default_source_language')
            if value in self._languages.keys() or value == 'auto':
                self._settings['default_source_language'] = value
                self.debug('loaded default_source_language setting: %s' % self._settings['default_source_language'])
            else:
                self.warning('invalid value speficied in settings/default_source_language (%s), '
                             'using default: %s' % (value, self._settings['default_source_language']))
        except NoOptionError:
            self.warning('could not find settings/default_source_language in config file, '
                         'using default: %s' % self._settings['default_source_language'])

        try:
            value = self.config.get('settings', 'default_target_language')
            if value in self._languages.keys():
                self._settings['default_target_language'] = value
                self.debug('loaded default_target_language setting: %s' % self._settings['default_target_language'])
            else:
                self.warning('invalid value speficied in settings/default_target_language (%s), '
                             'using default: %s' % (value, self._settings['default_target_language']))
        except NoOptionError:
            self.warning('could not find settings/default_target_language in config file, '
                         'using default: %s' % self._settings['default_target_language'])

        try:
            self._settings['display_translator_name'] = self.config.getboolean('settings', 'display_translator_name')
            self.debug('loaded display_translator_name setting: %s' % self._settings['display_translator_name'])
        except NoOptionError:
            self.warning('could not find settings/display_translator_name in config file, '
                         'using default: %s' % self._settings['display_translator_name'])
        except ValueError, e:
            self.error('could not load settings/display_translator_name config value: %s' % e)
            self.debug('using default value (%s) for settings/display_translator_name' %
                       self._settings['display_translator_name'])

        try:
            self._settings['translator_name'] = self.config.get('settings', 'translator_name')
            self.debug('loaded translator_name setting: %s' % self._settings['translator_name'])
        except NoOptionError:
            self.warning('could not find settings/translator_name in config file, '
                         'using default: %s' % self._settings['translator_name'])

        try:
            self._settings['min_sentence_length'] = self.config.getint('settings', 'min_sentence_length')
            self.debug('loaded min_sentence_length setting: %s' % self._settings['min_sentence_length'])
        except NoOptionError:
            self.warning('could not find settings/min_sentence_length in config file, '
                         'using default: %s' % self._settings['min_sentence_length'])
        except ValueError, e:
            self.error('could not load settings/min_sentence_length config value: %s' % e)
            self.debug('using default value (%s) for settings/min_sentence_length' %
                       self._settings['min_sentence_length'])

        try:
            value = self.config.get('settings', 'microsoft_client_id')
            if value and len(value.strip()) != 0:
                self._settings['microsoft_client_id'] = value
                self.debug('loaded microsoft_client_id setting: %s' % self._settings['microsoft_client_id'])
            else:
                self.warning('invalid value speficied in settings/microsoft_client_id: plugin will be disabled')
        except NoOptionError:
            self.warning('could not find settings/microsoft_client_id in config file: plugin will be disabled')

        try:
            value = self.config.get('settings', 'microsoft_client_secret')
            if value and len(value.strip()) != 0:
                self._settings['microsoft_client_secret'] = value
                self.debug('loaded microsoft_client_secret setting: %s' % self._settings['microsoft_client_secret'])
            else:
                self.warning('invalid value speficied in settings/microsoft_client_secret: plugin will be disabled')
        except NoOptionError:
            self.warning('could not find settings/microsoft_client_secret in config file: plugin will be disabled')

        if not self._settings['microsoft_client_id'] or not self._settings['microsoft_client_secret']:
            self.error('microsoft translator is not configured properly: disabling the plugin...')
            self.disable()

    def onStartup(self):
        """\
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:    
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

                func = self.getCmd(cmd)
                if func: 
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)
        
        # register the events needed
        self.registerEvent(b3.events.EVT_CLIENT_SAY, self.onSay)
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_SAY, self.onSay)

        # notice plugin startup
        self.debug('plugin started')
        
    ####################################################################################################################
    ##                                                                                                                ##
    ##   EVENTS                                                                                                       ##
    ##                                                                                                                ##
    ####################################################################################################################

    def onEnable(self):
        """\
        Executed when the plugin is enabled
        """
        if not self._settings['microsoft_client_id'] or not self._settings['microsoft_client_secret']:
            self.disable()
            self.warning('could not enable plugin translator: microsoft translator is not configured properly')
            self.console.say('Plugin ^3Translator ^7is now ^1OFF')

    def onSay(self, event):
        """\
        Handle EVT_CLIENT_SAY and EVT_CLIENT_SAY_TEAM
        """
        client = event.client
        message = event.data.strip()

        # if not enough length
        if len(message) < self._settings['min_sentence_length']:
            return

        # if it's a b3 command
        if message[0] not in (self._adminPlugin.cmdPrefix,
                              self._adminPlugin.cmdPrefixLoud,
                              self._adminPlugin.cmdPrefixBig,
                              self._adminPlugin.cmdPrefixPrivate):

            # save for future use
            self._last_message_said = message

            # we have now to send a translation to all the
            # clients that enabled the automatic translation
            for cl in self.console.clients.getList():

                # if it's the same client
                if cl == client:
                    continue

                # skip if automatic translation is disabled
                if not cl.var(self, 'transauto').value:
                    continue

                # start the translation in a separate thread
                thread.start_new_thread(self.translate, (message, cl.var(self, 'translang').value, '', cl))

    ####################################################################################################################
    ##                                                                                                                ##
    ##   UTILITIES                                                                                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None

    @staticmethod
    def to_byte_string(s):
        """\
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given
        """
        if isinstance(s, str):
            return s
        return s.encode('utf-8')

    @staticmethod
    def str_sanitize(s):
        """\
        Sanitize the given string
        """
        return re.sub('\^[0-9]', '', re.sub(r'<[^>]*>', '', s)).replace('ß', 'ss').replace('ü', 'ue').\
            replace('ö', 'oe').replace('ä', 'ae').replace('à', 'a').replace('è', 'e').replace('é', 'e').\
            replace('ì', 'i').replace('ò', 'o').replace('ù', 'u').replace('ç', 'c').replace('€', 'euro').\
            replace('$', 'dollar').replace('£', 'pound').replace('%', 'pc').replace('"', "''").strip()

    ####################################################################################################################
    ##                                                                                                                ##
    ##   FUNCTIONS                                                                                                    ##
    ##                                                                                                                ##
    ####################################################################################################################

    def get_access_token(self, client_id, client_secret):
        """\
        Make an HTTP POST request to the token service, and return the access_token
        See description here: http://msdn.microsoft.com/en-us/library/hh454949.aspx
        """
        data = urlencode(dict(client_id=client_id, client_secret=client_secret,
                              grant_type='client_credentials', scope='http://api.microsofttranslator.com'))
    
        try:

            self.debug('requesting microsoft translator access token.....')
            req = Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13')
            req.add_data(data)
            res = urlopen(req)
            rtn = json.loads(res.read())
    
            if 'access_token' in rtn.keys():
                return rtn['access_token']

        except (URLError, TypeError), e:
            # just print error in log and let the method return false
            # this was split into several exceptions catches but it makes no
            # sense since without the access token we are not able to translate
            self.error('could not request microsoft translator access token: %s' % e)

        return False

    def translate(self, sentence, target, source, client, cmd=None):
        """\
        Translate the given sentence in the specified target language
        """
        try:

            token = self.get_access_token(self._settings['microsoft_client_id'],
                                          self._settings['microsoft_client_secret'])
        
            if not token:
                client.message('^7unable to translate')
                return
            
            data = dict(text=self.to_byte_string(sentence), to=target)
            
            if source != 'auto' and source != '':
                data['from'] = source

            # getting the translation
            req = Request('http://api.microsofttranslator.com/v2/Http.svc/Translate?' + urlencode(data))
            req.add_header('Authorization', 'Bearer ' + token)
            res = urlopen(req)
            rtn = res.read()
            
            # formatting the string
            msg = self.str_sanitize(rtn)

            if not msg:
                self.debug('could not translate message (%s): empty string returned' % sentence)
                client.message('^7unable to translate')
                return

            # print as verbose not to spam too many log lines in debug configuration
            self.verbose('message translated [ source <%s> : %s | result <%s> : %s ]' % (source, sentence, target, msg))

            # prepend translator name if specified
            if self._settings['display_translator_name']:
                msg = '%s %s' % (self._settings['translator_name'], msg)

            if not cmd:
                client.message(msg)
            else:
                cmd.sayLoudOrPM(client, msg)

        except (URLError, TypeError), e:
            self.error('could not translate message (%s): %s' % e)
            client.message('^7unable to translate')

    ####################################################################################################################
    ##                                                                                                                ##
    ##   COMMANDS                                                                                                     ##
    ##                                                                                                                ##
    ####################################################################################################################

    def cmd_translate(self, data, client, cmd=None):
        """\
        [<source>]*[<target>] <sentence> - translate a message
        """
        if not data: 
            client.message('^7Missing data, try ^3!^7help translate')
            return

        src = self._settings['default_source_language']
        tar = self._settings['default_target_language']

        if '*' in data:

            # language codes specified for this translation
            r = re.compile(r'''^(?P<source>\w*)[*]?(?P<target>\w*)\s*(?P<message>.+)$''')
            m = r.match(data)
            if not m:
                client.message('Invalid data. Try ^3!^7help translate')
                return

            src = m.group('source')
            tar = m.group('target')
            msg = m.group('message')

            if src and src != 'auto' and src not in self._languages.keys():
                self.verbose('invalid source language (%s) specified in !translate command: unable to translate' % src)
                client.message('^7Invalid ^1source ^7language specified, try ^3!^7translang')
                return

            if not tar:
                # fallback to default target language
                tar = self._settings['default_target_language']
            elif tar not in self._languages.keys():
                self.verbose('invalid target language (%s) specified in !translate command: unable to translate' % tar)
                client.message('^7Invalid ^1target ^7language specified, try ^3!^7translang')
                return

            data = msg

        # start the translation in a separate thread
        thread.start_new_thread(self.translate, (re.sub('\^[0-9]', '', data), tar, src, client, cmd))

    def cmd_translast(self, data, client, cmd=None):
        """\
        [<target>] - translate the last available sentence from the chat
        """
        if not self._last_message_said:
            client.message('^7unable to translate')
            return
        
        tar = self._settings['default_target_language']
        
        if data:

            if data not in self._languages.keys():
                self.verbose('invalid target language (%s) specified in !translast command: unable to translate' % data)
                client.message('^7Invalid ^1target ^7language specified, try ^3!^7translang')
                return

            tar = data

        # start the translation in a separate thread
        thread.start_new_thread(self.translate, (self._last_message_said, tar, '', client, cmd))
    
    def cmd_transauto(self, data, client, cmd=None):
        """\
        <on|off> [<language>] - turn on/off the automatic translation
        """
        if not data: 
            client.message('^7Missing data, try ^3!^7help transauto')
            return

        r = re.compile(r'''^(?P<option>on|off)\s*(?P<target>\w*)$''')
        m = r.match(data)
        if not m:
            client.message('Invalid data, try ^3!^7help transauto')
            return

        opt = m.group('option')
        tar = m.group('target')

        if opt == 'on':

            if tar:

                if tar not in self._languages.keys():
                    self.verbose('invalid target language (%s) in !transauto command: unable to translate' % tar)
                    client.message('^7Invalid ^1target ^7language specified, try ^3!^7translang')
                    return

            elif client.isvar(self, 'translang'):
                # using previously stored target language
                tar = client.var(self, 'translang').value
            else:
                # using default target language
                tar = self._settings['default_target_language']

            client.setvar(self, 'transauto', True)
            client.setvar(self, 'translang', tar)
            client.message('^7Transauto: ^2ON ^7- Language: ^3%s' % self._languages[tar])
        
        elif opt == 'off':
            
            client.setvar(self, 'transauto', False)
            client.message('^7Transauto: ^1OFF')

    def cmd_translang(self, data, client, cmd=None):
        """\
        Display a list of available language codes
        """
        codes = []
        for k, v in self._languages.items():
            codes.append('^2%s^7:%s' % (k, v))

        cmd.sayLoudOrPM(client, '^7Language codes: %s' % ', '.join(codes))