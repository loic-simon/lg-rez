
def test(ctx):
    arg = ctx.message.content.split(maxsplit=1)[1]  # enlève le !test du début
    auteur = ctx.author.name
    salon = ctx.channel.name if hasattr(ctx.channel, "name") else f"DMChannel de {ctx.channel.recipient.name}"
    serveur = ctx.guild.name if hasattr(ctx.guild, "name") else "(DM)"
    # pref = ctx.prefix
    # com = ctx.command
    # ivkw = ctx.invoked_with
    return (f"```arg = {arg}\n"
            f"auteur = {auteur}\n"
            f"salon = {salon}\n"
            f"serveur = {serveur}```"
           )
