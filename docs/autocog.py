import sphinx
from sphinx.ext.autodoc import ClassDocumenter
from discord.ext.commands import Cog  # the class that needs modified documentation


cognote = """
.. note::
    Cette classe est un **Cog**, *i.e.* un rassemblements de commandes.

    L'ensemble des commandes qu'elle contient, créées par le décorateur :py:func:`@discord.ext.commands.command <discord.ext.commands.command>`, sont des objets
    :py:class:`discord.ext.commands.Command` accessibles comme ``cog.cmd_name``.

    Pour plus de lisiblité, seules les fonctions appellées lors de l'invoquation des commandes (:py:attr:`Command.callback <discord.ext.commands.Command.callback>`) sont décrites ci-après, mais toutes les méthodes de :py:class:`~discord.ext.commands.Command` sont évidemment accessibles.

    Ces *callbacks* prennent comme premier argument ``ctx`` (:py:class:`discord.ext.commands.Context`), le **contexte d'invocation** de la commande. Cet argument est construit automatiquement par ``discord.py`` à l'appel de :py:meth:`Bot.process_commands <discord.ext.commands.Bot.process_commands>` ou :py:meth:`Bot.get_context <discord.ext.commands.Bot.get_context>`, puis passé au callback suivi des arguments entrés par l'utilisateur.
"""


class CogDocumenter(ClassDocumenter):
    directivetype = 'class'
    objtype = 'cog'
    priority = 20  # higher priority than ClassDocumenter

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, type) and issubclass(member, Cog)

    def get_doc(self, encoding=None, ignore=1):
        doc = super().get_doc(encoding, ignore)
        # do something to modify the output documentation
        if getattr(self, "_signature_method_name", None) != "__new__":     # Premier passage
            doc[0].append(cognote)

            for command in self.object.get_commands():
                doc[0].append(f".. automethod:: {self.fullname}.{command.callback.__name__}.callback")

        print("YOUHOUHOUHOUOHU", doc, self, self.__dict__)
        return doc

def setup(app):
    app.add_autodocumenter(CogDocumenter)
    # app.add_directive_to_domain("py", "autocog", MyClassDocumenter.directive)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
