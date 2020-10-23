import sphinx
from sphinx.ext.autodoc import ClassDocumenter
from discord.ext.commands import Cog  # the class that needs modified documentation


class MyClassDocumenter(ClassDocumenter):
    directivetype = 'autocog'
    objtype = 'autocog'
    priority = 20  # higher priority than ClassDocumenter

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, type) and issubclass(member, Cog)

    def get_doc(self, encoding=None, ignore=1):
        doc = super().get_doc(encoding, ignore)
        # do something to modify the output documentation
        doc[0].insert(0, "I AM A COG AND I LIKE IT")
        doc[0].append(doc)
        return doc

def setup(app):
    app.add_autodocumenter(MyClassDocumenter)
    app.add_directive_to_domain("py", "autocog", MyClassDocumenter.directive)
