
# o numero de tags p e t não estão consistentes.. então não dá para confiar nelas

import re
import json

# original_filename = 'Bosque_CF_8.0.ad.visl.txt'
filename = 'Bosque_CF_8.0.ad.visl_utf8.txt'

# This files was loaded and saved as utf-8. Then it was fixed by hand some issues
# with open(original_filename, 'r', encoding='cp1252') as f:
#     data = f.read()

# with open(filename, 'w', encoding='utf-8') as f:
#     f.write(data)

# The issues below were fixed by hand in the utf8 file version
# This seems to be an error, need to edit, removing the <s> and </s>
#data = data.replace("\n</s>\n<s>\n&&\nA", "&&\nA")

# Another formatting error
#data = data.replace(".\n\nSOURCE:", ".\n\n</s>\n</p>\n<p>\n<s>\n\nSOURCE:")

# There was other typos in the file, that was not specified here in the code, and they were fixed.

with open(filename, 'r', encoding='utf-8') as f:
    data = f.read()
data = data.strip()

# foco em fazer rapido e iterar para ver se é isso msm: 
# - coletar todas as arvores
# - interpretar elas de alguma forma, sem adentrar na linguistica, apenas para saber quando um item é diferente de outro
# - com isso, computar frequencia de regras
# - pronto, vc vai ter as estatisticas.. faz um sisteminha simples baseado em estatistica (frequencia)
# - da pra fazer um sistema de inferencia e testar.. 


sentence_idx = 0
visl_content = {}

def process_s_content(s_content):

    def handdle_A(s_content_A):
        s_content_A = s_content_A.strip()
        return s_content_A.split('\n')

    global sentence_idx
    sc = {}

    s_content_splited = s_content.split('\n')
    s_content_splited = s_content_splited[1:] # removing header
    sentence = ' '.join(s_content_splited[0].split(' ')[1:]) # removing CP# code
    s_content = '\n'.join(s_content_splited[2:])

    i = 1
    while True:
        if f'&&\nA{i+1}' in s_content:
            s_content_splited = s_content.split(f'&&\nA{i+1}')
            assert len(s_content_splited) == 2
            sc[f'{sentence_idx}_A{i}'] = handdle_A(s_content_splited[0])
            s_content = s_content_splited[1]
        else:
            sc[f'{sentence_idx}_A{i}'] = handdle_A(s_content)
            break

        i += 1

    sentence_idx += 1
    return {sentence: sc}


def process_ext_content(ext_content):

    content = []

    while True:

        match = re.search('<s>', ext_content)

        if match is None:
            break

        _, start_content = match.span()

        match = re.search('</s>', ext_content)
        end_content, end_tag = match.span()

        s_content = ext_content[start_content:end_content]

        content.append(process_s_content(s_content.strip()))

        ext_content = ext_content[end_tag:]
    
    return content


while data != '':

    match = re.search('<ext', data)
    start_tag, _ = match.span()
    match = re.search('>', data)
    _, end_tag = match.span()
    
    ext_attributes = data[start_tag:end_tag]
    assert ext_attributes not in visl_content
    start_content = end_tag

    match = re.search('</ext>', data)
    end_content, end_tag = match.span()

    ext_content = data[start_content:end_content]
    visl_content[ext_attributes] = process_ext_content(ext_content.strip())

    data = data[end_tag:]

with open('formatted.json', 'w', encoding='utf-8') as f:
    json.dump(visl_content, f, indent=4, ensure_ascii=False)
