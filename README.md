Translator Plugin for BigBrotherBot [![BigBrotherBot](http://i.imgur.com/7sljo4G.png)][B3]
=================================

Description
-----------

A [BigBrotherBot][B3] plugin which is capable o translating in-game chat messages into a specified language.

******
*NOTE: since B3 v1.10.1 beta this plugin has been included in the standard plugins set, thus all patches and updates will be performed in the official B3 repository.*
******

Download
--------

Latest version available [here](https://github.com/danielepantaleone/b3-plugin-translator/archive/master.zip).

Installation
------------

* copy the `translator` folder into `b3/extplugins`
* add to the `plugins` section of your `b3.xml` config file:

  ```xml
  <plugin name="translator" config="@b3/extplugins/translator/conf/plugin_translator.ini" />
  ```

* install langdetect python module (from pypi) to support exclude_language setting.

In-game user guide
------------------

* **!translate [&lt;source&gt;]*[&lt;target&gt;] &lt;message&gt;** `translate a message`
* **!translast [&lt;target&gt;]** `translate the last available sentence from the chat`
* **!transauto &lt;on|off&gt;** `turn on/off the automatic translation` - STRONGLY DISADVISED (unless you would like your server to get banned from Google...)
* **!translang** `display the list of available language codes`

It is advised to increase min_time_between to reduce the likelihood of a google temporary ban.

Support
-------

If you have found a bug or have a suggestion for this plugin, please report it on the [B3 forums][Support].

[B3]: http://www.bigbrotherbot.net/ "BigBrotherBot (B3)"
[Support]: http://forum.bigbrotherbot.net/plugins-by-fenix/translator-plugin-(by-mr-click) "Support topic on the B3 forums"

[![Build Status](https://travis-ci.org/danielepantaleone/b3-plugin-translator.svg?branch=master)](https://travis-ci.org/danielepantaleone/b3-plugin-translator)
