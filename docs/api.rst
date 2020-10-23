Référence de l'API
=====================

Bot
----------------

LGBot
~~~~~~~~~~

.. autoclass:: lgrez.LGBot
    :members:


Commandes spéciales
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bot.Special
    :members:

    ..include:: cognote.rst

    .. automethod:: lgrez.bot.Special.do.callback
    .. automethod:: lgrez.bot.Special.shell.callback
    .. automethod:: lgrez.bot.Special.co.callback
    .. automethod:: lgrez.bot.Special.doas.callback
    .. automethod:: lgrez.bot.Special.secret.callback
    .. automethod:: lgrez.bot.Special.stop.callback
    .. automethod:: lgrez.bot.Special.help.callback


Fonctionnalités
-----------------

.. automodule:: lgrez.features

.. toctree::
   :maxdepth: 3

   features


Blocs
-----------------

.. automodule:: lgrez.blocs

.. toctree::
   :maxdepth: 3

   blocs
