Référence de l'API
=====================


``LGBot`` (classe principale)
--------------------------------

.. autoclass:: lgrez.LGBot
    :members:
    :member-order: bysource



``lgrez.bot`` (fonctions centrales)
------------------------------------------------

Système d'unicité
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: lgrez.bot.already_in_command
.. autoexception:: lgrez.bot.AlreadyInCommand
.. autofunction:: lgrez.bot.add_to_in_command
.. autofunction:: lgrez.bot.remove_from_in_command


Commandes spéciales
~~~~~~~~~~~~~~~~~~~~~

.. --autocog--:lgrez.bot.Special: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.bot.Special
    :members:

    .. include:: cognote.rst
    - :Commande ``!panik`` (alias ``!kill``) : .. automethod:: lgrez.bot.Special.panik.callback
    - :Commande ``!do`` : .. automethod:: lgrez.bot.Special.do.callback
    - :Commande ``!shell`` : .. automethod:: lgrez.bot.Special.shell.callback
    - :Commande ``!co`` : .. automethod:: lgrez.bot.Special.co.callback
    - :Commande ``!doas`` : .. automethod:: lgrez.bot.Special.doas.callback
    - :Commande ``!secret`` (alias ``!autodestruct``, ``!ad``) : .. automethod:: lgrez.bot.Special.secret.callback
    - :Commande ``!stop`` : .. automethod:: lgrez.bot.Special.stop.callback
    - :Commande ``!help`` (alias ``!aide``, ``!aled``, ``!oskour``) : .. automethod:: lgrez.bot.Special.help.callback

.. }



``lgrez.features`` (Commandes et autres fonctionnalités)
-------------------------------------------------------------------

.. automodule:: lgrez.features


Actions publiques
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.actions_publiques
   :members:
   :exclude-members: ActionsPubliques
   :member-order: bysource

.. --autocog--:lgrez.features.actions_publiques.ActionsPubliques: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.actions_publiques.ActionsPubliques
    :members:

    .. include:: cognote.rst
    - :Commande ``!haro`` : .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.haro.callback
    - :Commande ``!candid`` : .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.candid.callback
    - :Commande ``!wipe`` : .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.wipe.callback
    - :Commande ``!listharo`` : .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.listharo.callback
    - :Commande ``!listcandid`` : .. automethod:: lgrez.features.actions_publiques.ActionsPubliques.listcandid.callback

.. }


Commandes annexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.annexe
   :members:
   :exclude-members: Annexe
   :member-order: bysource

.. --autocog--:lgrez.features.annexe.Annexe: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.annexe.Annexe
    :members:

    .. include:: cognote.rst
    - :Commande ``!roll`` : .. automethod:: lgrez.features.annexe.Annexe.roll.callback
    - :Commande ``!coinflip`` (alias ``!cf``, ``!pf``) : .. automethod:: lgrez.features.annexe.Annexe.coinflip.callback
    - :Commande ``!ping`` (alias ``!pong``) : .. automethod:: lgrez.features.annexe.Annexe.ping.callback
    - :Commande ``!addhere`` : .. automethod:: lgrez.features.annexe.Annexe.addhere.callback
    - :Commande ``!purge`` : .. automethod:: lgrez.features.annexe.Annexe.purge.callback
    - :Commande ``!akinator`` : .. automethod:: lgrez.features.annexe.Annexe.akinator.callback
    - :Commande ``!xkcd`` : .. automethod:: lgrez.features.annexe.Annexe.xkcd.callback

.. }


Gestion des actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.gestion_actions
   :members:
   :member-order: bysource


IA des réponses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.IA
   :members:
   :exclude-members: GestionIA
   :member-order: bysource

.. --autocog--:lgrez.features.IA.GestionIA: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.IA.GestionIA
    :members:

    .. include:: cognote.rst
    - :Commande ``!stfu`` : .. automethod:: lgrez.features.IA.GestionIA.stfu.callback
    - :Commande ``!fals`` (alias ``!cancer``, ``!214``) : .. automethod:: lgrez.features.IA.GestionIA.fals.callback
    - :Commande ``!react`` (alias ``!r``) : .. automethod:: lgrez.features.IA.GestionIA.react.callback
    - :Commande ``!reactfals`` (alias ``!rf``) : .. automethod:: lgrez.features.IA.GestionIA.reactfals.callback
    - :Commande ``!addIA`` : .. automethod:: lgrez.features.IA.GestionIA.addIA.callback
    - :Commande ``!listIA`` : .. automethod:: lgrez.features.IA.GestionIA.listIA.callback
    - :Commande ``!modifIA`` : .. automethod:: lgrez.features.IA.GestionIA.modifIA.callback

.. }


Commandes informatives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.informations
   :members:
   :exclude-members: Informations
   :member-order: bysource

.. --autocog--:lgrez.features.informations.Informations: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.informations.Informations
    :members:

    .. include:: cognote.rst
    - :Commande ``!roles`` (alias ``!role``, ``!rôles``, ``!rôle``, ``!camp``, ``!camps``) : .. automethod:: lgrez.features.informations.Informations.roles.callback
    - :Commande ``!rolede`` : .. automethod:: lgrez.features.informations.Informations.rolede.callback
    - :Commande ``!quiest`` : .. automethod:: lgrez.features.informations.Informations.quiest.callback
    - :Commande ``!menu`` : .. automethod:: lgrez.features.informations.Informations.menu.callback
    - :Commande ``!infos`` : .. automethod:: lgrez.features.informations.Informations.infos.callback
    - :Commande ``!actions`` : .. automethod:: lgrez.features.informations.Informations.actions.callback
    - :Commande ``!vivants`` (alias ``!joueurs``, ``!vivant``) : .. automethod:: lgrez.features.informations.Informations.vivants.callback
    - :Commande ``!morts`` (alias ``!mort``) : .. automethod:: lgrez.features.informations.Informations.morts.callback

.. }


Process d'inscription
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.inscription
   :members:
   :member-order: bysource


Ouverture / fermeture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.open_close
   :members:
   :exclude-members: OpenClose
   :member-order: bysource

.. --autocog--:lgrez.features.open_close.OpenClose: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.open_close.OpenClose
    :members:

    .. include:: cognote.rst
    - :Commande ``!open`` : .. automethod:: lgrez.features.open_close.OpenClose.open.callback
    - :Commande ``!close`` : .. automethod:: lgrez.features.open_close.OpenClose.close.callback
    - :Commande ``!remind`` : .. automethod:: lgrez.features.open_close.OpenClose.remind.callback
    - :Commande ``!refill`` : .. automethod:: lgrez.features.open_close.OpenClose.refill.callback
    - :Commande ``!cparti`` : .. automethod:: lgrez.features.open_close.OpenClose.cparti.callback

.. }


Synchronisation GSheets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.sync
   :members:
   :exclude-members: Sync
   :member-order: bysource

.. --autocog--:lgrez.features.sync.Sync: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.sync.Sync
    :members:

    .. include:: cognote.rst
    - :Commande ``!sync`` : .. automethod:: lgrez.features.sync.Sync.sync.callback
    - :Commande ``!fillroles`` : .. automethod:: lgrez.features.sync.Sync.fillroles.callback

.. }


Tâches planifiées
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.taches
   :members:
   :exclude-members: GestionTaches
   :member-order: bysource

.. --autocog--:lgrez.features.taches.GestionTaches: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.taches.GestionTaches
    :members:

    .. include:: cognote.rst
    - :Commande ``!taches`` : .. automethod:: lgrez.features.taches.GestionTaches.taches.callback
    - :Commande ``!planif`` (alias ``!doat``) : .. automethod:: lgrez.features.taches.GestionTaches.planif.callback
    - :Commande ``!delay`` (alias ``!retard``, ``!doin``) : .. automethod:: lgrez.features.taches.GestionTaches.delay.callback
    - :Commande ``!cancel`` : .. automethod:: lgrez.features.taches.GestionTaches.cancel.callback

.. }


Commandes de votes et d'action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.voter_agir
   :members:
   :exclude-members: VoterAgir
   :member-order: bysource

.. --autocog--:lgrez.features.voter_agir.VoterAgir: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.voter_agir.VoterAgir
    :members:

    .. include:: cognote.rst
    - :Commande ``!vote`` : .. automethod:: lgrez.features.voter_agir.VoterAgir.vote.callback
    - :Commande ``!votemaire`` : .. automethod:: lgrez.features.voter_agir.VoterAgir.votemaire.callback
    - :Commande ``!voteloups`` : .. automethod:: lgrez.features.voter_agir.VoterAgir.voteloups.callback
    - :Commande ``!action`` : .. automethod:: lgrez.features.voter_agir.VoterAgir.action.callback

.. }


Communication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.features.communication
   :members:
   :exclude-members: Communication
   :member-order: bysource

.. --autocog--:lgrez.features.communication.Communication: { 
.. (this bloc is autogenerated each time docs are build, don't change manually! See end of conf.py)
.. autoclass:: lgrez.features.communication.Communication
    :members:

    .. include:: cognote.rst
    - :Commande ``!embed`` : .. automethod:: lgrez.features.communication.Communication.embed.callback
    - :Commande ``!send`` (alias ``!tell``) : .. automethod:: lgrez.features.communication.Communication.send.callback
    - :Commande ``!post`` : .. automethod:: lgrez.features.communication.Communication.post.callback
    - :Commande ``!plot`` : .. automethod:: lgrez.features.communication.Communication.plot.callback
    - :Commande ``!annoncemort`` : .. automethod:: lgrez.features.communication.Communication.annoncemort.callback

.. }




``lgrez.blocs`` (Blocs transversaux)
---------------------------------------------------

.. automodule:: lgrez.blocs


Gestion des données
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.bdd
   :members:
   :member-order: bysource


Outils pour tables de données
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.bdd_tools
   :members:
   :member-order: bysource


Interfaçage Google Sheets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.gsheets
   :members:
   :member-order: bysource


Lecture des variables d'environnement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.env
   :members:
   :member-order: bysource


Envoi de webhooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.webhook
   :members:
   :member-order: bysource


Outils divers et variés
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.tools
   :members:
   :member-order: bysource


Émulation de terminal Python (avancé)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: lgrez.blocs.realshell
