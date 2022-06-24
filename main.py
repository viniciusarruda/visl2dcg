
# o numero de tags s e t não estão consistentes.. então não dá para confiar nelas

import re
import json

filename = 'Bosque_CP_8.0.ad.visl.txt'

with open(filename, 'r', encoding='cp1252') as f:
    data = f.read()

data = data.strip()

visl_content = {}


def process_s_content(s_content):
    # tem uns #W #D e #E que eu to ignorando tbm, esta vindo com o titulo da frase.. n sei o que significa
    s_content = s_content.split('\n')

    s_content = s_content[1:] # removing header

    sentence = ' '.join(s_content[0].split(' ')[1:]) # removing CP# code

    assert s_content[1] == 'A1' # to be ignored, since all sentences have this A1

    return {sentence: s_content[2:]}



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

with open('out.json', 'w', encoding='utf-8') as f:
    json.dump(visl_content, f, indent=4, ensure_ascii=False)
