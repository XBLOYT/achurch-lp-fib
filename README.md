# AChurch
## Pràctica Compiladors LP Q2-2023 (Nota: 9,5)

Achurch és un intèrpret de λ-càlcul que aplica α-conversions i β-reduccions a les expressions donades.
A més, per cada expressió, obté l'arbre que la representa, de forma gràfica.

## Instal·lació
Cal tenir instal·lades les llibreries següents pel correcte funcionament del bot:
- Python
- ANTLR4
- Python Telegram Bot

Un cop instal·lades, cal executar la següent comanda:

```sh
antlr4 -Dlanguage=Python3 -no-listener -visitor lc.g4
```
Per accedir al bot de Telegram, s'ha de fer mitjançant el següent enllaç:
[AChurch](https://t.me/achurch_lpbot)

## Ús
IMPORTANT: S'ha d'introduir un TOKEN a l'arxiu achurch.py (línia 20: TOKEN = "##########"). S'ha de canviar el "##########" pel token que l'usuari tingui.

Per utilitzar el bot només cal iniciar-lo amb la següent comanda:
```sh
python3 achurch.py
```
A continuació ja es pot utilitzar el bot a Telegram. El bot admet les següents comandes:
- /start (imprimeix un missatge de benvinguda)
- /author (el bot imprimeix el nom de l'autor)
- /help (s'imprimeixen totes les comandes que admet el bot)
- /macros (s'imprimeixen totes les macros registrades)
- /maxiterations <nombre> (el nombre màxim d'intents de reducció que es proven passa a ser <nombre>. Si la reducció en qüestió requereix més passes, el bot considerarà que no té solució.)
- Expressió en λ-càlcul (Ha de ser una expressió vàlida. El bot l'avaluarà i farà totes les reduccions que pugui).


## Expressions en λ-càlcul

Les expressions que admet el bot són:

Aplicacions:

```sh
terme terme 
```
(si un terme és quelcom complex, ha d'anar entre parèntesi)

Parèntesis:

```sh
(terme)
```

Abstraccions:

```sh
(\ | λ) Lletres . terme
```
Les abstraccions admeten més d'una lletra.

Lletres:
```sh
Lletra
```
Cada lletra codifica una variable. Només es poden anomenar com una lletra minúscula entre a i z. Això limita el nombre de variables que una expressió pot tenir a 26, cal tenir-ho en compte.

Macros i infixos:
```sh
(MACRO | INFIX) (= | ≡) terme
```
Les macros es poden fer servir com a termes, és a dir, serveixen per qualsevol dels casos anteriors.
Restriccions: 
- Les macros només admeten noms en majúscula. Els noms poden tenir múltiples lletres i nombres.
- Els únics símbols que poden tenir els infixos són: + - _ # $ % &

Operacions amb infixos
```sh
MACRO INFIX MACRO
```

Tot el que s'introdueixi per text que no s'ajusti a això provocarà errors.

## Autor
Xavier Bernat López
