import argparse
import re
import json
import xml.etree.ElementTree as ET
import os
from collections import defaultdict
import string

# original_filename = '../dataset/Bosque_CF_8.0.PennTreebank.ptb'
# filename = '../dataset/Bosque_CF_8.0.PennTreebank_utf8.ptb'

# #This files was loaded and saved as utf-8. Then it was fixed by hand some issues
# with open(original_filename, 'r', encoding='cp1252') as f:
#     data = f.read()

# with open(filename, 'w', encoding='utf-8') as f:
#     f.write(data)

# exit()

def remove_punct(text):
    spaces = ' ' * len(string.punctuation)
    return text.translate(str.maketrans(string.punctuation, spaces))

def read_TigerXML(filename: str):

    # OBS
    # s1, s2 n tem referencia a um terminal
    # tem um edge (s1674) com nome de secedge, dar um ctrl+f e mostrar
    # tem um erro na referencia de dois ids terminais em s9
    # s2363 tem id referenciando terminal em s1683
    # s1683 tem terminal não sendo referenciado
    black_list = ['s1', 's2', 's3', 's4', 's1674', 's9', 's1683', 's2363']
    # essa lista não para de crescer!
    # ta anotado errado

    # TODO
    # colocar em lowercase os terminals e nonterminals em uppercase
    # checar casos em que ha algum terminal n referenciado -> encontrei que sim por acidente.. olhar OBS
    # TODO pegar todos os POS que serao os terminais ao inves de diretamente os terminais

    tree = ET.parse(filename)
    root = tree.getroot()

    # head = root[0] # metadata
    body = root[1]

    print(f'Number of sentences: {len(body)}')

    
    dcg_terminals = defaultdict(int) # zero as default
    dcg_nonterminals = defaultdict(int) # zero as default

    for s in body:

        if s.attrib['id'] not in black_list: # see OBS above
            
            dcg_rules = defaultdict(int) # zero as default
            referenced = []
            dcg_ids_nonterminals = {}
            graph_ids = {}
            graph = s[0]

            root_id = graph.attrib['root']
            
            terminals = graph[0]
            for t in terminals:
                assert t.attrib['id'] not in graph_ids # sanity check
                graph_ids[t.attrib['id']] = t.attrib['word'].lower()

            nonterminals = graph[1]
            for nt in nonterminals:
                assert nt.attrib['id'] not in graph_ids # sanity check
                graph_ids[nt.attrib['id']] = nt.attrib['cat'].upper()
                
                assert nt.attrib['id'] not in dcg_ids_nonterminals # sanity check
                dcg_ids_nonterminals[nt.attrib['id']] = [edge.attrib['idref'] for edge in nt]

            for left, right in dcg_ids_nonterminals.items():
                dcg_rules[f"{graph_ids[left]} --> {' '.join([graph_ids[r] for r in right])}"] += 1
                referenced += [r for r in right]

            # sanity check
            not_referenced = set(graph_ids.keys()) - set(referenced) - set([root_id])
            if len(not_referenced) > 0:
                print(f"Sentence {s.attrib['id']} has no reference to {not_referenced}")
                # exit()

    # print(dcg_nonterminals)

def tmp(tree, terminals: defaultdict, level=-1):

    # print(tree, level)

    if tree == '':
        return []
    elif tree[0] == '(':
        return tmp(tree[1:].strip(), terminals, level + 1)
    elif tree[0] == ')':
        return tmp(tree[1:].strip(), terminals, level - 1)
    else:
        idx = min([v for v in [tree.find('('), tree.find(')')] if v >= 0])

        if tree.startswith('FRASE'):
            label = 's'
        else:
            # print()
            # print(tree)
            # print(tree[idx])
            # print(idx)
            label = tree[:idx].strip().split(':')
            
            if len(label) > 1:
                label = label[1].lower()
            else:
                assert len(label) == 1
                label = label[0]
                # TODO analizar talvez esse cara aqui já é um terminal e n tem que ser colocado como label? ou ele msm nem deve ser uma label

            if tree[idx] == ')': # is leaf
                # label += '_' + tree[:idx].strip().split(' ')[-1]
                terminals[label].append(remove_punct(tree[:idx].strip().split(' ')[-1].lower()))
                

        return [(label, level)] + tmp(tree[idx:].strip(), terminals, level)


def format_tree2(tree):

    formatted_tree = defaultdict(list)

    label, level = tree[0]
    previous_level = level
    assert level == 0
    stack = [(label, level)]

    for label, level in tree[1:]:
        
        print(stack)
        print(formatted_tree)

        previous_level = stack[-1][1]

        assert abs(level - previous_level) == 1, f'{label} {level} {previous_level}'
        assert level >= 0
        assert len(stack) >= 1

        if level > previous_level:
            stack.append((label, level))
        elif level < previous_level:
            child, _ = stack.pop()
            parent, _ = stack[-1]
            formatted_tree[parent].append(child)
        else:
            print('impossible')
            exit()

        assert level >= 0
        assert len(stack) >= 1

    return formatted_tree

def format_tree(tree, terminals: defaultdict):

    # give a unique id for the labels, because I will use a hash (dict) to keep the tree
    tree = [(f'{label}_{e}', level) for e, (label, level) in enumerate(tree)]
    remove_id = lambda label: '_'.join(label.split('_')[:-1])

    formatted_tree = defaultdict(list)

    _, level = tree[0]
    assert level == 0

    stack = [tree.pop(0)]

    while len(tree) > 0 or len(stack) > 1:

        print('###########')
        print(stack, '\t\t\t', tree)
        # print(formatted_tree)
        if len(tree) > 0 and len(stack) > 1:
            assert abs(tree[0][1] - stack[-1][1]) <= 1, (tree[0], stack[-1])

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
            print('impossibvel')
            exit()

    # print(stack, '\t\t\t', tree)
    # print(formatted_tree)

    dcg = []

    # non terminals
    for left, right in formatted_tree.items():
        left = remove_id(left)
        right = [remove_id(r) for r in right]
        dcg.append(f"{left} --> {', '.join(right)}.")

    dcg.sort()

    # terminals
    for left, right in terminals.items():
        right = [f'[{r}]' for r in right]
        dcg.append(f"{left} --> {' | '.join(right)}.")

    return dcg

def read_PennTreebank(filename: str):

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lines = [d.strip() for d in lines]
    lines = [d for d in lines if d != '']

    i = 0
    while i < len(lines):

        if lines[i][0] == '#':
            i += 1

            trees = []
            while i < len(lines) and lines[i][0] != '#': 
                assert lines[i].startswith('(FRASE')
                tree = [lines[i]]
                i += 1
                while i < len(lines) and lines[i][0] != '#' and not lines[i].startswith('(FRASE'):
                    tree.append(lines[i])
                    i += 1
                trees.append(' '.join(tree))

        tree = trees[0]

        terminals = defaultdict(list)
        # try:
        print(tree)
        ret = tmp(tree, terminals)
        print()
        print(terminals)
        print()
        print(ret)
        dcg = format_tree(ret, terminals)
        # except:
        #     print(tree)
        #     # exit()

        # print(dcg)

        with open('PennTreebank.output', 'w', encoding='utf-8') as f:
            f.write('\n'.join(dcg))


        if i > 5:
            exit()


def read_file(fileformat: str, filename: str):

    if fileformat == 'TigerXML':
        return read_TigerXML(filename)

    elif fileformat == 'PennTreebank':
        return read_PennTreebank(filename)


def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--fileformat', type=str, help='File fileformat.', 
                        choices=['VISL', 'PennTreebank', 'TigerXML'], required=True)
    # # Switch
    # parser.add_argument('--switch', action='store_true',
    #                     help='A boolean switch')
    args = parser.parse_args()

    return args


def main():

    filepath = '../dataset/'
    filenames = {'TigerXML': 'Bosque_CF_8.0.TigerXML_utf8.xml', 
                 'PennTreebank': 'Bosque_CF_8.0.PennTreebank_utf8.ptb'}

    args = get_args()

    read_file(args.fileformat, os.path.join(filepath, filenames[args.fileformat]))


if __name__ == '__main__':
    main()


# REUNIAO
# TODO checar se esta no https://www.linguateca.pt/Floresta/doc/VISLsymbolset-Floresta.html as formas que estou estraindo

# s(X, []) prolog
# resultar a proabilidade da arvore final
# duas versoes, uma pura e limpa e outra com a arvore deitada e as probabilidades
# leitura!!!! 

# cortar disciplina do andre..