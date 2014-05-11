Translator Plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
=================================

Description
-----------

A [BigBrotherBot][B3] plugin which is capable o translating in-game chat messages into a specified language.

Download
--------

Latest version available [here](https://github.com/FenixXx/b3-plugin-translator/archive/master.zip).

Installation
------------

* copy the `translator.py` file into `b3/extplugins`
* copy the `plugin_translator.ini` file in `b3/extplugins/conf`
* add to the `plugins` section of your `b3.xml` config file:

  ```xml
  <plugin name="translator" config="@b3/extplugins/conf/plugin_translator.ini" />
  ```

Microsoft Translator API configuration
--------------------------------------

1. Create a new [Windows Live ID](https://signup.live.com)
2. Create an account on the [Azure Data Market](https://datamarket.azure.com/developer/applications/)
3. Pick a service [plan](https://datamarket.azure.com/dataset/1899a118-d202-492c-aa16-ba21c33c06cb)
4. Register an Azure [application](https://datamarket.azure.com/developer/applications)
5. While registering the new application you will need to specify a **website** and a **software name**: you can use
as website **http://localhost** and as software name whatever name you like more

The Azure Application registration, provides two critical fields for **API** access: **client id** and **client secret**:
you have to put those credentials inside the plugin configuration file.

In-game user guide
------------------

* **!translate [&lt;source&gt;]*[&lt;target&gt;] &lt;message&gt;** `translate a message`
* **!translast [&lt;target&gt;]** `translate the last available sentence from the chat`
* **!transauto &lt;on|off&gt;** `turn on/off the automatic translation`
* **!translang** `display the list of available language codes`

Support
-------

If you have found a bug or have a suggestion for this plugin, please report it on the [B3 forums][Support].

[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"
[Support]: http://forum.bigbrotherbot.net/plugins-by-fenix/translator-plugin-(by-mr-click) "Support topic on the B3 forums"

[![Build Status](https://travis-ci.org/FenixXx/b3-plugin-translator.svg?branch=master)](https://travis-ci.org/FenixXx/b3-plugin-translator)
