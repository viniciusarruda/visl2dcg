import argparse
import os
from collections import defaultdict
import string
import graphviz
from tqdm import tqdm
from unidecode import unidecode
from typing import List, Dict, Tuple

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

def render_graphviz(caption: str, formatted_tree: defaultdict, terminals: defaultdict, output_folder: str, filename: str):

    g = graphviz.Digraph('G', filename=os.path.join(output_folder, 'graphviz', f'{filename}.gv'))
    g.attr(label=caption)
    g.attr('node', shape='ellipse')

    set_of_nodes = set()
    def add_node(g: graphviz.Digraph, node: str, set_of_nodes: dict, is_terminal: bool = False):
        # just to control and to not duplicate creation of the node, 
        # I dont think this is a problem, but just for sanity

        def handle_punct(s: str, is_terminal: bool):
            if s[0] == "'" and s[-1] == "'":
                s = s[1:-1]
            if is_terminal:
                return s
            return f'punct_{map_puncts[s]}' if s in map_puncts else s

        if node not in set_of_nodes:
            set_of_nodes.add(node)
            label = '_'.join(node.split('_')[:-1])
            g.node(node, label=handle_punct(label, is_terminal))

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
            add_node(g, child, set_of_nodes, is_terminal=True)
            g.edge(parent, child)
    g.save()
                
    graphviz.render('dot', 'jpg', os.path.join(output_folder, 'graphviz', f'{filename}.gv'))
    os.remove(os.path.join(output_folder, 'graphviz', f'{filename}.gv')) # removes graphviz graph file


def parse_PennTreebank(tree, terminals: defaultdict, level=-1, label_id=0):

    def remove_punct(text):
        puncts = string.punctuation.replace('_', '') + '«»'
        spaces = ' ' * len(puncts)
        text_punct_removed = text.translate(str.maketrans(puncts, spaces)).replace(' ', '')
        return f"'{text}'" if len(text_punct_removed) == 0 else text_punct_removed

    remove_extra_dash = lambda label: label[:-1] if len(label) > 1 and label[-1] == '-' and label[-2].isalpha() else label 

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
            label = tree[:idx].strip().split(':')
            
            if len(label) > 1:
                label = label[1].lower()
                label = remove_extra_dash(label)
                label = f'{label}_{label_id}'
                label_id += 1
            else:
                assert len(label) == 1
                label = label[0]
                label = remove_extra_dash(label)
                label = f'{label}_{label_id}'
                label_id += 1

            if tree[idx] == ')' and len(remove_punct(tree[:idx].strip().split(' ')[-1])) > 0: # is leaf
                leaf = remove_punct(tree[:idx].strip().split(' ')[-1].lower())
                leaf = f'{leaf}_{label_id}'
                label_id += 1
                terminals[label].append(leaf)

        return [(label, level)] + parse_PennTreebank(tree[idx:].strip(), terminals, level, label_id)


def format_tree(tree):

    formatted_tree = defaultdict(list)

    _, level = tree[0]
    assert level == 0

    stack = [tree.pop(0)]

    while len(tree) > 0 or len(stack) > 1:

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
            print('Unexpected scenario!')
            exit()

    return formatted_tree


def format_save_dcg(formatted_tree: defaultdict, terminals: defaultdict, rule2sentence_tracker: defaultdict, output_folder: str, identifier: str):
    """
    TOFIX Tracks the sentences where each rule occurs.
    Parameters:
      rule2sentence_tracker - A dictionary (defaultdict(set)) mapping the rule to a list of sentence code (number followed by an id, e.g, #4213 CF999-1).
                     This will be used later to save the original annotation to a file separated by rules.
      header - Header of the annotated sentence.
    """


    def process_non_terminal(non_terminal: str, terminals_to_add: dict = None):

        if non_terminal in map_puncts:
            left = f'punct_{map_puncts[non_terminal]}'
            right = f"'{non_terminal}'" # map_puncts[non_terminal]
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
        dcg_rule = f"{left} --> {', '.join(right)}."
        dcg.append(dcg_rule)
        rule2sentence_tracker[dcg_rule].add(identifier.split('_')[0]) # Only the number part, without the #

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

    with open(os.path.join(output_folder, 'dcgs', f"{identifier}.dcg"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(dcg))

def save_rule2sentence_tracker(file_path: str, rule2sentence_tracker: defaultdict, output_folder: str) -> None:

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read()

    lines = lines.split('#')
    lines = [line for line in lines if len(line) > 0] # remove some empty lines
    lines = {line.split(' ')[0]: line for line in lines} # make a hash to access in O(1)
    

    # Due to long rules, handle filenames that can be longer than the allowed by the OS
    max_filename_length = 64 # considering only the dcg_rule length

    # Counts the truncated filenames frequency
    filename_counter = defaultdict(int)
    for dcg_rule in rule2sentence_tracker:
        shortened_dcg_rule = dcg_rule[:max_filename_length]
        filename_counter[shortened_dcg_rule] += 1
    
    duplicated_filenames_ids = defaultdict(int)
    filename_mapping = {}
    for dcg_rule in rule2sentence_tracker:
        shortened_dcg_rule = dcg_rule[:max_filename_length]
        if filename_counter[shortened_dcg_rule] == 1:
            if len(dcg_rule) > max_filename_length:
                filename_mapping[dcg_rule] = f"{dcg_rule}_truncated.ptb"
            else:
                filename_mapping[dcg_rule] = f"{dcg_rule}.ptb"
        else:
            # handle conflicts
            filename_mapping[dcg_rule] = f'{shortened_dcg_rule}_truncated_id_{duplicated_filenames_ids[shortened_dcg_rule]}.ptb'
            duplicated_filenames_ids[shortened_dcg_rule] += 1

    for dcg_rule, sentences_number in tqdm(rule2sentence_tracker.items()):

        with open(os.path.join(output_folder, 'sentences_by_rule', filename_mapping[dcg_rule]), 'w', encoding='utf-8') as f:
            f.write(f'{len(sentences_number)} sentence(s) containing the rule: {dcg_rule}\n\n' + ''.join(['#' + lines[sn] for sn in sentences_number]))

def read_PennTreebank(file_path: str, output_folder: str, graphviz: bool):

    with open(file_path, 'r', encoding='utf-8') as f:
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

    rule2sentence_tracker = defaultdict(set)
    for header, tree in tqdm(trees):

        identifier = '_'.join(header[1:].split(' ')[:2])

        terminals = defaultdict(list)
        parsed_tree = parse_PennTreebank(tree, terminals)
        formatted_tree = format_tree(parsed_tree)
        format_save_dcg(formatted_tree, terminals, rule2sentence_tracker, output_folder, identifier)
        
        if graphviz:
            render_graphviz(header, formatted_tree, terminals, output_folder, filename=identifier)

    save_rule2sentence_tracker(file_path, rule2sentence_tracker, output_folder)
        

def read_format_save(file_format: str, file_path: str, output_folder: str, graphviz: bool):

    if file_format == 'PennTreebank':
        return read_PennTreebank(file_path, output_folder, graphviz=graphviz)
    else:
        print('File format not implemented yet.')
        exit()


def join_dcgs(file_path: str, output_file_path: str):

    filenames = [f for f in os.listdir(file_path) if f.endswith('.dcg')]

    rules = defaultdict(int)
    terminals = []

    for filename in tqdm(filenames):

        filename = os.path.join(file_path, filename)

        with open(filename, 'r', encoding='utf-8') as f:
            data = f.readlines()
        data = [d.strip() for d in data]

        terminals += [d for d in data if '[' in d]
        
        non_terminals = [d for d in data if '[' not in d]
        for nt in non_terminals:
            if nt not in rules:
                rules[nt] = {'freq': 0, 'sentence_freq': 0}
            
            rules[nt]['freq'] += 1

        for nt in set(non_terminals):
            rules[nt]['sentence_freq'] += 1

    print(f'Number of non terminal rules: {sum([freq["freq"] for _, freq in rules.items()])}')
    print(f'Number of unique non terminal rules: {len(rules)}')
    print(f'Number of terminal rules (it can have more than one terminal per rule): {len(terminals)}')

    # non terminal
    # group by left to compute the probs
    grouped_left = defaultdict(list)
    for r, freq in rules.items():
        grouped_left[r.split(' --> ')[0]].append((r, freq))

    for right, grouped_rules in grouped_left.items():
        n = sum([freq['freq'] for _, freq in grouped_rules])
        for i in range(len(grouped_rules)):
            grouped_rules[i] = (grouped_rules[i][0], grouped_rules[i][1]['freq'], grouped_rules[i][1]['sentence_freq'], grouped_rules[i][1]['freq'] / n) 
    
    rules = []
    for right, grouped_rules in grouped_left.items():
        rules += grouped_rules
    rules.sort(key=lambda x: (x[1], x[3]), reverse=True)
    non_terminals_output = [f"{r}\t\t%freq: {c}; sentence_freq: {s}; prob: {f'{p:.6f}'.replace('.', ',')}" 
                            for r, c, s, p in rules]
    # sorting to group the rules by its initials (SWI-Prolog warns about this)
    # non_terminals_output.sort(key=lambda x: x.split(' --> ')[0])

    # terminal
    terminal_rules = defaultdict(list)
    for t in terminals:
        t = t[:-1] # remove last dot
        left = t.split(' --> ')[0]
        right = t.split(' --> ')[1].split(' | ')
        right = [x[1:-1] for x in right] # remove brackets
        terminal_rules[left] += right

    terminal_output = []
    for left, right in terminal_rules.items():
        right = list(set(right))
        right = [f'n{r}' if r[0].isnumeric() else r for r in right]
        right.sort()
        right = ' | '.join([f'[{r}]' for r in right])
        terminal_output.append(f'{left} --> {right}.')
    # sorting to group the rules by its initials (SWI-Prolog warns about this)
    # terminal_output.sort(key=lambda x: x.split(' --> ')[0])

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write('%\n% NON TERMINALS\n%\n')
        f.write('\n'.join(non_terminals_output))
        f.write('\n%\n% TERMINALS\n%\n')
        f.write('\n'.join(terminal_output))


def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str, help='File path in the specified format.', 
                        required=True)
    parser.add_argument('--file_format', type=str, help='File format.', 
                        choices=['VISL', 'PennTreebank', 'TigerXML'], required=True) # Only PennTreebank is available
    parser.add_argument('--output_folder', type=str, help='Output folder.', 
                        default='output', required=True)
    parser.add_argument('--graphviz', action='store_true',
                        help='A boolean switch to render the tree in graphviz')
    args = parser.parse_args()

    return args


def main():

    # This snippet is to convert the original data downloaded from 
    # https://www.linguateca.pt/Floresta/corpus.html#download -> CETENFolha -> formato PennTreebank
    # to utf8. Also, some bad format of the annotations were fixed.
    #
    # original_filename = '../dataset/Bosque_CF_8.0.PennTreebank.ptb'
    # filename =          '../dataset/Bosque_CF_8.0.PennTreebank_utf8.ptb'
    #
    # This files was loaded and saved as utf-8. Then it was fixed by hand some issues
    # with open(original_filename, 'r', encoding='cp1252') as f:
    #     data = f.read()
    #
    # with open(filename, 'w', encoding='utf-8') as f:
    #     f.write(data)

    args = get_args()

    os.makedirs(args.output_folder)

    # To store the graphviz files
    os.makedirs(os.path.join(args.output_folder, 'graphviz'))

    # To store the DCG of each sentence
    os.makedirs(os.path.join(args.output_folder, 'dcgs'))

    # To store the sentence of each DCG rule
    os.makedirs(os.path.join(args.output_folder, 'sentences_by_rule'))

    # Read the file in the specified format, process each sentence in a DCG format then save it individually.
    read_format_save(args.file_format, args.file_path, args.output_folder, args.graphviz)

    # Join all individual DCG files into one along with its statistics
    output_filename = '.'.join(args.file_path.split(os.sep)[-1].split(".")[:-1])
    join_dcgs(os.path.join(args.output_folder, 'dcgs'), 
              os.path.join(args.output_folder, f'{output_filename}.dcg'))

if __name__ == '__main__':
    main()


