import json
import graphviz
import os

with open('formatted.json', 'r', encoding='utf-8') as f:
    visl_content = json.load(f)

def format_levels(tree):

    formatted_tree = []
    formatted_tree.append((0, 'N0', tree[0]))
    e = 1
    for t in tree[1:]:
        
        level = 1
        while t[0] == '=':
            t = t[1:]
            level += 1

        if '\t' in t:
            ts = t.split('\t')
            assert len(ts) == 2
            formatted_tree.append((level, f'N{e}', ts[0]))
            e += 1
            formatted_tree.append((level + 1, f'N{e}', ts[1]))
        else:
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


def rulefy(nodes, edges, treebank_rules, treebank_lexicon, called):

    def standardize(label):
        if '(' in label and ')' in label:
            filtered_label = label.split('(')[0]
            if len(filtered_label) > 0:
                label = filtered_label
            # TODO print('Warning: e se tiver uma folha ou alguma outra coisa com parenteses? n deveria certo?'), tratei mais ou menos com o if acima, mas ainda posso estar deixando passar coisa
            # the if checking for leaf in the for loop below will handle this
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

called = 0
treebank_rules, treebank_lexicon = {}, {}
for ext, tree_sentences in visl_content.items():
    for ts in tree_sentences:
        xs = list(ts.items())
        assert len(xs) == 1
        sentence, trees = xs[0]

        if len(trees) > 0:

            for ax, tree in trees.items():

                try:
                    nodes, edges = make_graph(tree)
                except:
                    print(sentence)
                    print(tree)
                    print(nodes)
                    print(edges)
                    exit()

                draw(nodes, edges, filename=f'output/{ax}.gv', render= ax == '592_A1')
                rulefy(nodes, edges, treebank_rules, treebank_lexicon, called)
                called += 1
            
# treebank_rules = dict(sorted(treebank_rules.items(), key=lambda item: item[1], reverse=True))
with open('treebank_rules.json', 'w', encoding='utf-8') as f:
    json.dump(treebank_rules, f, indent=4, ensure_ascii=False, sort_keys=True)

with open('treebank_lexicon.json', 'w', encoding='utf-8') as f:
    json.dump(treebank_lexicon, f, indent=4, ensure_ascii=False, sort_keys=True)


ignorar os erros do corpus por enquanto
1) ver video do finger que esta na aba
2) colocar tudo no formato do prolog -> colocar lendo o arquivo treebank_rules e treebank_lexicon e nao aqui direto (por enquanto)
3) conseguir rodar e verificar se uma sentença está na gramatica
    da para testar se esta ok rodando todas as sentenças do corpus no sistema e deve dar True para todas!