"""lg-rez / blocs / Interfaçage Google Sheets

Connection, récupération de classeurs, modifications
(implémentation de https://pypi.org/project/gspread)
"""

import json

from lgrez.blocs import env
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class Modif():
    """Modification à appliquer à un Google Sheet.

    Attributes:
        row (int): Numéro de la ligne (0 = ligne 1)
        column (int): Numéro de la colonne (0 = colonne A)
        val (Any): Nouvelle valeur
    """
    def __init__(self, row, column, val):
        """Initializes self."""
        self.row = row
        self.column = column
        self.val = val

    def __repr__(self):
        """Returns repr(self)"""
        return f"<gsheets.Modif: ({self.row}, {self.column}) = {self.val}>"


def connect(key):
    """Charge les credentials GSheets et renvoie le classeur demandé.

    Nécessite la variable d'environment ``LGREZ_GCP_CREDENTIALS``.

    Args:
        key (str): ID du classeur à charger (25 caractères)

    Returns:
        :class:`gspread.models.Spreadsheet`
    """
    # use creds to create a client to interact with the Google Drive API
    LGREZ_GCP_CREDENTIALS = env.load("LGREZ_GCP_CREDENTIALS")

    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(LGREZ_GCP_CREDENTIALS),
        scope)
    client = gspread.authorize(creds)

    # Open the workbook
    workbook = client.open_by_key(key)

    return workbook


def update(sheet, *modifs):
    """Met à jour une feuille GSheets avec les modifications demandées.

    Args:
        sheet (gspread.models.Worksheet): La feuille à modifier
        *modifs (list[.Modif]): Modification(s) à apporter

    Le type de la nouvelle valeur sera interpreté par ``gspread`` pour
    donner le type GSheets adéquat à la cellule (texte, numérique,
    temporel...)

    Les entiers trop grands pour être stockés sans perte de précision
    (IDs des joueurs par exemple) sont convertis en :class:`str`. Les
    ``None`` sont convertis en ``''``.
    """
    # Bordures de la zone à modifier
    lm = max([modif.row for modif in modifs])
    cm = max([modif.column for modif in modifs])

    # Récupère toutes les valeurs sous forme de cellules gspread
    cells = sheet.range(1, 1, lm + 1, cm + 1)
    # gspread indexe à partir de 1 (comme les gsheets)

    cells_to_update = []
    for modif in modifs:
        # On récupère l'objet Cell correspondant aux coords à modifier
        cell = next(cell for cell in cells
                    if cell.col == modif.column + 1
                    and cell.row == modif.row + 1)

        if isinstance(modif.val, int) and modif.val > 10**14:
            # Entiers trop grands pour être stockés sans perte de
            # précision (IDs des joueurs par ex.): passage en str
            cell.value = str(modif.val)
        elif modif.val is None:
            cell.value = ""
        else:
            cell.value = modif.val

        cells_to_update.append(cell)

    sheet.update_cells(cells_to_update)
