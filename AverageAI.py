import math
from poke_env.player.player import Player
from BattleUtilities import get_opponent_fnt_counter, get_my_fnt_counter
from BattleUtilities import i_am_faster, calculate_damage
from BattleUtilities import calculate_atk, calculate_spa, calculate_def
from BattleUtilities import calculate_spd, calculate_current_hp
from BattleUtilities import FAINTED
from VirtualTeam import VirtualTeam
from poke_env.environment.move import Move, MoveCategory
from poke_env.environment.weather import Weather
from poke_env.environment.side_condition import SideCondition
from poke_env.environment.status import Status
from poke_env.environment.effect import Effect
from poke_env.environment.pokemon_type import PokemonType

class AverageAI(Player):

    def __init__(self, verbose, *args, **kwargs):
        self.verbose = verbose
        super().__init__(*args, **kwargs) 
        self.sweep_utilities = {
            "sweep_counter": 0,
            "sweep_turn": 0
        }
        self.opponent_team = VirtualTeam()
    
    def choose_move(self, battle):
        self.opponent_team.update_team(battle)
        if self.verbose:
            print("\n#################################")
            print(f"TURN {battle.turn}")
            print(f"My Pokemon: {battle.active_pokemon}")
            print(f"Opponent Pokemon: {battle.opponent_active_pokemon}")
            print("#################################")
        if not battle.available_moves:
            return self.create_order(self.find_best_switch(battle, is_forced=True)[0])
        ohko_move = self.kill_if_ohko(battle)
        if ohko_move is not None:
            return self.create_order(ohko_move)
        switch = self.should_i_switch(battle)
        if switch is not None:
            if self.verbose:
                print(f"Switch to: {switch.species}\n")
            return self.create_order(switch)
        return self.attack(battle)


    def attack(self, battle):
        best_move = battle.available_moves[0]
        best_value = 0 # dumb init
        ohko_moves = []
        for move in battle.available_moves:
            # look if there are any ohko moves and save them in a list
            if self.can_kill(move, battle.active_pokemon, battle.opponent_active_pokemon, battle):
                ohko_moves.append(move)
            # normal calculation for best_move
            value = self.evaluate_move(
                move,
                battle.active_pokemon,
                battle.opponent_active_pokemon,
                battle
                )
            if value > best_value:
                best_value = value
                best_move = move
        # If there is at least one ohko move, best_move = most accurate
        if len(ohko_moves) != 0:
            best_move = max(ohko_moves, key=lambda move: move.accuracy)
        # Handle shedinja:
        if battle.opponent_active_pokemon.species == "shedinja":
            _, killing_move = self.find_shedinja_killing_move(
                battle.opponent_active_pokemon, 
                battle.available_moves)
            best_move = killing_move
        if self.verbose:
            print(f"Selected move: {best_move.id}, Value: {best_value}\n")
        return self.create_order(best_move)


    def should_i_switch(self, battle):
        current_value = self.current_pokemon_value(battle)
        best_switch, switch_value = self.find_best_switch(battle, is_forced=(current_value==FAINTED))
        if best_switch == None:
            return None
        if self.verbose:
            print(f"\nActive pkmn value: {current_value}, Best switch: {best_switch.species} ({switch_value})\n")
        if switch_value > current_value:
            return best_switch
        return None
    

    def find_best_switch(self, battle, is_forced):
        best_value = FAINTED
        best_switch = None
        opponent_is_sweeping = self.opponent_sweeping(battle)
        for pokemon in battle.available_switches:
            ###
            # NORMAL CALCULATION
            faster = i_am_faster(pokemon, battle.opponent_active_pokemon)
            revenge_value = 0
            if is_forced:
                revenge_killer = self.is_revenge_killer(
                    pokemon,
                    battle.opponent_active_pokemon,
                    battle
                    )
                if revenge_killer:
                    revenge_value = 15
            sweep_block_value = 0
            if is_forced and opponent_is_sweeping:
                if faster or (pokemon.item == "focussash" and not
                             (SideCondition.STEALTH_ROCK in battle.side_conditions or
                              SideCondition.SPIKES in battle.side_conditions)):
                    sweep_block_value = 15
            # Points evaluation
            type_value = self.evaluate_type_advantage(pokemon, battle.opponent_active_pokemon)
            hp_value = self.evaluate_hp(pokemon)
            best_defence_value = self.evaluate_defences(pokemon, battle.opponent_active_pokemon)
            atk_value = self.evaluate_strongest_attack(pokemon, battle.opponent_active_pokemon, battle)
            opponent_best_damage = self.find_opponent_best_damage(
                pokemon,
                battle.opponent_active_pokemon,
                battle,
                strict=True
                )
            opp_best_move_value = -self.damage_to_value_conversion(opponent_best_damage)
            if faster:
                if is_forced:
                    opp_best_move_value /= 4
                else:
                    opp_best_move_value /= 2
            # Penalize type disadvantage when switching in the middle of the turn
            if not is_forced: 
                if type_value < 0:
                    type_value *= 4
            # When switch is forced:
            else:
                # Still penalize slow pokemon with low hp
                if not faster:
                    hp_value /= 3
                # If faster, do not penalize low hp
                else:
                    hp_value = 0
            # Strengthen attack points when faster
            if faster:
                atk_value *= 1.5
            # Calculate final points
            total_value = (
                type_value + 
                best_defence_value +
                atk_value + 
                hp_value +
                opp_best_move_value + 
                revenge_value +
                sweep_block_value
                )
            # EXCEPTION: Shedinja
            if pokemon.species == "shedinja":
                shed_switch_value = self.evaluate_shedinja(battle, pokemon, is_forced, True)
                if not (SideCondition.STEALTH_ROCK in battle.side_conditions or
                        SideCondition.SPIKES in battle.side_conditions or
                        (SideCondition.TOXIC_SPIKES in battle.side_conditions and pokemon.status == None) or
                        battle.weather == Weather.HAIL or battle.weather == Weather.SANDSTORM):
                    # if shedinja is untouchable
                    if shed_switch_value > 0:
                        return (pokemon, shed_switch_value)
                    # else: shedinja value -> negative
                    total_value = shed_switch_value
                # if hazards on the ground: shed -> negative
                total_value = -100
            ###
            if total_value > best_value:
                best_value = total_value
                best_switch = pokemon
            if self.verbose:
                print(f"\nName: {pokemon.species}\nType: {type_value}, Def: {best_defence_value}, "
                      f"HP: {hp_value}, Atk: {atk_value}, Opp DMG: {opp_best_move_value}, "
                      f"Revenge: {revenge_value}, Sweep block: {sweep_block_value}, Is faster: {faster}, "
                      f"TOTAL: {total_value}")
        return (best_switch, best_value)


    def current_pokemon_value(self, battle):
        momentum_value = 2
        if battle.active_pokemon.fainted:
            return FAINTED
        
        type_value = self.evaluate_type_advantage(
            battle.active_pokemon,
            battle.opponent_active_pokemon
            )
        best_defence_value = self.evaluate_defences(
            battle.active_pokemon, 
            battle.opponent_active_pokemon
            )
        atk_value = self.evaluate_strongest_attack(
            battle.active_pokemon, 
            battle.opponent_active_pokemon, 
            battle
            )
        if i_am_faster(battle.active_pokemon, battle.opponent_active_pokemon):
            atk_value *= 1.5
        # Shedinja:
        shedinja_value = 0
        if battle.active_pokemon.species == "shedinja":
            shedinja_value = self.evaluate_shedinja(
                battle,
                battle.active_pokemon,
                is_forced=False,
                my_side=True)
        opponent_shedinja_value = 0
        if battle.opponent_active_pokemon.species == "shedinja":
            opponent_shedinja_value = self.evaluate_shedinja(
                battle,
                pokemon=None,
                is_forced=None,
                my_side=False)
        total_value = (type_value + best_defence_value + atk_value + momentum_value +
                       shedinja_value + opponent_shedinja_value)
        return total_value
    

    def evaluate_move(self, move, my_pokemon, opponent_pokemon, battle):
        damage = calculate_damage(move, my_pokemon, opponent_pokemon, battle, True)
        value = self.damage_to_value_conversion(damage)
        opponent_best_damage = self.find_opponent_best_damage(
            my_pokemon, 
            opponent_pokemon, 
            battle, 
            strict=False
            )
        my_hp = calculate_current_hp(my_pokemon)
        hp_loss = opponent_best_damage / my_hp
        boost_value = self.calculate_boost_value(
            move,
            hp_loss,
            my_pokemon,
            opponent_pokemon
            )
        hazard_value = self.calculate_hazard_value(
            move,
            hp_loss,
            my_pokemon,
            opponent_pokemon,
            battle
            )
        dehazard_value = self.calculate_dehazard_value(
            move,
            hp_loss,
            my_pokemon,
            opponent_pokemon,
            battle
            )
        heal_value = self.calculate_heal_value(
            move,
            hp_loss,
            my_pokemon,
            opponent_pokemon,
            battle
        )
        status_value = self.calculate_status_value(
            move,
            hp_loss,
            my_pokemon,
            opponent_pokemon,
            battle
            )
        value = value + boost_value + hazard_value + dehazard_value + heal_value + status_value
        return value


    def calculate_boost_value(self, move, hp_loss, my_pokemon, opponent_pokemon):
        boost_value = 0
        if my_pokemon.current_hp_fraction > (1/2):
            # if boost move
            if move.boosts is not None:
                # if self boost -> add boost_value
                if move.target == "self":
                    for k,v in move.boosts.items():
                        # TODO: fix boost value never 0 bug
                        boost_increase = (6 - my_pokemon.boosts[k]) / 6
                        boost_value += v * boost_increase
                # if target malus -> add -boost_value
                else:
                    for k,v in move.boosts.items():
                        boost_increase = (-6 - opponent_pokemon.boosts[k]) / 6
                        boost_value += v * boost_increase
                # Divider to increase boost moves value when the opponent pokemon deals 
                # little damage to our pokemon
                boost_booster = (1.7 * hp_loss) ** 3
                boost_value /= (boost_booster + 0.05)  # add 0.05 to avoid divide by zero
                if self.verbose:
                    print(boost_value)
                return boost_value
        return 0


    def calculate_hazard_value(self, move, hp_loss, my_pokemon, opponent_pokemon, battle):
        hazard_value = 0
        fnt_counter = get_opponent_fnt_counter(battle)
        pokemon_left = 6 - fnt_counter
        # When opponent attack is not going to kill
        if i_am_faster(my_pokemon, opponent_pokemon) or hp_loss < 1:
            if (move.id == "stealthrock" and
                SideCondition.STEALTH_ROCK not in battle.opponent_side_conditions):
                # Function increasing value in the first turns of the fight
                hazard_value = (pokemon_left / 2) ** 2.2
                if hazard_value <= 0:
                    hazard_value = 0
            elif move.id == "spikes":
                if SideCondition.SPIKES in battle.opponent_side_conditions:
                    layer_num = battle.opponent_side_conditions[SideCondition.SPIKES]
                    if layer_num < 3:
                        hazard_value = ((pokemon_left / 2) ** 2.2)
                        hazard_value -= hazard_value * layer_num / 4
                else:
                    hazard_value = (pokemon_left / 2) ** 2.2
            elif move.id == "toxicspikes":
                if SideCondition.TOXIC_SPIKES in battle.opponent_side_conditions:
                    layer_num = battle.opponent_side_conditions[SideCondition.TOXIC_SPIKES]
                    if layer_num < 2:
                        hazard_value = ((pokemon_left / 2) ** 2.2)
                        hazard_value -= hazard_value * layer_num / 3
                else:
                    hazard_value = (pokemon_left / 2) ** 2.2
        return hazard_value
    

    def calculate_dehazard_value(self, move, hp_loss, my_pokemon, opponent_pokemon, battle):
        dehazard_value = 0
        fnt_counter = get_my_fnt_counter(battle)
        pokemon_left = 6 - fnt_counter
        if i_am_faster(my_pokemon, opponent_pokemon) or hp_loss < 1: 
            if (SideCondition.STEALTH_ROCK in battle.side_conditions or
                SideCondition.SPIKES in battle.side_conditions or
                SideCondition.TOXIC_SPIKES in battle.side_conditions):
                if move.id == "defog":
                    # logarithmic function -> encourage hazard removal if 
                    # more than one pokemon left
                    dehazard_value = 15 * math.log(pokemon_left, 10)
                elif (move.id == "rapidspin" and
                    opponent_pokemon.type_1 != PokemonType.GHOST or
                    opponent_pokemon.type_2 != PokemonType.GHOST):
                    dehazard_value = 15 * math.log(pokemon_left, 10)
        return dehazard_value


    def calculate_heal_value(self, move, hp_loss, my_pokemon, opponent_pokemon, battle):
        heal_value = 0
        # TODO: if heal is useless (hp loss > heal) -> attack
        hp_left = my_pokemon.current_hp_fraction
        if "heal" in move.flags:
            heal_value = (1 / hp_left**2.5) - 1
        return heal_value


    def calculate_status_value(self, move, hp_loss, my_pokemon, opponent_pokemon, battle):
        status_value = 0
        virtual_pokemon = self.opponent_team.get_pokemon(opponent_pokemon.species)
        possible_moves = virtual_pokemon.get_possible_moves()
        if (opponent_pokemon.ability == "leafguard" and
            battle.weather == Weather.SUNNYDAY):
            return 0
        if (opponent_pokemon.ability == "hydration" and
            battle.weather == Weather.RAINDANCE):
            return 0
        if hp_loss < 1 and SideCondition.SAFEGUARD not in battle.opponent_side_conditions:
            # if i'm faster
            if (i_am_faster(my_pokemon, opponent_pokemon) and 
                not Effect.SUBSTITUTE in opponent_pokemon.effects):
                status_value += self.evaluate_burn(move, opponent_pokemon)
                status_value += self.evaluate_para(move, opponent_pokemon)
                status_value += self.evaluate_sleep(move, opponent_pokemon, battle)
                status_value += self.evaluate_poison(move, opponent_pokemon)
                status_value += self.evaluate_toxic(move, opponent_pokemon)
            # if i'm slower
            elif ("substitute" not in possible_moves and 
                not Effect.SUBSTITUTE in opponent_pokemon.effects):
                status_value += self.evaluate_burn(move, opponent_pokemon)
                status_value += self.evaluate_para(move, opponent_pokemon)
                status_value += self.evaluate_sleep(move, opponent_pokemon, battle)
                status_value += self.evaluate_poison(move, opponent_pokemon)
                status_value += self.evaluate_toxic(move, opponent_pokemon)
        return status_value


    def evaluate_burn(self, move, target_pokemon):
        status_value = 0
        if move.status == Status.BRN and target_pokemon.status == None:
            # fire type / flashfire immunity
            if (target_pokemon.type_1 != PokemonType.FIRE or
                target_pokemon.type_2 != PokemonType.FIRE or
                target_pokemon.ability != "flashfire"):
                # check abilities
                if (target_pokemon.ability != "waterveil" or
                    target_pokemon.ability != "waterbubble" or
                    target_pokemon.ability != "comatose"):
                    if target_pokemon.base_stats["atk"] > target_pokemon.base_stats["spa"]:
                        status_value = 10
                    else:
                        status_value = 5
                elif (target_pokemon.ability == "guts" or
                      target_pokemon.ability == "marvelscale" or
                      target_pokemon.ability == "quickfeet" or
                      target_pokemon.ability == "flareboost"):
                    status_value = -5
        return status_value


    def evaluate_para(self, move, target_pokemon):
        status_value = 0
        # electric type immunity and grass immunity to stunspore: from gen 6 onward
        if move.status == Status.PAR and target_pokemon.status == None:
            # TODO: base_speed or calculate_speed()?
            if (target_pokemon.ability != "limber" and
                target_pokemon.ability != "comatose"):
                status_value = target_pokemon.base_stats["spe"] / 10
            if target_pokemon.ability == "magicguard":
                status_value /= 2
            if (target_pokemon.ability == "guts" or
                target_pokemon.ability == "marvelscale" or
                target_pokemon.ability == "quickfeet" or
                target_pokemon.ability == "flareboost"):
                status_value = -5
            if ((target_pokemon.type_1 == PokemonType.GROUND or
                target_pokemon.type_2 == PokemonType.GROUND) and
                move.id == "thunderwave"):
                return 0
        return status_value


    def evaluate_sleep(self, move, target_pokemon, battle):
        # grass immunity to sleep powder from gen 6 onward
        # Check in opponent team if someone is already sleeping -> sleep clause
        status_value = 0
        for _, pokemon in battle.opponent_team.items():
            if pokemon.status == Status.SLP:
                return 0
        if (move.id == "yawn" and
            target_pokemon.status == None and
            Effect.YAWN not in target_pokemon.effects):
            if (target_pokemon.ability != "vitalspirit" and
                target_pokemon.ability != "insomnia" and
                target_pokemon.ability != "comatose"):
                return 10
        if move.status == Status.SLP and target_pokemon.status == None:
            if (target_pokemon.ability != "vitalspirit" or
                target_pokemon.ability != "insomnia" or
                target_pokemon.ability != "comatose"):
                if move.accuracy >= 1:
                    status_value = 11
                elif move.accuracy >= 0.7:
                    status_value = 8
                else:
                    status_value = 5
        return status_value

    def evaluate_poison(self, move, target_pokemon):
        status_value = 0
        if move.status == Status.PSN and target_pokemon.status == None:
            if (target_pokemon.ability != "immunity" and
                target_pokemon.ability != "magicguard" and
                target_pokemon.ability != "comatose"):
                status_value = 7
            if (target_pokemon.ability == "guts" or
                target_pokemon.ability == "marvelscale" or
                target_pokemon.ability == "quickfeet"):
                status_value = -5
            if (target_pokemon.type_1 == PokemonType.POISON or
                target_pokemon.type_2 == PokemonType.POISON or
                target_pokemon.type_1 == PokemonType.STEEL or
                target_pokemon.type_2 == PokemonType.STEEL):
                return 0
        return status_value

    def evaluate_toxic(self, move, target_pokemon):
        status_value = 0
        if move.status == Status.TOX and target_pokemon.status == None:
            if (target_pokemon.ability != "immunity" and
                target_pokemon.ability != "magicguard" and
                target_pokemon.ability != "comatose"):
                status_value = 10
            if (target_pokemon.ability == "guts" or
                target_pokemon.ability == "marvelscale" or
                target_pokemon.ability == "quickfeet"):
                status_value = -5
            if (target_pokemon.type_1 == PokemonType.POISON or
                target_pokemon.type_2 == PokemonType.POISON or
                target_pokemon.type_1 == PokemonType.STEEL or
                target_pokemon.type_2 == PokemonType.STEEL):
                return 0
        return status_value


    def find_opponent_best_damage(self, my_pokemon, opponent_pokemon, battle, strict):
        pokemon = self.opponent_team.get_pokemon(opponent_pokemon.species)
        move_names = pokemon.get_moves()
        if not strict and len(move_names) < 4:
            move_names = pokemon.get_possible_moves()
        best_damage = 0
        for move_name in move_names:
            move = Move(move_name)
            damage = calculate_damage(
                move,
                opponent_pokemon,
                my_pokemon,
                battle,
                False,
                1)
            if damage > best_damage:
                best_damage = damage
        # if self.verbose:
        #     print(f"Opponent moves: {move_names}, Best value: {best_damage}\n")
        return best_damage


    def evaluate_type_advantage(self, my_pokemon, opponent_pokemon):
        advantage = my_pokemon.damage_multiplier(opponent_pokemon.type_1)
        if opponent_pokemon.type_2:
            advantage = max(advantage, my_pokemon.damage_multiplier(opponent_pokemon.type_2))
        if advantage == 0:
            advantage = -2
        elif advantage < 1:
            advantage = -((1/advantage) - 1)
        else:
            advantage -= 1
        return -advantage * 2.5
    

    def evaluate_strongest_attack(self, my_pokemon, opponent_pokemon, battle):
        best_damage = 0
        for _, move in my_pokemon.moves.items():
            damage = calculate_damage(move, my_pokemon, opponent_pokemon, battle, True)
            if damage > best_damage:
                best_damage = damage
        return self.damage_to_value_conversion(best_damage)


    def damage_to_value_conversion(self, damage):
        # exponential function for softening high damages
        return (damage**.53) / 3


    def evaluate_defences(self, my_pokemon, opponent_pokemon):
        opponent_atk = calculate_atk(opponent_pokemon)
        opponent_spa = calculate_spa(opponent_pokemon)
        my_def = calculate_def(my_pokemon)
        my_spd = calculate_spd(my_pokemon)
        if abs(opponent_atk - opponent_spa) < 50:
            ratio = max((opponent_atk/my_def), (opponent_spa/my_spd))
            if ratio < 1:
                ratio = -((1 / ratio) - 1)
            else:
                ratio -= 1
            return -ratio * 4
        elif opponent_atk > opponent_spa:
            ratio = opponent_atk/my_def
            if ratio < 1:
                ratio = -((1 / ratio) - 1)
            else:
                ratio -= 1
            return -ratio * 4
        else:
            ratio = opponent_spa/my_spd
            if ratio < 1:
                ratio = -((1 / ratio) - 1)
            else:
                ratio -= 1
            return -ratio * 4

    def evaluate_hp(self, pokemon):
        hp = calculate_current_hp(pokemon)
        # Non-linear function :3
        hp_value = (1000 / (hp + 10))**0.9 - 4
        return -hp_value

    def handle_odd_moves(self, move, best_move, user_pokemon, opponent_pokemon, battle):
        # TODO: handle odd moves behavior (explosion, solarbeam, ...)
        if move.id == "fakeout" and user_pokemon.first_turn == True:
            if self.verbose:
                print("Go straight with Fake out")
            return move
        # TODO: fix explosion
        # if i'm slower, explode when hp left are < 1/2
        elif move.id == "explosion" and move == best_move and user_pokemon.current_hp_fraction < (1/2):
            if not i_am_faster(user_pokemon, opponent_pokemon):
                return move
            else:
                # or if i'm faster, explode when hp left is < 1/4
                if user_pokemon.current_hp_fraction < (1/4):
                    return move
        # solarbeam
        elif (move.id == "solarbeam" and
              battle.weather != Weather.SUNNYDAY):
            for m in battle.available_moves:
                if m.id == "sunnyday":
                    return m
        elif (move.id == "sunnyday" and
              battle.weather != Weather.SUNNYDAY and
              user_pokemon.current_hp_fraction > (2/3)):
            return move
        elif (move.id == "raindance" and
              battle.weather != Weather.RAINDANCE and
              user_pokemon.current_hp_fraction > (2/3)):
            return move
        # transform
        # pursuit
        return None
    

    def is_revenge_killer(self, user_pokemon, target_pokemon, battle):
        for _, move in user_pokemon.moves.items():
            if self.can_kill(move, user_pokemon, target_pokemon, battle):
                if move.priority > 0:
                    return True
                if i_am_faster(user_pokemon, target_pokemon):
                    return True
        return False


    def kill_if_ohko(self, battle):
        if not battle.available_moves:
            return None
        ohko_moves = []
        for move in battle.available_moves:
            if self.can_kill(move, battle.active_pokemon, battle.opponent_active_pokemon, battle):
                ohko_moves.append(move)
        if len(ohko_moves) == 0:
            return None
        for move in ohko_moves:
            if move.priority > 0:
                if self.verbose:
                    print(f"\nOHKO priority: {move.id}\n")
                return move
        if not i_am_faster(battle.active_pokemon, battle.opponent_active_pokemon):
            return None
        ohko_moves = list(filter(lambda move: move.priority == 0, ohko_moves))
        if len(ohko_moves) == 0:
            return None
        best_ohko_move = max(ohko_moves, key=lambda move: move.accuracy)
        if self.verbose:
            print(f"\nOHKO simple move: {best_ohko_move.id}\n")
        return best_ohko_move
    
    def can_kill(self, move, user_pokemon, target_pokemon, battle):
        target_left_hp = calculate_current_hp(target_pokemon)
        damage = calculate_damage(move, user_pokemon, target_pokemon, battle, True, rng_modifier=0.85)
        if damage >= target_left_hp:
            return True
        return False
    
    def get_sweep_counter(self, battle):
        # Sweep -> only if my pokemon are swept in subsequent turns
        # Return number of swept pokemon in a row
        current_turn = battle.turn
        # if a pokemon is killed
        if battle.active_pokemon.status == Status.FNT:
            if self.sweep_utilities["sweep_turn"] == current_turn - 1:
                self.sweep_utilities["sweep_turn"] = current_turn
                self.sweep_utilities["sweep_counter"] += 1
            else:
                self.sweep_utilities["sweep_turn"] = current_turn
                self.sweep_utilities["sweep_counter"] = 1
        # If turn ends without kills: set counter to 0
        else:
            # (to avoid reset because counter pokmn not FNT)
            if self.sweep_utilities["sweep_turn"] != current_turn - 1:
                self.sweep_utilities["sweep_counter"] = 0
        if self.verbose:
            print(self.sweep_utilities)
        return self.sweep_utilities["sweep_counter"]

    def opponent_sweeping(self, battle):
        sweep_counter = self.get_sweep_counter(battle)
        if sweep_counter >= 2:
            return True
        return False

    def evaluate_shedinja(self, battle, pokemon, is_forced, my_side):
        # I have a shedinja
        if my_side:
            my_pokemon = pokemon
            opponent_pokemon = battle.opponent_active_pokemon
            if is_forced:
                if self.is_revenge_killer(my_pokemon, opponent_pokemon, battle):
                    return 100
            virtual_pokemon = self.opponent_team.get_pokemon(opponent_pokemon.species)
            # See opponent 4 moves (if you know all or them), else: possible_moves
            possible_moves = virtual_pokemon.get_moves()
            if len(possible_moves) < 4:
                possible_moves = virtual_pokemon.get_possible_moves()
            can_kill, _ = self.find_shedinja_killing_move(pokemon, possible_moves)
            if not can_kill:
                return 100
            return -100
        # else: opponent has a shedinja
        can_kill, _ = self.find_shedinja_killing_move(pokemon, battle.available_moves)
        if can_kill:
            return 100
        return -100
                
    def find_shedinja_killing_move(self, pokemon, movepool):
        can_kill = False
        killing_move = None
        for move in movepool:
            if (Move(move).category != MoveCategory.STATUS and 
                pokemon.damage_multiplier(Move(move)) > 1):
                can_kill = True
                killing_move = Move(move)
            # if PSN / BRN moves or leech seed
            elif (Move(move).status == Status.PSN or
                Move(move).status == Status.TOX or
                Move(move).status == Status.BRN) and\
                pokemon.status == None:
                can_kill = True
                killing_move = Move(move)
            elif move == "leechseed":
                can_kill = True
                killing_move = Move(move)
        return can_kill, killing_move


                    
