import sys
import re
import traceback
import asyncio
import keyword


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
        PseudoShellExit.__init__(self, f"PseudoShell : Exception in {method}, exited.")
        self.method = method            # Méthode ayant levé l'exception
        self.original = original        # Exception originale

    def __repr__(self):
        """Return repr(self)"""
        return f"<pseudoshell.ShellIOError: Exception raised on Shell.{self.method}: \"{self.original}\">"


class Shell(object):          # Les attributs de cette classe peuvent être modifiés via exec
    """Pseudo-terminal Python"""

    def __init__(self, globals, locals, pull=input, push=print, welcome_text="", shut_keywords=[],
                 bridge_name="_shell", result_name="_", coro_name="_coro", prov_name="_prov", var_name="_var"):
        """Initialize self"""
        self.globals = globals                  # Variables globales de l'environnement d'exécution (dictionnaire)
        self.locals = locals                    # Variables locales de l'environnement d'exécution (dictionnaire)
        self._pull = pull                       # Fonction / coroutine None -> str d'input
        self._push = push                       # Fonction / coroutine str -> None d'output
        self.welcome_text = welcome_text        # Texte affiché au lancement
        self.shut_keywords = shut_keywords      # Liste des mots-clés réservés (str), coupant l'exécution sans appeller le terminal
        self.bridge_name = bridge_name          # Nom de la variable associée à self dans les locals des exec
        self.result_name = result_name          # Nom de la variable utilisée pour récupérer les résultats des exec
        self.coro_name = coro_name              # Nom de la variable utilisée pour la gestion des coroutines des exec
        self.prov_name = prov_name              # Nom de la variable utilisée pour diverses utilités temporaires
        self.var_name = var_name                # Nom de la variable utilisée pour des affectations extérieures

        self.locals[self.bridge_name] = self    # Permet d'accéder au shell dans les exec

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

    async def push(self, text, color=False):
        """Envoie <text> dans le pseudo-terminal"""
        try:
            result = self._push(text, color)
            if asyncio.iscoroutine(result):
                result = await result
        except Exception as exc:
            raise ShellIOError(method="push", original=exc)

    async def help(self):
        """Envoie le message d'aide d'utilisation du pseudo-terminal"""
        await self.push(
            """Bon flemme d'écrire toute la doc' pour ça, en gros il faut bien comprendre que seules les syntaxes simples marcheront :
    - assignation           (var = expression)
    - évaluation            (expression)
    - instruction for       fin avec "end" ou "endfor", clause "else" reconnue
    - instruction while     fin avec "end" ou "endwhile" clause "else" reconnue
    - instruction if        fin avec "end" ou "endif", clauses "elif" et "else" reconnues

Les insctuctions try / (async) with / (async) def / class / async for ne sont pas disponibles pour l'instant, notemment.
Les clauses break et continue ne sont pas implémentées et soulèvent une erreur d'exécution.

Chaque ligne est exécutée séparément : il est impossible de séparer des instructions en plusieurs lignes (\, \"\"\", continuations de parenthèses...)"""
        )

    async def run(self):
        """Lance le pseudo-terminal"""
        # Pré-vérifications
        if "sys" not in self.globals:
            self.globals["sys"] = sys       # On doit avoir sys importé dans shell.globals

        # Run
        version_info = sys.version.replace('\n', '')
        if self.shut_keywords:
            shut_keywords = ", ".join(f"\"{kw}\"" for kw in self.shut_keywords) + " (arrêt immédiat), "
        else:
            shut_keywords = ""
        await self.push(f"""Python {version_info}\n{self.welcome_text}\n"""
                        f"""Mots-clés réservés : {shut_keywords}"end", "endfor", "endif", "endwhile" (sortie de structure), \"{self.bridge_name}", \"{self.result_name}", \"{self.coro_name}", \"{self.prov_name}" et \"{self.var_name}".\n"""
                        f"""Utiliser "help" pour plus d'informations sur les spécificités de ce pseudo-terminal (help(obj) non modifié)"""
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
        self.prompt = ">>> " + "    "*self.depth
        self.prompt_dots = ">>> " + "··· "*self.depth + "        << : end"
        self.self_prompt = ">>> " + "    "*(self.depth - 1)
        self.endwords = ["end"]
        self.buffer = []               # Lignes en attende d'exécution
        self.exit = False

    def __repr__(self):
        """Return repr(self)"""
        return f"""<pseudoshell.{type(self).__name__} \"{self.caller}" on shell {self.shell}>"""

    async def run(self):
        """Exécute la boucle jusqu'à recevoir un ordre de fin"""
        if self.history:
            await self.shell.push(self.history, color=True)

        while not self.exit:
            await self.shell.push(self.prompt_dots, color=True)
            entree = await self.shell.pull()

            try:
                if entree in self.endwords:
                    self.history += f"{self.self_prompt}\n"
                    self.exit = True

                elif entree == "help":
                    await self.shell.help()

                elif entree.endswith(":"):      # Commande d'entrée structure / clause

                    # Structures
                    new_struct = None
                    if entree.startswith("for"):
                        new_struct = For
                    elif entree.startswith("while"):
                        new_struct = While
                    elif entree.startswith("if"):
                        new_struct = If

                    if new_struct:
                        loop = new_struct(shell=self.shell, caller=entree, depth=self.depth + 1,
                                          history=f"{self.history}{self.prompt}{entree}\n")
                        await loop.run()                    # Récupération instructions
                        self.buffer.append(loop)            # Une fois boucle finie, on l'enregistre (objet If)
                        self.history = loop.history         # On actualise l'historique


                    # Clauses des différentes structures
                    elif entree.startswith("else"):
                        self.add_clause("else", entree)
                        self.history += f"{self.self_prompt}{entree}\n"
                    elif entree.startswith("elif"):
                        self.add_clause("elif", entree)
                        self.history += f"{self.self_prompt}{entree}\n"

                    else:
                        raise PseudoShellError(f"BadSyntax - Clause non reconnue")


                else:       # Si ni for, while, if, ..., exit :
                    self.buffer.append(Line(shell=self.shell, text=entree))
                    self.history += f"{self.prompt}{entree}\n"


                if self.depth == 0:       # Boucle principale : on exécute
                    try:
                        result = await self.exec()

                    except ExecutionError as exc:
                        await self.shell.push(f"{exc.original_traceback()}")

                    except Exception:
                        await self.shell.push(f"PseudoShell - Fatal exception during execution :\n{traceback.format_exc()}\n"
                                              f"No change made, retry:")
                        await self.shell.push(self.history, color=True)

                    else:
                        await self.shell.push(self.history, color=True)
                        await self.shell.push(result.text)
                        # await self.shell.push(f"{self.history}{result.text}\n\nbuffer : {self.buffer}")

                    finally:
                        self.buffer = []
                        self.history = ""

                else:                     # Dans une structure : on enregistre
                    await self.shell.push(self.history, color=True)

            except Exception as exc:
                await self.shell.push(f"Trying to add\n{self.prompt}{entree}\n"
                                      f"{''.join(traceback.format_exception_only(type(exc), exc))}\n"
                                      f"No change made, retry:"
                )
                await self.shell.push(self.history, color=True)


    def add_clause(self, clause, caller):
        """Gère l'ajout de la clause <clause> à la structure. À overwrite."""
        raise PseudoShellError(f"BadSyntax - Clause {clause} incorrecte / non appliquable ici")

    async def exec_buffer(self, start=None, end=None) -> Result:
        """Exécute les objets et structures dans self.buffer[start:end] (défaut tous)"""
        results = ResultsList()
        for obj in self.buffer[start:end]:   # lignes et structures dans buffer
            result = await obj.exec()               # ON EXÉCUTE TOUT
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
        self.prompt_dots += ", endfor"

        if match := re.match(r"for\s*(.+?)\s*in\s*(.+?)\s*:", self.caller):     # Entrée dans boucle
            self.variter_txt = match.group(1).strip()
            self.iterator_txt = match.group(2).strip()
        else:
            raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une boucle for")

        self.else_index = None


    def add_clause(self, clause, caller):
        """Enregistre la clause <clause>"""
        if clause == "else":
            if self.else_index:
                raise PseudoShellError("BadSyntax - Il ne peux y avoir plus d'une clause else")
            elif match := re.match(r"else\s*:", caller):
                self.else_index = len(self.buffer)          # Indice de début de clause else
            else:
                raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une clause else")

        else:
            raise PseudoShellError(f"BadSyntax - Clause {clause} incorrecte dans if")

    async def exec(self) -> Result:
        """Exécute la boucle"""
        text = f"{self.shell.prov_name} = {self.iterator_txt}"
        await Line(shell=self.shell, text=text).exec()      # On affecte l'itérateur à _prov (dans le contexte de shell)

        text = f"{self.variter_txt} = {self.shell.var_name}"
        results = ResultsList()
        for self.shell.locals[self.shell.var_name] in self.shell.locals[self.shell.prov_name]:   # for _var in _prov
            await Line(shell=self.shell, text=text).exec()                  # On affecte _var à {variter} (dans le contexte de shell)
            iter_result = await self.exec_buffer(end=self.else_index)       # Résultat de l'itération en cours
            results.append(iter_result)

        if self.else_index:
            iter_result = await self.exec_buffer(start=self.else_index)      # Exécution clause else
            results.append(iter_result)

        return results.join()      # Joins les results entre eux (crée un Result, garde le success du dernier result de la liste)


class While(Loop):
    """Boucle while d'un pseudo-terminal Shell"""

    def __init__(self, *args, **kwargs):
        """Initialize self"""
        Loop.__init__(self, *args, **kwargs)
        self.endwords.append("endwhile")
        self.prompt_dots += ", endwhile"

        if match := re.match(r"while\s*(.+?)\s*:", self.caller):     # Entrée dans boucle
            self.condition = match.group(1).strip()
        else:
            raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une boucle while")

        self.else_index = None

    def add_clause(self, clause, caller):
        """Enregistre la clause <clause>"""
        if clause == "else":
            if self.else_index:
                raise PseudoShellError("BadSyntax - Il ne peux y avoir plus d'une clause else")
            elif match := re.match(r"else\s*:", caller):
                self.else_index = len(self.buffer)          # Indice de début de clause else
            else:
                raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une clause else")

        else:
            raise PseudoShellError(f"BadSyntax - Clause {clause} incorrecte dans while")

    async def exec(self) -> Result:
        """Exécute la boucle"""
        text = f"{self.shell.prov_name} = {self.condition}"
        await Line(shell=self.shell, text=text).exec()      # On affecte la condition à _prov (dans le contexte de shell)

        results = ResultsList()
        while self.shell.locals[self.shell.prov_name]:
            iter_result = await self.exec_buffer(end=self.else_index)       # Résultat de l'itération en cours
            results.append(iter_result)

            await Line(shell=self.shell, text=text).exec()      # On recalcule la condition

        if self.else_index:
            iter_result = await self.exec_buffer(start=self.else_index)      # Exécution clause else
            results.append(iter_result)

        return results.join()      # Joins les results entre eux (crée un Result, garde le success du dernier result de la liste)



class If(Loop):
    """Boucle if (niklérajeu) d'un pseudo-terminal Shell"""

    def __init__(self, *args, **kwargs):
        """Initialize self"""
        Loop.__init__(self, *args, **kwargs)
        self.endwords.append("endif")
        self.prompt_dots += ", endif"

        if match := re.match(r"if\s*(.+?)\s*:", self.caller):
            self.conditions = [match.group(1).strip()]
            self.indexes = [0]
        else:
            raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une clause if")

        self.else_index = None


    def add_clause(self, clause, caller):
        """Enregistre la clause <clause>"""
        if clause == "else":
            if self.else_index:
                raise PseudoShellError("BadSyntax - Il ne peux y avoir plus d'une clause else")
            elif match := re.match(r"else\s*:", caller):
                self.else_index = len(self.buffer)          # Indice de début de clause else
            else:
                raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une clause else")

        elif clause == "elif":
            if self.else_index:
                raise PseudoShellError("BadSyntax - Une clause elif ne peut venir après une clause else")
            elif match := re.match(r"elif\s*(.+?)\s*:", caller):
                self.conditions.append(match.group(1).strip())
                self.indexes.append(len(self.buffer))       # Indice de début de le clause elif
            else:
                raise PseudoShellError("BadSyntax - Mauvaise syntaxe pour une clause elif")

        else:
            raise PseudoShellError(f"BadSyntax - Clause {clause} incorrecte dans if")


    async def exec(self) -> Result:
        """Exécute la boucle"""
        self.indexes.append(self.else_index)       # P'tit trix
        for i, condition in enumerate(self.conditions):     # Pour chaques elifs (y compris le if initial)
            text = f"{self.shell.prov_name} = {condition}"
            await Line(shell=self.shell, text=text).exec()      # On affecte la condition à _prov (dans le contexte de shell)

            if self.shell.locals[self.shell.prov_name]:
                results = await self.exec_buffer(start=self.indexes[i], end=self.indexes[i+1])
                return results

        if self.else_index:
            results = await self.exec_buffer(start=self.else_index)
            return results



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

        source = self.text

        # Gestion coroutine
        if "await" in source:
            left, right = source.split("await", maxsplit=1)                             # Ex. left = "mess = ", right = " ctx.send('oh')"
            res = await Line(self.shell, f"{self.shell.coro_name} = {right}").exec()    # On exec la partie droite  ==> _coro = <coroutine object ...>
            self.shell.locals[self.shell.coro_name] = await self.shell.locals[self.shell.coro_name]     #   On await ==> _coro = <Message id=...>
            source = f"{left} {self.shell.coro_name}"                                   #  Notre nouvelle source, ex. : "mess =  _coro"

        # Préparation récupération résultat
        if not ("=" in source
                or keyword.iskeyword(source.split()[0])):       # Ligne à exécuter
            source = f"{self.shell.result_name} = {source}"

        # Exécution
        source = f"{source} ; {self.shell.bridge_name}.globals = globals() ; {self.shell.bridge_name}.locals = locals()"
        try:
            exec(source, self.shell.globals, self.shell.locals)

        except Exception as exc:
            raise ExecutionError(original=exc)

        except SystemExit:
            raise PseudoShellExit("PseudoShell : exited.")

        else:
            # Récupération résultat
            if self.shell.result_name in self.shell.locals:
                if not self.result:
                    self.result.text = repr(self.shell.locals[self.shell.result_name])
                self.shell.locals.pop(self.shell.result_name)

            return self.result

        finally:
            self.shell.globals["sys"].stdout = stdout


    def write(self, text):
        """Petit hack pour pouvoir rediriger print vers self, élimine les \n envoyés seuls à la fin"""
        if text != "\n":
            self.result.text += text
