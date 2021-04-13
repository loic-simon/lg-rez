
``lgrez.LGBot`` (classe principale)
==========================================

.. autoclass:: lgrez.LGBot
    :members:
    :member-order: bysource

    .. automethod:: on_guild_channel_delete
    .. automethod:: on_guild_channel_update
    .. automethod:: on_guild_channel_create
    .. automethod:: on_guild_role_delete
    .. automethod:: on_guild_role_update
    .. automethod:: on_guild_role_create
    .. automethod:: on_guild_emojis_update
    .. automethod:: on_webhooks_update

        Méthodes appelées par Discord aux différents évènements correspondants.

        LG-Bot n'utilise ces méthodes que pour vérifier qu'aucun objet
        indispensable au fonctionnement du bot n'a été altéré
        (voir :meth:`check_and_prepare_objects`).
