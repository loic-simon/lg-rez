import unidecode
import re

def remove_accents(s):
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)

with open("ias.txt", 'r', encoding='utf-8') as Fich:
    a = Fich.read()

print(len(a))

i = 0
im = -1
k = 100
trigs = []
loct = []
reps = []
sql = ""
rep = ""
while i > im:
    im = i

    opseq_trig = """<span data-slate-content="true">"""
    endseq_trig = """</span>"""
    i_trig = a.find(opseq_trig, i+1)

    opseq_rep = """placeholder="Enter reply text..." """
    opseq2_rep = """>"""
    endseq_rep = """</textarea>"""
    i_rep = a.find(opseq_rep, i+1)

    if i_trig < i_rep:
        if rep != "":       # on a enregistré une réponse ==> suivant
            reps.append( f"({k}, \"{rep}\")" )
            trigs.extend( [f"(\'{t}\', {k})" for t in loct] )
            loct = []
            rep = ""
            k += 1
            # input()

        i = i_trig
        j = a.find(endseq_trig, i+len(opseq_trig))
        # print("Trigger : " + a[i+len(opseq_trig):j])
        trig = a[i+len(opseq_trig):j].replace("'", "''")
        if (t := remove_accents(trig).lower()) not in loct:
            loct.append(t)

    else:
        i = i_rep
        i = a.find(opseq2_rep, i+len(opseq_rep))
        j = a.find(endseq_rep, i+len(opseq2_rep))
        if rep != "":
            rep += " <||> "
        rep += a[i+len(opseq2_rep):j].replace("'", "''")

reps.append( f"({k}, \"{rep}\")" )
trigs.append( f"(\"{' ; '.join(loct)}\", {k})" )


with open("chatfuel_IA3.sql", 'w', encoding='utf-8') as Fich:
#     Fich.write(f"""INSERT INTO "public"."reactions" ("id", "reponse") VALUES {", ".join(reps)};
# INSERT INTO "public"."triggers" ("trigger", "reac_id") VALUES {", ".join(trigs)};""")
    Fich.write(f"""INSERT INTO "public"."triggers" ("trigger", "reac_id") VALUES {", ".join(trigs)};""")
