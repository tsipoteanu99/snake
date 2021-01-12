import json
import sys

''' 
    JSON Unpacking:
    Am folosit modulul json pentru a face load la stringul din fisierul de config si pentru a-l transforma intr-un dictionar.
    Am folosit modulul sys pentru a lua datele argumentului argv[1] de la linia de comanda, adica fisierul json.
    La final am salvat toate datele din fisierul de config in niste variabile pentru a manevra mai usor datele.
'''


def unpack_json():
    with open(sys.argv[1], 'r') as f:
        contents = f.read()
    cfg = json.loads(contents)
    return cfg


config = unpack_json()
borderless = config['borderless']
obstacles = [tuple(x) for x in config['obstacles']]
width = config['table_size'][0]
height = config['table_size'][1]

print("Borderless:", borderless)
print("Obstacles:", obstacles)
print("Width:", width)
print("Height:", height)
