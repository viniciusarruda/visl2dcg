import json
import graphviz
import os

with open('formatted.json', 'r', encoding='utf-8') as f:
    visl_content = json.load(f)


def format_levels(tree):

    formatted_tree = []
    formatted_tree.append((0, 'N0', tree[0], False))
    e = 1
    for t in tree[1:]:
        
        level = 1
        while t[0] == '=':
            t = t[1:]
            level += 1
        
        if '\t' in t:
            ts = t.split('\t')
            assert len(ts) == 2
            formatted_tree.append((level, f'N{e}', ts[0], False))
            e += 1
            formatted_tree.append((level + 1, f'N{e}', ts[1], True))
        else:
            formatted_tree.append((level, f'N{e}', t, False))

        e += 1

    return formatted_tree

a2s = []
tn = 0
for ext, tree_sentences in visl_content.items():
    for ts in tree_sentences:
        xs = list(ts.items())
        assert len(xs) == 1
        sentence, trees = xs[0]

        if len(trees) > 0:

            for ax, tree in trees.items():

                g = graphviz.Digraph('G', filename=f'output/{tn}_{ax}.gv')
                g.attr('node', shape='ellipse')
                
                try:
                    tree = format_levels(tree)
                except:
                    print(sentence)
                    print(tree)
                    exit()
                for t in tree:
                    if t[3]: # is leaf
                        g.attr('node', shape='plaintext')
                        g.node(t[1], label=t[2].replace(':', '&#58;'))
                        g.attr('node', shape='ellipse')
                    else:
                        g.node(t[1], label=t[2].replace(':', '&#58;'))

                parent = []
                for i in range(1, len(tree)):
                    
                    if tree[i][0] > tree[i-1][0]:
                        parent.append(tree[i-1][1])
                    elif tree[i][0] < tree[i-1][0]:
                        parent.pop()

                    g.edge(parent[-1], tree[i][1])

                g.save()
            
            tn += 1


for tn in os.listdir('output'):
    graphviz.render('dot', 'png', f'output/{tn}')
