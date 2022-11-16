import json
from VirtualPokemon import VirtualPokemon
from ParseUtilities import parse_string
  
class VirtualTeam:
    def __init__(self):
        f = open("gen4randomteams.json")
        self.data = json.load(f)
        f.close()
        self.pokemon_team = []
    
    def add_pokemon(self, pokemon_name):
        for pokemon in self.pokemon_team:
            if pokemon_name == pokemon.get_name():
                return
        self.pokemon_team.append(VirtualPokemon(pokemon_name, self.data))

    def get_pokemon(self, pokemon_name):
        for pokemon in self.pokemon_team:
            if pokemon_name == pokemon.get_name():
                return pokemon
        return None
    
    def get_pokemon_list(self):
        return self.pokemon_team
    
    def print_team(self):
        for pokemon in self.pokemon_team:
            pokemon.print()

    def update_team(self, battle):
        for name, pokemon in battle.opponent_team.items():
            # for i, char in enumerate(name):
            #     if char == " ":
            #         name = parse_string(name[i+1:])
            #         break
            self.add_pokemon(pokemon.species)
            virtual_pokemon = self.get_pokemon(pokemon.species)
            for move_name, _ in pokemon.moves.items():
                virtual_pokemon.set_move(move_name)