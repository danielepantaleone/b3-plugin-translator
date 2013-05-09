Translator Plugin for BigBrotherBot (www.bigbrotherbot.net)
===========================================================

Description
-----------

This plugin is capable o translating in-game chat messages into a specified language using the Microsoft Translator API service

How to install
--------------

### Plugin installation

* copy translator.py into b3/extplugins
* copy translator.xml into b3/extplugins/conf
* edit your b3.xml config file adding : <plugin name="translator" config="@b3/extplugins/conf/translator.xml"/>

### Microsoft Translator API configuration

* Register a Windows Live ID: https://signup.live.com/
* While logged with your Windows Live ID, create an Account on the Azure Data Market: https://datamarket.azure.com/developer/applications/
* Go to the Microsoft Translator Data Service and Pick a Plan: https://datamarket.azure.com/dataset/1899a118-d202-492c-aa16-ba21c33c06cb
* Register an Azure application: https://datamarket.azure.com/developer/applications
* While registering the new application you will need to specify a "valid" website and a "valid" software name. You can just use as website "http://localhost" and as software name.....well you can enter whatever you want

The Azure Application registration, provides two critical fields for API access: **client id** and **client secret**
Put those credentials inside the plugin configuration file (be sure not to add spaces before and after)