# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

*If you are reading this on GitHub, you may consider switching to the docs
to benefit Sphinx internal links to Python objects:*
https://lg-rez.readthedocs.io/fr/2.2.0/changelog.html


## 3.0.0 - 2022-10-12

  - Biggest update to date, switching from "bot commands" to Discord built-in
    application commands, using Discordpy 2.0.
  - A lot of major, breaking changes. Sorry, no time for changelog.
  - Who matters anyway?


## 2.4.4 - 2022-05-27

### Fixed

  - :func:`features.sync.process_mort` boudoir transfer selected dead player;
  - Small formatting problem with ``!cancel``.


## 2.4.3 - 2022-05-26

### Fixed

  - :func:`features.sync.process_mort` crashed if dead player was gerant of
    boudoirs, disallowing sync of dead players;
  - ``!planif`` crashed for dates in the past;
  - ``!mp`` crashed if combined names were > 32 characters long;
  - ``!refill`` crashed if only one action was refillable;
  - :func:`blocs.tools.mention_MJ` always returned a role mention.


## 2.4.2 - 2022-05-01

### Fixed

  - ``server_structure.json`` was not included in package data;
  - Minimal Python version was not updated (must be >=3.10 since 2.4).


## 2.4.1 - 2022-04-17

### Fixed

  - Fix dependency conflicts;
  - ReadTheDocs could not compile due to multiple problems;
  - Missed doc for new module :mod:`.blocs.structure`.


## 2.4.0 - 2022-04-17

### Added

  - Server automatic setup (guild, channels, roles, emojis...):
      - New command ``!setup``;
      - New module :mod:`.blocs.structure` to check server structure;
      - New config variables :attr:`.config.server_structure` (default:
        new file ``server_structure.json``) and :attr:`.config.is_setup`;
      - New functions :func:`.blocs.gsheets.get_files_in_folder`,
        :func:`.blocs.gsheets.download_file` and
        :func:`.config.set_config_from_server_structure`;
  - Remind to enable Dashboard backup Google Apps trigger in ``!cparti``;
  - Put role name in player's private chan topic on role sync;
  - New subcommands ``!boudoir find`` and ``!boudoir help``;
  - New command ``!mp`` to easily create a boudoir with some other player;
  - New command ``!cfini`` to automatically delete tasks at game end;
  - New command ``!nextroll``.

### Changed

  - Boudoirs are now transferred to most ancient member when owner dies;
  - A cross mark is now added to boudoir name when moved to cemetery;
  - ``!refill``: now ask to chose action (if > 1) instead of refilling all;
  - ``!lore``: better handle of players mentions (1 to 4 words);
  - ``!planif``: now planif to tomorrow if past date (rather that instant);
  - ``!cancel``: now directly cancels (no confirmation), but show command to
    type to re-planif task;
  - :func:`.features.gestion_actions.add_action` now creates action only if
    not already existing (changed signature: now takes action parameters);
  - Bumped packages dependencies.

### Fixed

  - Some bot parts did not work because of circular imports between
    :mod:`.bdd.model_joueurs` and :mod:`.blocs.tools`. Fixed by moving
    ``Boudoir.add_joueur``/``Boudoir.remove_joueur`` to new functions
    :func:`.features.chans.add_joueur_to_boudoir`/
    :func:`.features.chans.remove_joueur_from_boudoir`.
  - Crash when trying to add a joueur to a boudoir in cemetery;
  - ``!lore`` sometimes crashed when evaluating a role mention;
  - Admin console was endlessly rebooting when sending an EOF or when
    input pipe was closed (e.g. bot not launched from a TTY);
  - README's What's New in 2.3 was missing.


## 2.3.2 - 2021-11-11

### Changed

  - When a player is removed from / added to a boudoir, the boudoir is
    automatically sent to / from the boudoirs cemetery;
  - ``!roll`` now has limitations to avoid bot overloading by huge rolls;
    new special values ``ludopathe`` and ``tavernier``.

### Fixed

  - Automatic archiving of boudoirs when a player dies was not working
    as intended.


## 2.3.1 - 2021-11-10

### Changed

  - When a player die, useless boudoirs are now automatically moved in
    category :attr:`.config.old_boudoirs_category_name` (new config option,
    checked at startup) by new function :func:`.features.sync.process_mort`;
  - Code optimizations using new utility functions
    :func:`.blocs.tools.multicateg`, :func:`.blocs.tools.in_multicateg` and
    new decorator :func:`.features.chans.gerant_only`;
   - Added special values for ``!roll``: ``joueur``, ``vivant``, ``mort``,
    ``rôle``, ``camp``.

### Fixed

  - Joueurs could be added several times to boudoirs (several invites);
  - Some ``!boudoir`` options parameters were mandatory where they should not;
  - One-command limitation was not working with private commands outside
    private chans.


## 2.3.0 - 2021-11-06

### Added

  - New subcommand `!boudoir ping`;
  - New admin console to execute code/commands from the shell running
    the bot (BETA: direct commands execution) using new module
    :mod:`.blocs.console`;
  - New indicative messages about the `stop` keyword;
  - New property :meth:`.bdd.Camp.embed` (like :meth:`.bdd.Role.embed`).

### Changed

  - Command ``!roles`` separated inro ``!roles`` and new command ``!camps``
    to address some names overlapping issues and for more clarity.

### Fixed

  - Help message was not accurate for some subcommands errors;
  - Adding IA reactions could produce API 400 errors (empty messages).


## 2.2.2 - 2021-11-01

### Changed

  - Made gsheets operations asynchronous (using new dependency module
    :mod:`gspread_asyncio`): :func:`.blocs.gsheets.connect` and
    :func:`~.blocs.gsheets.update` are now asynchronous and work with
    :class:`~gspread_asyncio.AsyncioGspreadWorksheet` objects; some
    dependant functions made asynchronous too.

### Fixed

  - References to ``tools`` could not be used in reactions evaluations.
  - Bot activity was sometimes lost when errors occured.
  - Messages reactions caused fatal errors in some cases.


## 2.2.1 - 2021-10-24

### Fixed

  - Critical error in :func:`.features.sync.transtype` caused by
    SQLAlchemy internals changes between 1.3.x and 1.4.x.
  - Minor fixes in some commands docstrings.


## 2.2.0 - 2021-10-06

### Added

  - New command ``!modif`` to edit a bot message;
  - New commands table in :mod:`lgrez.features` doc page;
  - New convenience method :func:`.blocs.env.__getattr__`.

### Changed

  - Extended to Python 3.10
  - Bumped all requirements to their latest version

### Fixed

  - Diverse documentation fixes.


## 2.1.4 - 2021-07-10

### Changed

  - ``!lore`` can now replace ``@role_slug`` (:class:`.config.Role` attributes
    only) with role mention;
  - ``!doas`` can now act for players that left the server (limited range);
  - Database host and name is now printed at bot startup;
  - ``.gitignore`` now ignores all ``start_bot*.py`` files.

### Fixed

  - ``!open``/``!close``: new safety check to avoid double opening/closing;
  - Added :obj:`.config.is_ready` to avoid double :meth:`.LGBot.on_ready` calls;
  - Added unique constraint to :class:`.bdd.Role`-:class:`.bdd.BaseAction`
    junction table to avoid duplicate rows;
  - ``!boudoir``: dead players could create some and sometimes write messages in;
  - ``!lore`` did not correctly detect some docs ID;
  - ``!lore`` formatting failed on some specific cases (e.g bullet lists +
    italic);
  - ``!action``: :attr:`.bdd.UtilEtat.remplie` was sometimes used istead of
    :attr:`.bdd.UtilEtat.ignoree`;
  - Fixed fatal errors on :func:`.blocs.tools.private` commands warning
    messages, :func:`.features.voter_agir.get_cible`, ``!infos``, and role
    creation detection (if missing required roles);
  - Bumped dependencies security upgrades.


## 2.1.3 - 2021-04-26

### Changed

  - ``!boudoir``: ``invite`` and ``expulse`` now take only one name as
    a full argument, other various improvements;
  - ``!sync``: role sync message now hides role slug.

### Fixed

  - :func:`.blocs.tools.private`: fixed :mod:`.blocs.one_command` bypass;
  - ``!actions``: new action creation did not properly added action;
  - ``!open`` / ``!close``: all open/close triggers were not triggered;
  - :func:`.features.gestion_actions.close_action`: base cooldown was set
    on actions even if no decision was made;


## 2.1.2 - 2021-04-23

### Changed

  - ``!annoncemort`` can now prepair several embeds and post them at once;
  - ``!addIA``: new fast-add syntax and duplicate tirggers security check.

### Fixed

  - Error when using ``!menu`` before the game has started;
  - "stop" messages were detected by every waiting functions, even if an
    other chennel; this is solved by new ``chan`` keyword argument to
    :func:`.blocs.tools.wait_for_message`. Dependant functions were
    modified consequently; while optionnal, omitting this argument may
    lead to undetected "stop" messages.


## 2.1.1 - 2021-04-15

### Fixed

  - Critical error (importing non-requied package) in ``__main__.py``;
  - Bad order in inscription messages if chambre and additional step.


## 2.1.0 - 2021-04-13

### Added

  - New Actions System:
      - Extended Data model with tables :class:`.bdd.Utilisation`,
        :class:`.bdd.BaseCiblage`, :class:`.bdd.Ciblage` and enums
        :class:`.bdd.CibleType`, :class:`.bdd.UtilEtat`, :class:`.bdd.Vote`;
      - New columns :attr:`.bdd.BaseAction.decision_format` and
        :attr:`.bdd.Action.active`;
      - New properties :attr:`.bdd.BaseAction.temporalite` and
        :attr:`.bdd.Role.embed` to describe a role, used in ``!role``,
        ``!fillroles`` and :func:`.features.IA.trigger_roles`;

      - New properties :attr:`.bdd.Action.utilisation_ouverte`,
        :attr:`.bdd.Action.derniere_utilisation`, :attr:`.bdd.Action.decision`,
        and :attr:`.bdd.Action.is_open` / :attr:`.bdd.Action.is_waiting`
        (hybrid);
      - New method :meth:`.bdd.Joueur.action_vote`;
      - New hybrid properties :attr:`.bdd.Joueur.est_vivant` and
        :attr:`.bdd.Joueur.est_mort`;
      - New class methods :meth:`.bdd.ActionTrigger.open` and
        :meth:`.bdd.ActionTrigger.close`;

      - New function :func:`.features.voter_agir.get_cible`, used by ``!vote``,
        ``!votemaire``, ``!voteloups`` et ``!action`` to handle user inputs;
      - ``!cparti`` now add "vote actions" to all players;

  - Task postponing now uses Discord-py webhooks:
      - dropped requirement for `discord-webhook` module;
      - tasks now use :obj:`.config.webhook`, created by
        :meth:`.LGBot.on_ready` if not existing;
      - new method :meth:`.bdd.Tache.send_webhook`;
      - deleted ``blocs.webhook`` module and usage of ``LGREZ_WEBHOOK_URL``
        environnement variable;

  - New boudoirs management system:
      - New tables :class:`.bdd.Boudoir` and :class:`.bdd.Bouderie`;
      - New group command ``!boudoir`` (with 8 subcommands) in new module
        :mod:`.features.chans`;
      - New configuration option :attr:`.config.boudoirs_category_name`,
        loaded by :meth:`.LGBot.on_ready`,
      - Updated ``!help`` and doc tools to handle group commands;

  - New command ``!lore`` using new Google Docs connection function
    :func:`.blocs.gsheets.get_doc_content`;

  - Miscellaneous:
      - New function :func:`.blocs.tools.boucle_query` for generic database
        instance lookup interactions;
      - New method :func:`.LGBot.check_and_prepare_objects` (originally
        directly in :func:`.LGBot.on_ready`), called by Discord events
        concerning roles, channels, emojis and webhooks ;
      - New customizable function :func:`.config.additional_inscription_step`;
      - :func:`.blocs.tools.wait_for_react_clic` and
        :func:`.blocs.tools.yes_no`: new kwarg ``first_text``;
      - New column :attr:`.bdd.Role.actif`, ``!roles``, ``!fillroles`` and IA
        now restricts to roles with ``actif = True``;
      - New convenience function :func:`.bdd.base.autodoc_DynamicOneToMany`
        for documenting dynamicly loaded one-to-many relationships;
      - New option ``nullable`` for :func:`.bdd.base.autodoc_ManyToOne`;

### Changed

  - Updated existing data classes attributes to link to new tables;
  - Made :attr:`.bdd.Action.base` nullable and added :attr:`.bdd.Action.vote`
    optionnal attributes to handle votes in a cleaner way (with instance
    initialization integrity check);
  - Updated :meth:`.features.open_close.recup_joueurs`, ``!open``,
    ``!close`` and ``!remind``;
  - :func:`.features.gestion_actions.delete_action` now updates
    :attr:`.bdd.Action.active` insteade of deleting the instance;
  - :func:`.features.voter_agir.export_vote` signature changed;
  - ``!plot`` now uses new actions system instead of loading votes from
    the Gsheet:
      - removed config options ``tdb_votecond_column``,
        ``tdb_votantcond_column``, ``tdb_votemaire_column`` and
        ``tdb_votantmaire_column``;
      - it now automatically computes votes additions and modifications
        (Corbeau / Intrigant), using new config options
        :attr:`config.ajout_vote_baseaction`, :attr:`config.n_ajouts_votes`,
        :attr:`config.modif_vote_baseaction`;
  - ``!fillroles`` now synchronise :class:`.bdd.BaseCiblage` too (see
    :attr:`.config.max_ciblages_per_action`) and post camps descriptions;
  - Moved ``!addhere`` and ``!purge`` from :mod:`.features.annexe` to
    new module :mod:`.features.chans`;
  - Updated some string columns max lengths;
  - Made ``__str__`` implementation specific for :class:`.bdd.Role`,
    :class:`.bdd.Camp`, :class:`.bdd.BaseAction` and :class:`.bdd.Joueur`.

### Removed

  - Tables columns :attr:`.bdd.Joueur._vote_condamne`,
    :attr:`.bdd.Joueur._vote_maire`, :attr:`.bdd.Joueur._vote_loups`,
    :attr:`.bdd.Action._decision`, :attr:`.bdd.BaseAction.changement_cible`;
  - ``.blocs.webhook`` module.

### Fixed

  - :func:`features.voter_agir.export_vote` (``!vote*`` et ``!action``):
    used hard-written sheet names istead of :attr:`config.db_votecond_sheet`,
    :attr:`config.db_votemaire_sheet`, :attr:`config.db_voteloups_sheet`
    and :attr:`config.db_actions_sheet`;
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
    - ``blocs.tools.yes_no``: new ``additional`` option to add additional emojis.

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
