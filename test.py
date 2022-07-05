import json
import graphviz
import os
import re
from unidecode import unidecode

with open('formatted.json', 'r', encoding='utf-8') as f:
    visl_content = json.load(f)

def format_levels(tree):

    previous_level = None
    previous_t = None
    formatted_tree = []
    formatted_tree.append((0, 'N0', tree[0]))
    e = 1
    for t in tree[1:]:
        current_t = t
        level = 1
        while t[0] == '=':
            t = t[1:]
            level += 1

        if '\t' in t:

            if previous_level is not None and previous_level < level:
                print(previous_level, level)
                print(previous_t)
                print(current_t)
                exit()
            previous_level = None

            ts = t.split('\t')
            assert len(ts) == 2
            formatted_tree.append((level, f'N{e}', ts[0]))
            e += 1
            formatted_tree.append((level + 1, f'N{e}', ts[1]))
            previous_level = level
            previous_t = current_t
        else:

            if previous_level is not None and previous_level < level:
                print(previous_level, level)
                print(previous_t)
                print(current_t)
                exit()
            previous_level = None

            formatted_tree.append((level, f'N{e}', t))

        e += 1

    return formatted_tree


def make_graph(tree):

    tree = format_levels(tree)

    edges = {node_id: [] for _, node_id, _ in tree}

    parent = []
    for i in range(1, len(tree)):

        if tree[i][0] > tree[i-1][0]:
            assert tree[i-1][0] + 1 == tree[i][0]
            parent.append(tree[i-1][1])
        elif tree[i][0] < tree[i-1][0]:
            offset = tree[i-1][0] - tree[i][0]
            assert offset < len(parent) # tem sempre que restar um parent
            parent = parent[:-offset]

        edges[parent[-1]].append(tree[i][1])

    nodes = {node_id: label for _, node_id, label in tree}

    return nodes, edges


def draw(nodes, edges, filename, render=False):

    g = graphviz.Digraph('G', filename=filename)
    g.attr('node', shape='ellipse')

    for node_id, label in nodes.items():
        g.node(node_id, label=label.replace(':', '&#58;'))

    for parent_id, children_id in edges.items():
        for child_id in children_id:
            g.edge(parent_id, child_id)

    g.save()

    if render:
        graphviz.render('dot', 'png', filename)


def rulefy(nodes, edges, treebank_rules, treebank_lexicon):

    def standardize(label):
        if '(' in label and ')' in label:
            filtered_label = label.split('(')[0]
            if len(filtered_label) > 0:
                label = filtered_label
            # TODO print('Warning: e se tiver uma folha ou alguma outra coisa com parenteses? n deveria certo?'), tratei mais ou menos com o if acima, mas ainda posso estar deixando passar coisa
            # the if checking for leaf in the for loop below will handle this
        
        # removing all spaces in the label
        # I found the case "N<ARGS :pp" with space, I think this is incorrectly labelled
        # So I am considering "N<ARGS :pp" == "N<ARGS:pp"
        label = ''.join(label.split(' '))
        return label

    rules, lexicon = [], []
    for parent_id, children_id in edges.items():
        
        if len(children_id) > 0: # if the parent_id is not a leaf

            parent_label = standardize(nodes[parent_id])
            
            # if the child_id of the parent_id is not a leaf
            # it should have only one child
            if all([len(edges[child_id]) == 0 for child_id in children_id]):
                assert len(children_id) == 1
                lexicon.append([parent_label, *[standardize(nodes[child_id]) for child_id in children_id]])
            else:
                # TODO tem terminals sendo salvos nas regras, ve o pq isso ocorre, ta colocando que terminais tem filhos em algum lugar
                # pelo pouco que vi (o, todo, uma) são erros nas anotações
                rules.append([parent_label, *[standardize(nodes[child_id]) for child_id in children_id]])


    for rule in rules:
        
        left, right = rule[0], rule[1:]
        formatted_rule = f"{left} -> {' '.join(right)}"

        try:
            treebank_rules[formatted_rule] += 1
        except KeyError:
            treebank_rules[formatted_rule] = 1

    for terminal in lexicon:
        
        left, right = terminal[0], terminal[1:]
        formatted_terminal = f"{left} -> {' '.join(right)}"
        
        try:
            treebank_lexicon[formatted_terminal] += 1
        except KeyError:
            treebank_lexicon[formatted_terminal] = 1


def rules2dcg():

    terminals = ['e', 'o', 'assassino', 'uma', 'de', 'ser', 'ficar', 'politicamente', 'tiro', 'como', 'todo', 'em', 'mais']
    puncts = {
        ':': 'colon', 
        ')': 'closeParentheses',
        '«': 'ltlt',
        '»': 'gtgt',
        ',': 'comma',
        ';': 'semicolon',
        "'": 'prime',
        ']': 'closeBracket',
        '[': 'openBracket',
        '/': 'slash',
        '!': 'exclamation',
        '.': 'dot',
        '?': 'question',
        '-': 'dash',
        '(': 'openParentheses',
        '...': 'threeDots',
        '--': 'doubleDash'
    }

    map_format = {
        "-": "hyphen",
        ":": "colon",
        "<": "lt",
        ">": "gt",
        "/": "slash",
        "[": "openBracket",
        "]": "closeBracket",
        "+": "plus",
        "&": "and"
    }

    map_lexicon = {
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
        '?': 'question',
        '(': 'open_parentheses',
        '...': 'threeDots',
        '--': 'doubleDash',
        '%': 'percentage_symbol',
        '$': 'currency_symbol'
    }

    def format_token(token):

        if token in terminals:
            formatted_token = 'terminal'
        elif token in puncts:
            formatted_token = 'punct'
        else:
            token = token.split(':')[-1]
            xs = re.findall(r"[\w]+|[^\s\w]", token)

            formatted = [] #['rule']
            for item in xs:
                if item in map_format:
                    formatted.append(map_format[item])
                else:
                    formatted.append(item)
            formatted_token = '_'.join(formatted)

        return formatted_token


    def format_lexicon(token):

        xs = re.findall(r"[\w]+|[^\s\w]", token)

        formatted = []
        for item in xs:
            if item in map_lexicon:
                formatted.append(map_lexicon[item])
            else:
                formatted.append(item)
        formatted_token = '_'.join(formatted)
    
        if formatted_token[0].isdigit():
            formatted_token = 'num_' + formatted_token

        return formatted_token.lower()

    with open('treebank_rules.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'Number of rules in the treebank_rules.json file: {len(data)}')

    formatted_terminals, formatted_puncts, formatted_rules = [], [], []
    for k in data.keys():
        ks = k.split(' -> ')
        assert len(ks) == 2
        left, right = ks[0], ks[1]
        right = right.split(' ')

        tokens = [left, *right]

        formatted_rule = []
        for token in tokens:
                
            if token in terminals:
                formatted_terminals.append(token)
            elif token in puncts:
                formatted_puncts.append(token)
            
            formatted_token = format_token(token)
            if formatted_token not in ['terminal', 'punct']:
                formatted_rule.append(formatted_token)
        
        if len(formatted_rule) > 0:
            assert len(formatted_rule) >= 2
            formatted_rule = f"{formatted_rule[0]} --> {', '.join(formatted_rule[1:])}."
            formatted_rules.append(formatted_rule)


    ## lexicon
    with open('treebank_lexicon.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'Number of entries in the treebank_lexicon.json file: {len(data)}')

    formatted_lexicon = []
    for k in data.keys():
        ks = k.split(' -> ')
        assert len(ks) == 2
        left, right = ks[0], ks[1]
        assert len(right.split(' ')) == 1
        assert left not in terminals and left not in puncts
        
        # TODO remover acento ainda

        # if '-' in right:
            # print(right)
        
        # if right.isalnum() and not right[0].isdigit():
        # formatted_lexicon.append(f"{format_token(left)} --> [{unidecode(right).lower()}].")
        formatted_lexicon.append(f"{format_token(left)} --> [{format_lexicon(right)}].")

    # len_data, len_before = len(data), len(formatted_lexicon)
    formatted_lexicon = list(set(formatted_lexicon))
    # len_after = len(formatted_lexicon)
    # print(len_data, len_before, len_after)
    # assert len_data == len_before == len_after

    formatted_rules = list(set(formatted_rules))

    formatted_terminals = list(set(formatted_terminals))
    formatted_puncts = [puncts[p] for p in list(set(formatted_puncts))]

    formatted_rules.sort()
    formatted_terminals.sort()
    formatted_puncts.sort()
    formatted_lexicon.sort()

    print(f'Number of entries in the formatted_rules list: {len(formatted_rules)}')
    print(f'Number of entries in the formatted_lexicon list: {len(formatted_lexicon)}')

    pl = ''

    pl += '\n%%%%%RULES%%%%\n\n'
    pl += '\n'.join(formatted_rules)

    # pl += '\n\n\n%%%%%TERMINALS%%%%\n\n'
    # pl += '\n'.join([f'terminal --> [{t}].' for t in formatted_terminals])

    # pl += '\n\n\n%%%%%PUNCTS%%%%\n\n'
    # pl += '\n'.join([f'punct --> [{p}].' for p in formatted_puncts])

    pl += '\n\n\n%%%%%LEXICON%%%%\n\n'
    pl += '\n'.join(formatted_lexicon)

    with open('data.pl', 'w') as f:
        f.write(pl)


treebank_rules, treebank_lexicon = {}, {}
for k, (ext, tree_sentences) in enumerate(visl_content.items()):
    for ts in tree_sentences:
        xs = list(ts.items())
        assert len(xs) == 1
        sentence, trees = xs[0]

        if len(trees) > 0:

            for ax, tree in trees.items():

                tree = ['sentence', tree[0]] + [f'={x}' for x in tree[1:]]
                # print(tree)
                # exit()
                try:
                    nodes, edges = make_graph(tree)
                except:
                    # print(sentence)
                    # print(tree)
                    # print(nodes)
                    # print(edges)
                    exit()

                # draw(nodes, edges, filename=f'output/{ax}.gv', render= ax == '5_A1')
                rulefy(nodes, edges, treebank_rules, treebank_lexicon)
        # break
    # break
    k += 1
    # if k == 150:
        # break

# treebank_rules = dict(sorted(treebank_rules.items(), key=lambda item: item[1], reverse=True))
with open('treebank_rules.json', 'w', encoding='utf-8') as f:
    json.dump(treebank_rules, f, indent=4, ensure_ascii=False, sort_keys=True)

with open('treebank_lexicon.json', 'w', encoding='utf-8') as f:
    json.dump(treebank_lexicon, f, indent=4, ensure_ascii=False, sort_keys=True)

rules2dcg()
# ignorar os erros do corpus por enquanto
# 1) ver video do finger que esta na aba
# 2) colocar tudo no formato do prolog -> colocar lendo o arquivo treebank_rules e treebank_lexicon e nao aqui direto (por enquanto)
# 3) conseguir rodar e verificar se uma sentença está na gramatica
#     da para testar se esta ok rodando todas as sentenças do corpus no sistema e deve dar True para todas!