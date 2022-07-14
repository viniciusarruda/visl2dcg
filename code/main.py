import argparse
import re
import json
import xml.etree.ElementTree as ET
import os
from collections import defaultdict

# original_filename = '../dataset/Bosque_CF_8.0.PennTreebank.ptb'
# filename = '../dataset/Bosque_CF_8.0.PennTreebank_utf8.ptb'

# #This files was loaded and saved as utf-8. Then it was fixed by hand some issues
# with open(original_filename, 'r', encoding='cp1252') as f:
#     data = f.read()

# with open(filename, 'w', encoding='utf-8') as f:
#     f.write(data)

# exit()

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


def tmp(tree, level=-1):

    # print(tree, level)

    if tree == '':
        return []
    elif tree[0] == '(':
        return tmp(tree[1:].strip(), level + 1)
    elif tree[0] == ')':
        return tmp(tree[1:].strip(), level - 1)
    else:
        idx = min([v for v in [tree.find('('), tree.find(')')] if v >= 0])

        if tree.startswith('FRASE'):
            label = 'S'
        else:
            # print()
            # print(tree)
            # print(tree[idx])
            # print(idx)
            label = tree[:idx].strip().split(':')[1].upper()

            if tree[idx] == ')': # is leaf
                label += '_' + tree[:idx].strip().split(' ')[-1]

        return [(label, level)] + tmp(tree[idx:].strip(), level)


def read_PennTreebank(filename: str):

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lines = [d.strip() for d in lines]
    lines = [d for d in lines if d != '']

    i = 0
    while i < len(lines):

        if lines[i][0] == '#':
            s = ' '.join(lines[i].split(' ')[2:])
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

        print(s)
        tree = trees[0]

        ret = tmp(tree)
        
        print(ret)
        print(tree)
        print()

        n_levels = max([level for label, level in ret]) + 1
        for i in range(n_levels):
            for item in ret:
                if item[1] == i:
                    label = item[0]

                fazendoo.. 


        exit()

        levels = {}

        level = 0
        assert tree[0] in ['(', ')'], f"{tree}"
        tree = tree[1:].strip()

        print(tree)

        while tree != '':

            o = tree.find('(')
            c = tree.find(')')

            level_offset = 0
            if o == -1 and c == -1:
                assert tree == ''
                print('estranho')
                exit()
                break
            elif o == -1:
                idx = c
                level_offset = -1
            elif c == -1:
                print('Impossible 1')
                exit()
            elif c < o:
                idx = c
                level_offset = -1
            elif c > o:
                idx = o
                level_offset = 1
            else:
                print('Impossible 2')
                exit()            

            assert level >= 0
            
            content = tree[:idx].strip()

            if content.startswith('FRASE'):
                label = 'S'
            elif content == '':
                label = None
            else:
                label = content.strip().split(':')[1]

            print('----')
            print(tree)
            print(content)
            print(level)
            print(label)
            # exit()


            level += level_offset
            tree = tree[idx + 1:].strip()

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