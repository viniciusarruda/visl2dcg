import json
import graphviz

with open('formatted.json', 'r', encoding='utf-8') as f:
    visl_content = json.load(f)


g = graphviz.Digraph('G', filename='hello.gv')
g.edge('Hello', 'World')
# g.view()
graphviz.render('dot', 'png', 'spam.gv')

for ext, tree_sentences in visl_content.items():
    for ts in tree_sentences:
        xs = list(ts.items())
        assert len(xs) == 1
        sentence, trees = xs[0]
        # for ax, tree in trees.items():