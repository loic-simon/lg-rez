import sys
import re
import traceback
import asyncio


### AVERTISSMENT : le code ci-dessous est peu commenté et pas mal technique (full orienté objet et quelques regex)


class PseudoShellExit(BaseException):
    """Ordonne la fermeture du pseudo-terminal Python"""

    def __repr__(self):
        """Return repr(self)"""
        return f"<pseudoshell.PseudoShellExit {BaseException.__repr__(self)}>"


class ShellIOError(PseudoShellExit):
    """Erreur lors d'une entrée / sortie du pseudo-terminal Python"""

    def __init__(self, method, original):
        """Initialize self"""
        PseudoShellExit.__init__(self)
        self.method = method            # Méthode ayant levé l'exception
        self.original = original        # Exception originale

    def __repr__(self):
        """Return repr(self)"""
        return f"<pseudoshell.ShellIOError: Exception raised on Shell.{self.method}: \"{self.original}\">"


class Shell(object):          # Les attributs de cette classe peuvent être modifiés via exec
    """Pseudo-terminal Python"""

    def __init__(self, globals, locals, pull=input, push=print, welcome_text="",
                shut_keywords=[], bridge_name="_shell", result_name="_", coro_name="_coro"):
        """Initialize self"""
        self.globals = globals                  # Variables globales de l'environnement d'exécution (dictionnaire)
        self.locals = locals                    # Variables locales de l'environnement d'exécution (dictionnaire)
        self._pull = pull                       # Fonction / coroutine None -> str d'input
        self._push = push                       # Fonction / coroutine str -> None d'output
        self.welcome_text = welcome_text        # Texte affiché au lancement
        self.shut_keywords = shut_keywords      # Liste des mots-clés réservés (str), coupant l'exécution sans appeller le terminal
        self.bridge_name = bridge_name          # Nom de la variable associée à self dans les locals des exec
        self.result_name = result_name          # Nom de la variable associée utilisée pour récupérer les résultats des exec
        self.coro_name = coro_name              # Nom de la variable associée pour la gestion des coroutines des exec

        self.locals[self.bridge_name] = self    # Permet d'accéder au shell dans les exec

    # def __repr__(self):
    #     """Return repr(self)"""
    #     return f"<pseudoshell.Shell: {object.__repr__(self)}"

    async def pull(self):
        """Retourne une entrée utilisateur (normalement str) dans le pseudo-terminal"""
        try:
            result = self._pull()
            if asyncio.iscoroutine(result):
                result = await result
        except Exception as exc:
            raise ShellIOError(method="pull", original=exc)
        else:
            return result

    async def push(self, text):
        """Envoie <text> dans le pseudo-terminal"""
        try:
            result = self._push(text)
            if asyncio.iscoroutine(result):
                result = await result
        except Exception as exc:
            raise ShellIOError(method="push", original=exc)

    async def run(self):
        """Lance le pseudo-terminal"""
        version_info = sys.version.replace('\n', '')
        if self.shut_keywords:
            shut_keywords = ", ".join(f"\"{kw}\"" for kw in self.shut_keywords) + " (arrêt immédiat), "
        else:
            shut_keywords = ""
        await self.push(f"""Python {version_info}\n{self.welcome_text}\n"""
                        f"""Mots-clés réservés : {shut_keywords}"end", "endfor", "endif", "endwhile" (sortie de structure), \"{self.bridge_name}", \"{self.result_name}" et \"{self.coro_name}".\n"""
        )

        main_loop = Loop(shell=self, depth=0)
        await main_loop.run()

        await self.push(f"""Exiting pseudo-shell, bye""")


class Result():
    """Résultat d'une exécution dans un pseudo-terminal"""

    def __init__(self, arg, success=None):
        """Initialize self"""
        if isinstance(arg, str):
            self.text = arg
            self.success = success or True                  # par défaut : succès
        else:
            raise TypeError(f"TypeError: Result() argument must be a string instance, not '{type(arg)}'")

    def __repr__(self):
        """Return repr(self)"""
        return f"""<pseudoshell.Result \"{self.text}" (success={self.success})>"""

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

    def __repr__(self):
        """Return repr(self)"""
        return f"""<pseudoshell.ResultsList {list.__repr__(self)}>"""

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


class PseudoShellError(Exception):
    """Erreur du pseudo-terminal Python"""

    def __repr__(self):
        """Return repr(self)"""
        return f"<pseudoshell.PseudoShellError {Exception.__repr__(self)}>"


class ExecutionError(PseudoShellError):
    """Erreur à l'exécution d'une ligne de pseudo-terminal Python"""

    def __init__(self, original):
        """Initialize self"""
        Exception.__init__(self)
        self.original = original        # Exception originale

    def __repr__(self):
        """Return repr(self)"""
        return f"<pseudoshell.ExecutionError original=\"{self.original}\">"

    def original_traceback(self):
        """Retourne le traceback de l'exception levée pendant l'exécution"""
        return "".join(s for i,s in enumerate(traceback.format_exception(type(self.original), self.original, self.original.__traceback__)) if i != 1)       # On extrait la ligne 1, qui contient les infos avant d'entrer dans le shell (appel d'exec())


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

    def __repr__(self):
        """Return repr(self)"""
        return f"""<pseudoshell.{type(self).__name__} \"{self.caller}" on shell {self.shell}>"""

    async def run(self):
        """Exécute la boucle jusqu'à recevoir un ordre de fin"""
        if self.history:
            await self.shell.push(self.history)

        while not self.exit:
            await self.shell.push(self.prompt)
            entree = await self.shell.pull()

            try:
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
                    try:
                        result = await self.exec()

                    except ExecutionError as exc:
                        await self.shell.push(f"{self.history}{exc.original_traceback()}")

                    except Exception:
                        raise       # Autre exception : on laisse le try général s'en occupée

                    else:
                        await self.shell.push(f"{self.history}{result.text}")
                        # await self.shell.push(f"{self.history}{result.text}\n\nbuffer : {self.buffer}")

                    finally:
                        self.buffer = []
                        self.history = ""

                else:                     # Dans une structure : on enregistre
                    await self.shell.push(self.history)

            except Exception as exc:
                await self.shell.push(f"Trying to add\n{self.prompt}{entree}\n"
                                      f"{''.join(traceback.format_exception_only(type(exc), exc))}\n"
                                      f"No change made, retry:\n\n"
                                      f"{self.history}"
                )

    async def exec_buffer(self) -> Result:
        """Exécute les objets et structures dans la boucle (dans le contexte actuel de self.shell)"""
        results = ResultsList()
        for obj in self.buffer:       # lignes et structures dans buffer
            result = await obj.exec()     # ON EXÉCUTE TOUT
            if result:
                results.append(result)

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
            raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une boucle for")

    async def exec(self) -> Result:
        """Exécute la boucle"""
        text = f"iterator = {self.iterator_txt}"
        await Line(shell=self.shell, text=text).exec()      # On affecte l'itérateur à iterator (dans le contexte de shell)

        results = ResultsList()
        for self.shell.locals[self.variter_txt] in self.shell.locals["iterator"]:
            iter_result = await self.exec_buffer()       # Résultat de l'itération en cours
            results.append(iter_result)

        return results.join()      # Joins les results entre eux (crée un Result, garde le success du dernier result de la liste)


class Line():
    """Ligne de commande Python reçue de l'utilisateur"""

    def __init__(self, shell, text):
        """Initialize self"""
        self.text = text
        self.shell = shell
        self.result = Result("")

    async def exec(self) -> Result:
        """Évalue la ligne dans le contexte de self.shell (globals et locals)"""
        self.result = Result("")        # On réinitialise pour pouvoir exécuter la ligne plusieurs fois
        stdout = sys.stdout
        self.shell.globals["sys"].stdout = self      # Petit hack pour envoyer print() vers self.result (via self.write)

        try:
            source = self.text

            # Gestion coroutine
            if "await" in source:
                left, right = source.split("await", maxsplit=1)                             # Ex. left = "mess = ", right = " ctx.send('oh')"
                res = await Line(self.shell, f"{self.shell.coro_name} = {right}").exec()    # On exec la partie droite  ==> _coro = <coroutine object ...>
                self.shell.locals[self.shell.coro_name] = await self.shell.locals[self.shell.coro_name]     #   On await ==> _coro = <Message id=...>
                source = f"{left} {self.shell.coro_name}"                                   #  Notre nouvelle source, ex. : "mess =  _coro"

            # Préparation récupération résultat
            if not (":" in source or "=" in source):       # Ligne à exécuter
                source = f"{self.shell.result_name} = {source}"

            # Exécution
            source = f"{source} ; {self.shell.bridge_name}.globals = globals() ; {self.shell.bridge_name}.locals = locals()"
            exec(source, self.shell.globals, self.shell.locals)

            # Récupération résultat
            if self.shell.result_name in self.shell.locals:
                if not self.result:
                    self.result.text = repr(self.shell.locals[self.shell.result_name])
                self.shell.locals.pop(self.shell.result_name)

            return self.result

        except ExecutionError:      # Déjà une ExecutionError : on fait remonter
            raise

        except Exception as exc:
            raise ExecutionError(original=exc)

        finally:
            self.shell.globals["sys"].stdout = stdout


    def write(self, text):
        """Petit hack pour pouvoir rediriger print vers self, élimine les \n envoyés seuls à la fin"""
        if text != "\n":
            self.result.text += text
