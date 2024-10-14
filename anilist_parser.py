from bs4 import BeautifulSoup
from openpyxl import Workbook
from difflib import SequenceMatcher
import random
import numpy as np
from scipy.integrate import quad
import matplotlib.pyplot as plt
import math

# Parsing list
animes = []
lookup = {}
wb = Workbook()
ws = wb.active
ws.append(['Title','Score', 'Progress', 'Status', 'Rank', 'New Score'])
with open("input.html") as fp:
    soup = BeautifulSoup(fp, 'html.parser')
    sections = soup.find_all(class_='list-wrap')
    i = 0
    for section in sections:
        if section.find(class_='section-name').text in ['Watching', 'Completed', 'Paused', 'Dropped', 'Planning']:
            for item in section.find_all(class_='entry row'):
                anime = [item.find(class_='title').a.text.strip(), int(item.find(label='Score')['score']), item.find(class_='progress').text.replace('+', '').strip(), item.find(class_='status').text.strip()]
                animes.append(anime)
                lookup[anime[0]] = i
                i += 1

# Simplifies data
def stringSimilar(a, b):
    conf = 0
    for x, y in zip(a, b):
        if x != y:
            break
        conf += 1
    if conf >= 12:
        return 1
    conf = conf ** 3 / 5000 + 0.02 * conf # Math witchcraft
    conf += SequenceMatcher(None, a, b).ratio() * 0.8
    return conf > 0.5

data = []
for i in range(0, 100):
    data.append([])
for anime in animes:
    if anime[1] != 0:
        data[anime[1] - 1].append([anime[0]])
for section in data:
    i = 0
    while i < len(section):
        head = section[i][0]
        remove = []
        k = i + 1
        while k < len(section):
            if stringSimilar(head, section[k][0]):
                section[i].append(section[k][0])
                del section[k]
            else:
                k += 1
        i += 1
data = [x for y in data for x in reversed(y)]

# Swaps sampled entries based on user input
for i in range(0, 100):
    a = random.randrange(len(data))
    b = random.randrange(len(data))
    while b == a:
        b = random.randrange(len(data))
    print(f'Better (y/n)? \n{data[a]}\n     >\n{data[b]}')
    str = input()
    while str != 'y' and str != 'n':
        str = input()
    if (a > b) ^ (str == 'y'):
        data[a], data[b] = data[b], data[a]

def integrand(x, a):
    return (x - x**2)**(a-1)

def cumintegrand(x, a, c):
    return integrand(x, a) / quad(integrand, 0, 1, args=(a,))[0] + c

inverse_table = []
a, c = 2.7, 0.3
for i in range(0, 500 + 1):
    inverse_table.append(quad(cumintegrand, 0, i / 500, args=(a, c))[0] / (1 + c))

# Approximates the inverse cdf of the rectangular beta distribution;
# This was fucking awful to create
def find_score(ratio):
    prev = inverse_table[0]
    i = 1
    while inverse_table[i] < ratio:
        prev = inverse_table[i]
        i += 1
    offset_ratio = (ratio - prev) / (inverse_table[i] - prev)
    return max(min(math.ceil((i - 1 + offset_ratio) / len(inverse_table) * 100), 100), 1)

# Normalizes data and adds it to the original list
for rank, names in enumerate(data):
    new_score = find_score(rank/(len(data) - 1))
    for name in names:
        entry = animes[lookup[name]]
        entry.append(len(data) - rank)
        entry.append(new_score)

# Saving data
try:
    for anime in animes:
        ws.append(anime)
    wb.save('./output.xlsx')
except:
    print('Output file is currently open.')