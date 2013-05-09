Translator Plugin for BigBrotherBot
===================================

## Description

This plugin is capable o translating in-game chat messages into a specified language using the Microsoft Translator API service.<br> 
Previous versions of this plugin were supporting 2 translation services: **Google Translate** and **Microsoft Translator**. I decided to remove the Google Translate support because Google Translate API service are now available only as a paid service. Microsoft Translator API otherwise offers different paid translation plans, plus a limited free translation plan.

## How to install

### Installing the plugin

* Copy **translator.py** into **b3/extplugins**
* Copy **translator.xml** into **b3/extplugins/conf**
* Load the plugin in your **b3.xml** configuration file

### Microsoft Translator API configuration

1. Register a Windows Live ID: https://signup.live.com/
2. Create an Account on the Azure Data Market: https://datamarket.azure.com/developer/applications/
3. Pick a plan: https://datamarket.azure.com/dataset/1899a118-d202-492c-aa16-ba21c33c06cb
4. Register an Azure application: https://datamarket.azure.com/developer/applications
5. While registering the new application you will need to specify a **valid** website and a **valid** software name

**NOTE**: You can use as website **http://localhost** and as software name whatever name you like more

The Azure Application registration, provides two critical fields for API access: **client id** and **client secret**<br>
Put those credentials inside the plugin configuration file (be sure not to add spaces before and after)

## Support

For support regarding this very plugin you can find me on IRC on **#urbanterror / #goreclan** @ **Quakenet**<br>
For support regarding Big Brother Bot you may ask for help on the official website: http://www.bigbrotherbot.net