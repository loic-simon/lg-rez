``lgrez.features`` (Commandes et autres fonctionnalités)
===============================================================


.. automodule:: lgrez.features


Liste des commandes :

+------------------+----------------------------------------------------------------------+--------------------------------------------------------------+------------------+
| **Commande**     | **Description**                                                      | **Autorisations**                                            | **Restrictions** |
|                  |                                                                      +-------------------+-----------------+---------------+--------+                  +
|                  |                                                                      | **Joueur en vie** | **Joueur mort** | **Rédacteur** | **MJ** |                  |
+==================+======================================================================+===================+=================+===============+========+==================+
| **Informations - Commandes pour en savoir plus sur soi et les autres :**                                                                                                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!roles``       | Affiche la liste des rôles / des informations sur un rôle            | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!rolede``      | Donne le rôle d'un joueur                                            |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!quiest``      | Liste les joueurs ayant un rôle donné                                |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!menu``        | Affiche des informations et boutons sur les votes / actions en cours | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!infos``       | Affiche tes informations de rôle / actions                           | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!actions``     | Affiche et modifie les actions d'un joueur                           |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!vivants``     | Affiche la liste des joueurs vivants                                 | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!morts``       | Affiche la liste des joueurs morts                                   | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **VoterAgir - Commandes de vote et d'action de rôle :**                                                                                                                   |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!vote``        | Vote pour le condamné du jour                                        | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!votemaire``   | Vote pour le nouveau maire                                           | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!voteloups``   | Vote pour la victime de l'attaque des loups                          | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!action``      | Utilise l'action de ton rôle / une des actions associées             | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **ActionsPubliques - Commandes d'actions vous engageant publiquement :**                                                                                                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!haro``        | Lance publiquement un haro contre un autre joueur.                   | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!candid``      | Candidate à l'élection du nouveau maire.                             | X                 |                 |               |        | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!wipe``        | Efface les haros / candidatures du jour                              |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **OpenClose - Commandes de gestion des votes et actions :**                                                                                                               |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!open``        | Lance un vote / des actions de rôle                                  |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!close``       | Ferme un vote / des actions de rôle                                  |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!remind``      | Envoi un rappel de vote / actions de rôle                            |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!refill``      | Recharger un/des pouvoirs rechargeables                              |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!cparti``      | Lance le jeu                                                         |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **Sync - Commandes de synchronisation des GSheets vers la BDD et les joueurs :**                                                                                          |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!sync``        | Récupère et applique les modifs du Tableau de bord                   |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!fillroles``   | Remplit les tables et #roles depuis le GSheet ad hoc                 |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **GestionTaches - Commandes de planification, exécution, annulation de tâches :**                                                                                         |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!taches``      | Liste les tâches en attente                                          |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!planif``      | Planifie une tâche au moment voulu                                   |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!delay``       | Exécute une commande après XhYmZs                                    |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!cancel``      | Annule une ou plusieurs tâche(s) planifiée(s)                        |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **Communication - Commandes d'envoi de messages, d'embeds, d'annonces... :**                                                                                              |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!embed``       | Prépare un embed (message riche) et l'envoie                         |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!send``        | Envoie un message à tous ou certains joueurs                         |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!post``        | Envoie un message dans un salon                                      |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!plot``        | Trace le résultat du vote et l'envoie sur #annonces                  |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!annoncemort`` | Annonce un ou plusieur mort(s) hors-vote                             |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!lore``        | Récupère et poste un lore depuis un Google Docs                      |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!modif``       | Modifie un message du bot                                            |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **GestionIA - Commandes relatives à l'IA (réponses automatiques du bot) :**                                                                                               |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!stfu``        | Active/désactive la réponse automatique du bot sur ton channel privé | X                 | X               |               | X      | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!fals``        | Active/désactive le mode « foire à la saucisse »                     | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!react``       | Force le bot à réagir à un message                                   | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!reactfals``   | Force le bot à réagir à un message comme en mode Foire à la saucisse | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!addIA``       | Ajoute une règle d'IA                                                |                   |                 | X             | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!listIA``      | Liste les règles d'IA reconnues par le bot                           |                   |                 | X             | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!modifIA``     | Modifie/supprime une règle d'IA                                      |                   |                 | X             | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **Annexe - Commandes annexes aux usages divers :**                                                                                                                        |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!roll``        | Lance un ou plusieurs dés                                            | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!coinflip``    | Renvoie le résultat d'un tirage à Pile ou Face (aléatoire)           | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!ping``        | Envoie un ping au bot                                                | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!akinator``    | J'ai glissé chef                                                     | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!xkcd``        | J'ai aussi glissé chef, mais un peu moins                            | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **GestionChans - Gestion des salons :**                                                                                                                                   |
+------------------+----------------------------------------------+-----------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!boudoir``     | Gestion des boudoirs                         | list                  | X                 | X               |               |        | ``private``      |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | create                | X                 |                 |               |        | ``private``      |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | invite                | X                 | X               |               |        | ``in_boudoir``   |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | expulse               | X                 | X               |               |        | ``in_boudoir``   |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | leave                 | X                 | X               |               |        | ``in_boudoir``   |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | transfer              | X                 | X               |               |        | ``in_boudoir``   |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | delete                | X                 | X               |               |        | ``in_boudoir``   |
|                  |                                              +-----------------------+-------------------+-----------------+---------------+--------+------------------+
|                  |                                              | rename                | X                 | X               |               |        | ``in_boudoir``   |
+------------------+----------------------------------------------+-----------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!addhere``     | Ajoute les membres au chan courant                                   |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!purge``       | Supprime tous les messages de ce chan                                |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| **Special - Commandes spéciales (méta-commandes et expérimentations) :**                                                                                                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!panik``       | Tue instantanément le bot, sans confirmation                         |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!do``          | Exécute du code Python et affiche le résultat                        |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!shell``       | Lance un terminal Python directement dans Discord                    |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!co``          | Lance la procédure d'inscription pour un membre                      |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!doas``        | Exécute une commande en tant qu'un autre joueur                      |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!secret``      | Supprime le message puis exécute la commande                         |                   |                 |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!stop``        | Peut débloquer des situations compliquées (beta)                     | X                 | X               |               | X      | ``private``      |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!help``        | Affiche la liste des commandes utilisables et leur utilisation       | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+
| ``!apropos``     | Informations et mentions légales du projet                           | X                 | X               |               | X      |                  |
+------------------+----------------------------------------------------------------------+-------------------+-----------------+---------------+--------+------------------+


``.special``
----------------------------------------------------------------------

.. automodule:: lgrez.features.special
   :members:
   :exclude-members: Special
   :member-order: bysource

.. --autocog--:lgrez.features.special.Special: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.special.Special
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _panik:

    - :Commande ``!panik``  (alias ``!kill``) :
        .. automethod:: lgrez.features.special.Special.panik.callback
        .. _do:
    - :Commande ``!do``  :
        .. automethod:: lgrez.features.special.Special.do.callback
        .. _shell:
    - :Commande ``!shell``  :
        .. automethod:: lgrez.features.special.Special.shell.callback
        .. _co:
    - :Commande ``!co``  :
        .. automethod:: lgrez.features.special.Special.co.callback
        .. _doas:
    - :Commande ``!doas``  :
        .. automethod:: lgrez.features.special.Special.doas.callback
        .. _secret:
    - :Commande ``!secret``  (alias ``!autodestruct``, ``!ad``) :
        .. automethod:: lgrez.features.special.Special.secret.callback
        .. _stop:
    - :Commande ``!stop``  :
        .. automethod:: lgrez.features.special.Special.stop.callback
        .. _help:
    - :Commande ``!help``  (alias ``!aide``, ``!aled``, ``!oskour``) :
        .. automethod:: lgrez.features.special.Special.help.callback
        .. _apropos:
    - :Commande ``!apropos``  (alias ``!about``, ``!copyright``, ``!licence``, ``!auteurs``) :
        .. automethod:: lgrez.features.special.Special.apropos.callback

.. }


``.actions_publiques``
----------------------------------------------------------------------

.. automodule:: lgrez.features.actions_publiques
   :members:
   :exclude-members: ActionsPubliques
   :member-order: bysource

.. --autocog--:lgrez.features.actions_publiques.ActionsPubliques: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.actions_publiques.ActionsPubliques
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _haro:

    - :Commande ``!haro``  :
        .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.haro.callback
        .. _candid:
    - :Commande ``!candid``  :
        .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.candid.callback
        .. _wipe:
    - :Commande ``!wipe``  :
        .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.wipe.callback

.. }


``.annexe``
----------------------------------------------------------------------

.. automodule:: lgrez.features.annexe
   :members:
   :exclude-members: Annexe
   :member-order: bysource

.. --autocog--:lgrez.features.annexe.Annexe: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.annexe.Annexe
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _roll:

    - :Commande ``!roll``  :
        .. automethod:: lgrez.features.annexe.Annexe.roll.callback
        .. _coinflip:
    - :Commande ``!coinflip``  (alias ``!cf``, ``!pf``) :
        .. automethod:: lgrez.features.annexe.Annexe.coinflip.callback
        .. _ping:
    - :Commande ``!ping``  (alias ``!pong``) :
        .. automethod:: lgrez.features.annexe.Annexe.ping.callback
        .. _akinator:
    - :Commande ``!akinator``  :
        .. automethod:: lgrez.features.annexe.Annexe.akinator.callback
        .. _xkcd:
    - :Commande ``!xkcd``  :
        .. automethod:: lgrez.features.annexe.Annexe.xkcd.callback

.. }


``.chans``
----------------------------------------------------------------------

.. automodule:: lgrez.features.chans
   :members:
   :exclude-members: GestionChans
   :member-order: bysource

.. --autocog--:lgrez.features.chans.GestionChans: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.chans.GestionChans
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _boudoir:

    - :Commande ``!boudoir``  (alias ``!boudoirs``) :
        .. automethod:: lgrez.features.chans.GestionChans.boudoir.callback

        .. include:: groupnote.rst

        .. _boudoir_create:

        - :Option ``!boudoir create``  (alias ``!new``, ``!creer``, ``!créer``) :
            .. automethod:: lgrez.features.chans.GestionChans.create.callback
            .. _boudoir_delete:
        - :Option ``!boudoir delete``  :
            .. automethod:: lgrez.features.chans.GestionChans.delete.callback
            .. _boudoir_expulse:
        - :Option ``!boudoir expulse``  (alias ``!remove``) :
            .. automethod:: lgrez.features.chans.GestionChans.expulse.callback
            .. _boudoir_invite:
        - :Option ``!boudoir invite``  (alias ``!add``) :
            .. automethod:: lgrez.features.chans.GestionChans.invite.callback
            .. _boudoir_leave:
        - :Option ``!boudoir leave``  (alias ``!quit``) :
            .. automethod:: lgrez.features.chans.GestionChans.leave.callback
            .. _boudoir_list:
        - :Option ``!boudoir list``  (alias ``!liste``) :
            .. automethod:: lgrez.features.chans.GestionChans.list.callback
            .. _boudoir_rename:
        - :Option ``!boudoir rename``  :
            .. automethod:: lgrez.features.chans.GestionChans.rename.callback
            .. _boudoir_transfer:
        - :Option ``!boudoir transfer``  (alias ``!transmit``) :
            .. automethod:: lgrez.features.chans.GestionChans.transfer.callback

        .. _addhere:
    - :Commande ``!addhere``  :
        .. automethod:: lgrez.features.chans.GestionChans.addhere.callback
        .. _purge:
    - :Commande ``!purge``  :
        .. automethod:: lgrez.features.chans.GestionChans.purge.callback

.. }


``.communication``
----------------------------------------------------------------------

.. automodule:: lgrez.features.communication
   :members:
   :exclude-members: Communication
   :member-order: bysource

.. --autocog--:lgrez.features.communication.Communication: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.communication.Communication
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _embed:

    - :Commande ``!embed``  :
        .. automethod:: lgrez.features.communication.Communication.embed.callback
        .. _send:
    - :Commande ``!send``  (alias ``!tell``) :
        .. automethod:: lgrez.features.communication.Communication.send.callback
        .. _post:
    - :Commande ``!post``  :
        .. automethod:: lgrez.features.communication.Communication.post.callback
        .. _plot:
    - :Commande ``!plot``  :
        .. automethod:: lgrez.features.communication.Communication.plot.callback
        .. _annoncemort:
    - :Commande ``!annoncemort``  :
        .. automethod:: lgrez.features.communication.Communication.annoncemort.callback
        .. _lore:
    - :Commande ``!lore``  :
        .. automethod:: lgrez.features.communication.Communication.lore.callback
        .. _modif:
    - :Commande ``!modif``  :
        .. automethod:: lgrez.features.communication.Communication.modif.callback

.. }


``.gestion_actions``
----------------------------------------------------------------------

.. automodule:: lgrez.features.gestion_actions
   :members:
   :member-order: bysource


``.IA``
----------------------------------------------------------------------

.. automodule:: lgrez.features.IA
   :members:
   :exclude-members: GestionIA
   :member-order: bysource

.. --autocog--:lgrez.features.IA.GestionIA: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.IA.GestionIA
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _stfu:

    - :Commande ``!stfu``  :
        .. automethod:: lgrez.features.IA.GestionIA.stfu.callback
        .. _fals:
    - :Commande ``!fals``  (alias ``!cancer``, ``!214``) :
        .. automethod:: lgrez.features.IA.GestionIA.fals.callback
        .. _react:
    - :Commande ``!react``  (alias ``!r``) :
        .. automethod:: lgrez.features.IA.GestionIA.react.callback
        .. _reactfals:
    - :Commande ``!reactfals``  (alias ``!rf``) :
        .. automethod:: lgrez.features.IA.GestionIA.reactfals.callback
        .. _addIA:
    - :Commande ``!addIA``  :
        .. automethod:: lgrez.features.IA.GestionIA.addIA.callback
        .. _listIA:
    - :Commande ``!listIA``  :
        .. automethod:: lgrez.features.IA.GestionIA.listIA.callback
        .. _modifIA:
    - :Commande ``!modifIA``  :
        .. automethod:: lgrez.features.IA.GestionIA.modifIA.callback

.. }


``.informations``
----------------------------------------------------------------------

.. automodule:: lgrez.features.informations
   :members:
   :exclude-members: Informations
   :member-order: bysource

.. --autocog--:lgrez.features.informations.Informations: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.informations.Informations
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _roles:

    - :Commande ``!roles``  (alias ``!role``, ``!rôles``, ``!rôle``, ``!camp``, ``!camps``) :
        .. automethod:: lgrez.features.informations.Informations.roles.callback
        .. _rolede:
    - :Commande ``!rolede``  :
        .. automethod:: lgrez.features.informations.Informations.rolede.callback
        .. _quiest:
    - :Commande ``!quiest``  :
        .. automethod:: lgrez.features.informations.Informations.quiest.callback
        .. _menu:
    - :Commande ``!menu``  :
        .. automethod:: lgrez.features.informations.Informations.menu.callback
        .. _infos:
    - :Commande ``!infos``  :
        .. automethod:: lgrez.features.informations.Informations.infos.callback
        .. _actions:
    - :Commande ``!actions``  :
        .. automethod:: lgrez.features.informations.Informations.actions.callback
        .. _vivants:
    - :Commande ``!vivants``  (alias ``!joueurs``, ``!vivant``) :
        .. automethod:: lgrez.features.informations.Informations.vivants.callback
        .. _morts:
    - :Commande ``!morts``  (alias ``!mort``) :
        .. automethod:: lgrez.features.informations.Informations.morts.callback

.. }


``.inscription``
----------------------------------------------------------------------

.. automodule:: lgrez.features.inscription
   :members:
   :member-order: bysource


``.open_close``
----------------------------------------------------------------------

.. automodule:: lgrez.features.open_close
   :members:
   :exclude-members: OpenClose
   :member-order: bysource

.. --autocog--:lgrez.features.open_close.OpenClose: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.open_close.OpenClose
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _open:

    - :Commande ``!open``  :
        .. automethod:: lgrez.features.open_close.OpenClose.open.callback
        .. _close:
    - :Commande ``!close``  :
        .. automethod:: lgrez.features.open_close.OpenClose.close.callback
        .. _remind:
    - :Commande ``!remind``  :
        .. automethod:: lgrez.features.open_close.OpenClose.remind.callback
        .. _refill:
    - :Commande ``!refill``  :
        .. automethod:: lgrez.features.open_close.OpenClose.refill.callback
        .. _cparti:
    - :Commande ``!cparti``  :
        .. automethod:: lgrez.features.open_close.OpenClose.cparti.callback

.. }


``.sync``
----------------------------------------------------------------------

.. automodule:: lgrez.features.sync
   :members:
   :exclude-members: Sync
   :member-order: bysource

.. --autocog--:lgrez.features.sync.Sync: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.sync.Sync
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _sync:

    - :Commande ``!sync``  :
        .. automethod:: lgrez.features.sync.Sync.sync.callback
        .. _fillroles:
    - :Commande ``!fillroles``  :
        .. automethod:: lgrez.features.sync.Sync.fillroles.callback

.. }


``.taches``
----------------------------------------------------------------------

.. automodule:: lgrez.features.taches
   :members:
   :exclude-members: GestionTaches
   :member-order: bysource

.. --autocog--:lgrez.features.taches.GestionTaches: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.taches.GestionTaches
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _taches:

    - :Commande ``!taches``  :
        .. automethod:: lgrez.features.taches.GestionTaches.taches.callback
        .. _planif:
    - :Commande ``!planif``  (alias ``!doat``) :
        .. automethod:: lgrez.features.taches.GestionTaches.planif.callback
        .. _delay:
    - :Commande ``!delay``  (alias ``!retard``, ``!doin``) :
        .. automethod:: lgrez.features.taches.GestionTaches.delay.callback
        .. _cancel:
    - :Commande ``!cancel``  :
        .. automethod:: lgrez.features.taches.GestionTaches.cancel.callback

.. }


``.voter_agir``
----------------------------------------------------------------------

.. automodule:: lgrez.features.voter_agir
   :members:
   :exclude-members: VoterAgir
   :member-order: bysource

.. --autocog--:lgrez.features.voter_agir.VoterAgir: {
.. (this bloc is autogenerated each time docs are build, don't
.. change manually! See end of conf.py for generation code.)
.. autoclass:: lgrez.features.voter_agir.VoterAgir
    :members:

    .. include:: cognote.rst

    Commandes définies dans ce cog :

        .. _vote:

    - :Commande ``!vote``  :
        .. automethod:: lgrez.features.voter_agir.VoterAgir.vote.callback
        .. _votemaire:
    - :Commande ``!votemaire``  :
        .. automethod:: lgrez.features.voter_agir.VoterAgir.votemaire.callback
        .. _voteloups:
    - :Commande ``!voteloups``  :
        .. automethod:: lgrez.features.voter_agir.VoterAgir.voteloups.callback
        .. _action:
    - :Commande ``!action``  :
        .. automethod:: lgrez.features.voter_agir.VoterAgir.action.callback

.. }
