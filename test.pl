sentenca --> sintagma_nominal, sintagma_verbal.

sintagma_nominal --> determinante, nome.

sintagma_verbal --> verbo_transitivo, sintagma_nominal.

determinante --> [o].
determinante --> [a].
determinante --> [um].
determinante --> [uma].

verbo_transitivo --> [comeu].

nome --> [menino].
nome --> [bolo].


det(Conc, Det) --> [Det], {det(Conc, Det)}.

det([masc, sing], o).
det([fem, sing], a).
det([masc, plur], os).
det([fem, plur], as).
det([masc, sing], um).
det([fem, sing], uma).
det([masc, plur], uns).
det([fem, plur], umas). 