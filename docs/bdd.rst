``lgrez.bdd`` (Gestion des données)
===============================================================


.. automodule:: lgrez.bdd
    :members: connect

    .. data:: tables

        Dictionnaire ``{nom de la base -> table}``, automatiquement rempli
        par :func:`sqlalchemy.ext.declarative.declarative_base` (via le
        paramètre ``class_registry``).

        :type: :class:`dict`\[:class:`str`, :class:`TableBase` subclass\]

    .. exception:: SQLAlchemyError

        Alias de :exc:`sqlalchemy.exc.SQLAlchemyError` : exception de
        BDD générale.

    .. exception:: DriverOperationalError

        Alias de :exc:`psycopg2.OperationalError` : erreur levée en cas
        de perte de connexion avec la BDD. Seul PostreSQL est géré
        nativement : le cas échéant, remplacer cette exception par
        l'équivalent pour un autre driver.



``.base``
-----------------------------------------

.. automodule:: lgrez.bdd.base
   :members: autodoc_Column, autodoc_ManyToOne,
             autodoc_OneToMany, autodoc_ManyToMany, TableMeta


Table de base
~~~~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.base.TableBase
    :members:

    .. automethod:: add
    .. automethod:: update
    .. automethod:: delete



Enums
-----------------------------------------

.. automodule:: lgrez.bdd.enums

Énumérations (sous-classes de :class:`enum.Enum`) utilisées dans les
différentes tables du modèle de données :

.. autoclass:: lgrez.bdd.Statut
.. autoclass:: lgrez.bdd.ActionTrigger
.. autoclass:: lgrez.bdd.CandidHaroType


Modèle de données - Joueurs
-----------------------------------------

.. automodule:: lgrez.bdd.model_joueurs

Enregistrement des joueurs et de leurs actions publiques

Joueurs
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Joueur
    :members:
    :member-order: bysource


CandidHaros
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.CandidHaro
    :members:
    :member-order: bysource


Modèle de données - Jeu
-----------------------------------------

.. automodule:: lgrez.bdd.model_jeu

Personnalisation des rôles, camps et actions liées

Rôles
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Role
    :members:
    :member-order: bysource


Camps
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Camp
    :members:
    :member-order: bysource


Actions de base
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.BaseAction
    :members:
    :member-order: bysource


Modèle de données - Actions
-----------------------------------------

.. automodule:: lgrez.bdd.model_actions

Actions, leurs utilisations et ciblages (à venir)

Actions
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Action
    :members:
    :member-order: bysource


Tâches
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Tache
    :members:
    :member-order: bysource



Modèle de données - IA
-----------------------------------------

.. automodule:: lgrez.bdd.model_ia

Réactions
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Reaction
    :members:
    :member-order: bysource


Triggers
~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bdd.Trigger
    :members:
    :member-order: bysource
