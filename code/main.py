import argparse
# import re
# import json
# import xml.etree.ElementTree as ET
import os
from collections import defaultdict
import string
import graphviz
from tqdm import tqdm
from unidecode import unidecode
import numpy as np 

# original_filename = '../dataset/Bosque_CF_8.0.PennTreebank.ptb'
# filename = '../dataset/Bosque_CF_8.0.PennTreebank_utf8.ptb'

# #This files was loaded and saved as utf-8. Then it was fixed by hand some issues
# with open(original_filename, 'r', encoding='cp1252') as f:
#     data = f.read()

# with open(filename, 'w', encoding='utf-8') as f:
#     f.write(data)

# exit()


def render_graphviz(caption: str, formatted_tree: defaultdict, terminals: defaultdict, filename: str):

    g = graphviz.Digraph('G', filename=f'output/{filename}.gv')
    g.attr(label=caption)
    g.attr('node', shape='ellipse')

    set_of_nodes = set()
    def add_node(g: graphviz.Digraph, node: str, set_of_nodes: dict):
        # just to control and to not duplicate creation of the node, 
        # I dont think this is a problem, but just for sanity
        if node not in set_of_nodes:
            set_of_nodes.add(node)
            g.node(node, label='_'.join(node.split('_')[:-1]))

    g.attr('node', shape='ellipse')
    for parent, children in formatted_tree.items():
        add_node(g, parent, set_of_nodes)
        for child in children:
            add_node(g, child, set_of_nodes)
            g.edge(parent, child)

    g.attr('node', shape='plaintext')
    for parent, children in terminals.items():
        assert parent in set_of_nodes # parent should have already been added
        for child in children:
            add_node(g, child, set_of_nodes)
            g.edge(parent, child)
    g.save()
                
    graphviz.render('dot', 'png', f'output/{filename}.gv')


def parse_PennTreebank(tree, terminals: defaultdict, level=-1, label_id=0):

    def remove_punct(text):
        puncts = string.punctuation.replace('_', '') + '«»'
        spaces = ' ' * len(puncts)
        return text.translate(str.maketrans(puncts, spaces)).replace(' ', '')

    remove_extra_dash = lambda label: label[:-1] if len(label) > 1 and label[-1] == '-' and label[-2].isalpha() else label 

    # print(tree, level)

    if tree == '':
        return []
    elif tree[0] == '(':
        return parse_PennTreebank(tree[1:].strip(), terminals, level + 1, label_id)
    elif tree[0] == ')':
        return parse_PennTreebank(tree[1:].strip(), terminals, level - 1, label_id)
    else:
        idx = min([v for v in [tree.find('('), tree.find(')')] if v >= 0])

        if tree.startswith('FRASE'):
            label = f's_{label_id}'
            label_id += 1
        else:
            # print()
            # print(tree)
            # print(tree[idx])
            # print(idx)
            label = tree[:idx].strip().split(':')
            
            if len(label) > 1:
                label = label[1].lower()
                label = remove_extra_dash(label)
                label = f'{label}_{label_id}'
                label_id += 1
            else:
                # assert tree[idx] == ')', (label, tree[:idx]) -> tem caso que falha, { é pai de 'De' em #474 CF121-2 por exemplo
                assert len(label) == 1
                label = label[0]
                label = remove_extra_dash(label)
                label = f'{label}_{label_id}'
                label_id += 1
                # TODO analizar talvez esse cara aqui já é um terminal e n tem que ser colocado como label? ou ele msm nem deve ser uma label

            # teste de maior que zero pq pode ser o caso de ser apenas uma pontuação.. e de fato n seria um terminal
            if tree[idx] == ')' and len(remove_punct(tree[:idx].strip().split(' ')[-1])) > 0: # is leaf
                # label += '_' + tree[:idx].strip().split(' ')[-1]
                # print()
                # print(tree[:idx].strip().split(':'))
                # print('aquiii::::::::::::', tree[:idx].strip().split(' ')[-1].lower(), label)
                leaf = remove_punct(tree[:idx].strip().split(' ')[-1].lower())
                leaf = f'{leaf}_{label_id}'
                label_id += 1

                terminals[label].append(leaf)

        return [(label, level)] + parse_PennTreebank(tree[idx:].strip(), terminals, level, label_id)


def format_tree(tree):

    # give a unique id for the labels, because I will use a hash (dict) to keep the tree
    # tree = [(f'{label}_{e}', level) for e, (label, level) in enumerate(tree)]
    # Already added in tmp function

    formatted_tree = defaultdict(list)

    _, level = tree[0]
    assert level == 0

    stack = [tree.pop(0)]

    while len(tree) > 0 or len(stack) > 1:

        # print('###########')
        # print(stack, '\t\t\t', tree)
        # print(formatted_tree)

        if len(tree) == 0:
            assert len(stack) > 0
            child = stack.pop()[0]
            formatted_tree[stack[-1][0]].append(child)
        elif tree[0][1] > stack[-1][1]:
            stack.append(tree.pop(0))
        elif tree[0][1] <= stack[-1][1]:
            child = stack.pop()[0]
            formatted_tree[stack[-1][0]].append(child)
        else:
            print(stack[-1], tree[0])
            print('impossivel')
            exit()

    # print(stack, '\t\t\t', tree)
    # print(formatted_tree)
    # print(terminals)

    return formatted_tree


def save_dcg(formatted_tree: defaultdict, terminals: defaultdict, filename: str):

    def process_non_terminal(non_terminal: str, terminals_to_add: dict = None):

        map_puncts = {
            '?': 'question_mark',
            "-": "hyphen",
            ":": "colon",
            "<": "lt",
            ">": "gt",
            "/": "slash",
            "[": "open_bracket",
            "]": "close_bracket",
            "+": "plus",
            "&": "and",
            ')': 'close_parentheses',
            '«': 'ltlt',
            '»': 'gtgt',
            ',': 'comma',
            ';': 'semicolon',
            "'": 'prime',
            '!': 'exclamation',
            '.': 'dot',
            '(': 'open_parentheses',
            '...': 'three_dots',
            '--': 'double_dash',
            '%': 'percentage_symbol',
            '$': 'currency_symbol',
            "{": "open_curly_bracket",
            "}": "close_curly_bracket"
        }

        if non_terminal in map_puncts:
            left = f'punct_{map_puncts[non_terminal]}'
            right = map_puncts[non_terminal]
            if terminals_to_add is not None:
                terminals_to_add[left] = right
            return left
        elif len(non_terminal.replace('-', '')) > 0:
            return non_terminal.replace('-', '_')
        else:
            return non_terminal

    remove_id = lambda label: '_'.join(label.split('_')[:-1])

    dcg = []
    terminals_to_add = {}

    # non terminals
    for left, right in formatted_tree.items():
        left = process_non_terminal(remove_id(left))
        right = [process_non_terminal(remove_id(r), terminals_to_add) for r in right]
        dcg.append(f"{left} --> {', '.join(right)}.")

    dcg.sort()

    # terminals

    # group terminals, because the id was keeping them separated
    grouped_terminals = defaultdict(list)
    for left, right in terminals.items():
        left = process_non_terminal(remove_id(left))
        right = [unidecode(remove_id(r)) for r in right]
        grouped_terminals[left] += right

    for left, right in terminals_to_add.items():
        grouped_terminals[left].append(right)

    for left, right in grouped_terminals.items():
        right = [f'[{r}]' for r in set(right)]
        dcg.append(f"{left} --> {' | '.join(right)}.")

    with open(f'output/{filename}.dcg', 'w', encoding='utf-8') as f:
        f.write('\n'.join(dcg))


def read_PennTreebank(filename: str, graphviz: bool):

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lines = [d.strip() for d in lines]
    lines = [d for d in lines if d != '']

    trees = []
    i = 0
    while i < len(lines):

        if lines[i][0] == '#':
            number = lines[i].split(' ')[0]
            sentence = ' '.join(lines[i].split(' ')[2:])
            i += 1

            while i < len(lines) and lines[i][0] != '#': 
                assert lines[i].startswith('(FRASE')
                code = lines[i].split(' ')[1]
                tree = [lines[i]]
                i += 1
                while i < len(lines) and lines[i][0] != '#' and not lines[i].startswith('(FRASE'):
                    tree.append(lines[i])
                    i += 1
                header = f'{number} {code} {sentence}'
                trees.append((header, ' '.join(tree)))

    for header, tree in tqdm(trees):

        identifier = '_'.join(header[1:].split(' ')[:2])

        terminals = defaultdict(list)
        parsed_tree = parse_PennTreebank(tree, terminals)
        formatted_tree = format_tree(parsed_tree)
        save_dcg(formatted_tree, terminals, filename=identifier)
        
        if graphviz:
            render_graphviz(header, formatted_tree, terminals, filename=identifier)
        



def read_file(fileformat: str, filename: str, graphviz: bool):

    if fileformat == 'PennTreebank':
        return read_PennTreebank(filename, graphviz=graphviz)
    else:
        print('File format not implemented yet.')
        exit()

def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--fileformat', type=str, help='File fileformat.', 
                        choices=['VISL', 'PennTreebank', 'TigerXML'], required=True)
    parser.add_argument('--graphviz', action='store_true',
                        help='A boolean switch to render the tree in graphviz')
    args = parser.parse_args()

    return args


def join_dcgs(filepath: str):

    filenames = [f for f in os.listdir(filepath) if f.endswith('.dcg')]

    non_terminals, terminals = [], []

    for filename in tqdm(filenames):

        filename = os.path.join(filepath, filename)

        with open(filename, 'r', encoding='utf-8') as f:
            data = f.readlines()
        data = [d.strip() for d in data]

        terminals += [d for d in data if '[' in d]
        non_terminals += [d for d in data if '[' not in d]

    print(f'Number of non terminal rules: {len(non_terminals)}')
    print(f'Number of unique non terminal rules: {len(set(non_terminals))}')
    print(f'Number of     terminal rules (it can have more than one terminal per rule): {len(terminals)}')

    # non terminal stuff
    rules = defaultdict(int)
    for nt in non_terminals:
        rules[nt] += 1

    sorted_rules = sorted(rules.items(), key=lambda x: x[1], reverse=True)
    with open('unified_output/unified_non_terminals.dcg', 'w', encoding='utf-8') as f:
        f.write('\n'.join([f'{k}\t{v}' for k, v in sorted_rules]))

    # probs per left
    ## group by left
    grouped_left = defaultdict(list)
    for r, count in rules.items():
        grouped_left[r.split(' --> ')[0]].append((r, count))

    for right, grouped_rules in grouped_left.items():
        n = sum([x for _, x in grouped_rules])
        for i in range(len(grouped_rules)):
            grouped_rules[i] = (grouped_rules[i][0], grouped_rules[i][1] / n) 
    
    rules = []
    for right, grouped_rules in grouped_left.items():
        rules += grouped_rules
    sorted_rules = sorted(rules, key=lambda x: x[1], reverse=True)
    with open('unified_output/unified_non_terminals_probs.dcg', 'w', encoding='utf-8') as f:
        f.write('\n'.join([f'{k}\t{v}' for k, v in sorted_rules]))

    # unique, counts = np.unique(np.array([v for _, v in rules]), return_counts=True)
    # print(np.asarray((unique, counts)).T)
    # exit()

    # terminal stuff
    terminal_rules = defaultdict(list)
    for t in terminals:
        t = t.replace('.', '').replace('[', '').replace(']', '').replace(' ', '')
        left = t.split('-->')[0]
        right = t.split('-->')[1].split('|')
        terminal_rules[left] += right

    rules = []
    for left, right in terminal_rules.items():
        right = list(set(right))
        right = [f'n{r}' if r[0].isnumeric() else r for r in right]
        right.sort()
        right = ' | '.join([f'[{r}]' for r in right])
        rules.append(f'{left} --> {right}.')

    with open('unified_output/unified_terminals.dcg', 'w', encoding='utf-8') as f:
        f.write('\n'.join(rules))

    ######
    # non terminals + terminals
    non_terminals = list(set(non_terminals))
    non_terminals.sort()
    rules.sort()

    all_rules = non_terminals + rules
    all_rules.sort()
    all_rules = [r for r in all_rules if 'P.vp' not in r] # -> P:vp
    all_rules = [r for r in all_rules if 'ARGO' not in r] # ARGOpp -> ARGO:pp
    with open('unified_output/unified_all.dcg', 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_rules))


def main():

    filepath = '../dataset/'
    filenames = {'TigerXML': 'Bosque_CF_8.0.TigerXML_utf8.xml', 
                 'PennTreebank': 'Bosque_CF_8.0.PennTreebank_utf8_mini.ptb'}

    args = get_args()

    read_file(args.fileformat, os.path.join(filepath, filenames[args.fileformat]), args.graphviz)
    join_dcgs('output')

if __name__ == '__main__':
    main()


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