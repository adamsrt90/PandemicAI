from __future__ import annotations
import json
import os
from PandemicGameData import allCities, playerCards, infectionCards
from random import shuffle, sample
from collections import Counter
from abc import ABC, abstractmethod

# Game object will use builder pattern to create a game board, players, and decks
# The actions will use the command pattern to call the appropriate methods on the game board
# will log actions for the game and allow undo and for AI memory.
# imagine you set up game IRL. You'll pull out the deck, shuffle it, and then deal out the cards.
# we'll do things in the order we'd do IRL. 1 setup player, 2 setup board 3 deal out cards 4 start game


class Game(object):
    def __init__(self, number_of_players, number_of_AI=0, number_of_epidemics=4):
        # step 1: setup players
        self.turncounter = 1
        self.number_of_players = number_of_players
        self.number_of_AI = number_of_AI
        self.AvailableRoles = {"Scientist": [1],
                               "Medic": [2],
                               "Researcher": [3],
                               "Operations_Expert": [4],
                               "Contingency_Planner": [5],
                               "Quarantine_Specialist": [6]
                               }
        self.PlayerRoles = sample(self.AvailableRoles.keys(
        ), k=self.number_of_players + self.number_of_AI)
        self.Players = []
        self.gameCities = {}
        self.PlayerDeck_Discards = []
        self.InfectionDeck_Discards = []
        self.number_of_epidemics = number_of_epidemics
        self.CuredDiseases = []
        self.Outbreaks = 0
        self.EradicatedDiseases = []
        self.InfectionCubes = {
            'Red': 24,
            'Blue': 24,
            'Yellow': 24,
            'Black': 24
        }
        self.epidemicpulls = 0
        self.draw_states = {0: 2, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4}
        self.draw_requirements = self.draw_states[self.epidemicpulls]

    def create_players_cities_and_deck(self):
        self.GameState = GameState(game=self)
        # creates game players, decks, and cities
        self.PlayerDeck = PlayerDeck(playerCards, game=self)
        self.InfectionDeck = InfectionDeck(infectionCards, game=self)
        if self.number_of_players > 0:
            for i in range(self.number_of_players):
                self.Players.append(
                    Player(f'Player: {i+1}', self.PlayerRoles[i], game=self))
        if self.number_of_AI > 0:
            for i in range(self.number_of_AI):
                self.Players.append(
                    AiPlayer(f'AI: {i+1}', self.PlayerRoles[self.number_of_players + i], game=self))
        for player in self.Players:
            print(player.role)
        for city in allCities:
            self.gameCities[city[0]] = City(
                city[0], city[1], city[2], city[3], city[4], game=self)

    def set_items(self):
        # Now the number of players and AIs are set, roles assigned, and added to the "Game"number_of_AI
        # step 2: setup create decks and infect cities
        self.PlayerDeck.shuffle()
        self.InfectionDeck.shuffle()
        # deal out player cards
        for i in range(6-len(self.Players)):
            for player in self.Players:
                player.hand.append(self.PlayerDeck.draw(0))
        # add epidemic cards to PlayerDeck. Must be done AFTER dealing out player cards
        self.PlayerDeck.add_epidemic_cards()

        # infect cities
        for i in range(3):
            self.InfectionDeck.infect_city(3)
        for i in range(3):
            self.InfectionDeck.infect_city(2)
        for i in range(3):
            self.InfectionDeck.infect_city(1)
        for city in self.gameCities:
            print(self.gameCities[city].city_id, self.gameCities[city].cubes)

    # step 3: shuffle decks, deal out cards, infect cities

    def setup_game(self):
        self.create_players_cities_and_deck()
        self.set_items()
        self.GameState.save_state()

    def start_turn(self):
        player = iter(self.Players)
        while True:
            try:
                self.Turn = Turn(next(player), self.turncounter, game=self)
                self.Turn.start_turn()
            except StopIteration:
                self.start_turn()

        # set up infection cities. First 3 cities pulled get 3 cubes of its color
        # second three cities get 2 cubes of its color
        # third three cities get 1 cube of its color


class GameState:
    '''
    This is for the AI to know the state of the game after each action.

    The states will be a dictionary of the following:
    Number of Players
    Each City ID and their cube counts based on color
    Each City's Connections in the form of the connecting cities' ID. 
    Each Card ID in each player's hand
    Each Infection Card ID in the discard pile
    Each Player's Role
    Each Player's Current City
    Status of each disease
    Number of Epidemic cards in the deck


    '''

    def __init__(self, game=None):
        self.game = game
        self.game_state = {}

    def get_state(self):
        self.game_state['Number_Players'] = [len(self.game.Players)]
        self.game_state['City_Status'] = [[self.game.gameCities[city].city_id, self.game.gameCities[city].cubes,
                                           self.game.gameCities[city].total_cubes, self.game.gameCities[city].connection_ids] for city in self.game.gameCities]
        self.game_state['Player_Status'] = [[player.name, str(
            player.role), player.hand, player.location] for player in self.game.Players]
        self.game_state['Board_Status'] = [[self.game.turncounter,
                                            self.game.number_of_epidemics, self.game.PlayerDeck_Discards]]
        self.game_state['Infection_Status'] = [[self.game.InfectionDeck_Discards,
                                                self.game.InfectionCubes, self.game.epidemicpulls, self.game.Outbreaks]]
        self.game_state['Cure_Status'] = [
            self.game.CuredDiseases, self.game.EradicatedDiseases]

    def save_state(self):
        self.get_state()
        # save the game state to a json file.
        # will only save the last 25 game states
        # if 10 states have been saved, the oldest state will be deleted use os.path.getctime() to get the time of the oldest saved state
        # over
        file_list = os.listdir('./GameState/')
        file_path = [".GameState/{0}".format(x) for x in file_list]
        if len(file_list) > 25:
            oldest_file = min(full_path, key=os.path.getctime)
            os.remove(oldest_file)
            with open(f'./GameState/GameState{self.game.turncounter}.json', 'w') as f:
                json.dump(self.game_state, f, indent=4)
        else:
            with open(f'./GameState/GameState{self.game.turncounter}.json', 'w') as f:
                json.dump(self.game_state, f, indent=4)


class PlayerDeck(object):
    '''
    Will track its status and game board can check variables and alter as needed.
    '''

    def __init__(self, cards, game=None):
        self.game = game
        self.deck = cards
        self.discards = []
        self.deck_name = 'PlayerDeck'

    def __repr__(self):
        return f'{self.deck_name}'

    def shuffle(self):
        '''
        Shuffles the deck.
        '''
        shuffle(self.deck)

    def draw(self, index=None):
        '''
        Draws a card from the deck.
        '''
        if index is None:
            return self.deck.pop()
        else:
            return self.deck.pop(index)

    def chunk_cards(self, deck, epidemic_cards):
        # generator that chunks the cards into groups based on the number of epidemic cards
        for i in range(0, len(deck), round(len(deck)/epidemic_cards)):
            yield deck[i:i + round(len(deck)/epidemic_cards)]

    def add_epidemic_cards(self):
        '''
        The game rules state that the deck should be cut into equal sections equal to number of pandemic cards.
        Then each section has a pandemic card added. Each section is then shuffled.
        Then combine the sections back into one deck. Below mimics this behavior. 
        '''
        chunk_list = []
        for num, chunk in enumerate(self.chunk_cards(self.deck, self.game.number_of_epidemics)):
            chunk.append(["Epidemic", [5, 6, num+1]])
            shuffle(chunk)
            for item in chunk:
                chunk_list.append(item)

        self.deck = chunk_list


class Turn(object):
    '''
    this object will track the Player's actions for the turn and keep track of any outbreaks in a list
    The idea is that if the outbreak has already happened to a city in the list during that turn, it will skip. Prevents infinite feedback loops
    each turn the variables will reset 
    '''

    def __init__(self, player, turncounter, game=None):
        self.player = player
        self.turncounter = turncounter
        self.game = game
        self.current_outbreaks = []
        self.player_actions = 4
        self.done = False
        self.MoveReceiver = MoveReceiver()
        self.UpdateCardsReceiver = UpdateCardsReceiver()
        self.GeneralActionReceiver = GeneralActionReceiver()
        self.ActionInvoker = ActionInvoker()

    def start_turn(self):
        print(f'{self.player.name} is starting turn {self.turncounter}')
        self.player_action(action=input('What would you like to do? '))

    def player_action(self, action, target_city=None, target_player=None):
        '''
        This method will be called by the player object to perform an action.
        This method will call the command pattern below which handles the specifics of actions
        '''
        while self.player_actions > 0:
            try:
                if action == 'Move':
                    print(
                        f'You are in {self.player.location} and can move to {self.game.gameCities[self.player.location].connected_cities}')
                    self.target_city = input(
                        f'Where would you like to move to? ')
                    if self.target_city == "Cancel":
                        print(f'{self.player.name} has cancelled their move.')
                        self.player_action(action=input(
                            'What would you like to do? '))
                    else:
                        self.ActionInvoker.set_on_start(
                            Move(self.MoveReceiver, self.player, self.target_city, game=self.game))
                        self.ActionInvoker.perform_action()

                        if self.player_actions != 0:
                            print(
                                f'You have {self.player_actions} moves left!')
                            self.player_action(action=input(
                                'What would you like to do next? '))
                        else:
                            print(f'{self.player.name} has finished their turn.')
                            self.end_turn()

                elif action == 'Direct Flight':
                    print(
                        f'You are in {self.player.location} and can directly fly to {[i[0] for i in self.player.hand]}'
                    )
                    self.target_city = input(
                        f'Where you would like to fly to? '
                    )
                    if self.target_city == "Cancel":
                        print(f'{self.player.name} has cancelled their move.')
                        self.player_action(action=input(
                            'What would you like to do? '))
                    else:
                        self.ActionInvoker.set_on_start(
                            DirectFlight(self.MoveReceiver, self.player, self.target_city, game=self.game))
                        self.ActionInvoker.perform_action()

                        if self.player_actions != 0:
                            print(
                                f'You have {self.player_actions} moves left!')
                            self.player_action(action=input(
                                'What would you like to do next? '))
                        else:
                            print(f'{self.player.name} has finished their turn.')
                            self.end_turn()

                elif action == 'Charter Flight':
                    print(
                        f'You are in {self.player.location} and can only charter a flight if you have current city in {self.player.hand}'
                    )
                    self.target_city = input(
                        f'Where you would like to charter a flight to? '
                    )
                    if self.target_city == "Cancel":
                        print(f'{self.player.name} has cancelled their move.')
                        self.player_action(action=input(
                            'What would you like to do? '))
                    else:
                        self.ActionInvoker.set_on_start(
                            ShuttleFlight(self.MoveReceiver, self.player, self.target_city, game=self.game))
                        self.ActionInvoker.perform_action()
                        print(
                            f'{self.player.name} has moved to {self.target_city}')
                        if self.player_actions != 0:
                            print(
                                f'You have {self.player_actions} moves left!')
                            self.player_action(action=input(
                                'What would you like to do next? '))
                        else:
                            print(f'{self.player.name} has finished their turn.')
                            self.end_turn()

                elif action == 'Pass':
                    self.player_actions = 0
                    self.end_turn()
                else:
                    print('Invalid action!')
                    self.player_action(action=input('Try again? '))
            except Exception as e:
                print(e)

    def end_turn(self):
        '''
        This method will be called at the end of the turn.
        It will reset the player actions to 4 and then call the game object to end the turn.
        '''

        # for i in range(self.game.draw_requirements):
        #     card = self.player.deck.draw()
        #     if card[0] == 'Epidemic':
        #         #shuffle infection deck discard pile
        #         #place them on top, then draw

        print(self.player.hand)
        self.game.turncounter += 1
        self.game.GameState.save_state()
        return None


class InfectionDeck(object):
    '''
    Will track its status as well as the game board can check variables and alter as needed.
    '''

    def __init__(self, cards, game=None):
        self.game = game
        self.deck = cards
        self.deck_name = 'InfectionDeck'

    def __repr__(self):
        return f'{self.deck_name}'

    def shuffle(self):
        '''
        Shuffles the deck.
        '''
        shuffle(self.deck)

    def draw(self, index=None):
        '''
        Draws a card from the deck.
        '''
        if index is None:
            self.game.InfectionDeck_Discards.append(self.deck.pop())
            return self.deck.pop()
        else:
            self.game.InfectionDeck_Discards.append(self.deck.pop(index))
            return self.deck.pop(index)

    def infect_city(self, num_of_cubes=1):
        '''
        Infects a city with the color in on the card
        gives the city object the color which to infect itself.
        '''
        city_to_infect = self.draw()
        for city in self.game.gameCities:
            if city_to_infect[0] == city:
                self.game.gameCities[city].infect_self(
                    city_to_infect[2], num_of_cubes)


class City(object):
    def __init__(self, name, city_id, color, connected_cities, connection_ids, game=None):
        self.game = game
        self.name = name
        self.city_id = city_id
        self.color = color
        self.connected_cities = connected_cities
        self.connection_ids = connection_ids
        self.total_cubes = 0
        self.cubes = {
            "Blue": 0,
            "Yellow": 0,
            "Black": 0,
            "Red": 0
        }

        self.research_station = False

    def __repr__(self):
        return f'{self.name}'

    def infect_self(self, color, num_of_cubes):
        '''
        checks city total cubes and infects if less than 3
        '''
        if self.total_cubes < 3:
            self.cubes[color] += num_of_cubes
            self.total_cubes += num_of_cubes
            self.game.InfectionCubes[color] -= num_of_cubes
            if num_of_cubes > 1:
                print(
                    f'{self.name} has been infected with {num_of_cubes} {color} cubes.')
            else:
                print(
                    f'{self.name} has been infected with {num_of_cubes} {color} cube.')
        else:
            self.outbreak(color)

    def outbreak(self, color):
        '''
        infects all connected cities
        '''
        for connection in self.connected_cities:
            for city in self.game.gameCities:
                if connection == city.name:
                    city.infect_self(color)
                    break

    def treat_self(self, color):
        '''removes specified number of color cubes from self
        The command patter will handle when and how cities treat itself. 
        '''
        if color in self.game.CuredDiseases:
            self.game.InfectionCubes[color] += self.cubes[color]
            self.cubes[color] = 0
        else:
            self.game.InfectionCubes[color] += 1
            self.cubes[color] -= 1


class Player(object):
    def __init__(self, name, role, location="Atlanta", game=None):
        self.game = game
        self.name = name
        self.hand = PlayerHand(player=self)
        self.role = PlayerRole(self, role)
        self.location = location

    def __repr__(self):
        return f'{self.name}'

    def discard_card(self, card):
        self.hand.discard(card)


class AiPlayer(object):
    '''Will be virtually identical to the Player class but will deal with card's IDs instead of the card itself though pulled from same pool.'''

    def __init__(self, name, role, location='Atlanta', game=None):
        self.game = game
        self.name = name
        self.hand = PlayerHand(player=self)
        self.role = PlayerRole(self, role)
        self.location = location

    def __repr__(self):
        return f'{self.name}'


class PlayerHand(list):
    def __init__(self, player):
        self.player = player

    def discard(self, card):
        self.remove(card)
        self.player.game.PlayerDeck_Discards.append(card)


class PlayerRole:
    def __init__(self, player, role):
        self.player = player
        self.role = role

    def __repr__(self):
        rep = f'{self.role}'
        return rep


# This part will use the command pattern to build the games and process user inputs.
# converts complex commands into objects that can be passed when invoked.
# this is a command pattern.

'''
To excute a command, we'll need a player, their role, and the available actions.
We will load them from the actions.json file.

'''

# these will need heavy editing and updating based on the classes above.
# the game will be passed into these commands so it can access the global status of the game.


class PlayerAction(ABC):

    @abstractmethod
    def execute(self):
        pass


class Move(PlayerAction):
    def __init__(self, receiver: MoveReceiver, player, target_city, game=None):
        self.player = player
        self.target_city = target_city
        self.game = game
        self.receiver = receiver

    def execute(self):
        while True:
            try:
                if self.target_city in self.game.gameCities[self.player.location].connected_cities:
                    self.receiver.move_player(self.player, self.target_city)
                    print(
                        f'{self.player.name} has moved to {self.target_city}.'
                    )
                    self.game.Turn.player_actions -= 1
                    break

                else:
                    print(
                        f'{self.player.name} cannot move to {self.target_city}. Try another location or cancel.')
                    break

            except Exception as e:
                print(f'{e} happened in the Move Command')
                break


class DirectFlight(PlayerAction):
    def __init__(self, receiver: MoveReceiver, player=None, target_city=None, game=None):
        self.game = game
        self.player = player
        self.target_city = target_city
        self.receiver = receiver

    def execute(self):
        while True:
            try:
                if self.target_city in [i[0] for i in self.player.hand]:
                    self.receiver.move_player(self.player, self.target_city)
                    print(
                        f'{self.player.name} has moved to {self.target_city}.'
                    )
                    self.game.Turn.player_actions -= 1
                    #janky af but works. Uses the index of the list comprehension match to remove card from hand.
                    self.player.hand.discard(self.player.hand[[i[0] for i in self.player.hand].index(self.target_city)])
                    break
                else:
                    print(
                        f'{self.player.name} cannot move to {self.target_city}. Try another location or cancel.')
                    break
            except Exception as e:
                print(f'{e} happened in the Direct Flight Command')
                break


class CharterFlight(PlayerAction):
    def __init__(self, receiver: MoveReceiver, player=None, target_city=None):
        self.player = player
        self.target_city = target_city
        self.receiver = receiver

    def execute(self):
        if self.target_city in self.player.player_cards.keys():
            self.receiver.move_player(self.player, self.target_city)
        else:
            print('You cannot move to that city.')


class ShuttleFlight(PlayerAction):
    def __init__(self, receiver: MoveReceiver, player=None, target_city=None):
        self.player = player
        self.target_city = target_city
        self.receiver = receiver

    def execute(self):
        if self.player.player_location["Research"] and self.target_city['Research']:
            self.receiver.move_player(self.player, self.target_city)
        else:
            print('You cannot move to that city.')


class ShareKnowledge(PlayerAction):
    def __init__(self, receiver: UpdateCardsReceiver, player=None, target_player=None, city_card=None):
        self.player = player
        self.city_card = city_card
        self.target_player = target_player
        self.receiver = receiver

    def execute(self):
        # must check if both players in the same city
        # must check if receiving party has less than 7 cards
        # must check if either party's role is researcher
        # if not a scientist, must check if if they are in the city of the card to transfer
        if self.player.player_location == self.target_player.player_location:
            if self.player.role == 'Researcher' or self.target_player.role == 'Researcher':
                self.receiver.remove_card(self.player, self.city_card)
                self.receiver.add_card(self.target_player, self.city_card)
            elif self.player.player_location == self.city_card:
                self.receiver.remove_card(self.player, self.city_card)
                self.receiver.add_card(self.target_player, self.city_card)
            else:
                print(
                    "You must be in the same city as the card you wish to trade or trade with a Researcher")

        else:
            print('You cannot share knowledge.')


class DiscoverCure(PlayerAction):
    def __init__(self, receiver: UpdateCardsReceiver, player=None, card_type=None):
        self.player = player
        self.card_type = card_type
        self.receiver = receiver
        # if scientist, only need four of same color card
        # else need 5 of same card type
        # player location must have research station
        #will use collections module to check if the player has the required cards.
        #check the card amounts against player role and behave accordingly.
        

    def execute(self):
        pass


class Treat(PlayerAction):
    def __init__(self, receiver: GeneralReceiver, player):
        self.player = player
        self.target_player = target_player
        self.disease = disease
        self.receiver = receiver

    def execute(self):
        print('You have treated a disease!')


class BuildResearch(PlayerAction):
    pass


class PlayEventCard(PlayerAction):
    pass


class SpecialAction(PlayerAction):
    def __init__(self, receiver: GeneralActionReceiver):
        self.receiver = receiver

    def execute(self):
        print("Special action started!")
        self.receiver.special_action()


class MoveReceiver:
    '''
    The Move, DirectFlight, ShuttleFlight are all essentially the same. 
    This will update player status while the individual commands will check if possible.
    '''

    def move_player(self, player, target_location):
        self.player = player
        self.player.location = target_location


class UpdateCardsReceiver:
    '''
    Will be used when a player voluntarily discards or transfers a card. Shuttles and Direct Flights will handle them automatically because I'm lazy and incompetent.
    '''

    def remove_card(self, player, card):
        self.player = player
        self.card = card
        self.player.player_cards.remove(self.card)
        return self.player

    def add_card(self, player, card):
        self.player = player
        self.card = card
        self.player.player_cards.append(self.card)
        return self.player


class GeneralActionReceiver:
    '''
    This will perform the general action of the command given.
    For non-common actions.
    '''

    def special_action(self):
        print("Special Action completed!")


class ActionInvoker:
    '''
    Each action will have a start action and an ending action.
    End action will usually return the player to the game and update Player's status.
    '''
    _on_start = None
    _on_end = None

    def set_on_start(self, command: PlayerAction):
        self._on_start = command

    def set_on_end(self, command: PlayerAction):
        self._on_end = command

    def perform_action(self):
        if isinstance(self._on_start, PlayerAction):
            self._on_start.execute()


if __name__ == '__main__':
    game = Game(2, 2, 4)
    game.setup_game()
    game.start_turn()
