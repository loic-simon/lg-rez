"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

from __future__ import annotations

import sqlalchemy

from lgrez.bdd import base
from lgrez.bdd.base import autodoc_Column, autodoc_ManyToOne, autodoc_OneToMany


# Tables de données


class Reaction(base.TableBase):
    """Table de données des réactions d'IA connues du bot.

    Les instances sont enregistrées via :meth:`\!addIA
    <.IA.GestionIA.GestionIA.addIA.callback>` et supprimées via
    :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """

    id: int = autodoc_Column(
        sqlalchemy.Integer(),
        primary_key=True,
        doc="Identifiant unique de la réaction, sans signification",
    )
    reponse: str = autodoc_Column(
        sqlalchemy.String(2000),
        nullable=False,
        doc="Réponse, suivant le format (mini-langage) personnalisé " '(``"txt <||> txt <&&> <##>react"``)',
    )

    # One-to-manys
    triggers: list[Trigger] = autodoc_OneToMany(
        "Trigger",
        back_populates="reaction",
        doc="Déclencheurs associés",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        extract = self.reponse.replace("\n", " ")[:15] + "..."
        return f"<Reaction #{self.id} ({extract})>"


class Trigger(base.TableBase):
    """Table de données des mots et expressions déclenchant l'IA du bot.

    Les instances sont enregistrées via :meth:`\!addIA
    <.IA.GestionIA.GestionIA.addIA.callback>` ou :meth:`\!modifIA
    <.IA.GestionIA.GestionIA.modifIA.callback>` et supprimées via
    :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """

    id: int = autodoc_Column(
        sqlalchemy.Integer(),
        primary_key=True,
        doc="Identifiant unique du déclencheur, sans signification",
    )
    trigger: str = autodoc_Column(
        sqlalchemy.String(500),
        nullable=False,
        doc="Mots-clés / expressions",
    )

    _reac_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey("reactions.id"),
        nullable=False,
    )
    reaction: Reaction = autodoc_ManyToOne(
        "Reaction",
        back_populates="triggers",
        doc="Réaction associée",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        extract = self.trigger.replace("\n", " ")[:15] + "..."
        return f"<Trigger #{self.id} ({extract})>"
