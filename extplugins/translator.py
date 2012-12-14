# coding: utf-8
#
# Translator Plugin for BigBrotherBot
# Copyright (C) 2012 Fenix
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
#
# CHANGELOG
#
# 02/06/2012 - 1.0
#  - first release
#
# 26/08/2012 - 1.1
#  - moved teamColor and stripColors into plugin class for standard b3 installation compatibility
#  - fixed an issue Microsoft Translator related
#  - bugfixes and code cleanup
#
# 11/09/2012 - 1.1.1
#  - fixed typo [thanks 82ndAB.Bravo17]
#
# 14/12/2012 - 1.2
#  - fixed some words spelling
#  - do not display translation, if the translator service returned back the given string


__author__ = 'Fenix - http://goreclan.net'
__version__ = '1.2'

import b3
import b3.plugin
import b3.events
import thread
import urllib, urllib2
import json
import re
import os
import platform

class TranslatorPlugin(b3.plugin.Plugin):
    
    _adminPlugin = None
    
    _defaultSourceLang = ''
    _defaultTargetlang = 'en'
    _favoriteTranslator = 'Google'
    _displayTranslatorName = False
    _minSentenceLength = 8
    _transTextColorPrefix = '^3'
    _microsoftClientId = ''
    _microsoftClientSecret = ''
    
    _mt_name = '^7[^4Microsoft^7]'
    _gt_name = '^7[^4Google^7]'
    
    _lastSentence = ''
    _colorCodes = ('^1','^2','^3','^4','^5','^6','^7','^8')
    _translators = ('Google', 'Microsoft')
    
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
        Load the config
        """
        self.verbose('Loading config')
        
        # Loading default source language configuration
        try:
            if not self._languages.has_key(self.config.get('settings', 'defaultSourceLang')):
                self.debug('Invalid or empty language code in default source language configuration. Using automatic language detection.')
            else:
                self._defaultSourceLang = self.config.get('settings', 'defaultSourceLang')
                self.debug('Default source language set to "%s".' % self._defaultSourceLang)
        except:
            self.error('Exception launched while loading default source language configuration. Check your XML config file.')
            pass
        
        # Loading default target language configuration
        try:
            if not self._languages.has_key(self.config.get('settings', 'defaultTargetLang')):
                self.debug('Invalid or empty language code in default target language configuration. Using default language code: "%s".' % self._defaultTargetlang)
            else:
                self._defaultTargetLang = self.config.get('settings', 'defaultTargetLang')
                self.debug('Default target language set to "%s".' % self._defaultTargetLang)
        except:
            self.error('Exception launched while loading default target language configuration. Check your XML config file.')
            pass
        
        # Loading favorite translator configuration
        try:
            if self.config.get('settings', 'favoriteTranslator') not in self._translators:
                self.debug('Invalid or empty value in favorite translator configuration. Using default translator: "%s".' % self._favoriteTranslator)
            else:
                self._favoriteTranslator = self.config.get('settings', 'favoriteTranslator')
                self.debug('Favorite translator set to "%s".' % self._favoriteTranslator)
        except:
            self.error('Exception launched while loading favorite translator configuration. Check your XML config file.')
            pass
        
        # Loading display translator name configuration
        try:
            self._displayTranslatorName = self.config.getboolean('settings', 'displayTranslatorName')
        except:
            self.error('Exception launched while loading display translator name configuration. Check your XML config file.')
            pass
        
        # Loading minimum sentence length for !translast command
        try:
            if self.config.getint('settings', 'minSentenceLength') <= 0:
                self.debug('Minimum sentence length value must be positive. Using default value: "%d".' % self._minSentenceLength)
            else:
                self._minSentenceLength = self.config.getint('settings', 'minSentenceLength')
                self.debug('Minimum sentence length set to "%d".' % self._minSentenceLength)
        except:
            self.error('Exception launched while loading minimum sentence length configuration. Check your XML config file.')
            pass
                
        # Loading translator color code prefix
        try:
            if self.config.get('settings', 'transTextColorPrefix') not in self._colorCodes:
                self.debug('Invalid or empty value in translation color code prefix configuration. Using default color code: "%s"' % self._transTextColorPrefix)
            else:
                self._transTextColorPrefix = self.config.get('settings', 'transTextColorPrefix')
                self.debug('Translation color code prefix set to "%s"' % self._transTextColorPrefix)
        except:
            self.error('Exception launched while loading translation color code prefix configuration. Check your XML config file.')
            pass
        
        # Loading Microsoft translator configuration
        try:
            if self.config.get('settings', 'microsoftClientId') == '':
                self.debug('Microsoft Translator API service client ID not specified. Microsoft Translator will be disabled.')
            else:
                self._microsoftClientId = self.config.get('settings', 'microsoftClientId')
                self.debug('Microsoft Translator API service client ID set to "%s"' % self._microsoftClientId)
        except:
            self.error('Exception launched while loading Microsoft Translator API service client ID configuration. Check your XML config file.')
            pass
        
        try:
            if self.config.get('settings', 'microsoftClientSecret') == '':
                self.debug('Microsoft Translator API service client secret not specified. Microsoft Translator will be disabled.')
            else:
                self._microsoftClientSecret = self.config.get('settings', 'microsoftClientSecret')
                self.debug('Microsoft Translator API service client secret set to "%s"' % self._microsoftClientSecret)
        except:
            self.error('Exception launched while loading Microsoft Translator API service client secret configuration. Check your XML config file.')
            pass
        
        # Checking favorite translator correct configuration
        if self._favoriteTranslator == 'Microsoft':
            
            if self._microsoftClientId == '' or self._microsoftClientSecret == '':
                self._favoriteTranslator = 'Google'
                self.debug('Disabling Microsoft Translator. Microsoft Translator API service credentials not specified.')
                self.debug('Favorite translator set to "%s".' % self._favoriteTranslator)
                if platform.system() in ('Windows', 'Microsoft'):
                    self.debug('Disabling Google Translator. You need a UNIX like operating system in order to use this functionality.')
                    self.debug('No other translation options available. Disabling the plugin.')
                    self.disable()
                    
        elif self._favoriteTranslator == 'Google':
            
            if platform.system() in ('Windows', 'Microsoft'):
                self._favoriteTranslator = 'Microsoft'
                self.debug('Disabling Google Translator. You need a UNIX like operating system in order to use this functionality.')
                self.debug('Favorite translator set to "%s".' % self._favoriteTranslator)
                if self._microsoftClientId == '' or self._microsoftClientSecret == '':
                    self.debug('Disabling Microsoft Translator. Microsoft Translator API service credentials not specified.')
                    self.debug('No other translation options available. Disabling the plugin.')
                    self.disable()


    def onStartup(self):
        """\
        Initialize plugin settings
        """
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:    
            self.error('Could not find admin plugin')
            return False
        
        # Register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2: cmd, alias = sp

                func = self.getCmd(cmd)
                if func: self._adminPlugin.registerCommand(self, cmd, level, func, alias)
        
        # Register the events needed
        self.registerEvent(b3.events.EVT_CLIENT_SAY)

        
    # ------------------------------------- Handle Events ------------------------------------- #        
        

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == b3.events.EVT_CLIENT_SAY:
            self.onSay(event)
            
                
    # --------------------------------------- Functions --------------------------------------- #
        
          
    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
        return None    
    
    
    def onSay(self, event):
        """\
        Handle say events
        """
        sentence = event.data.strip()
        client = event.client
        if len(sentence) >= self._minSentenceLength:
            if sentence[0] not in (self._adminPlugin.cmdPrefix, self._adminPlugin.cmdPrefixLoud, self._adminPlugin.cmdPrefixBig):
                # The given string is a correct sentence and not a b3 command
                # We can add the sentence to the _lastSentence variable
                self._lastSentence = sentence
                
                # We have now to send a translation to all the clients that enabled the automatic translation
                for c in self.console.clients.getList():
                    # Skipping translation for sentences said by the same guy
                    if c.cid != client.cid:
                        if c.isvar(self,'transauto') and c.var(self,'transauto').value == True:
                            thread.start_new_thread(self.translate, (c, None, sentence, c.var(self,'translang').value, ''))
                    
    
    def getMicrosoftAccessToken(self, client_id, client_secret):
        """
        Make an HTTP POST request to the token service, and return the access_token
        See description here: http://msdn.microsoft.com/en-us/library/hh454949.aspx
        """
        data = urllib.urlencode({
                'client_id' : client_id,
                'client_secret' : client_secret,
                'grant_type' : 'client_credentials',
                'scope' : 'http://api.microsofttranslator.com'
                })
    
        try:
    
            request = urllib2.Request('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13')
            request.add_data(data) 
            response = urllib2.urlopen(request)
            response_data = json.loads(response.read())
    
            if response_data.has_key('access_token'):
                # We got a proper token in the response
                return response_data['access_token']
            else:
                # No token received or bad one
                # We'll handle this somewhere else
                return False
    
        except urllib2.URLError, e:
            if hasattr(e,'reason'):
                self.debug('Could not connect to the Microsoft Translator server: %s.' % (e.reason))
                return False
            elif hasattr(e, 'code'):
                self.debug('Microsoft Translator server error: %s.' % (str(e.code)))
                return False
        
        except TypeError, e:
            self.debug('Translation using Microsoft Translator API service failed. TypeError exception: %s.' % e)
            return False
     
     
    def toByteString(self, s):
        """
        Convert the given unicode string to a bytestring, using utf-8 encoding.
        If it is already a bytestring, just return the string given
        """
        if isinstance(s, str): return s
        else: return s.encode('utf-8')   
    
    
    def replaceSpecialChars(self, s):
        """\
        Replace special chars
        """
        # German chars
        s = s.replace('ß','ss')
        s = s.replace('ü','ue')
        s = s.replace('ö','oe')
        s = s.replace('ä','ae')
        
        # Italian chars
        s = s.replace('à','a')
        s = s.replace('è','e')
        s = s.replace('é','e')
        s = s.replace('ì','i')
        s = s.replace('ò','o')
        s = s.replace('ù','u')
        
        # French chars
        s = s.replace('ç','c')
        
        # Special chars
        s = s.replace('€','eu')
        s = s.replace('$','us')
        s = s.replace('£','lt')
        s = s.replace('%','pc')
        s = s.replace('"',"''")
        
        return s
        
        
    def translateWithGoogle(self, client, cmd, sentence, targetLang, sourceLang = ''):
        """\
        Translate the given sentence using Google Translate API service
        """
        try:
            
            if platform.system() in ('Windows', 'Microsoft'):
                # Should never happen, but still...
                self.debug('Cannot perform translation using Google Translate API service. You need a UNIX like operating system in order to use this functionality.')
                return False
                
            self.debug('Performing a translation using Google Translate API service')
        
            # Replacing some characters
            text = sentence
            text = text.replace(' ', '%20')
            text = text.replace('"', '%22')
            text = text.replace('#', '%23')
            text = text.replace('&', '%26')
            text = text.replace('=', '%3D')
            text = text.replace('?', '%3F')
            
            # Sending the request through wget
            result = os.popen('wget -q --user-agent="SeaMonkey" "translate.google.com/translate_a/t?client=t&text=' + text + '&hl=en&sl=' + sourceLang + '&tl=' + targetLang + '&multires=1&otf=1&ssel=0&tsel=0&sc=1" -O -')
            message = result.readline()
            result.close();
            
            # Getting the translation
            # and formatting the string
            message = message[4:]
            message = message[:message.find('"')]
            message = message.lower()
            message = self.replaceSpecialChars(message)
            message = message.strip()
            message = message.capitalize()
            
            if message != '':
                # If the translated message is the same of the said sentence, do not display any message
                if message.lower() == sentence.lower().strip():
                    self.debug('Skipping translation display. Google Translate API service returned the given text string.')
                    return False
                
                self.displayTranslation(client, cmd, message,'Google')
                self.debug('Sentence correctly translated using Google Translate API service.')    
                return True
            else:
                self.debug('Translation using Google Translate API service failed. Empty string returned.')
                return False
            
        except TypeError, e:
            self.debug('Translation using Google Translate API service failed. TypeError exception: %s.' % e)
            return False
            

    def translateWithMicrosoft(self, client, cmd, sentence, targetLang, sourceLang = ''):
        """\
        Translate the given sentence using Microsoft Translator API service
        """
        try:
            
            self.debug('Performing a translation using Microsoft Translator API service.')
            
            token = self.getMicrosoftAccessToken(self._microsoftClientId, self._microsoftClientSecret)
            if not token:
                self.debug('Unable to get Microsoft Translator API access token using provided credentials: [Client ID: %s | Secret: %s].' % (self._microsoftClientId, self._microsoftClientSecret))
                return False
            else:
                # We got a proper access token. Trying to translate the sentence
                data = { 'text' : self.toByteString(sentence), 'to' : targetLang }
                if sourceLang != '':  data['from'] = sourceLang
                
                request = urllib2.Request('http://api.microsofttranslator.com/v2/Http.svc/Translate?' + urllib.urlencode(data))
                request.add_header('Authorization', 'Bearer ' + token)
                response = urllib2.urlopen(request)
                rtn = response.read()
                
                # Removing XML tags from the response
                # and formatting the string
                message = re.sub(r'<[^>]*>', '', rtn)
                message = message.lower()
                message = self.replaceSpecialChars(message)
                message = message.strip()
                message = message.capitalize()
                
                if message != '':
                    # If the translated message is the same of the said sentence, do not display any message
                    if message.lower() == sentence.lower().strip():
                        self.debug('Skipping translation display. Microsoft Translator API service returned the given text string.')
                        return False
                    
                    self.displayTranslation(client, cmd, message, 'Microsoft')
                    self.debug('Sentence correctly translated using Microsoft Translator API service.') 
                    return True
                else:
                    self.debug('Translation using Microsoft Translator API service failed. Empty string returned.')
                    return False
            
        except urllib2.URLError, e:
            if hasattr(e,'reason'):
                self.debug('Could not connect to the Microsoft Translator server: %s.' % (e.reason))
                return False
            elif hasattr(e, 'code'):
                self.debug('Microsoft Translator server error: %s.' % (str(e.code)))
                return False
        
        except TypeError, e:
            self.debug('Translation using Microsoft Translator API service failed. TypeError exception: %s.' % e)
            return False
            
    
    def translate(self, client, cmd, sentence, targetLang, sourceLang):
        """\
        Translate the given sentence in the specified target language
        """
        if self._favoriteTranslator == 'Google':
            
            result = self.translateWithGoogle(client, cmd, sentence, targetLang, sourceLang)
            if not result:
                if self._microsoftClientId != '' and self._microsoftClientSecret != '':
                    self.debug('Trying to backup using Microsoft Translator API service.')
                    result = self.translateWithMicrosoft(client, cmd, sentence, targetLang, sourceLang)
                    if not result:
                        self.debug('Giving up...')
                        client.message('^7Unable to translate')
                else:
                    self.debug('Unable to use Microsoft Translator API service.')
                    client.message('^7Unable to translate')
                    
        elif self._favoriteTranslator == 'Microsoft':
            
            result = self.translateWithMicrosoft(client, cmd, sentence, targetLang, sourceLang)
            if not result:
                self.debug('Trying to backup using Google Translate API service.')
                result = self.translateWithGoogle(client, cmd, sentence, targetLang, sourceLang)
                if not result:
                    self.debug('Giving up...')
                    client.message('^7Unable to translate')
         
                    
    def displayTranslation(self, client, cmd, message, translator):
        """\
        Display the translation to the given client
        """
        if self._displayTranslatorName:
            if translator == 'Google': translator = self._gt_name + ' '
            else: translator = self._mt_name + ' '
        else: translator = ''
        
        if cmd is not None:
            # Someone run a command so we are able to see who run that command
            if cmd.loud: cmd.sayLoudOrPM(client, '%s^3: %s%s%s' % (self.teamColor(client), translator, self._transTextColorPrefix, message))
            else: cmd.sayLoudOrPM(client, '%s%s%s' % (translator, self._transTextColorPrefix, message))
        else:
            # We get here when we use the !transauto command
            client.message('%s%s%s' % (translator, self._transTextColorPrefix, message))
            
                    
    def printSupportedLanguages(self, client, cmd):
        """\
        Display a list of supported language codes and the description
        """  
        codes = []
        for k,v in self._languages.items():
            line = '^2%s ^3: ^7%s' % (k, v)
            codes.append(line)
        
        cmd.sayLoudOrPM(client, '^3, '.join(codes))

    
    def stripColors(self, s):
        sanitized = re.sub('\^[0-9]{1}','',s)
        return sanitized
    
    
    def teamColor(self, client):
        pname = self.stripColors(client.name)    
        if (client.team == 2): cname = '^1%s^7' % pname
        elif (client.team == 3): cname = '^4%s^7' % pname
        else: cname = '^7%s^7' % pname
        return cname

        
    # --------------------------------------- Commands --------------------------------------- #
    
  
    def cmd_translate(self, data, client, cmd=None):
        """\
        [<source>*<target>] <sentence> - Translate a sentence
        """
        if not data: 
            client.message('^7Invalid data, try !help translate')
            return False

        sourceLang = self._defaultSourceLang
        targetLang = self._defaultTargetlang
        
        # Checking if the user specified language codes
        lang = data.split(' ', 1)[0]
        (source, separator, target) = lang.partition('*')
        
        if separator == '*':
            
            # Splitting language codes and checking if they are supported
            self.debug('Detected language codes. Checking if those codes are supported by the plugin')
            source = source.strip()
            target = target.strip()
            
            if source != '' and source not in self._languages.keys():
                self.debug('Invalid source language specified [\'%s\'] in !translate command. Unable to translate.' % source)
                client.message('^7Invalid source language specified, try !translang')
                return False
                
            self.debug('Performing translation with specified source language[\'%s\'].' % source)
            sourceLang = source
                
            if target != '' and target not in self._languages.keys():
                self.debug('Invalid target language specified [\'%s\'] in !translate command. Unable to translate.' % target)
                client.message('^7Invalid target language specified, try !translang')
                return False
                
            self.debug('Performing translation with specified target language[\'%s\'].' % target)
            targetLang = target
            
            # Since the language codes has been specified (at least one)
            # we are going to remove them from the sentence to be translated
            data = data.split(' ', 1)[1]
        
        # Removing Quake3 color codes
        data = self.stripColors(data)
            
        # We got everything we need to perform a translation
        thread.start_new_thread(self.translate, (client, cmd, data, targetLang, sourceLang))


    def cmd_translast(self, data, client, cmd=None):
        """\
        [<target>] - Translate the latest available sentence from the chat
        """
        if self._lastSentence == '':
            client.message('^7Unable to translate last sentence')
            return False
        
        targetLang = self._defaultTargetlang
        
        if data:
            # Checking if the specified language code is supported
            self.debug('Specified language code. Checking if this code is supported by the plugin')
            if data not in self._languages.keys():
                self.debug('Invalid target language specified [\'%s\'] in !translast command. Unable to translate.' % data)
                client.message('^7Invalid target language specified, try !translang')
                return False
                
            self.debug('Performing translation with specified target language[\'%s\'].' % data)
            targetLang = data
        
        # We got everything we need to perform a translation
        thread.start_new_thread(self.translate, (client, cmd, self._lastSentence, targetLang, ''))
        
    
    def cmd_transauto(self, data, client, cmd=None):
        """\
        <on|off> [<language>] - Turn on and off the automatic translation
        """
        if not data: 
            client.message('^7Invalid data, try !help transauto')
            return False
        
        items = data.split(' ')
        
        if (len(items) != 1 and len(items) != 2) or (items[0] not in ('on','off')):
            client.message('^7Invalid data, try !help transauto')
            return False
        
        if items[0] == 'on':
            
            if len(items) == 1: 
                # Using default target language
                targetLang = self._defaultTargetlang
            else:
                # Target language specified
                targetLang = items[1]
                if targetLang not in self._languages.keys():
                    self.debug('Invalid target language specified [\'%s\'] in !transauto command.' % targetLang)
                    client.message('^7Invalid target language specified, try !translang')
                    return False
           
            client.setvar(self,'transauto',True)
            client.setvar(self,'translang',targetLang)
            client.message('^7Automatic translation: ^2ON^7. Language: ^4%s' % self._languages[targetLang])
        
        elif items[0] == 'off':
            
            client.setvar(self,'transauto',False)
            client.message('^7Automatic translation: ^1OFF')
                
        
    def cmd_translang(self, data, client, cmd=None):
        """\
        Display a list of available language codes
        """
        thread.start_new_thread(self.printSupportedLanguages, (client, cmd))
        
    
    def cmd_transchange(self, data, client, cmd=None):
        """\
        Switch the favourite translator service
        """
        if self._favoriteTranslator == 'Microsoft':
            
            if platform.system() in ('Windows', 'Microsoft'):
                client.message('^7Unable to change Translator service')
                return False
            
            self._favoriteTranslator = 'Google'
            self.debug('Favorite Translator service changed to %s.' % self._favoriteTranslator)
            client.message('^7Translator service changed to ^4%s' % self._favoriteTranslator)
            
        else:
            
            if self._microsoftClientId == '' or self._microsoftClientSecret == '':
                client.message('^7Unable to change Translator service')
                return False
            
            self._favoriteTranslator = 'Microsoft'
            self.debug('Favorite Translator service changed to %s' % self._favoriteTranslator)
            client.message('^7Translator service changed to ^4%s' % self._favoriteTranslator)
        
    
    def cmd_transname(self, data, client, cmd=None):
        """\
        <on|off> - Switch the the translator name on and off
        """
        if not data or data not in ('on','off'): 
            client.message('^7Invalid data, try !help transname')
            return False
        
        if data == 'on':
            self._displayTranslatorName = True
            client.message('^7Translator name: ^2ON')
        elif data == 'off':
            self._displayTranslatorName = False
            client.message('^7Translator name: ^1OFF')
