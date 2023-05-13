# Pokemon Showdown Bot
A Pokémon battle bot that can play battles on [pokemonshowdown.com](https://pokemonshowdown.com/).

The bot is (for now) strictly rule-based, and it is currently implemented only for single battles in the [Gen 4] Random Battle format. 

It is written in Python (version 3.10) and [poke-env](https://github.com/hsahovic/poke-env) library was used for interfacing with showdown's websocket protocol and creating the main agent.

I'm trying to constantly add more features and (slowly) keep it updated, but note that it is just a project made for fun in my spare time. 

## Overview

The bot is made out of different modules:

### `app.py`
This is the main loop. It creates a bot, sends a challenge to showdown's server and then updates the event loop to keep track on everything that's happening.

### `AverageAI.py`
This module holds the **main agent** of the bot, `AverageAI`, which is a class inheriting from `Player`. `Player` has one abstract method, `choose_move(self, battle: Battle) -> str`, which is used at every query of the main loop to read data from a `Battle` object and return a move order. To learn more about agents, take a look at `poke-env`'s [documentation](https://poke-env.readthedocs.io/en/stable/max_damage_player.html#creating-a-player). 

The brain of the AI is a **point evaluation system** for both your current pokemon and the rest of your available team. It is carried out by the `should_i_switch` and `attack` methods. The evaluation has two possible outcomes: 
1) Find the best switch (if any) and switch out; 
2) If not, choose the best move (attacking or status) from your current pokemon.

The switch value calculation is performed over the opponent by the `find_best_switch` method, comparing all of your team with your current pokemon. For the current pokemon (and all other pokemon's) moves evaluation, the AI relies on the `evaluate_move` method.
```
choose_move
        ├── should_i_switch ──> create_order(switch)
        |          ├── current_pokemon_value
        |          └── find_best_switch
        |
        └── attack ──> create_order(best_move)
                └── evaluate_move
```
The pokemon evaluation (`find_best_switch` and `current_pokemon_value`) is based on a lot of factors: type advantage, current hp, atk-def ratio, moves, opponent's possible advantages (such as supereffective moves) and so on. The move evaluation (`evaluate_move`) on the other hand is aimed to find the best move for the current turn (attacking, status, healing, boost, hazards) based on the current battleground situation, current hp, opponent condition and other special cases. <p>For now, even if a lot of variables are taken into account, it's still an only half-decent and not too smart AI, hence the name :)

### `BattleUtilities.py`
A list of functions and utilities for calculation of damage, pokémon stats, boost multipliers, abilities and items, and other useful stuff.

### `OdditiesUtilities.py`
TODO: will keep all the oddities, special cases and peculiar moves and pokemon (such as: Shedinja, the sweep counter, etc.) to reduce complexity from the `AverageAI` module.

### `VirtualTeam.py`
A class used to create a virtual instance of the opponent team. It is used as a helper to get information about the opponent team and current opponent state. 

### `VirtualPokemon.py`
A class used to create a virtual instance of a single (opponent) pokemon. All the new pokemon instances are added to the `VirtualTeam`. In the constructor, it reads by default a `.json` data file used to store information about the opponent pokemon, and their possible moves and abilities. The data is referenced and adapted from the [pkmn/randbats](https://github.com/pkmn/randbats) repository for showdown random battles. The class holds a bunch of helper functions to get info about possible or assured moves (if you've already seen all 4 moves), abilities, items and so on.


## How to use
Clone into the repository and install dependencies:
```
git clone https://github.com/EnrcDamn/PokemonShowdownBot
cd PokemonShowdownBot
pip install -r requirements.txt
```
Register an account on [pokemonshowdown.com](https://pokemonshowdown.com/), then set up `player_configuration` with your account credentials `("your_username", "your_password")` in `app.py` and run it:
```
python .\app.py --verbose
```
You must specify `--verbose` or `--no-verbose` as an argument, depending if you want to display the log prints and live messages about the game status.


## State of work
The preferred format for the time being would be **[Gen 4] Random Battle**, but it can achieve decent results in [Gen 4] OU as well.

Gen 5 will be probably implemented as well, but for now it not supported.

Some form of reinforcement learning and "real" AI _might_ be implemented as well, sooner or later. Maybe to train the bot to behave differently (predict?) based on different ladder levels, but it would only be an integration over the rule-based approach. I think the full RL approach would be too weak for the number of variables and special cases a game like Pokémon has, and not as fun too :)

#### Future improvements:
- Handle odd moves behavior and combined moves (e.g. Sunny Day + Solar Beam);
- Implement other generations, starting from Gen 5;
- Implement double battles;
- Implement predicts.