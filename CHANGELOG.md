# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unrealeased

### Added

  - Extended Data model with New Actions System (NAS) data classes
    (:class:`.bdd.Utilisation`, :class:`.bdd.BaseCiblage` and
    :class:`.bdd.Ciblage`) and enums (:class:`.bdd.CibleType`,
    :class:`.bdd.UtilEtat` and :class:`.bdd.Vote`);
  - Updated ``!fillroles`` to fill BaseCiblages too (new config option
    :attr:`config.max_ciblages_per_action`);
  - ``!cparti`` now add "vote actions" to all players;
  - New convenience function :func:`.bdd.base.autodoc_DynamicOneToMany`
    for documenting dynamicly loaded one-to-many relationships;

### Changed

  - Updated existing data classes attributes to link to new tables;
  - Made :attr:`.bdd.Action.base` nullable and added :attr:`.bdd.Action.vote`
    optionnal attributes to handle votes in a cleaner way; also added
    :attr:`.bdd.Action.active` attribute to keep track;
  - New properties :attr:`.bdd.Action.utilisation_ouverte`,
    :attr:`.bdd.Action.decision`, :attr:`.bdd.Action.is_open` (hybrid)
    and :attr:`.bdd.Action.is_waiting` (hybrid);
  - New method :meth:`.bdd.Joueur.action_vote`;
  - Updated :meth:`.features.open_close.recup_joueurs`, ``!open``,
    ``!close`` and ``!remind``;
  - New option ``nullable`` for :func:`.bdd.base.autodoc_ManyToOne`;
  - New class methods for :class:`.bdd.ActionTrigger` enum to get
    vote-related triggers from :class:`.bdd.Vote` enum ;
  - ``!fillroles`` now post camps descriptions in roles channel;
  - Extended :attr:`.bdd.model_jeu.Camp.description` max length to 1000.

### Fixed

  - Documentation errors & typos.



## 2.0.0 - 2021-03-24

### Major refactorings

#### Data management

  - ``blocs.bdd`` moved to :mod:`.bdd` module and splitted in
    :mod:`.bdd.base` (base classes and utilities),
    :mod:`.bdd.enums` (enums, directly imported in ``.bdd``),
    and :mod:`.bdd.model_joueurs`, :mod:`.bdd.model_jeu`,
    :mod:`.bdd.model_actions`, :mod:`.bdd.model_ia` modules
    (data classes, directly imported in ``bdd``);
  - Every data classes names changed to singular names
    (:class:`.bdd.Joueur`, :class:`.bdd.Role`...);
  - Implemented SQLAlchemy relationships and made foreign key
    arguments private (``Joueur.role`` -> ``Joueur._role_slug``,
    ``Joueur.role`` = direct access to ``Role`` object);
  - Added custom metaclass ``bdd.TableMeta`` for class tables: more
    robust implementation of ``Table.query``, and other convenience
    properties;
  - Enhanced data classes with custom properties and classmethods:
    :meth:`.bdd.Joueur.member`, :meth:`.bdd.Joueur.private_chan`,
    :meth:`.bdd.Joueur.from_member`, :meth:`.bdd.Role.nom_complet`,
    :meth:`.bdd.Role.default`, :meth:`.bdd.Camp.default`,
    :meth:`.bdd.Camp.discord_emoji`,
    :meth:`.bdd.Camp.discord_emoji_or_none`;
  - Enhanced data classes with instances methods:
    :meth:`~.bdd.base.TableBase.add`, :meth:`~.bdd.base.TableBase.delete`
    (global handy methods), :meth:`.bdd.Tache.add`, and specific
    :meth:`.bdd.Tache.delete`, :meth:`.bdd.Tache.register`,
    :meth:`.bdd.Tache.cancel`, :meth:`.bdd.Tache.execute`;
  - Use Enums when needed: :class:`.bdd.Statut`,
    :class:`.bdd.ActionTrigger`, :class:`.bdd.CandidHaroType`;
  - ``bdd.__all__`` contains all data classes (for ``import *``).

#### Global namespace

New :mod:`.config` namespace module for:
  - **Global variables**: implemented system of readiness check on
    attributes (through new :mod:`.blocs.ready_check` module), used for:
      - Bot objects: :attr:`.config.bot` (loaded by :meth:`.LGBot.run`)
        and :attr:`.config.loop` (loaded by :meth:`.LGBot.on_ready`),
      - Server: :attr:`.config.guild` (loaded by :meth:`.LGBot.on_ready`),
      - Database connection: :attr:`.config.engine` and
        :attr:`.config.session` (loaded by :meth:`.bdd.connect`),
      - Discord objects: :class:`.config.Role`, :class:`.config.Channel`,
        :class:`.config.Emoji` classes store roles/channels/emojis
        the bot needs to work, registered as names (customizable) and
        then transformed in connected objects by :meth:`.LGBot.on_ready`.
  - **Customization**:
      - Private channels creation: :attr:`.config.private_chan_prefix`,
        :attr:`.config.private_chan_category_name`,
      - Old ``bot.config`` keys: :attr:`~lgrez.config.debut_saison`,
        :attr:`~lgrez.config.demande_chambre`,
        :attr:`~lgrez.config.chambre_mj`,
        :attr:`~lgrez.config.output_liveness`.

Consequences:
  - **LGBot is no more thread-safe**: only one bot instance should
    run concurrently in an interpreter.

  - "Connected" arguments (``bot``, ``ctx``, ``loop``...) removed from
    several functions signatures, now using ``config`` attributes:
      - :func:`.blocs.tools.channel`, :func:`~.blocs.tools.role`,
        :func:`~.blocs.tools.member`, :func:`~.blocs.tools.emoji`,
        :func:`~.blocs.tools.log`, :func:`~.blocs.tools.yes_no`,
        :func:`~.blocs.tools.wait_for_message`,
        :func:`~.blocs.tools.boucle_message`,
        :func:`~.blocs.tools.wait_for_react_clic`,
        :func:`~.blocs.tools.choice`, :func:`~.blocs.tools.create_context`;
      - :func:`.features.gestion_actions.add_action`,
        :func:`~.features.gestion_actions.delete_action`,
        :func:`~.features.gestion_actions.open_action`,
        :func:`~.features.gestion_actions.close_action` ;
      - :func:`.features.inscription.main`;
      - :func:`.features.IA.process_IA`,
        :func:`~.features.IA.trigger_reactions`,
        :func:`~.features.IA.trigger_sub_reactions`,
        :func:`~.features.IA.trigger_gif` ;
      - :func:`.features.sync.modif_joueur`.


### Also added

  - :class:`bdd.Camp` table (and made :attr:`.bdd.Joueur.camp` and
    :attr:`.bdd.Role.camp` relationships);
  - :func:`.bdd.base.autodoc_Column`, :func:`.autodoc_OneToMany`,
    :func:`.autodoc_ManyToOne` and :func:`.autodoc_ManyToMany`
    convenience functions to easily document bdd attributes;
  - :attr:`.bdd.Tache.handler` convenience property;
  - :func:`.blocs.tools.en_pause` helper function.


### Also changed

  - ``bot.Special`` cog moved to new :mod:`.features.special` module.
  - :class:`~.LGbot` one-command-at-a-time system moved to new
    :mod:`.blocs.one_command` module.
  - Renamed ``blocs.bdd.Tables`` in :attr:`lgrez.bdd.tables`, and
    made it auto-build by SQLAlchemy Declarative;
  - Renamed ``blocs.bdd.Base`` in :attr:`lgrez.bdd.base.TableBase`;
  - :meth:`<Table>.query <.bdd.base.TableMeta.query>` uses
    :attr:`config.session` (raises :exc:`.blocs.ready_check.NotReadyError`
    if not initialised);
  - made `gestion_actions.get_actions` not async;
  - Adapted ``!roles`` behavior to new ``Camp`` table;
  - Removed unused option ``chan`` from
    :func:`.features.gestion_actions.open_action` and
    :func:`~.features.gestion_actions.close_action`;
  - :func:`.blocs.tools.next_occurence` now relies on
    :func:`~.blocs.tools.debut_pause` and :func:`~.blocs.tools.fin_pause`
    functions instead of hard-coded pause times;
  - Updated the *Configuration Assistant Tool* (``__main__.py``) with
    some changes on Google Sheets script editor and other minor changes;
  - Splitted API Reference in several doc pages, and other global
    documentation and codestyle improvements (source code now almost
    entirely PEP8-compliant).

### Also removed

  - ``!modifIA``: removed option to edit both triggers and response;
  - Made ``blocs.bdd.BaseActionsRoles`` private: use directly
    :attr:`.bdd.BaseAction.roles` and :attr:`.bdd.Role.base_actions`
    *many-to-many relationship* attributes);
  - :class:`.bdd.BaseAction`: removed ``base_`` arguments, not specific
    to the action (use ``action.base.<arg>`` instead);
  - :mod:`blocs.tools`: removed ``emoji_camp``, ``private_chan`` and
    ``nom_role`` functions (use :attr:`.bdd.Camp.discord_emoji` or
    :attr:`~.bdd.Camp.discord_emoji_or_none` properties /
    :attr:`.bdd.Joueur.private_chan` property / :attr:`.bdd.Role.nom`
    attribute or :attr:`.bdd.Role.nom_complet` property instead);
  - Removed ``blocs.bdd_tools`` module (use
    :attr:`<Table>.columns <.bdd.base.TableMeta.columns>` and
    :attr:`<Table>.primary_col <.bdd.base.TableMeta.primary_col>` properties,
    :meth:`<Table>.find_nearest() <.bdd.base.TableMeta.find_nearest>` method,
    and :func:`.features.sync.transtype` function instead);
  - Removed ``features.taches.add_task``, ``delete_task``, ``execute``
    functions (use :meth:`.bdd.Tache.add`, :meth:`~.bdd.Tache.delete` and
    :meth:`~.bdd.Tache.execute` methods instead);
  - Removed ``LGBot.config`` attribute (use :mod:`.lgrez.config` module
    instead).



## 1.2.0 - 2020-12-18
### Added

- Commands:
    - ``!vivants``: new aliases ``!joueurs`` and ``!vivant`` / ``!morts``: new aliases ``!mort``.
    - ``!post`` (in ``features.communication.Communication``) to send a message to a specific channel.
    - ``!panik`` (in ``bot.Special``) to instantly kill the bot.
    - ``!actions`` (in ``features.informations.Informations``) to see and edit players actions [beta].
    - ``!quiest`` and ``!rolede`` (in ``features.informations.Informations``) to see players with a given role and vice versa.
    - ``!reactfals`` (alias ``!rf``, in ``features.IA.GestionIA``) using new function ``features.IA.fetch_tenor``.
    - ``!xkcd`` (in ``features.annexe.Annexe``).
- Bot behavior:
    - New IA rule: "A ou B" ==> "B" (``features.IA.trigger_a_ou_b``).
    - ``!plot cond``: thumbnail of camp.
    - ``!open cond``: send post on #haros and wipes.
    - New liveness checking system: new method ``LGBot.i_am_alive`` writes every 60s current UTC time to a ``"alive.log"`` (set ``LGBot.config["output_liveness"]`` to ``True`` to enable)
- API usage:
    - Inscription: customize default chambre with ``LGBot.config["chambre_mj"]``.
    - ``blocs.tools.yes_no``: new ``additionnal`` option to add aditionnal emojis.

### Changed

- Commands:
    - ``!send`` can now accept a player name (send to private chan).
    - ``!plot cond`` now shows faction (emoji) of killed player.
    - ``!annoncemort`` now announces if killed player is living-dead.
    - ``!sync`` now asks for confirmation before applying modifications.
- Bot behavior:
    - Calling a command when already in a command now tries to stop running command and run afterwards instead of aborting.
    - Actions by emojis: only trigger in private chans.
    - Now sends a reminder every morning to always-usable actions.
- API usage:
    - Renamed ``features.IA.tenor`` in ``features.IA.trigger_gif`` (consistency).
    - ``features.sync``: better management of modification with new class ``TDBModif`` and of exceptions with new specific function ``validate_sync``.
    - ``tools.bdd_tools.find_nearest``: standardized first word comparison with ``match_first_word`` option.
    - ``!shell``: now using (new) ``blocs.realshell`` module (based on (new dependency) ``asyncode`` module) instead of (removed) ``blocs.pseudoshell``.
- Other minor improvements.

### Fixed

- Fixed critical bug when changing ``role`` (through ``!sync``).
- ``features.taches``: fixed critical bug when too much tasks at the same times (Discord's webhooks rate limits).
- Inscription: fixed critical bug when > 50 players.
- Some docstrings corrections.
- Other minor bugs.


## 1.1.0 - 2020-11-03
### Added

- New command ``!annoncemort`` (in new module ``features.communication``).
- Added ``LGBot.config`` to permit easier bot customization.
    - Customize inscription with ``LGBot.config["demande_chambre"]`` and ``["debut_saison"]``.
- ``!help`` now shows bot version and commands outside of cogs.
- ``!open cond/maire`` now wipes CandidHaros.
- ``!refill`` now opens back permanent actions with new charges.
- Documentation now covers every public classes, functions and commands.

### Changed

- Made some functions private (leading ``_``).
- Changed data attributes with leading underscores (like ``Joueurs._chan_id``) with trailing underscores (``Joueurs.chan_id_``).
- Data column ``Joueurs.chambre`` is now nullable.
- ``!fals`` can now be used in non-private channels.
- ``blocs.bdd_tools.find_nearest`` is no longer a coroutine.
- Some refactoring:
    - ``features.informations.emoji_camp`` moved to ``blocs.tools.emoji_camp``.
    - ``!plot`` moved from ``features.actions_publiques`` to ``features.communication``.
    - ``!send`` and ``!embed`` moved from ``features.annexe`` to ``features.communication``.
    - ``!fillroles`` moved from ``features.remplissage_bdd`` (deleted) to ``features.communication``.

### Removed

- Deleted command ``!droptable``.
- Deleted module ``features.remplissage_bdd``.

### Fixed

- Issue with bot intents: proprer access to member list.
- Improved handling of BDD disconnections.
- Critical bug with ``!stop`` and voting commands.
- ``!plot`` now creates ``./figures`` folder if not existing.
- ``blocs.tools.wait_for_react_clic`` now handles correctly custom emojis.
- Configuration Assistant Tool: escape ``\n``s in ``LGREZ_GCP_CREDENTIALS``.
- Other minor bug fixes and improvements.


## 1.0.3 - 2020-10-22
### Added

- Created this changelog
- Added module and submodules docstrings and meta informations.
- Created Sphinx documentation (beta) on lg-rez.readthedocs.io.

### Changed

- README improvements (badges!) and corrections.
- Rewriting of bot.LGBot class and methods docstrings.
- More PyPI classifiers.

### Fixed

- Relative links in PyPI project description now redirect to files on GitHub (not to a 404 page).


## 1.0.2 - 2020-10-20
### Fixed

- Critical bug fix.


## 1.0.1 - 2020-10-20

Initial release.
