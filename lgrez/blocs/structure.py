"""lg-rez / blocs / Vérification de structure

"""

from contextlib import contextmanager
import enum
import types
from typing import Any, Iterator, Iterable

import discord


class Union(list):
    """Represent a union of possible structures.

    Args:
        *args: Accepted structures.
    """

    def __init__(self, *args) -> None:
        super().__init__(args)  # Pack items

    def __hash__(self) -> int:
        return 0  # don't do that

    def __str__(self) -> str:
        return "  OR  ".join(str(item) for item in self)

    def __repr__(self) -> str:
        return "  OR  ".join(repr(item) for item in self)


Data = dict | list | str | int | float | bool | None
Model = Union | type | types.UnionType | dict | list | None


class MatchError(RuntimeError):
    """Error occuring when matching a structure.

    Derives from :exc:`RuntimeError`.

    Args:
        msg: Exception message.
        data: Object we try to match.
        model: Structure we want to match on.
        path: JSON-like path from the structure root.
    """

    def __init__(
        self,
        msg: str,
        data: Data,
        model: Model,
        path: list[str],
    ) -> None:
        path_str = " > ".join(path)
        lines = [
            msg,
            f"  * Path: {path_str}",
            f"  * Model: {model!r}",
            f"  * Data: {data!r}",
        ]
        super().__init__("\n".join(lines))


class _StructureMatcher:
    def __init__(self) -> None:
        self.path = []

    @contextmanager
    def _dig_in(self, step: str) -> Iterator[None]:
        self.path.append(step)
        try:
            yield
        finally:
            self.path.pop(-1)

    def _check_structure_generic_dict(self, data: dict, model: dict) -> None:
        model_key, model_value = next(iter(model.items()))
        for key, value in data.items():
            with self._dig_in("(new key)"):
                self.check_structure(key, model_key)
            with self._dig_in(f'"{key}"'):
                self.check_structure(value, model_value)

    def _check_structure_dict(self, data: dict, model: dict) -> None:
        for key, model_value in model.items():
            if key not in data:
                raise MatchError(f"Missing {key!r} in data.", data, model, self.path)
            with self._dig_in(key):
                self.check_structure(data[key], model_value)

    def _check_structure_generic_list(self, data: list, model: list) -> None:
        model_item = next(iter(model))
        for count, item in enumerate(data):
            with self._dig_in(f"[{count}]"):
                self.check_structure(item, model_item)

    def _check_structure_list(self, data: list, model: list) -> None:
        if len(data) != len(model):
            raise MatchError("Lists are not of same length.", data, model, self.path)
        for count, (data_item, model_item) in enumerate(zip(data, model)):
            with self._dig_in(f"[{count}]"):
                self.check_structure(data_item, model_item)

    def _check_structure_enum(self, data: Any, model: enum.EnumMeta) -> None:
        try:
            model[data]
        except (KeyError, TypeError):
            raise MatchError(
                f"Data is not one in the values list.",
                data,
                Union(elem.name for elem in model),
                self.path,
            ) from None

    @staticmethod
    def _is_generic(iterable: list | dict) -> bool:
        if len(iterable) != 1:
            return False
        key = next(iter(iterable))
        if isinstance(key, str | int | float | bool | type(None)):
            return False
        return True

    def test_structure(self, data: Data, model: Model) -> bool:
        try:
            self.check_structure(data, model)
        except MatchError:
            return False
        else:
            return True

    def check_structure(self, data: Data, model: Model) -> None:
        match model, data:
            # OR
            case Union(), _:
                for submodel in model:
                    if self.test_structure(data, submodel):
                        break
                else:
                    raise MatchError("Could not match data on either of models.", data, model, self.path)

            # Type restriction
            case (enum.EnumMeta() | discord.enums.EnumMeta()), _:
                self._check_structure_enum(data, model)
            case type(), model():  # isinstance but 500 IQ (self-slurping yes)
                pass
            case type(), _:
                raise MatchError(f"Data is not of requested type.", data, model, self.path)
            case types.UnionType(), _:
                if not isinstance(data, model):
                    raise MatchError(f"Data is not of any of the requested types.", data, model, self.path)

            # Submodel
            case dict(), dict() if self._is_generic(model):
                self._check_structure_generic_dict(data, model)
            case dict(), dict():
                self._check_structure_dict(data, model)
            case list(), list() if self._is_generic(model):
                self._check_structure_generic_list(data, model)
            case list(), list():
                self._check_structure_list(data, model)
            case (dict() | list()), _:
                raise MatchError(f"Data is not of requested type.", data, model, self.path)

            # Literal
            case (str() | int() | float() | True | False | None), _:
                if data != model:
                    raise MatchError(f"Data is not the required literal.", data, model, self.path)

            # Fallback
            case _:
                raise MatchError(f"Could not match.", data, model, self.path)


def check_structure(data: Data, model: Model) -> None:
    """Check that a given object matches a required structure.

    Args:
        data: Object to match.
        model: Structure to match on.

    Raises:
        .MatchError: If matching failed.
    """
    _StructureMatcher().check_structure(data, model)


def check_server_structure(
    structure: dict,
    required_roles: Iterable[str],
    required_channels: Iterable[str],
    required_emojis: Iterable[str],
) -> None:
    """Check that the given dict represents a valid server structure.

    Args:
        structure: The dict to check.
        required_roles: The slugs of roles needed in the structure.
        required_channels: The slugs of channels needed in the structure.
        required_emojis: The slugs of emojis needed in the structure.

    Raises:
        .MatchError: If matching failed.
    """
    # Pseudo-types autorisés dans la structure
    role = Union("@everyone", *structure.get("roles", {}))
    channel = Union()
    for categ in structure.get("categories", {}).values():
        channel.extend(categ.get("channels", {}))
    permission = Union(*discord.Permissions.VALID_FLAGS)
    PermissionsGroup = enum.Enum(
        "PermissionsGroup",
        {
            prop: getattr(discord.Permissions, prop)()
            for prop in [
                "advanced",
                "all",
                "all_channel",
                "general",
                "membership",
                "stage",
                "stage_moderator",
                "text",
                "voice",
            ]
        },
    )

    # Structure requise
    required_structure = {
        "name": str,
        "icon": Union(
            None,
            {
                "drive": bool,
                "png_path_or_id": str,
            },
        ),
        "afk_channel": Union(channel, None),
        "afk_timeout": int,
        "verification_level": discord.VerificationLevel,
        "default_notifications": discord.NotificationLevel,
        "explicit_content_filter": discord.ContentFilter,
        "system_channel": channel,
        "system_channel_flags": {
            "join_notifications": bool,
            "premium_subscriptions": bool,
        },
        "preferred_locale": str,
        "roles": {
            str: {
                "name": str,
                "color": str,
                "hoist": bool,
                "mentionable": bool,
                "permissions": Union(PermissionsGroup, [permission]),
            },
        },
        "base_role": role,
        "everyone_permissions": [permission],
        "categories": {
            str: {
                "name": str,
                "overwrites": {role: {permission: bool}},
                "channels": {
                    str: {
                        "name": str,
                        "topic": str | None,
                        "overwrites": {role: {permission: bool | None}},
                    },
                },
                "voice_channels": {
                    str: {
                        "name": str,
                        "overwrites": {role: {permission: bool | None}},
                    },
                },
            },
        },
        "emojis": {
            "drive": bool,
            "folder_path_or_id": str,
            "required": {str: str},
            "restrict_roles": {str: Union(None, [role])},
        },
    }

    check_structure(structure, required_structure)

    # Vérification éléments imposés minimums
    for role in required_roles:
        if role == "everyone":
            continue
        if not role in structure["roles"]:
            raise RuntimeError('config.server_structure["roles"]: ' f'Missing role "{role}", required for playing!')
    for channel in required_channels:
        for categ in structure["categories"].values():
            if channel in categ["channels"]:
                break
        else:
            raise RuntimeError(
                'config.server_structure["categories"][<any categ>]'
                '["channels"]: '
                f'Missing channel "{channel}", required for playing!'
            )
    for emoji in required_emojis:
        if not emoji in structure["emojis"]["required"]:
            raise RuntimeError('config.server_structure["emojis"]: ' f'Missing emoji "{emoji}", required for playing!')
