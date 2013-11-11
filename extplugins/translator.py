# coding: utf-8
#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2013 Daniele Pantaleone <fenix@bigbrotherbot.net)
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

__author__ = 'Fenix - http://www.urbanterror.info'
__version__ = '2.2'

import b3
import b3.plugin
import b3.events
import thread
import urllib, urllib2
import json
import re


class TranslatorPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None

    # configuration values
    _defaultSourceLang = ''
    _defaultTargetLang = 'en'
    _displayTranslatorName = True
    _translatorName = '^7[^1T^7] '
    _messagePrefix = '^3'
    _minSentenceLength = 6
    _microsoftClientId = ''
    _microsoftClientSecret = ''

    _lastSentenceSaid = ''
    _messageParseRegEx = re.compile(r"""^(?P<source>\w*)[*]?(?P<target>\w*) (?P<sentence>.+)$""");
    _transautoParseRegEx = re.compile(r"""^(?P<option>on|off)\s*(?P<target>\w*)$""");

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
        self.verbose('Loading configuration file...')
        
        try:

            if not self.config.get('settings', 'default_source_language'):
                self.debug('default source language detected empty: using automatic language detection')
            elif not self.config.get('settings', 'default_source_language') in self._languages.keys():
                self.warning('invalid language specified as default source: using automatic language detection')
            else:
                self._defaultSourceLang = self.config.get('settings', 'default_source_language')
                self.debug('default source language set to: %s' % self._defaultSourceLang)
        
        except Exception, e:
            self.error('could not read default source language setting: %s' % e)
            self.debug('using automatic language detection as source language')
        
        try:

            if not self.config.get('settings', 'default_target_language') in self._languages.keys():
                self.warning('invalid language specified as default target: using default: %s' % self._defaultTargetLang)
            else:
                self._defaultTargetLang = self.config.get('settings', 'default_target_language')
                self.debug('default target language set to: %s' % self._defaultTargetLang)
        
        except Exception, e:
            self.error('could not read default target language setting: %s' % e)
            self.debug('using default setting as target language: %s' % self._defaultTargetLang)

        try:
            
            self._displayTranslatorName = self.config.getboolean('settings', 'display_translator_name')
            self.debug('translator name display set to: %r' % self._displayTranslatorName)
            
        except Exception, e:            
            self.error('could not read translator name display setting: %s' % e)
            self.debug("using default setting for translator name display: %r" % self._displayTranslatorName)

        try:
            
            self._translatorName = self.config.get('settings', 'translator_name')
            self.debug('translator name set to: %s' % self._translatorName)
            
        except Exception, e:
            self.error('could not read translator name setting: %s' % e)
            self.debug('using default setting for translator name: %s' % self._translatorName)
        
        try:
            
            self._messagePrefix = self.config.get('settings', 'message_prefix')
            self.debug('message prefix set to: %s' % self._messagePrefix)
            
        except Exception, e:
            self.error('could not read message prefix setting: %s' % e)
            self.debug('using default setting for message prefix: %s' % self._messagePrefix)
        
        try:
            
            if self.config.getint('settings', 'min_sentence_length') <= 0:
                self.warning('minimum sentence length must be positive: using default: %d' % self._minSentenceLength)
            else:
                self._minSentenceLength = self.config.getint('settings', 'min_sentence_length')
                self.debug('minimum sentence length set to: %d' % self._minSentenceLength)
        
        except Exception, e:
            self.error('could not read minimum sentence length setting: %s' % e)
            self.debug('using default setting for minimum sentence length: %d' % self._minSentenceLength)
        
        try:
            
            if not self.config.get('settings', 'microsoft_client_id'):
                self.warning('microsoft translator client id not specified: plugin will be disabled')
            else:     
                self._microsoftClientId = self.config.get('settings', 'microsoft_client_id')
                self.debug('microsoft translator client id set to: %s' % self._microsoftClientId)
            
        except Exception, e:
            self.error('could not read microsoft translator client id setting: %s' % e)
            self.debug('could not start plugin without microsoft client id.: plugin will be disabled')
        
        try:
            
            if not self.config.get('settings', 'microsoft_client_secret'):
                self.warning('microsoft translator client secret not specified: plugin will be disabled')
            else:     
                self._microsoftClientSecret = self.config.get('settings', 'microsoft_client_secret')
                self.debug('microsoft translator client secret set to: %s' % self._microsoftClientSecret)
            
        except Exception, e:
            self.error('could not read microsoft translator client secret setting: %s' % e)
            self.debug('could not start plugin without microsoft client secret: plugin will be disabled')
    
        # checking correct microsoft Translator api service configuration
        if not self._microsoftClientId or not self._microsoftClientSecret:
            self.debug('microsoft translator is not configured properly: disabling the plugin...')
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
        self.registerEvent(b3.events.EVT_CLIENT_SAY)
        
    ############################################################################################    
    # ######################################## EVENTS ######################################## #
    ############################################################################################        

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == b3.events.EVT_CLIENT_SAY:
            self.onSay(event)

    def onSay(self, event):
        """\
        Handle say events
        """
        ms = event.data.strip()
        cl = event.client

        # not enough length for !translast
        # and !transauto so just skip it
        if len(ms) < self._minSentenceLength:
            return
            
        # check if a b3 command has been issued and if so do nothing
        if ms[0] not in (self._adminPlugin.cmdPrefix, self._adminPlugin.cmdPrefixLoud, self._adminPlugin.cmdPrefixBig):

            # storing for future use
            self._lastSentenceSaid = ms

            # we have now to send a translation to all the
            # clients that enabled the automatic translation
            for c in self.console.clients.getList():

                # skip if the same client
                if c.cid == cl.cid:
                    continue

                # skip if automatic translation is disabled
                if not c.isvar(self,'transauto') or c.var(self,'transauto').value:
                    continue

                thread.start_new_thread(self.translate, (c, None, ms, c.var(self,'translang').value, ''))

    ############################################################################################    
    # ####################################### FUNCTIONS ###################################### #
    ############################################################################################
          
    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None    

    def getMicrosoftAccessToken(self, client_id, client_secret):
        """\
        Make an HTTP POST request to the token service, and return the access_token
        See description here: http://msdn.microsoft.com/en-us/library/hh454949.aspx
        """
        data = urllib.urlencode(dict(client_id=client_id,
                                     client_secret=client_secret,
                                     grant_type='client_credentials',
                                     scope='http://api.microsofttranslator.com'))
    
        try:
    
            req = urllib2.Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13')
            req.add_data(data)
            res = urllib2.urlopen(req)
            rtn = json.loads(res.read())
    
            if 'access_token' in rtn.keys():
                return rtn['access_token']
    
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                self.debug('could not connect to the microsoft translator server: %s' % e.reason)
            elif hasattr(e, 'code'):
                self.debug('microsoft translator server error: %s' % (str(e.code)))
        
        except TypeError, e:
            self.debug('translation using microsoft translator server failed: %s' % e)

        return False
     
    def toByteString(self, s):
        """
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given
        """
        if isinstance(s, str): 
            return s
        return s.encode('utf-8')   

    def sanitize(self, s):
        """\
        Sanitize the given string
        """
        # remove XML/HTML markup
        s = re.sub(r'<[^>]*>', '', s)

        # remove color codes
        s = re.sub('\^[0-9]', '', s)

        # replace unpritable chars
        s = s.replace('ß', 'ss')
        s = s.replace('ü', 'ue')
        s = s.replace('ö', 'oe')
        s = s.replace('ä', 'ae')
        s = s.replace('à', 'a')
        s = s.replace('è', 'e')
        s = s.replace('é', 'e')
        s = s.replace('ì', 'i')
        s = s.replace('ò', 'o')
        s = s.replace('ù', 'u')
        s = s.replace('ç', 'c')
        s = s.replace('€', 'eu')
        s = s.replace('$', 'us')
        s = s.replace('£', 'lt')
        s = s.replace('%', 'pc')
        s = s.replace('"', "''")

        return s.strip()

    def translate(self, client, cmd, sentence, target, source):
        """\
        Translate the given sentence in the specified target language
        """
        try:
            
            self.debug('requesting microsoft translator api access token.....')
            token = self.getMicrosoftAccessToken(self._microsoftClientId, self._microsoftClientSecret)
        
            if not token:
                self.warning('could not retrieve microsoft translator api access token')
                client.message('^7Unable to translate')
                return
            
            data = dict(text=self.toByteString(sentence), to=target)
            
            if source != '':
                data['from'] = source
            
            req = urllib2.Request('http://api.microsofttranslator.com/v2/Http.svc/Translate?' + urllib.urlencode(data))
            req.add_header('Authorization', 'Bearer ' + token)
            res = urllib2.urlopen(req)
            rtn = res.read()
            
            # formatting the string
            msg = self.sanitize(rtn)

            if not msg:
                self.debug('translation failed: empty string returned')
                client.message('^7Unable to translate')
                return
            
            self.debug('message translated [ source [%s] : %s | result [%s] : %s ]' % (source, sentence, target, msg))

            # set the correct message prefix
            name = self._translatorName if self._displayTranslatorName else ''
            
            if cmd is None:
                client.message('%s%s%s' % (name, self._messagePrefix, msg))
            else:
                cmd.sayLoudOrPM(client, '%s%s%s' % (name, self._messagePrefix, msg))

            return

        except urllib2.URLError, e:
            
            if hasattr(e, 'reason'):
                self.debug('could not connect to the microsoft translator server: %s' % e.reason)
            elif hasattr(e, 'code'):
                self.debug('microsoft translator server error: %s' % (str(e.code)))

        except TypeError, e:
            self.debug('translation failed: %s' % e)

        # inform of the failure
        client.message('^7Unable to translate')
    
    ############################################################################################    
    # ####################################### COMMANDS ####################################### #
    ############################################################################################  

    def cmd_translate(self, data, client, cmd=None):
        """\
        [<source>*<target>] <sentence> - Translate a sentence
        """
        if not data: 
            client.message('^7Invalid data, try ^3!^7help translate')
            return

        src = self._defaultSourceLang
        tgt = self._defaultTargetLang

        if '*' in data:
            # language codes specified for this translation
            match = self._messageParseRegEx.match(data)
            if not match:
                client.message('Invalid data. Try ^3!^7help translate')
                return

            src = match.group('source')
            tgt = match.group('target')
            msg = match.group('sentence')

            self.verbose('detected language codes: checking if those codes are supported by the plugin')
            
            if not src:
                self.verbose('source language not specified: using default source language for the translation')
            elif src not in self._languages.keys():
                self.verbose('invalid source language [%s] in !translate command: unable to translate' % src)
                client.message('^7Invalid source language specified, try ^3!^7translang')
                return
            else:
                # just print in the log so we know that the source language is supported
                self.verbose('performing translation using specified source language [%s]' % src)
                
            if not tgt:
                tgt = self._defaultTargetLang
                self.verbose('target language not specified: using default target language for the translation')
            elif tgt not in self._languages.keys():
                self.verbose('invalid target language [%s] in !translate command: unable to translate' % tgt)
                client.message('^7Invalid target language specified, try ^3!^7translang')
                return
            else:
                # just print in the log so we know that the target language is supported
                self.verbose('performing translation using specified target language [%s]' % tgt)

            data = msg
        
        data = re.sub('\^[0-9]', '', data)
        thread.start_new_thread(self.translate, (client, cmd, data, tgt, src))

    def cmd_translast(self, data, client, cmd=None):
        """\
        [<target>] - Translate the latest available sentence from the chat
        """
        if not self._lastSentenceSaid:
            client.message('^7Unable to translate last message')
            return
        
        tgt = self._defaultTargetLang
        
        if data:
            
            self.verbose('detected language code: checking if it\'s supported by the plugin')
            
            if data not in self._languages.keys():
                self.verbose('invalid target language [%s] in !translast command: unable to translate' % data)
                client.message('^7Invalid target language specified, try ^3!^7translang')
                return
            else:
                tgt = data
                self.verbose('performing translation using specified target language[\'%s\']' % data)
        
        thread.start_new_thread(self.translate, (client, cmd, self._lastSentenceSaid, tgt, ''))
    
    def cmd_transauto(self, data, client, cmd=None):
        """\
        <on|off> [<language>] - Turn on and off the automatic translation
        """
        if not data: 
            client.message('^7Invalid data, try ^3!^7help transauto')
            return

        match = self._transautoParseRegEx.match(data)
        if not match:
            client.message('Invalid data. Try ^3!^7help transauto')
            return

        option = match.group('option')
        target = match.group('target')

        if option == 'on':

            if target:
                # target language specified
                if target not in self._languages.keys():
                    self.debug('invalid target language [%s] in !transauto command' % target)
                    client.message('^7Invalid target language specified, try ^3!^7translang')
                    return
            elif client.isvar(self, 'translang'):
                # using previously stored target language
                target = client.var(self, 'translang').value
            else:
                # using default targt language
                target = self._defaultTargetLang

            client.setvar(self, 'transauto', True)
            client.setvar(self, 'translang', target)
            client.message('^7Transauto: ^2enabled^7. Language: ^3%s' % self._languages[target])
        
        elif option == 'off':
            
            client.setvar(self, 'transauto', False)
            client.message('^7Transauto: ^1disabled')

    def cmd_translang(self, data, client, cmd=None):
        """\
        Display a list of available language codes
        """
        codes = []
        for k, v in self._languages.items():
            codes.append('^2%s ^3: ^7%s' % (k, v))

        cmd.sayLoudOrPM(client, '^3, '.join(codes))