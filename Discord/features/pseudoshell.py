import sys
import re
import traceback
import asyncio


### AVERTISSMENT : le code ci-dessous est peu commenté et pas mal technique (full orienté objet et quelques regex)


class Shell():          # Les attributs de cette classe peuvent être modifiés via exec
    """Pseudo-terminal Python"""

    def __init__(self, globals, locals, pull=input, push=print, welcome_text="", bridge_name="_shell"):
        """Initialize self"""
        self.globals = globals                  # Variables globales de l'environnement d'exécution (dictionnaire)
        self.locals = locals                    # Variables locales de l'environnement d'exécution (dictionnaire)
        self._pull = pull                       # Fonction / coroutine None -> str d'input
        self._push = push                       # Fonction / coroutine str -> None d'output
        self.welcome_text = welcome_text        # Texte affiché au lancement
        self.bridge_name = bridge_name          # Nom de la variable associée à self dans les locals des exec

        self.locals[self.bridge_name] = self    # Permet d'accéder au shell dans les exec

    async def pull(self):
        """Retourne une entrée utilisateur (notmalement str) dans le pseudo-terminal"""
        result = self._pull()
        if asyncio.iscoroutine(result):
            result = await result
        return result

    async def push(self, text):
        """Envoie <text> dans le pseudo-terminal"""
        result = self._push(text)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    async def run(self):
        """Lance le pseudo-terminal"""
        version_info = sys.version.replace('\n', '')
        await self.push(f"""Python {version_info}\n{self.welcome_text}""")

        main_loop = Loop(shell=self, depth=0)
        await main_loop.run()

        await self.push(f"""Exit.""")


class Result():
    """Résultat d'une exécution dans un pseudo-terminal"""

    def __init__(self, arg, success=None):
        """Initialize self"""
        if isinstance(arg, str):
            self.text = arg
            self.success = success or True                  # par défaut : succès
        else:
            raise TypeError(f"TypeError: Result() argument must be a string instance, not '{type(arg)}'")

    def __bool__(self):
        """Return self.text.__bool__"""
        return bool(self.text)


class ResultsList(list):
    """Liste d'objets Result"""
    def __init__(self, iterable=(), /, success=None):
        """Initialize self"""
        try:
            if all(isinstance(obj, Result) for obj in iterable):    # Si que des Result:
                list.__init__(self, iterable)
                if success is None:        # Si la liste n'est pas vide
                    self.success = self[-1].success if self else True
                else:
                    self.success = success
            else:
                raise TypeError
        except (TypeError, ValueError) as e:
            raise TypeError("TypeError: ResultsList() argument must be an iterator of Result instances") from e

    def append(self, item):
        """Implémente list.append(item) ; self.success = item.success"""
        if isinstance(item, Result):
            list.append(self, item)
            self.success = item.success
        else:
            raise TypeError("TypeError: ResultsList.append() argument must be a Result instance")

    def extend(self, iterable):
        """Implémente list.extend(results_list) ; self.success = iterable.success"""
        try:
            if not isinstance(iterable, ResultsList):
                try:
                    iterable = ResultsList(iterable)
                except:
                    raise
            list.extend(self, iterable)
            self.success = iterable.success
        except (TypeError, ValueError) as e:
            raise TypeError("TypeError: ResultsList.extend() argument must be a ResultsList instance or any iterator of Result instances") from e

    def join(self, sep="\n") -> Result:
        """Joins les résultats dans la liste -> Result"""
        text = sep.join(result.text for result in self)
        return Result(text, success=self.success)


class Loop():
    """Boucle de pseudo-terminal Python"""

    def __init__(self, shell, depth, caller="", history=""):
        """Initialize self"""
        self.shell = shell
        self.depth = depth
        self.caller = caller          # Ligne d'appel de la boucle
        self.history = history        # Lignes / structures pas encore exécutées
        self.prompt = ">>>" + "·"*(4*self.depth) + " "
        self.endwords = ["end"]
        self.buffer = []               # Lignes en attende d'exécution
        self.exit = False

    async def run(self):
        """Exécute la boucle jusqu'à recevoir un ordre de fin"""
        if self.history:
            await self.shell.push(self.history)

        while not self.exit:
            await self.shell.push(self.prompt)
            entree = await self.shell.pull()

            if entree in self.endwords:
                self.exit = True

            elif entree.startswith("for "):
                _for_loop = For(shell=self.shell, caller=entree, depth=self.depth + 1,
                                 history=f"{self.history}{self.prompt}{entree}\n")
                await _for_loop.run()                   # Récupération instructions
                self.buffer.append(_for_loop)           # Une fois boucle finie, on l'enregistre (objet For)
                self.history = _for_loop.history        # On actualise l'historique

            else:       # Si ni for, while, if, ..., exit :
                self.buffer.append(Line(shell=self.shell, text=entree))
                self.history += f"{self.prompt}{entree}\n"


            if self.depth == 0:       # Boucle principale : on exécute
                result = await self.exec()

                await self.shell.push(f"{self.history}{result.text}")
                # await self.shell.push(f"{self.history}{result.text}\n\nbuffer : {self.buffer}")
                self.buffer = []
                self.history = ""

            else:                     # Dans une structure : on enregistre
                await self.shell.push(self.history)
                # await self.shell.push(f"{self.history}\n\nbuffer : {self.buffer}")

    async def exec_buffer(self) -> Result:
        """Exécute les objets et structures dans la boucle (dans le contexte actuel de self.shell)"""
        results = ResultsList()
        for obj in self.buffer:       # lignes et structures dans buffer
            result = await obj.exec()     # ON EXÉCUTE TOUT
            if result:
                results.append(result)
                if not result.success:      # En cas d'exception
                    break                       # On arrête l'exécution ici

        return results.join()      # Joins les results entre eux (garde le success du dernier result)

    exec = exec_buffer      # Pour la boucle "de base", ça revient au même


class For(Loop):
    """Boucle for d'un pseudo-terminal Shell"""

    def __init__(self, *args, **kwargs):
        """Initialize self"""
        Loop.__init__(self, *args, **kwargs)
        self.endwords.append("endfor")

        if match := re.match(r"for\s*(.+?)\s*in\s*(.+?)\s*:", self.caller):     # Entrée dans boucle
            self.variter_txt = match.group(1).strip()
            self.iterator_txt = match.group(2).strip()
        else:
            raise SyntaxError("PseudoShell : Mauvaise syntaxe pour une boucle for")

    async def exec(self) -> Result:
        """Exécute la boucle"""
        text = f"iterator = {self.iterator_txt}"
        await Line(shell=self.shell, text=text).exec()      # On affecte l'itérateur à iterator (dans le contexte de shell)

        results = ResultsList()
        for self.shell.locals[self.variter_txt] in self.shell.locals["iterator"]:
            iter_result = await self.exec_buffer()       # Résultat de l'itération en cours
            results.append(iter_result)
            if not iter_result.success:     # En cas d'exception
                break                           # On arrête l'exécution ici

        return results.join()      # Joins les results entre eux (crée un Result, garde le success du dernier result de la liste)


class Line():
    """Ligne de commande Python reçue de l'utilisateur"""

    def __init__(self, shell, text):
        """Initialize self"""
        self.text = text
        self.shell = shell
        self.result = Result("")

    async def exec(self) -> Result:
        """Évalue la ligne"""
        self.result = Result("")        # On réinitialise pour pouvoir exécuter la ligne plusieurs fois
        stdout = sys.stdout
        self.shell.globals["sys"].stdout = self      # Petit hack pour envoyer print() vers self.result (via self.write)

        try:
            source = self.text
            if not (":" in source
                    or "=" in source):       # Ligne a exécuter
                source = f"_ = {source}"

            source = f"{source} ; {self.shell.bridge_name}.globals = globals() ; {self.shell.bridge_name}.locals = locals()"
            exec(source, self.shell.globals, self.shell.locals)
            # TODO: Gérer les coroutines

            if "_" in self.shell.locals:
                if not self.result:
                    self.result.text = repr(self.shell.locals["_"])
                self.shell.locals.pop("_")

        except RuntimeError:
            raise

        except Exception:
            self.result.text = traceback.format_exc()
            self.result.success = False

        finally:
            self.shell.globals["sys"].stdout = stdout
            return self.result


    def write(self, text):
        """Petit hack pour pouvoir rediriger print vers self, élimine les \n envoyés seuls à la fin"""
        if text != "\n":
            self.result.text += text
