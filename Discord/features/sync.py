import json

from discord.ext import commands
import tools
from bdd_connect import db, Joueurs
from blocs import bdd_tools


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
    async def sync(self, ctx, silent, *, serial):
        """Déserialise les infos JSON et log"""

        dic = json.loads(serial)
        message = self.changelog(ctx, dic)
        notif = ":zap: :zap: Une action divine a modifié ton existence ! :zap: :zap: \n Les caractères modifiés sont les suivants :\n"

        for k in dic.keys():
            for key,v in dic[k].items():
                bdd_tools.modif(Joueurs.query.get(int(k)), key, v)
                if silent=='False':
                    notif += "-"+ key + " : " + v + "\n"
            if silent=='False':
                await tools.private_chan(ctx.guild.get_member(int(k))).send(notif)
                notif = ":zap: :zap: Une action divine a modifié ton existence ! :zap: :zap: \n Les caractères modifiés sont les suivants :\n"

        db.session.commit()

        await tools.log(ctx, f"Synchronisation TDB (silencieux = {silent}) :\n{tools.code_bloc(message)}")
