import json

from discord.ext import commands
import tools
from bdd_connect import db, Joueurs


class Sync(commands.Cog):
    """Sync : synchronisation"""
    
    def changelog(self, ctx, dic):
        message = ""
        for (id, attrs) in dic.items():
            member = ctx.guild.get_member(int(id))
            message += f"- {member.display_name} :\n"
            
            for (col,val) in attrs.items():
                message += f"    - {col} : {val}\n"
            message += "\n"
            
        return message
        

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def sync_silent(self, ctx, *, serial):
        """Déserialise les infos JSON et log"""

        dic = json.loads(serial)
        message = self.changelog(ctx, dic)
        
        await tools.log(ctx, f"Synchronisation TDB - mode silencieux :\n{tools.code_bloc(message)}")


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def sync(self, ctx, *, serial):
        """Informe le joueur des actions (non implémenté encore)"""

        dic = json.loads(serial)
        message = self.changelog(ctx, dic)
        
        await tools.log(ctx, f"Synchronisation TDB :\n{tools.code_bloc(message)}")
        await tools.log(ctx, "bla bla je fais des trucs c'est super")
