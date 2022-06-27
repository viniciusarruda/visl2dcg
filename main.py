
# o numero de tags s e t não estão consistentes.. então não dá para confiar nelas

import re
import json

filename = 'Bosque_CF_8.0.ad.visl.txt'

with open(filename, 'r', encoding='cp1252') as f:
    data = f.read()

with open('Bosque_CF_8.0.ad.visl_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(data)


vou ter que corrigir no arquivo msm.. tem jeito n
corrigir o que eu criei no utf8? vai no mais facil.. se o prof n aprovar,
ai vc deixa as correções aqui no codigomas isso é pessimo

foco em fazer rapido e iterar para ver se é isso msm: 
- coletar todas as arvores
- interpretar elas de alguma forma, sem adentrar na linguistica, apenas para saber quando um item é diferente de outro
- com isso, computar frequencia de regras
- pronto, vc vai ter as estatisticas.. faz um sisteminha simples baseado em estatistica (frequencia)
- da pra fazer um sistema de inferencia e testar.. 

exit()
data = data.strip()

# This seems to be an error, need to edit, removing the <s> and </s>
data = data.replace("\n</s>\n<s>\n&&\nA", "&&\nA")

# Another formatting error
data = data.replace(".\n\nSOURCE:", ".\n\n</s>\n</p>\n<p>\n<s>\n\nSOURCE:")

# eu acabei bugando uma coisa, preciso baixar de novo
# ai segue concertando via codigo msm..
# confirmar se tem o numero correto de arvores..
# depois que tera as arvores certas, comecar a interpretar o que esta querendo dizer aquilo
# concertar aqui.. é melhor via codigo msm
# ta faltando as quebras de s 


visl_content = {}

def process_s_content(s_content):

    def handdle_A(s_content_A):
        s_content_A = s_content_A.strip()
        return s_content_A.split('\n')

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
            sc[f'A{i}'] = handdle_A(s_content_splited[0])
            s_content = s_content_splited[1]
        else:
            sc[f'A{i}'] = handdle_A(s_content)
            break

        i += 1

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
