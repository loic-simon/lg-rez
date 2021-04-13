"""lg-rez / blocs / Interfaçage Google Sheets

Connection, récupération de classeurs, modifications
(implémentation de https://pypi.org/project/gspread)
"""

import enum
import json

import gspread
from oauth2client import service_account
from googleapiclient.discovery import build

from lgrez import bdd
from lgrez.blocs import env


WorksheetNotFound = gspread.exceptions.WorksheetNotFound

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
        return f"<gsheets.Modif: ({self.row}, {self.column}) = {self.val!r}>"

    def __eq__(self, other):
        """Returns self == other"""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.row == other.row
                and self.column == other.column
                and self.val == other.val)

    def __hash__(self):
        return hash((self.row, self.column, self.val))



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
    creds = service_account.ServiceAccountCredentials.from_json_keyfile_dict(
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
    ``None`` sont convertis en ``''``. Les membres d':class:`~enum.Enum`
    sont stockés par leur **nom**.
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

        val = modif.val

        # Transformation objets complexes
        if isinstance(val, enum.Enum):
            # Enums : stocker le nom
            val = val.name
        elif isinstance(modif.val, bdd.base.TableBase):
            # Instances : stocker la clé primaire
            val = val.primary_key

        # Adaptation types de base
        if isinstance(val, int) and val > 10**14:
            # Entiers trop grands pour être stockés sans perte de
            # précision (IDs des joueurs par ex.): passage en str
            cell.value = str(val)
        elif val is None:
            cell.value = ""
        else:
            cell.value = val

        cells_to_update.append(cell)

    sheet.update_cells(cells_to_update)


def a_to_index(column):
    """Utilitaire : convertit une colonne ("A", "B"...) en indice.

    Args:
        column (str): nom de la colonne. Doit être composé de caractères
            dans [a-z, A-Z] uniquement.

    Returns:
        int: L'indice de la colonne, **indexé à partir de 0** (cellules
            considérées comme une liste de liste).

    Raises:
        gspread.exceptions.IncorrectCellLabel: valeur incorrecte.
    """
    a1 = column + "1"
    row, col = gspread.utils.a1_to_rowcol(a1)
    return col - 1      # a1_to_rowcol indexe à partir de 1


def get_doc_content(doc_id):
    """Récupère le contenu d'un document Google Docs.

    Transforme le document pour ne garder que les fragments de
    texte et leur mise en forme. Les paragraphes de listes à
    points sont transformés en ajoutant un fragment ``    -  ``
    à l'endroit adéquat ; les autres options de mise en forme des
    paragraphes et les autres objets GDocs sont ignorés.

    Args:
        doc_id (str): ID du document à récupérer (doit être public
            ou dans le Drive partagé avec le compte de service).

    Returns:
        list[tuple(str, dict)]: Les différents fragments de texte
        du document et leur formattage (référence : https://developers.\
        google.com/docs/api/reference/rest/v1/documents#TextStyle)

    Raises:
        googleapiclient.errors.HttpError: ID incorrect ou document non
            accessible.
    """
    LGREZ_GCP_CREDENTIALS = env.load("LGREZ_GCP_CREDENTIALS")

    scope = ['https://www.googleapis.com/auth/documents.readonly']
    creds = service_account.ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(LGREZ_GCP_CREDENTIALS), scope
    )
    service = build('docs', 'v1', credentials=creds)

    # Retrieve the documents contents from the Docs service.
    document = service.documents().get(documentId=doc_id).execute()

    content = []
    blocs = document["body"]["content"]
    for bloc in blocs:
        paragraph = bloc.get("paragraph")
        if not paragraph:
            continue

        bullet = paragraph.get("bullet")
        if bullet:
            content.append(("    -  ", bullet["textStyle"]))

        elements = paragraph["elements"]
        for element in elements:
            run = element.get("textRun")
            if run:     # bout de texte
                content.append((run["content"], run["textStyle"]))

    return content
