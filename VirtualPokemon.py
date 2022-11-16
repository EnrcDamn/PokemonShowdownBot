
class VirtualPokemon:
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.possible_abilities = self.data[name]["abilities"]
        self.possible_items = self.data[name]["items"]
        self.possible_moves = self.data[name]["moves"]
        self.unlikely_moves = []
        self.moves = []
        if len(self.possible_moves) <= 4:
            self.moves = self.possible_moves
        self.item = ""
        self.ability = ""
        if len(self.possible_items) == 1:
            self.item = self.possible_items[0]
        if len(self.possible_abilities) == 1:
            self.ability = self.possible_abilities[0]
    
    def get_name(self):
        return self.name
    
    def get_possible_moves(self):
        return self.possible_moves
    
    def get_possible_abilities(self):
        return self.possible_abilities
    
    def get_possible_items(self):
        return self.possible_items
    
    def get_moves(self):
        return self.moves
    
    def get_ability(self):
        return self.ability

    def get_item(self):
        return self.item
    
    def set_move(self, move):
        if move not in self.moves:
            self.moves.append(move)
            if move not in self.possible_moves:
                print(f"Warning: the move {move} shouldn't be an available candidate")
    
    def add_unlikely_move(self, move):
        if move not in self.unlikely_moves:
            self.unlikely_moves.append(move)
            if move not in self.possible_moves:
                print(f"Warning: the move {move} shouldn't be an available candidate")
    
    def set_ability(self, ability):
        self.ability = ability
        if ability not in self.possible_abilities:
            print(f"Warning: the ability {ability} shouldn't be an available candidate")

    def set_item(self, item):
        self.item = item
        if item not in self.possible_items:
            print(f"Warning: the item {item} shouldn't be an available candidate")
    
    def print(self):
        print(self.name)
        print(self.possible_abilities)
        print(self.possible_items)
        print(self.possible_moves)
        print(self.moves)
        print(self.item)
        print(self.ability)