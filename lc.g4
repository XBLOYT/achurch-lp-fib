grammar lc;
root : terme             
     ;
terme :NOMMACRO INFIX NOMMACRO                  #infixop
     | (NOMMACRO | INFIX) ('='|'≡') terme     #defmacro
     | (NOMMACRO | INFIX)                      #macro
     |'('terme')'                              # parentesis
     | terme terme                              #aplicacio
     | <assoc=right> ('λ'|'\\') (LLETRA+) '.' terme         # abstraccio
     | LLETRA                               # lletra
     ;

NOMMACRO : [A-Z0-9]+;
INFIX : [+-_#$%&];
LLETRA : [a-z] ;
WS  : [ \t\n\r]+ -> skip ;
