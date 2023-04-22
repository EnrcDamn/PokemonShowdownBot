# Pokemon Showdown Bot
A Pokémon battle bot that can play battles on [pokemonshowdown.com](https://pokemonshowdown.com/).

The bot is strictly rule-based, and it is currently implemented only for single battles in the [Gen 4] Random Battle format. 

It is written in Python (version 3.10) and it uses the [poke-env](https://github.com/hsahovic/poke-env) library for interfacing with showdown's websocket protocol and creating the main agent.

I'm trying to constantly add more features and (slowly) keep it updated, but note that it is just a project made for fun in my spare time. 

## Overview

The bot is made of different modules:

| `app.py` |
| :--- |
| This is the main loop. It creates a bot, sends a challenge to showdown's server and then updates the event loop to keep track on everything that's happening. |

| `AverageAI.py` |
| :--- |
| <p>This module holds the main agent of the bot, `AverageAI`, which is a class inheriting from `Player`. `Player` has one abstract method, `choose_move(self, battle: Battle) -> str`, which is used to read data from a `Battle` object and return a move order. To learn more about agents, take a look at `poke-env`'s [documentation](https://poke-env.readthedocs.io/en/stable/max_damage_player.html#creating-a-player). <p>The brain of the AI is a point evaluation system for both your current pokemon and the rest of your available team. It is carried out by the `should_i_switch` and `attack` methods. The evaluation has two possible outcomes: <p>1) Find the best switch (if any) and switch out. <p>2) If not, choose the best move (attacking or status) from your current pokemon; <p>The switch value calculation is performed by the `find_best_switch` method, comparing all of your team with your current pokemon.<p> For the current pokemon (and all other pokemon's) moves evaluation, the AI relies on the `evaluate_move` method.<p> The move evaluation `evaluate_move` on the other hand is aimed to find the best move for the current turn (attacking, status, healing, boost, hazards) based on the current battleground situation, current hp, opponent condition and other special cases. <p>For now, even if a lot of variables are taken into account, it's still an only half-decent and not too smart AI, hence the name. :) |
```
choose_move
        ├── should_i_switch ──> create_order(switch)
        |          ├── current_pokemon_value
        |          └── find_best_switch
        |
        └── attack ──> create_order(best_move)
                └── evaluate_move
```

| `BattleUtilities.py` |
| :--- | 
| A list of functions and utilities for calculation of damage, pokémon stats, boost multipliers, abilities and items, and other useful stuff. |

| `OdditiesUtilities.py` |
| :--- |
| TODO: will keep all the oddities, special cases and peculiar moves and pokemon (such as: Shedinja, the sweep counter, etc.) to reduce complexity from the `AverageAI` agent. |

| `VirtualTeam.py` |
| :--- |


| `VirtualPokemon.py` |
|---|

## How to use
Clone into the repository and install dependencies:
```
git clone https://github.com/EnrcDamn/PokemonShowdownBot
cd PokemonShowdownBot
pip install -r requirements.txt
```



## State of work
The preferred format for the time being would be **[Gen 4] Random Battle**, but it can achieve decent results in [Gen 4] OU as well.

Gen 5 will be probably implemented as well, but for now it not supported.