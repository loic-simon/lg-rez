from __future__ import annotations
import asyncio
import datetime
import functools

from typing import Callable, Coroutine, NamedTuple, TypeVar
import typing

import discord
from discord import ui

from lgrez import commons
from lgrez.blocs import tools


class DiscordJourneyView(ui.View):
    def __init__(self, journey: DiscordJourney, timeout: float | None = 180):
        self.journey = journey
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.journey._interaction_check(interaction)


class DiscordJourneyModal(ui.Modal):
    def __init__(self, journey: DiscordJourney, title: str, timeout: float | None = 180):
        self.journey = journey
        super().__init__(title=title, timeout=timeout)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.journey.interaction = interaction
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.journey._interaction_check(interaction)


def _create_button(input: ui.Button | str | discord.Emoji) -> ui.Button:
    if isinstance(input, ui.Button):
        input.label = input.label[:80]
        return input
    if isinstance(input, discord.Emoji):
        return ui.Button(emoji=input)
    if len(input) <= 2 and not input.isascii():
        return ui.Button(emoji=input)
    else:
        return ui.Button(label=str(input)[:80])


def _create_select_option(input: discord.SelectOption | str) -> discord.SelectOption:
    if isinstance(input, discord.SelectOption):
        return input
    return discord.SelectOption(label=input)


_Key = TypeVar("_Key")


class DiscordJourney:
    RUNNING_INTERACTION = None
    TIMEOUT_DELAY = 2

    _catch_next_command_channel: discord.TextChannel | None = None
    _catch_next_command_member: discord.Member | None = None
    _catch_next_command_coro: typing.Coroutine
    _tasks = set()

    def __init__(
        self,
        interaction: discord.Interaction,
        *,
        ephemeral: bool = False,
        author_only: discord.Member | None = None,
        timeout: float | None = None,
    ) -> None:
        self.interaction = interaction
        self.ephemeral = ephemeral
        self.author_only = author_only
        self.timeout = timeout

        self.member = interaction.user
        if not isinstance(self.member, discord.Member):
            raise ValueError(f"Interaction user is not a guild member (type {type(self.member)})")
        self.channel: discord.TextChannel = interaction.channel
        self.created_at: datetime.datetime = interaction.created_at

        self._stopped: bool = False

    @property
    def interaction(self) -> discord.Interaction:
        return self._interaction

    @interaction.setter
    def interaction(self, new_interaction: discord.Interaction) -> None:
        if not isinstance(new_interaction, discord.Interaction):
            raise TypeError(f"DiscordJourney.interaction must be a discord.Interaction! (got {type(new_interaction)})")
        self._interaction = new_interaction
        asyncio.get_running_loop().call_later(self.TIMEOUT_DELAY, self._timeout_interaction)

    def _timeout_interaction(self) -> None:
        if self.interaction.response.is_done():
            return
        task = asyncio.create_task(self.interaction.response.defer(thinking=True))
        self._tasks.add(task)  # Cf. https://docs.python.org/fr/3/library/asyncio-task.html#asyncio.create_task
        task.add_done_callback(self._tasks.discard)

    async def _send_message(
        self,
        content: str | None = None,
        view: ui.View | None = None,
        code: bool = False,
        prefix: str = "",
        ephemeral: bool = False,
        **kwargs,
    ) -> list[discord.Message]:
        ephemeral = ephemeral or self.ephemeral
        return await tools.send_blocs(self.interaction, content, code=code, view=view, ephemeral=ephemeral, **kwargs)

    async def final_message(
        self, content: str | None = None, code: bool = False, prefix: str = "", **kwargs
    ) -> list[discord.Message]:
        return await self._send_message(content, code=code, prefix=prefix, **kwargs)

    def _check_state(self) -> None:
        if self._stopped:
            raise RuntimeError("Journey is stopped")

    async def _interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_only and self.author_only != interaction.user:
            return False
        return True

    async def __aenter__(self):
        DiscordJourney.RUNNING_INTERACTION = None
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self.interaction.response.is_done():
            if exc_type:
                DiscordJourney.RUNNING_INTERACTION = self.interaction
            else:
                try:
                    await self.interaction.response.defer()
                except discord.HTTPException:
                    pass
        self._stopped = True

    @staticmethod
    def _clicked_button_cleanup(button: ui.Button, view: ui.View) -> None:
        button.disabled = True

    @staticmethod
    def _not_clicked_button_cleanup(button: ui.Button, view: ui.View) -> None:
        view.remove_item(button)

    async def buttons(
        self,
        content: str,
        buttons: dict[_Key, ui.Button | str | discord.Emoji],
        clicked_button_cleanup: Callable[[ui.Button, ui.View], None] = _clicked_button_cleanup,
        not_clicked_button_cleanup: Callable[[ui.Button, ui.View], None] = _not_clicked_button_cleanup,
        **kwargs,
    ) -> _Key:
        self._check_state()
        view = DiscordJourneyView(self, timeout=self.timeout)
        clicked_button = None

        def _get_button_callback(button: ui.Button) -> Callable[[discord.Interaction], Coroutine]:
            async def _callback(interaction: discord.Interaction):
                nonlocal clicked_button
                self.interaction = interaction
                clicked_button = button
                view.stop()

            return _callback

        for key, button in buttons.items():
            button = _create_button(button)
            button.callback = _get_button_callback(button)
            view.add_item(button)
            buttons[key] = button

        *_, message = await self._send_message(content, view, **kwargs)  # Show buttons to user
        try:
            timeout = await view.wait()  # Wait for user click
        except asyncio.CancelledError:
            pass  # Clean view when cancelled
        else:
            if timeout:
                raise RuntimeError("Journey timeout")

        # Clean view
        clicked_key = None
        for key, button in buttons.items():
            if button == clicked_button:
                clicked_key = key
                clicked_button_cleanup(button, view)
            else:
                not_clicked_button_cleanup(button, view)
        await message.edit(view=view)

        return clicked_key

    async def yes_no(self, content: str, yes_emoji="✅", no_emoji="❌", **kwargs) -> bool:
        buttons = {
            True: ui.Button(emoji=yes_emoji, style=discord.ButtonStyle.success),
            False: ui.Button(emoji=no_emoji, style=discord.ButtonStyle.secondary),
        }
        return await self.buttons(content, buttons, **kwargs)

    async def ok_cancel(self, content: str, ok_emoji="✅", cancel_emoji="❌", **kwargs) -> None:
        ok_button = ui.Button(emoji=ok_emoji, style=discord.ButtonStyle.success)
        cancel_button = ui.Button(emoji=cancel_emoji, style=discord.ButtonStyle.secondary)

        def clicked_button_cleanup(button: ui.Button, view: ui.View) -> None:
            self._clicked_button_cleanup(button, view)
            if button == cancel_button:
                button.label = "Mission aborted."

        if not await self.buttons(
            content, {True: ok_button, False: cancel_button}, clicked_button_cleanup=clicked_button_cleanup, **kwargs
        ):
            await self.interaction.response.defer()
            raise commons.CommandAbortedError()

    async def select(
        self,
        content: str,
        options: dict[_Key, discord.SelectOption | str],
        placeholder: str | None = None,
        validate: str | None = None,
    ) -> _Key:
        self._check_state()
        view = DiscordJourneyView(self, timeout=self.timeout)

        options = {key: _create_select_option(option) for key, option in options.items()}
        select = ui.Select(options=options.values(), placeholder=placeholder)
        view.add_item(select)

        async def _callback(interaction: discord.Interaction):
            self.interaction = interaction
            view.stop()

        if validate:
            button = ui.Button(label=validate)
            view.add_item(button)
            button.callback = _callback

            async def _noop_callback(interaction: discord.Interaction):
                await interaction.response.defer()

            select.callback = _noop_callback
        else:
            select.callback = _callback

        *_, message = await self._send_message(content, view)  # Show select to user
        try:
            timeout = await view.wait()  # Wait for user click
        except asyncio.CancelledError:
            pass  # Clean view and exit
        else:
            if timeout:
                raise RuntimeError("Journey timeout")

        # Clean view
        if select.values:
            [value] = select.values
            key, option = next((key, option) for key, option in options.items() if option.value == value)
            option.default = True
            select.options = [option]
            select.disabled = True
        else:
            view.remove_item(select)
        if validate:
            view.remove_item(button)
        await message.edit(view=view)

        return key

    async def modal(self, title: str, *items: discord.TextInput | str) -> list[str]:
        self._check_state()
        modal = DiscordJourneyModal(self, title=title, timeout=self.timeout)

        inputs = [ui.TextInput(label=item) if isinstance(item, str) else item for item in items]
        for input in inputs:
            modal.add_item(input)

        if self.interaction.response.is_done():
            raise RuntimeError("No active interaction, cannot send modal")

        await self.interaction.response.send_modal(modal)  # Show modal to user
        timeout = await modal.wait()  # Wait for modal completion
        if timeout:
            raise RuntimeError("Journey timeout")
        self._check_state()

        return [input.value for input in inputs]

    @classmethod
    async def _catch_next_command(self) -> tuple[discord.Interaction, Callable[[DiscordJourney], typing.Coroutine]]:
        class _Awaitable:
            # Oh, well... let's say it just work?
            # If you really want to dig, begin with https://stackoverflow.com/a/60118660
            def __await__(self):
                while True:
                    result = yield
                    if result:
                        yield
                        return result

        async def _catch_next_command():
            return await _Awaitable()

        self._catch_next_command_channel = self.channel
        self._catch_next_command_member = self.member
        self._catch_next_command_coro = _catch_next_command()

        try:
            return await self._catch_next_command_coro
        finally:  # Stop catching
            self._catch_next_command_channel = None
            self._catch_next_command_member = None
            self._catch_next_command_coro = None

    async def catch_next_command(self, next_command_message: str):
        catch_task = asyncio.Task(self._catch_next_command())
        cancel_task = asyncio.Task(
            self.buttons(
                f"{next_command_message} :arrow_down:",
                {"cancel": discord.ui.Button(label="Annuler", emoji="❌")},
                ephemeral=True,
            )
        )
        done, _ = await asyncio.wait([catch_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)

        match list(done):
            case [task] if task == catch_task:
                cancel_task.cancel()  # Remove cancel button
                return catch_task.result()
            case [task] if task == cancel_task:
                catch_task.cancel()  # Stop command catching
                raise commons.CommandAbortedError()
            case []:  # Exception in one of the coroutines
                catch_task.cancel()
                cancel_task.cancel()
                raise commons.CommandAbortedError()
            case _:
                raise RuntimeError(f"heu -> {done}")

    @classmethod
    def _journey_command(cls, callable):
        @functools.wraps(callable)
        async def new_callable(interaction: discord.Interaction, **kwargs):
            async def _run_command(_journey: DiscordJourney):  # Closure
                await callable(_journey, **kwargs)

            if (
                cls._catch_next_command_channel
                and interaction.channel == cls._catch_next_command_channel
                and interaction.user == cls._catch_next_command_member
            ):
                cls._catch_next_command_channel = None
                cls._catch_next_command_member = None
                cls._catch_next_command_coro.send((interaction, _run_command))
                return  # Do not execute command

            async with cls(interaction) as journey:
                await _run_command(journey)

        return new_callable


def journey_command(callable: Callable[[DiscordJourney], None]) -> Callable[[discord.Interaction], None]:
    return DiscordJourney._journey_command(callable)


_CT = typing.TypeVar("_CT", discord.Message, discord.Member)


def journey_context_menu(callable: Callable[[DiscordJourney, _CT], None]) -> Callable[[discord.Interaction, _CT], None]:
    @functools.wraps(callable)
    async def new_callable(interaction: discord.Interaction, arg: _CT):
        async with DiscordJourney(interaction) as journey:
            await callable(journey, arg)

    return new_callable
