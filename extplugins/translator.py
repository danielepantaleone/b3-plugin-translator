# coding: utf-8
#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) Copyright (C) 2012 Fenix <fenix@urbanterror.info)
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
__version__ = '2.0.1'

import b3
import b3.plugin
import b3.events
import thread
import urllib, urllib2
import json
import re

class TranslatorPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    _lastMessage = ''
    
    _settings = { 
        'default_source_language' : '',
        'default_target_language' : 'en',
        'display_translator_name' : True,
        'translator_name'         : '^7[^1TRANSLATOR^7] ',
        'message_prefix'          : '^3',
        'min_sentence_length'     : 6,
        'microsoft_client_id'     : '',
        'microsoft_client_secret' : '' 
    }
    
    _languages = { 
        'ca' : 'Catalan',
        'cs' : 'Czech',
        'da' : 'Danish',
        'nl' : 'Dutch',
        'en' : 'English',
        'et' : 'Estonian',
        'fi' : 'Finnish',
        'fr' : 'French',
        'de' : 'German',
        'el' : 'Greek',
        'ht' : 'Haitian Creole',
        'he' : 'Hebrew',
        'hi' : 'Hindi',
        'hu' : 'Hungarian',
        'id' : 'Indonesian',
        'it' : 'Italian',
        'lv' : 'Latvian',
        'lt' : 'Lithuanian',
        'no' : 'Norwegian',
        'pl' : 'Polish',
        'pt' : 'Portuguese',
        'ro' : 'Romanian',
        'sl' : 'Slovenian',
        'es' : 'Spanish',
        'sv' : 'Swedish',
        'th' : 'Thai',
        'tr' : 'Turkish',
        'uk' : 'Ukrainian',
    }
    
    
    def onLoadConfig(self):
        """\
        Load the configuration file
        """
        self.verbose('Loading configuration file...')
        
        try:
            
            if not self.config.get('settings', 'default_source_language'):
                self.debug('Default source language detected as empty. Using automatic language detection')
            elif not self._languages.has_key(self.config.get('settings', 'default_source_language')):
                self.warn('Invalid language code specified as default source language. Using automatic language detection')
            else:
                self._settings['default_source_language'] = self.config.get('settings', 'default_source_language')
                self.debug('Default source language set to: %s' % self._languages[self._settings['default_source_language']])
        
        except Exception, e:
            self.error('Unable to read default source language setting: %s' % e)
            self.debug('Using automatic language detection as source language')
        
        try:
            
            if not self._languages.has_key(self.config.get('settings', 'default_target_language')):
                self.warn('Invalid language code specified as default target language. Using default setting: %s' % self._languages[self._settings['default_target_language']])
            else:
                self._settings['default_target_language'] = self.config.get('settings', 'default_target_language')
                self.debug('Default target language set to: %s' % self._languages[self._settings['default_target_language']])
        
        except Exception, e:
            self.error('Unable to read default target language setting: %s' % e)
            self.debug('Using default setting as target language: %s' % self._languages[self._settings['default_target_language']])

        
        try:
            
            self._settings['display_translator_name'] = self.config.getboolean('settings', 'display_translator_name')
            self.debug('Translator name display set to: %r' % self._settings['display_translator_name'])
            
        except Exception, e:            
            self.error('Unable to read translator name display setting: %s' % e)
            self.debug("Using default setting for translator name display: %r" % self._settings['display_translator_name'])

        try:
            
            self._settings['translator_name'] = self.config.get('settings', 'translator_name')
            self.debug('Translator name set to: %s' % self._settings['translator_name'])
            
        except Exception, e:
            self.error('Unable to read translator name setting: %s' % e)
            self.debug('Using default setting for translator name: %s' % self._settings['translator_name'])
        
        try:
            
            self._settings['message_prefix'] = self.config.get('settings', 'message_prefix')
            self.debug('Message prefix set to: %s' % self._settings['message_prefix'])
            
        except Exception, e:
            self.error('Unable to read message prefix setting: %s' % e)
            self.debug('Using default setting for message prefix: %s' % self._settings['message_prefix'])
        
        try:
            
            if self.config.getint('settings', 'min_sentence_length') <= 0:
                self.warn('Minimum sentence length value must be positive. Using default setting: %d' % self._settings['min_sentence_length'])
            else:
                self._settings['min_sentence_length'] = self.config.getint('settings', 'min_sentence_length')
                self.debug('Minimum sentence length set to: %d' % self._settings['min_sentence_length'])
        
        except Exception, e:
            self.error('Unable to read minimum sentence length setting: %s' % e)
            self.debug('Using default setting for minimum sentence length: %d' % self._settings['min_sentence_length'])
        
        try:
            
            if not self.config.get('settings', 'microsoft_client_id'):
                self.warn('Microsoft translator client id not specified. Plugin will be disabled')
            else:     
                self._settings['microsoft_client_id'] = self.config.get('settings', 'microsoft_client_id')
                self.debug('Microsoft translator client id set to: %s' % self._settings['microsoft_client_id'])
            
        except Exception, e:
            self.error('Unable to read Microsoft translator client id setting: %s' % e)
            self.debug('Unable to start plugin without Microsoft client id. Plugin will be disabled')
        
        try:
            
            if not self.config.get('settings', 'microsoft_client_secret'):
                self.warn('Microsoft translator client secret not specified. Plugin will be disabled')
            else:     
                self._settings['microsoft_client_secret'] = self.config.get('settings', 'microsoft_client_secret')
                self.debug('Microsoft translator client secret set to: %s' % self._settings['microsoft_client_secret'])
            
        except Exception, e:
            self.error('Unable to read Microsoft translator client secret setting: %s' % e)
            self.debug('Unable to start plugin without Microsoft client secret. Plugin will be disabled')
    
        # Checking correct Microsoft Translator API service configuration
        if not self._settings['microsoft_client_id'] or not self._settings['microsoft_client_secret']:
            self.debug('Disabling the plugin...')
            self.disable()
        

    def onStartup(self):
        """\
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:    
            self.error('Unable to start without admin plugin')
            return False
        
        # Register our commands
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
        
        # Register the events needed
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
        message = event.data.strip()
        client = event.client
        
        if len(message) >= self._settings['min_sentence_length']:
            
            # Check if a b3 command has been issued and if so do nothing
            if message[0] not in (self._adminPlugin.cmdPrefix, self._adminPlugin.cmdPrefixLoud, self._adminPlugin.cmdPrefixBig):
                
                # Storing for future use
                self._lastMessage = message
                
                # We have now to send a translation to all the 
                # clients that enabled the automatic translation
                for c in self.console.clients.getList():
                    
                    if c.cid == client.cid:
                        continue
                    
                    if c.isvar(self,'transauto') and c.var(self,'transauto').value == True:
                        thread.start_new_thread(self.translate, (c, None, message, c.var(self,'translang').value, ''))
                        
                
    ############################################################################################    
    # ####################################### FUNCTIONS ###################################### #
    ############################################################################################
        
          
    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None    
                    
    
    def getAccessToken(self, client_id, client_secret):
        """
        Make an HTTP POST request to the token service, and return the access_token
        See description here: http://msdn.microsoft.com/en-us/library/hh454949.aspx
        """
        data = urllib.urlencode({ 'client_id'     : client_id,
                                  'client_secret' : client_secret,
                                  'grant_type'    : 'client_credentials',
                                  'scope'         : 'http://api.microsofttranslator.com' })
    
        try:
    
            request = urllib2.Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13')
            request.add_data(data) 
            response = urllib2.urlopen(request)
            response_data = json.loads(response.read())
    
            if response_data.has_key('access_token'):
                return response_data['access_token']
            else:
                return False
    
        except urllib2.URLError, e:
            if hasattr(e,'reason'):
                self.debug('Could not connect to the Microsoft Translator server: %s' % (e.reason))
                return False
            elif hasattr(e, 'code'):
                self.debug('Microsoft Translator server error: %s' % (str(e.code)))
                return False
        
        except TypeError, e:
            self.debug('Translation using Microsoft Translator API service failed. TypeError exception: %s' % e)
            return False
     
     
    def toByteString(self, s):
        """
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given
        """
        if isinstance(s, str): 
            return s
        return s.encode('utf-8')   
    
    
    def replaceSpecialChars(self, s):
        """\
        Replace special chars
        """
        s = s.replace('ß','ss')
        s = s.replace('ü','ue')
        s = s.replace('ö','oe')
        s = s.replace('ä','ae')
        s = s.replace('à','a')
        s = s.replace('è','e')
        s = s.replace('é','e')
        s = s.replace('ì','i')
        s = s.replace('ò','o')
        s = s.replace('ù','u')
        s = s.replace('ç','c')
        s = s.replace('€','eu')
        s = s.replace('$','us')
        s = s.replace('£','lt')
        s = s.replace('%','pc')
        s = s.replace('"',"''")
        
        return s
                             
                             
    def printSupportedLanguages(self, client, cmd):
        """\
        Display a list of supported language codes and the description
        """  
        codes = []
        for k,v in self._languages.items():
            codes.append('^2%s ^3: ^7%s' % (k, v))
        
        cmd.sayLoudOrPM(client, '^3, '.join(codes))

    
    def stripColors(self, s):
        """
        Remove color codes from a given string
        """
        return re.sub('\^[0-9]{1}','', s)
    
    
    def translate(self, client, cmd, sentence, target_language, source_language):
        """\
        Translate the given sentence in the specified target language
        """
        try:
            
            self.debug('Requesting Microsoft Translator API access token.....')
            token = self.getAccessToken(self._settings['microsoft_client_id'], self._settings['microsoft_client_secret'])
        
            if not token:
                self.warn('Unable to retrieve Microsoft Translator API access token using provided credentials: [ client id: %s | secret: %s ].' % (self._settings['microsoft_client_id'], self._settings['microsoft_client_secret']))
                client.message('^7Unable to translate')
                return
            
            data = { 'text' : self.toByteString(sentence), 
                     'to'   : target_language }
            
            if source_language != '':  
                data['from'] = source_language
            
            request = urllib2.Request('http://api.microsofttranslator.com/v2/Http.svc/Translate?' + urllib.urlencode(data))
            request.add_header('Authorization', 'Bearer ' + token)
            response = urllib2.urlopen(request)
            rtn = response.read()
            
            # Formatting the string
            message = re.sub(r'<[^>]*>', '', rtn)           # Remove XML markup tags    
            message = self.replaceSpecialChars(message)     # Replace some languages special chars
            message = message.strip()                       # Remove unnecessary white spaces
            
            if not message:
                self.debug('Translation using Microsoft Translator API service failed: empty string returned')
                client.message('^7Unable to translate')
                return False
            
            self.debug('Message correctly translated [ source : %s | result : %s ]' % (sentence, message))
            name_prefix = self._settings['translator_name'] if self._settings['display_translator_name'] else ''
            
            if cmd is None:
                # No command has been invoked so just display the translation to the given client
                client.message('%s%s%s' % (name_prefix, self._settings['message_prefix'], message))
                return True
            else:
                # A command has been issued for the translation so take care of the command prefix
                cmd.sayLoudOrPM(client, '%s%s%s' % (name_prefix, self._settings['message_prefix'], message))
                return True
            
        except urllib2.URLError, e:
            
            if hasattr(e,'reason'):
                self.debug('Could not connect to the Microsoft Translator server: %s' % (e.reason))
                client.message('^7Unable to translate')
                return
            elif hasattr(e, 'code'):
                self.debug('Microsoft Translator server error: %s' % (str(e.code)))
                client.message('^7Unable to translate')
                return
        
        except TypeError, e:
            self.debug('Translation failed. TypeError exception: %s.' % e)
            client.message('^7Unable to translate')
            return
        
    
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

        source_language = self._settings['default_source_language']
        target_language = self._settings['default_target_language']
        
        language = data.split(' ', 1)[0]
        (source, separator, target) = language.partition('*')
        
        if separator == '*':
            
            self.verbose('Detected language codes: checking if those codes are supported by the plugin')
            
            if not source:
                self.verbose('Source language not specified. Using default source language for the translation')
            elif source not in self._languages.keys():
                self.verbose('Invalid source language specified [\'%s\'] in !translate command: unable to translate' % source)
                client.message('^7Invalid source language specified, try ^3!^7translang')
                return
            else:
                self.verbose('Performing translation using specified source language[\'%s\']' % source)
                source_language = source
                
            if not target:
                self.verbose('Target language not specified. Using default target language for the translation')
            elif source not in self._languages.keys():
                self.verbose('Invalid target language specified [\'%s\'] in !translate command: unable to translate' % target)
                client.message('^7Invalid target language specified, try ^3!^7translang')
                return
            else:
                self.verbose('Performing translation using specified target language[\'%s\']' % target)
                target_language = target
            
            # Since the language codes has been specified (at least one)
            # we are going to remove them from the sentence to be translated
            data = data.split(' ', 1)[1]
        
        data = self.stripColors(data)
        thread.start_new_thread(self.translate, (client, cmd, data, target_language, source_language))


    def cmd_translast(self, data, client, cmd=None):
        """\
        [<target>] - Translate the latest available sentence from the chat
        """
        if not self._lastMessage:
            client.message('^7Unable to translate last message')
            return
        
        target_language = self._settings['default_target_language']
        
        if data:
            
            self.verbose('Detected language code: checking if it\'s supported by the plugin')
            
            if data not in self._languages.keys():
                self.verbose('Invalid target language specified [\'%s\'] in !translast command: unable to translate' % data)
                client.message('^7Invalid target language specified, try ^3!^7translang')
                return
            else:
                self.verbose('Performing translation using specified target language[\'%s\']' % data)
                target_language = data
        
        thread.start_new_thread(self.translate, (client, cmd, self._lastMessage, target_language, ''))
        
    
    def cmd_transauto(self, data, client, cmd=None):
        """\
        <on|off> [<language>] - Turn on and off the automatic translation
        """
        if not data: 
            client.message('^7Invalid data, try ^3!^7help transauto')
            return
        
        params = data.split(' ')
        
        if (len(params) != 1 and len(params) != 2) or (params[0] not in ('on','off')):
            client.message('^7Invalid data, try ^3!^7help transauto')
            return
        
        if params[0] == 'on':
            
            target_language = self._settings['default_target_language']
            
            if len(params) == 2:
                if params[1] not in self._languages.keys():
                    self.debug('Invalid target language specified [\'%s\'] in !transauto command' % params[1])
                    client.message('^7Invalid target language specified, try ^3!^7translang')
                    return
                
                target_language = params[1]
           
            client.setvar(self, 'transauto', True)
            client.setvar(self, 'translang', target_language)
            client.message('^7Automatic translation: ^2ON^7. Language: ^4%s' % self._languages[target_language])
        
        elif params[0] == 'off':
            
            client.setvar(self, 'transauto', False)
            client.message('^7Automatic translation: ^1OFF')
                
        
    def cmd_translang(self, data, client, cmd=None):
        """\
        Display a list of available language codes
        """
        thread.start_new_thread(self.printSupportedLanguages, (client, cmd))
        