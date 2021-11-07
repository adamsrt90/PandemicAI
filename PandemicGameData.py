import json
from random import shuffle
with open('./variables/cities.json','r') as f:
    allCities = json.load(f)
with open('./variables/player_cards.json','r') as f:
    playerCards = json.load(f)
with open('./variables/infection_cards.json','r') as f:
    infectionCards = json.load(f)