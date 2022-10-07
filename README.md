# visl2dcg

https://www.linguateca.pt/Floresta/corpus.html#download
https://www.linguateca.pt/Floresta/documentacao.html
https://visl.sdu.dk/visl/pt/info/symbolset-manual.html
https://docs.ufpr.br/~arthur/orients/joao_inic.pdf
https://github.com/UniversalDependencies/UD_Portuguese-Bosque
https://visl.sdu.dk/constraint_grammar.html
https://visl.sdu.dk/visl/pt/parsing/automatic/trees.php


# bugs
anotacao 473 esta com o parenteses no lugar errado
3649
3422
56244

arvore 1484_A1 tem algum bug que n consegui identificar, corrigi de uma forma que ache mais adequada


rodar o script para gerar o utf de novo
fazer o diff com o utf que eu tenho (que é o corrigido)
e para as arvores que deu diferença, analisar e ver se eu corrigi a anotação certo e caso contrário ver como corrigir


pontuaçao de acordo com o que o finger colocou inicia com $, tipo $(, $:, etc


- posso jogar fora as setas de dependencia?
- o que eu posso jogar fora e ignorar nessas regras?
FUNCAO:forma ?

- como identificar quem tem loop para colocar por ultimo?
- ainda sim se não estiver na gramática vai entrar em loop
    - como faço esse cut para retornar falso?



 # python3 main.py --filepath ../dataset/Bosque_CF_8.0.PennTreebank_utf8_mini.ptb --fileformat PennTreebank --output output

# REUNIAO
# TODO checar se esta no https://www.linguateca.pt/Floresta/doc/VISLsymbolset-Floresta.html 
# as formas que estou extraindo

# s(X, []) prolog
# resultar a proabilidade da arvore final
# duas versoes, uma pura e limpa e outra com a arvore deitada e as probabilidades
# leitura!!!! 

# cortar disciplina do andre..


# dá um ctrl + f em P.vp -> só tem uma ocorrencia, acho que é bug, acho que deveria ser P:vp



# EXEMPLO DE DCG e entrada para arvore deitada
# s(sent(sn(X),sv(Y))) --> sn(X), sv(Y).
# sn(pro(X)) --> pro(X).
# sv(v(X)) --> v(X).
# pro(ele) --> [ele].
# v(correu) --> [correu].

# s(X,Frase,[]).



# opção 
# gerar a gramatica com estrutura de argumento
# gerar probabilistica
# opçao de corte de regras, para cortar regras abaixo de um threshold de frequencia