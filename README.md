# VISL/PennTreebank to DCG converter

<!---Esses são exemplos. Veja https://shields.io para outras pessoas ou para personalizar este conjunto de escudos. Você pode querer incluir dependências, status do projeto e informações de licença aqui--->

<!-- ![GitHub repo size](https://img.shields.io/github/repo-size/iuricode/README-template?style=for-the-badge)
![GitHub language count](https://img.shields.io/github/languages/count/iuricode/README-template?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/iuricode/README-template?style=for-the-badge)
![Bitbucket open issues](https://img.shields.io/bitbucket/issues/iuricode/README-template?style=for-the-badge)
![Bitbucket open pull requests](https://img.shields.io/bitbucket/pr-raw/iuricode/README-template?style=for-the-badge)

<img src="exemplo-image.png" alt="exemplo imagem"> -->

> This source code converts a given corpus in the PennTreebank format to the DCG format, being appropriate to run in Prolog.

### Adjustments and improvements

The project is still in development and upcoming updates will address the following tasks:

- [x] Enable PennTreebank format
- [x] Compute probability and frequency count for rules
- [ ] Reorder the rules for better efficiency and remove loops
- [ ] Generate the probability for the parse tree
- [ ] Generate the grammar with argument structure
- [ ] Add option for rule cut, pruning the rules with a frequency below a given threshold. 

## 💻 Requirements

This project was tested with Python 3.8.
To install the dependencies install the requirements:

```
pip install -r requirements.txt
```

## ☕ Using the DCG converter

To use the DCG converter just run the `main.py` script with the following arguments:

```
usage: main.py [-h] --file_path FILE_PATH --file_format {VISL,PennTreebank,TigerXML} --output_folder OUTPUT_FOLDER [--graphviz]

optional arguments:
  -h, --help            show this help message and exit
  --file_path FILE_PATH
                        File path in the specified format.
  --file_format {VISL,PennTreebank,TigerXML}
                        File format.
  --output_folder OUTPUT_FOLDER
                        Output folder.
  --graphviz            A boolean switch to render the tree in graphviz
```

Example of usage:
```
python main.py --file_path ../dataset/Bosque_CF_8.0.PennTreebank_utf8.ptb --file_format PennTreebank --output_folder ../output
```


# visl2dcg
OLD STUFF, TO INCLUDE LATER


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


# REUNIAO
TODO checar se esta no https://www.linguateca.pt/Floresta/doc/VISLsymbolset-Floresta.html 
as formas que estou extraindo

s(X, []) prolog
resultar a proabilidade da arvore final
duas versoes, uma pura e limpa e outra com a arvore deitada e as probabilidades
leitura!!!! 

dá um ctrl + f em P.vp -> só tem uma ocorrencia, acho que é bug, acho que deveria ser P:vp



# EXEMPLO DE DCG e entrada para arvore deitada
s(sent(sn(X),sv(Y))) --> sn(X), sv(Y).
sn(pro(X)) --> pro(X).
sv(v(X)) --> v(X).
pro(ele) --> [ele].
v(correu) --> [correu].

s(X,Frase,[]).

