from __future__ import annotations
from antlr4 import *
from lcLexer import lcLexer
from lcParser import lcParser
from lcVisitor import lcVisitor
from dataclasses import dataclass
import datetime
import logging
from graphviz import Digraph
import uuid

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


TOKEN = "##########"
NITSMAX = 20

@dataclass
class Lletra:
    nom: str


@dataclass
class Abstraccio:
    simbol: str
    parametre: Lletra
    cos: Terme


@dataclass
class Aplicacio:
    terme1: Terme
    terme2: Terme


@dataclass
class Parentesi:
    terme: Terme


macrosDic = {}
vars = set()
Terme = Lletra | Abstraccio | Aplicacio | Parentesi

imprimeixMacro = False


class TreeVisitor(lcVisitor):

    def __init__(self):
        self.nivell = 0

    def visitAbstraccio(self, ctx):
        parametres = list(ctx.getChildren())
        simbol = parametres[0]
        parametres.pop(0)

        textlletres = []
        while parametres[0].getText() != '.':
            textlletres.append(parametres[0].getText())
            parametres.pop(0)

        terme = self.visit(parametres[1])

        for lletra in reversed(textlletres):
            terme = Abstraccio(simbol.getText(), Lletra(lletra), terme)
        return terme

    def visitAplicacio(self, ctx):
        [terme1, terme2] = list(ctx.getChildren())
        return Aplicacio(self.visit(terme1), self.visit(terme2))

    def visitParentesis(self, ctx):
        [obre, terme, tanca] = list(ctx.getChildren())
        return Parentesi(self.visit(terme))

    def visitLletra(self, ctx):
        [lletra] = list(ctx.getChildren())
        return Lletra(lletra.getText())

    def visitDefmacro(self, ctx):
        [nom, equal, expr] = list(ctx.getChildren())
        macrosDic[nom.getText()] = self.visit(expr)
        global imprimeixMacro
        imprimeixMacro = True
        return macrosDic[nom.getText()]

    def visitMacro(self, ctx):
        [nom] = list(ctx.getChildren())
        return macrosDic[nom.getText()]

    def visitInfixop(self, ctx):
        [macro1, inf, macro2] = list(ctx.getChildren())
        return Aplicacio(Aplicacio(macrosDic[inf.getText()], macrosDic[macro1.getText()]), macrosDic[macro2.getText()])


def construeixGraf(t, graf, node_pare, lligadures):
    node = str(uuid.uuid4())
    match t:
        case Lletra(l):
            graf.node(node, shape='none', label=l)
            if node_pare:
                graf.edge(node_pare, node)
            if l in lligadures:
                graf.edge(node, lligadures[l], style="dotted")
        case Parentesi(terme):
            return construeixGraf(terme, graf, node_pare, lligadures)
        case Aplicacio(t1, t2):
            graf.node(node, shape='none', label='@')
            if node_pare:
                graf.edge(node_pare, node)
            construeixGraf(t1, graf, node, lligadures)
            construeixGraf(t2, graf, node, lligadures)
        case Abstraccio(simbol, variable, cos):
            graf.node(node, shape='none', label=('λ' + variable.nom))
            if node_pare:
                graf.edge(node_pare, node)
            lligadures[variable.nom] = node
            construeixGraf(cos, graf, node, lligadures)


def imprimeixGraf(t: Terme) -> Digraph:
    graf = Digraph()
    lligadures = {}
    construeixGraf(t, graf, "", lligadures)
    return graf


def imprimeixTerme(t: Terme) -> str:
    match t:
        case Lletra(l):
            return l
        case Parentesi(terme):
            return imprimeixTerme(terme)
        case Aplicacio(t1, t2):
            terme1 = imprimeixTerme(t1)
            terme2 = imprimeixTerme(t2)
            return "(" + terme1 + terme2 + ")"
        case Abstraccio(simbol, param, cos):
            Valor = "(" + simbol
            Valor = Valor + imprimeixTerme(param)
            return Valor + "." + imprimeixTerme(cos) + ")"
        case _:
            return ""


async def substituir(abs: Terme, var: Lletra, subs: Terme, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Terme:
    match abs:
        case Lletra(l):
            if Lletra(l) == var:
                return subs
            else:
                return Lletra(l)
        case Aplicacio(t1, t2):
            return Aplicacio(await substituir(t1, var, subs, update, context), await substituir(t2, var, subs, update, context))
        case Abstraccio(simbol, variable, cos):
            if variable == var:
                return Abstraccio(simbol, subs, await substituir(cos, var, subs, update, context))
            else:
                return Abstraccio(simbol, variable, await substituir(cos, var, subs, update, context))
        case Parentesi(t1):
             return Parentesi(await substituir(t1, var, subs, update, context))


def variableslliures(t, lligadures, lliures):
    match t:
        case Parentesi(t1):
            variableslliures(t1, lligadures, lliures)
        case Lletra(l):
            if l not in lligadures:
                lliures.add(l)
        case Aplicacio(t1, t2):
            variableslliures(t1, lligadures, lliures)
            variableslliures(t2, lligadures, lliures)
        case Abstraccio(sim, var, cos):
            lligadures.add(var.nom)
            variableslliures(cos, lligadures, lliures)
            if var.nom in lligadures:
                lligadures.remove(var.nom)


def detectalligadures(t, lligadures):
    match t:
        case Abstraccio(sim, var, cos):
            lligadures.add(var.nom)
            detectalligadures(cos, lligadures)
        case Parentesi(t):
            detectalligadures(t, lligadures)
        case Aplicacio(t1, t2):
            detectalligadures(t1, lligadures)
            detectalligadures(t2, lligadures)
        case Lletra(l):
            return

def detectaAbstraccions(t:Terme) -> bool:
    match t:
        case Lletra(l):
            return False
        case Parentesi(te):
            return detectaAbstraccions(te)
        case Aplicacio(t1, t2):
            return detectaAbstraccions(t1) or detectaAbstraccions(t2)
        case Abstraccio():
            return True

def retornaAbstraccioMesExterna(t:Terme) -> Terme:
    match t:
        case Lletra(l):
            return Lletra(l)
        case Parentesi(te):
            return retornaAbstraccioMesExterna(te)
        case Aplicacio(t1, t2):
            if detectaAbstraccions(t1): return retornaAbstraccioMesExterna(t1)
            elif detectaAbstraccions(t2): return retornaAbstraccioMesExterna(t2)
        case Abstraccio(simbol, variable, cos):
            return t

async def avalua(t: Terme, reduccio: bool, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Terme:
    match t:
        case Aplicacio(t1, t2):
            if isinstance(t1, Abstraccio):
                lliures = set()
                variableslliures(t2, set(), lliures)
                lligadures = set()
                detectalligadures(t1, lligadures)
                nout = t1
                alfaconv = False
                taux = t1.cos
                while detectaAbstraccions(taux):
                    lligadures_internes = set()
                    taux = retornaAbstraccioMesExterna(taux)
                    detectalligadures(taux, lligadures_internes)
                    if t1.parametre.nom in lligadures_internes:
                        alfaconv = True
                        lletra = "error"
                        for i in range(ord('a'), ord('z') + 1):
                            lletra = chr(i)
                            if lletra not in vars:
                                vars.add(lletra)
                                break
                            else: lletra = "error"
                        if lletra != "error":
                            taux = await substituir(taux, Lletra(taux.parametre.nom), Lletra(lletra), update, context)
                            nout = await substituir(nout, Lletra(t1.parametre.nom), Lletra(lletra), update, context)
                        else:
                            await update.message.reply_text("ERROR: Nombre màxim de variables assolit. No es pot realitzar l'α-conversió")
                            return
                    taux = taux.cos
                for var in lligadures:
                    if var in lliures:
                        alfaconv = True
                        lletra = "error"
                        for i in range(ord('a'), ord('z') + 1):
                            lletra = chr(i)
                            if lletra not in vars:
                                vars.add(lletra)
                                break
                        if lletra == "error":
                            await update.message.reply_text("ERROR: Nombre màxim de variables assolit. No es pot realitzar l'α-conversió")
                            return
                        else:
                            nout = await substituir(nout, Lletra(var), Lletra(lletra), update, context)
                if alfaconv:
                    await update.message.reply_text(imprimeixTerme(t1) + "→ α → " + imprimeixTerme(nout))
                    alfa_convertit = nout
                    nout = await substituir(nout.cos, t1.parametre, t2, update, context)
                    await update.message.reply_text(imprimeixTerme(Aplicacio(alfa_convertit, t2)) + "→ β → " + imprimeixTerme(nout))
                else:
                    nout = await substituir(nout.cos, t1.parametre, t2, update, context)
                    await update.message.reply_text(imprimeixTerme(t) + "→ β → " + imprimeixTerme(nout))
                return nout
            else:
                return Aplicacio(await avalua(t1, True, update, context), await avalua(t2, True, update, context))
        case Abstraccio(simbol, variable, cos):
            return Abstraccio(simbol, variable, await avalua(cos, True, update, context))
        case Parentesi(a):
            if reduccio:
                return await avalua(a, True, update, context)
            else:
                return t
        case Lletra(l):
            return Lletra(l)


def irreductible(t: Terme) -> bool:
    match t:
        case Lletra(l):
            return True
        case Abstraccio(simbol, var, cos):
            return irreductible(cos)
        case Aplicacio(t1, t2):
            if isinstance(t1, Abstraccio):
                return False
            elif isinstance(t1, Parentesi):
                return irreductible(Aplicacio(t1.terme, t2))
            else:
                return irreductible(t1) and irreductible(t2)
        case Parentesi(cos):
            return irreductible(cos)


def llistavars(t):
    global vars
    match t:
        case Lletra(l):
            vars.add(l)
        case Abstraccio(simbol, variable, cos):
            llistavars(cos)
        case Aplicacio(t1, t2):
            llistavars(t1)
            llistavars(t2)
        case Parentesi(t):
            llistavars(t)


async def macros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(macrosDic) != 0:
        paraimprimir = ""
        for macro, exp in macrosDic.items():
            paraimprimir = paraimprimir + macro + " ≡ " + imprimeixTerme(exp) + "\n"
        await update.message.reply_text(paraimprimir)
    else:
        await update.message.reply_text("No has definit cap macro encara!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respondre"""
    input = update.message.text
    input_stream = InputStream(input)
    lexer = lcLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = lcParser(token_stream)
    tree = parser.root()

    if parser._syntaxErrors > 0:
        await update.message.reply_text("Missatge no vàlid. Recorda que només accepto o bé expressions lambda o bé les comandes que pots veure si fas /help")
        return

    visitor = TreeVisitor()
    arbre = visitor.visit(tree)
    global imprimeixMacro, vars
    vars = set()
    if not imprimeixMacro:
        await update.message.reply_text(imprimeixTerme(arbre))
        llistavars(arbre)
        graf = imprimeixGraf(arbre)
        graf.attr(dpi='200')
        graf.render('arbre_base.gv', view=False, format='png')
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('arbre_base.gv.png', 'rb'))
        reductible = True
        nitsmax = NITSMAX
        while reductible and nitsmax >= 0:
            if isinstance(arbre, Parentesi):
                res = await avalua(arbre.terme, False, update, context)
            else:
                res = await avalua(arbre, False, update, context)
            nitsmax -= 1
            arbre = res
            if irreductible(res):
                reductible = False
        if nitsmax >= 0:
            await update.message.reply_text(imprimeixTerme(res))
            graf2 = imprimeixGraf(res)
            graf2.attr(dpi='200')
            graf2.render('arbre_res.gv', view=False, format='png')
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('arbre_res.gv.png', 'rb'))
        else:
            await update.message.reply_text("Nothing")
    else:
        imprimeixMacro = False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    first_name = user.first_name
    await context.bot.send_message(chat_id=update.effective_chat.id, text="AChurchBot!\nBenvingut/uda " + first_name + "!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="/start\n/author\n/help\n/macros\n/maxiterations <nombre>\nExpressió λ-càlcul")


async def author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /author is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="AChurchBot\n@ Xavier Bernat López, Q2 2023")


async def maxits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Select a new max number of nits"""
    global NITSMAX
    try:
        num = int(context.args[0])
        MAXNITS = num
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Com a màxim es faran "+ str(MAXNITS) + " iteracions.")
    except (IndexError, ValueError):
        await update.message.reply_text('No has introduït cap nombre! Recorda que la comanda es fa servir així:\n/maxiterations <nombre>')


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("macros", macros))
    application.add_handler(CommandHandler("author", author))
    application.add_handler(CommandHandler("maxiterations", maxits))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
