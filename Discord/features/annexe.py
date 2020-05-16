import tools

def test(ctx):
    arg = tools.command_arg(ctx)    # Arguments de la commande (sans le !test)
    auteur = ctx.author.name
    salon = ctx.channel.name if hasattr(ctx.channel, "name") else f"DMChannel de {ctx.channel.recipient.name}"
    serveur = ctx.guild.name if hasattr(ctx.guild, "name") else "(DM)"
    # pref = ctx.prefix
    # com = ctx.command
    # ivkw = ctx.invoked_with
    
    return tools.code_bloc(
        f"arg = {arg}\n"
        f"auteur = {auteur}\n"
        f"salon = {salon}\n"
        f"serveur = {serveur}")
