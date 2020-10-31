# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased
### Added
- Documentation now covers every public classes and functions
- ``!help`` now shows bot version

### Changed
- Made some functions private (leading _)
- Changed data attributes with leading underscores (like ``Joueurs._chan_id``) with trailing underscores (``Joueurs.chan_id_``)
- Removed useless parameter in blocs.tools.create_context
- Disabled ``!droptable``

### Fixed

- Issue with bot intents: proprer access to member list
- Critical bug with ``!stop`` and voting commands
- Configuration Assistant Tool: escape ``\n``s in ``LGREZ_GCP_CREDENTIALS``
- ``!plot`` now creates ``./features`` folder if not existing


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
