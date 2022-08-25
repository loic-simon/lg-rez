
``lgrez.config`` (variables globales)
==========================================

.. automodule:: lgrez.config
    :members:
    :member-order: bysource

    .. data:: guild

        Le serveur Discord sur lequel se déroule la partie.

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel de
        :meth:`.LGBot.on_ready`.

        :type: :class:`discord.Guild`

    .. data:: bot

        Le bot en activité.

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel à
        :meth:`.LGBot.run`.

        :type: :class:`.LGBot`

    .. data:: loop

        La boucle asynchrone d'évènement utilisée par le bot et les
        tâches planifiées (raccourci pour pour ``config.bot.loop``).

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel de
        :meth:`.LGBot.on_ready`.

        :type: :class:`asyncio.AbstractEventLoop`

    .. data:: engine

        Le moteur de connexion à la base de données.

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel à
        :func:`.bdd.connect` (inclus dans :meth:`.LGBot.run`).

        :type: :class:`sqlalchemy.engine.Engine`

    .. data:: session

        La session de transaction avec la base de données.

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel à
        :func:`.bdd.connect` (inclus dans :meth:`.LGBot.run`).

        :type: :class:`sqlalchemy.orm.session.Session`

    .. data:: webhook

        Le webhook utilisé par les tâches planifiées.
        Poste dans :attr:`.config.Channel.logs`.

        Lève une :exc:`~readycheck.NotReadyError` avant l'appel de
        :meth:`.LGBot.on_ready`.

        :type: :class:`discord.Webhook`
