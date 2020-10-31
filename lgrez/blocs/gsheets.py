"""lg-rez / blocs / Interfaçage Google Sheets

Connection, récupération de classeurs, modifications (implémentation de https://pypi.org/project/gspread)
"""

import json

from lgrez.blocs import env
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect(key):
    """Charge les credentials GSheets (variable d'environment ``LGREZ_GCP_CREDENTIALS``) et renvoie le classeur demandé

    Args:
        key (str): ID du classeur à charger (25 caractères)

    Returns:
        :class:`gspread.models.Spreadsheet`
    """
    # use creds to create a client to interact with the Google Drive API
    LGREZ_GCP_CREDENTIALS = env.load("LGREZ_GCP_CREDENTIALS")

    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(LGREZ_GCP_CREDENTIALS), scope)
    client = gspread.authorize(creds)

    # Open the workbook
    workbook = client.open_by_key(key)

    return workbook


def update(sheet, modifs):
    """Met à jour une feuille GSheets avec les modifications demandées

    Args:
        sheet (:class:`gspread.models.Worksheet`): la feuille à modifier
        modifs (:class:`list`\[\(:class:`int`, :class:`int`, :class:`object`\)\]): liste de tuples ``(ligne, colonne, valeur)``

    Les IDs sont indexés à partir de ``0`` (cellule ``A1`` en ``(0, 0)``.

    Le type de la nouvelle valeur sera interpreté par ``gspread`` pour donner le type GSheets adéquat à la cellule (texte, numérique, temporel...)
    """
    lm = max([l for (l, c, v) in modifs])       # ligne max de la zone à modifier
    cm = max([c for (l, c, v) in modifs])       # colonne max de la zone à modifier

    # Récupère toutes les valeurs sous forme de cellules gspread
    cells = sheet.range(1, 1, lm+1, cm+1)   # gspread indexe à partir de 1 (comme les gsheets)

    cells_to_update = []
    for (l, c, v) in modifs:
        cell = [cell for cell in cells if cell.col == c+1 and cell.row == l+1][0]    # on récup l'objet Cell correspondant aux coords à modifier
        if isinstance(v, int) and v > 10**14:
            cell.value = str(v)
        elif v is None:
            cell.value = ""
        else:
            cell.value = v              # cells : ([<L1C1>, <L1C2>, ..., <L1Ccm>, <L2C1>, <L2C2>, ..., <LlmCcm>]
        cells_to_update.append(cell)

    sheet.update_cells(cells_to_update)
