"""lg-rez / features / Process d'inscription

Étapes préliminaires pour les joueurs avant le début de saison

"""

from discord.ext import commands

from lgrez.blocs.bdd import Joueurs
from lgrez.blocs import tools, bdd, env, gsheets, bdd_tools


# Routine d'inscription (fonction appellée par la commande !co)
async def main(bot, member):
    """Exécute le processus d'inscription d'un joueur

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        member (:class:`~discord.Member`): joueur à inscrire

    Crée et paramètre le salon privé du joueur, lui pose des questions et l'inscrit en base.

    Personalisation :
        - Si :attr:`bot.config <.LGBot.config>` ``["demande_chambre"]`` vaut ``False``, ne demande pas la chambre
        - Sinon :attr:`bot.config <.LGBot.config>` ``["chambre_mj"]`` indique la chambre par défaut (défaut : ``"[chambre MJ]"``)
        - :attr:`bot.config <.LGBot.config>` ``["debut_saison"]`` permet de personnaliser la date de début de saison indiquée à la fin du processus (défaut : ``"32 plopembre"``)

    Commande appellée à l'arrivée sur le serveur, utiliser :meth:`\!co <.bot.Special.Special.co.callback>` pour trigger cette commande depuis Discord.
    """
    if Joueurs.query.get(member.id):                                            # Joueur dans la bdd = déjà inscrit
        await tools.private_chan(member).set_permissions(member, read_messages=True, send_messages=True)
        await tools.private_chan(member).send(f"Saloww ! {member.mention} tu es déjà inscrit, viens un peu ici enculé !")
        return
    elif chan := tools.get(member.guild.text_channels, topic=f"{member.id}"):   # Inscription en cours
        await chan.set_permissions(member, read_messages=True, send_messages=True)
        await chan.send(f"Tu as déjà un channel à ton nom, {member.mention}, par ici !")
    else:           # Pas d'inscription déjà en cours : création channel
        categ = tools.channel(member, "CONVERSATION BOT")
        if len(categ.channels) >= 50:         # Limitation Discord : 50 channels par catégorie
            ok = False
            N = 2
            while not ok:
                categ_new = tools.channel(member, f"CONVERSATION BOT {N}", must_be_found=False)
                if not categ_new:
                    categ = await categ.clone(name=f"CONVERSATION BOT {N}")
                    ok = True
                elif len(categ_new.channels) < 50:      # Catégorie N pas pleine
                    categ = categ_new
                    ok = True
                N += 1

        chan = await member.guild.create_text_channel(f"conv-bot-{member.name}",  topic=str(member.id), category=categ)
        await chan.set_permissions(member, read_messages=True, send_messages=True)


    ### Mise en mode STFU le temps de l'inscription, si pas déjà fait par l'appel à !co (arrivée nouveau membre)

    if chan.id not in bot.in_stfu:
        bot.in_stfu.append(chan.id)


    ### Récupération nom et renommages

    await chan.send(f"Bienvenue {member.mention} ! Je suis le bot à qui tu auras affaire tout au long de la partie.\nTu es ici sur ton channel privé, auquel seul toi et les MJ ont accès ! C'est ici que tu lanceras toutes les commandes pour voter, te renseigner... mais aussi que les MJ discuteront avec toi en cas de soucis.\n\nPas de panique, je vais tout t'expliquer !")

    await tools.sleep(chan, 5)    # tools.sleep(x) = attend x secondes avec l'indicateur typing...'

    await chan.send(f"""Avant toute chose, finalisons ton inscription !\nD'abord, un point règles nécessaire :\n\n{tools.quote_bloc("En t'inscrivant au Loup-Garou de la Rez, tu garantis vouloir participer à cette édition et t'engages à respecter les règles du jeu. Si tu venais à entraver le bon déroulement de la partie pour une raison ou une autre, les MJ s'autorisent à te mute ou t'expulser du Discord sans préavis.")}""")

    await tools.sleep(chan, 5)    # tools.sleep(x) = attend x secondes avec l'indicateur typing...'

    message = await chan.send(f"""C'est bon pour toi ?\n{tools.ital("(Le bot te demandera souvent confirmation, en t'affichant deux réactions comme ceci. Clique sur ✅ si ça te va, sur ❎ sinon. Tu peux aussi répondre (oui, non, ...) par écrit.)")}""")
    if not await tools.yes_no(bot, message):
        await chan.send(f"Pas de soucis. Si tu changes d'avis ou que c'est un missclick, appelle un MJ aled ({tools.code('@MJ')}).")
        return


    await chan.send(f"Parfait. Je vais d'abord avoir besoin de ton (vrai) prénom, celui par lequel on t'appelle au quotidien. Attention, tout troll sera foudracanonné™ {tools.emoji(chan, 'foudra')}")

    def check_chan(m): #Check que le message soit envoyé par l'utilisateur et dans son channel perso
        return m.channel == chan and m.author != bot.user
    ok = False
    while not ok:
        await chan.send(f"""Quel est ton prénom, donc ?\n{tools.ital("(Répond simplement dans ce channel, à l'aide du champ de texte normal)")}""")
        prenom = await tools.wait_for_message(bot, check=check_chan)

        await chan.send(f"Très bien, et ton nom de famille ?")
        nom_famille = await tools.wait_for_message(bot, check=check_chan)
        nom = f"{prenom.content.title()} {nom_famille.content.title()}"         # .title met en majuscule la permière lettre de chaque mot

        message = await chan.send(f"""Tu me dis donc t'appeller {tools.bold(nom)}. C'est bon pour toi ? Pas d'erreur, pas de troll ?""")
        ok = await tools.yes_no(bot, message)


    await chan.edit(name=f"conv-bot-{nom}")         # Renommage conv
    if not tools.role(member, "MJ") in member.roles:
        await member.edit(nick=nom)                 # Renommage joueur (ne peut pas renommer les MJ)

    await chan.send("Parfait ! Je t'ai renommé(e) pour que tout le monde te reconnaisse, et j'ai renommé cette conversation.")


    if bot.config.get("demande_chambre", True):
        await tools.sleep(chan, 5)
        a_la_rez = await tools.yes_no(bot, await chan.send("Bien, dernière chose : habites-tu à la Rez ?"))

        if a_la_rez:
            def sortie_num_rez(m):
                return len(m.content) < 200     # Longueur de chambre de rez maximale
            chambre = (await tools.boucle_message(bot, chan, "Alors, quelle est ta chambre ?", sortie_num_rez, rep_message="Désolé, ce n'est pas un numéro de chambre valide, réessaie...")).content
        else:
            chambre = bot.config.get("chambre_mj", "[chambre MJ]")

        await chan.send(f"{nom}, en chambre {chambre}... Je t'inscris en base !")

    else:
        chambre = None
        await chan.send(f"{nom}... Je t'inscris en base !")


    async with chan.typing():     # Envoi indicateur d'écriture pour informer le joueur que le bot fait des trucs
        # Ajout à la BDD

        joueur = Joueurs(discord_id=member.id, chan_id_=chan.id, nom=member.display_name,
                         chambre=chambre, statut="vivant", role="nonattr", camp="Non attribué",
                         votant_village=True, votant_loups=False, role_actif=False)
        bdd.session.add(joueur)
        bdd.session.commit()

        # Ajout au TDB

        cols = [col for col in bdd_tools.get_cols(Joueurs) if not col.endswith('_')]    # On élimine les colonnes locales

        SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

        workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
        sheet = workbook.worksheet("Journée en cours")
        values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
        NL = len(values)

        head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
        TDB_index = {col: head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
        TDB_tampon_index = {col: head.index(f"tampon_{col}") for col in cols if col != 'discord_id'}    # Idem pour la partie « tampon »

        plv = 3        # Première ligne vide (si tableau vide, 4e ligne ==> l=3)
        for l in range(NL):
            if values[l][TDB_index["discord_id"]].isdigit():    # Si il y a un vrai ID dans la colonne ID, ligne l
                plv = l + 1

        modifs = [(plv, TDB_index[col], getattr(joueur, col)) for col in TDB_index] + [(plv, TDB_tampon_index[col], getattr(joueur, col)) for col in TDB_tampon_index]   # modifs : toutes les colonnes de la partie principale + du cache
        gsheets.update(sheet, modifs)


        # Grant accès aux channels joueurs et information

        await member.add_roles(tools.role(member, "Joueur en vie"))
        await chan.edit(topic="Ta conversation privée avec le bot, c'est ici que tout se passera !")


    # Conseiller d'ACTIVER TOUTES LES NOTIFS du chan (et mentions only pour le reste, en activant @everyone)
    await chan.send("Tu es maintenant inscrit(e) ! Je t'ai attribué le rôle \"Joueur en vie\", qui te donne l'accès à tout plein de nouveaux channels à découvrir.")
    await chan.send(f"Juste quelques dernières choses :\n - Plein de commandes te sont d'ores et déjà accessibles ! Découvre les toutes en tapant {tools.code('!help')} ;\n - Si tu as besoin d'aide, plus de bouton MJ ALED : mentionne simplement les MJs ({tools.code('@MJ')}) et on viendra voir ce qui se passe !\n - Si ce n'est pas le cas, je te conseille fortement d'installer Discord sur ton téléphone, et d'{tools.bold('activer toutes les notifications')} pour ce channel ! Promis, pas de spam :innocent:\nPour le reste du serveur, tu peux le mettre en \"mentions only\", en activant le {tools.code('@everyone')} – il est limité ;\n\nEnfin, n'hésite pas à me parler, j'ai toujours quelques réponses en stock...")

    await tools.sleep(chan, 5)
    debut_saison = bot.config.get("debut_saison", "32 plopembre")
    await chan.send(f"Voilà, c'est tout bon ! Installe toi bien confortablement, la partie commence le {debut_saison}.")

    # Log
    await tools.log(member, f"Inscription de {member.name}#{member.discriminator} réussie\n - Nom : {nom}\n - Chambre : {chambre}\n - Channel créé : {chan.mention}")


    # Retrait du mode STFU
    if chan.id in bot.in_stfu:
        bot.in_stfu.remove(chan.id)
