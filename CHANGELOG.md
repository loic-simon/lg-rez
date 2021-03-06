# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 1.2.0 - 2020-12-18
### Added

- Commands:
    - ``!vivants``: new aliases ``!joueurs`` and ``!vivant`` / ``!morts``: new aliases ``!mort``.
    - ``!post`` (in ``features.communication.Communication``) to send a message to a specific channel.
    - ``!panik`` (in ``bot.Special``) to instantly kill the bot.
    - ``!actions`` (in ``features.informations.Informations``) to see and edit players actions [beta].
    - ``!reactfals`` (alias ``!rf``, in ``features.IA.GestionIA``) using new function ``features.IA.fetch_tenor``.
    - ``!xkcd (in ``features.annexe.Annexe``).
    -
- Bot behavior:
    - New IA rule: "A ou B" ==> "B" (``features.IA.trigger_a_ou_b``).
    - ``!plot cond``: thumbnail of camp.
    - ``!open cond``: send post on #haros and wipes.
    - New liveness checking system: new method ``LGBot.i_am_alive`` writes every 60s current UTC time to a ``"alive.log"`` (set `LGBot.config["output_liveness"]`` to ``True`` to enable)
    - Now BONKs every message of users with "puni" in their top role name (needs a :bonk: emoji)
- API usage:
    - Emojis with names starting with ``"suric"`` are deleted and ``"!r suricate"`` is invoked in their private chan if no-MJ user.
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
