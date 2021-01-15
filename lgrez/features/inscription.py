"""lg-rez / features / Process d'inscription

Étapes préliminaires pour les joueurs avant le début de saison

"""

from lgrez import config
from lgrez.blocs import tools, env, gsheets
from lgrez.bdd import Joueur, Role, Camp, Statut


async def _new_channel(member):
    """Crée un nouveau chan privé"""
    categ = tools.channel(config.private_chan_category_name)
    if len(categ.channels) >= 50:
        # Limitation Discord : 50 channels par catégorie
        ok = False
        N = 2
        while not ok:
            nom_nouv_cat = f"{config.private_chan_category_name} {N}"
            categ_new = tools.channel(nom_nouv_cat, must_be_found=False)
            if not categ_new:
                categ = await categ.clone(name=nom_nouv_cat)
                ok = True
            elif len(categ_new.channels) < 50:
                # Catégorie N pas pleine
                categ = categ_new
                ok = True
            N += 1

    chan = await member.guild.create_text_channel(
        f"{config.private_chan_prefix}{member.name}",
        topic=str(member.id),       # topic provisoire : ID du membre
        category=categ,
    )
    await chan.set_permissions(member, read_messages=True,
                               send_messages=True)

    return chan


# Routine d'inscription (fonction appellée par la commande !co)
async def main(member):
    """Exécute le processus d'inscription d'un joueur

    Args:
        member (:class:`~discord.Member`): joueur à inscrire

    Crée et paramètre le salon privé du joueur, lui pose des questions
    et l'inscrit en base.

    Personalisation voir :attr:`config.demande_chambre`,
    :attr:`config.chambre_mj` et :attr:`config.debut_saison`.

    Commande appellée à l'arrivée sur le serveur, utiliser
    :meth:`\!co <.bot.Special.Special.co.callback>` pour trigger cette
    commande depuis Discord.
    """
    try:
        joueur = Joueur.from_member(member)
    except ValueError:      # Joueur pas encore inscrit en base
        pass
    else:                   # Joueur dans la bdd = déjà inscrit
        chan = joueur.private_chan
        await chan.set_permissions(member, read_messages=True,
                                   send_messages=True)
        await chan.send(
            f"Saloww ! {member.mention} tu es déjà inscrit, "
            "viens un peu ici !"
        )
        return

    if (chan := tools.get(config.guild.text_channels, topic=str(member.id))):
        # Inscription en cours (topic du chan = ID du membre)
        await chan.set_permissions(member, read_messages=True,
                                   send_messages=True)
        await chan.send(
            f"Tu as déjà un channel à ton nom, {member.mention}, par ici !"
        )

    else:           # Pas d'inscription déjà en cours : création channel
        chan = await _new_channel(member)

    # Récupération nom et renommages

    await chan.send(
        f"Bienvenue {member.mention} ! Je suis le bot à qui tu auras "
        "affaire tout au long de la partie.\nTu es ici sur ton channel "
        "privé, auquel seul toi et les MJ ont accès ! C'est ici que tu "
        "lanceras toutes les commandes pour voter, te renseigner... mais "
        "aussi que les MJ discuteront avec toi en cas de soucis.\n\nPas "
        "de panique, je vais tout t'expliquer !"
    )

    await tools.sleep(chan, 5)

    await chan.send(
        "Avant toute chose, finalisons ton inscription !\nD'abord, un "
        "point règles nécessaire :\n\n"
        + tools.quote_bloc(
            "En t'inscrivant au Loup-Garou de la Rez, tu garantis vouloir "
            "participer à cette édition et t'engages à respecter les "
            "règles du jeu. Si tu venais à entraver le bon déroulement de "
            "la partie pour une raison ou une autre, les MJ "
            "s'autorisent à te mute ou t'expulser du Discord sans préavis."
        )
    )

    await tools.sleep(chan, 5)

    message = await chan.send(
        "C'est bon pour toi ?\n"
        + tools.ital(
            "(Le bot te demandera souvent confirmation, en t'affichant "
            "deux réactions comme ceci. Clique sur ✅ si ça te va, sur "
            "❎ sinon. Tu peux aussi répondre (oui, non, ...) par écrit.)"
        )
    )
    if not await tools.yes_no(message):
        await chan.send(
            "Pas de soucis. Si tu changes d'avis ou que c'est un "
            f"missclick, appelle un MJ aled ({tools.code('@MJ')})."
        )
        return

    await chan.send(
        "Parfait. Je vais d'abord avoir besoin de ton (vrai) prénom, "
        "celui par lequel on t'appelle au quotidien. Attention, tout "
        "troll sera foudracanonné™ !"
    )

    def check_chan(m):
        # Message de l'utilisateur dans son channel perso
        return m.channel == chan and m.author != config.bot.user

    ok = False
    while not ok:
        await chan.send(
            "Quel est ton prénom, donc ?\n"
            + tools.ital("(Répond simplement dans ce channel, "
                         "à l'aide du champ de texte normal)")
        )
        prenom = await tools.wait_for_message(check=check_chan)

        await chan.send("Très bien, et ton nom de famille ?")
        nom_famille = await tools.wait_for_message(check=check_chan)
        nom = f"{prenom.content.title()} {nom_famille.content.title()}"
        # .title met en majuscule la permière lettre de chaque mot

        message = await chan.send(
            f"Tu me dis donc t'appeller {tools.bold(nom)}. "
            "C'est bon pour toi ? Pas d'erreur, pas de troll ?"
        )
        ok = await tools.yes_no(message)

    await chan.edit(name=config.private_chan_prefix + nom)  # Renommage conv
    if member.top_role < config.Role.mj:
        # Renommage joueur (ne peut pas renommer les MJ)
        await member.edit(nick=nom)

    await chan.send(
        "Parfait ! Je t'ai renommé(e) pour que tout le monde te "
        "reconnaisse, et j'ai renommé cette conversation."
    )

    if config.demande_chambre:
        await tools.sleep(chan, 5)
        a_la_rez = await tools.yes_no(await chan.send(
            "Bien, dernière chose : habites-tu à la Rez ?"
        ))

        if a_la_rez:
            def sortie_num_rez(m):
                # Longueur de chambre de rez maximale
                return len(m.content) < 200
            mess = await tools.boucle_message(
                chan, "Alors, quelle est ta chambre ?", sortie_num_rez,
                rep_message=("Désolé, ce n'est pas un numéro de chambre "
                             "valide, réessaie...")
            )
            chambre = mess.content
        else:
            chambre = config.chambre_mj

        await chan.send(
            f"{nom}, en chambre {chambre}... Je t'inscris en base !"
        )

    else:
        chambre = None
        await chan.send(f"{nom}... Je t'inscris en base !")

    # Indicateur d'écriture pour informer le joueur que le bot fait des trucs
    async with chan.typing():
        # Ajout à la BDD

        joueur = Joueur(
            discord_id=member.id, chan_id_=chan.id, nom=member.display_name,
            chambre=chambre, statut=Statut.vivant, role=Role.default(),
            camp=Camp.default(), votant_village=True, votant_loups=False,
            role_actif=False
        )
        config.session.add(joueur)
        config.session.commit()

        # Ajout au TDB

        cols = [col for col in Joueur.columns if not col.endswith('_')]
        # On élimine les colonnes locales

        SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

        workbook = gsheets.connect(SHEET_ID)
        sheet = workbook.worksheet("Journée en cours")
        values = sheet.get_all_values()
        # Liste de liste des valeurs des cellules
        NL = len(values)

        head = values[2]
        # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
        TDB_index = {col: head.index(col.key) for col in cols}
        # Indices des colonnes GSheet pour chaque colonne de la table
        TDB_tampon_index = {col: head.index(f"tampon_{col.key}")
                            for col in cols if not col.primary_key}
        # Idem pour la partie « tampon »

        plv = 3     # Première Ligne Vide (si tableau vide, 4e ligne ==> 3)
        for l in range(NL):
            if values[l][TDB_index[Joueur.primary_col]].isdigit():
                # Si il y a un vrai ID dans la colonne ID, ligne l
                plv = l + 1

        modifs = [gsheets.Modif(plv, TDB_index[col], getattr(joueur, col.key))
                  for col in TDB_index]
        tampon = [gsheets.Modif(plv, TDB_tampon_index[col],
                                getattr(joueur, col.key))
                  for col in TDB_tampon_index]
        gsheets.update(sheet, *modifs, *tampon)

        # Grant accès aux channels joueurs et information

        await member.add_roles(config.Role.joueur_en_vie)
        await chan.edit(
            topic="Ta conversation privée avec le bot, "
                  "c'est ici que tout se passera !"
        )

    # Conseiller d'ACTIVER TOUTES LES NOTIFS du chan
    # (et mentions only pour le reste, en activant @everyone)
    await chan.send(
        f"Tu es maintenant inscrit(e) ! Je t'ai attribué le rôle "
        f"{config.Role.joueur_en_vie.mention}, qui te donne l'accès à "
        "tout plein de nouveaux channels à découvrir."
    )
    await chan.send(
        "Juste quelques dernières choses :\n "
        "- Plein de commandes te sont d'ores et déjà accessibles ! "
        f"Découvre les toutes en tapant {tools.code('!help')} ;\n "
        "- Si tu as besoin d'aide, plus de bouton MJ ALED : mentionne "
        f"simplement les MJs ({tools.code('@' + config.role.mj.name)}) "
        "et on viendra voir ce qui se passe !\n "
        "- Si ce n'est pas le cas, je te conseille fortement d'installer "
        "Discord sur ton téléphone, "
        f"et d'{tools.bold('activer toutes les notifications')} pour ce "
        "channel ! Promis, pas de spam :innocent:\n"
        "Pour le reste du serveur, tu peux le mettre en \"mentions only\", "
        f"en activant le {tools.code('@everyone')} – il est limité ;\n\n"
        "Enfin, n'hésite pas à me parler, j'ai toujours quelques réponses "
        "en stock..."
    )

    await tools.sleep(chan, 5)
    await chan.send(
        "Voilà, c'est tout bon ! Installe toi bien confortablement, "
        f"la partie commence le {config.debut_saison}."
    )

    # Log
    await tools.log(
        f"Inscription de {member.name}#{member.discriminator} "
        f"réussie\n - Nom : {nom}\n - Chambre : {chambre}\n"
        f" - Channel créé : {chan.mention}"
    )
