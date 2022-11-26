from poke_env.environment.move_category import MoveCategory
from poke_env.environment.status import Status
from poke_env.environment.weather import Weather
from poke_env.environment.pokemon_type import PokemonType
from poke_env.environment.effect import Effect
from poke_env.environment.side_condition import SideCondition


RANDOM_BATTLE_EVs = 84
RANDOM_BATTLE_IVs = 31

RNG_PESSIMISTIC = 0.85
RNG_OPTIMISTIC = 1
RNG_MEAN = (0.85 + 1) / 2


def calculate_stats_from_evs(evs):
    # 4 EVs -> +1 stats point
    return evs // 4

def calculate_full_hp(pokemon):
    hp = pokemon.base_stats["hp"] * 2
    hp += calculate_stats_from_evs(RANDOM_BATTLE_EVs + 1) + RANDOM_BATTLE_IVs
    hp = (hp * pokemon.level) / 100
    hp = hp + pokemon.level + 10
    return hp

def calculate_current_hp(pokemon):
    hp = calculate_full_hp(pokemon)
    hp *= pokemon.current_hp_fraction
    return hp

def calculate_atk(pokemon):
    # TODO: consider burn
    attack = pokemon.base_stats["atk"] * 2
    attack += calculate_stats_from_evs(RANDOM_BATTLE_EVs) + RANDOM_BATTLE_IVs
    attack = (attack * pokemon.level) / 100
    attack += 5
    boost = boost_multiplier(pokemon, "atk")
    return attack * boost
    
def calculate_def(pokemon):
    defense = pokemon.base_stats["def"] * 2
    defense += calculate_stats_from_evs(RANDOM_BATTLE_EVs) + RANDOM_BATTLE_IVs
    defense = (defense * pokemon.level) / 100
    defense += 5
    boost = boost_multiplier(pokemon, "def")
    return defense * boost

def calculate_spa(pokemon):
    sp_attack = pokemon.base_stats["spa"] * 2
    sp_attack += calculate_stats_from_evs(RANDOM_BATTLE_EVs) + RANDOM_BATTLE_IVs
    sp_attack = (sp_attack * pokemon.level) / 100
    sp_attack += 5
    boost = boost_multiplier(pokemon, "spa")
    return sp_attack * boost

def calculate_spd(pokemon):
    sp_defense = pokemon.base_stats["spd"] * 2
    sp_defense += calculate_stats_from_evs(RANDOM_BATTLE_EVs) + RANDOM_BATTLE_IVs
    sp_defense = (sp_defense * pokemon.level) / 100
    sp_defense += 5
    boost = boost_multiplier(pokemon, "spd")
    return sp_defense * boost

def calculate_spe(pokemon):
    # TODO: consider para
    speed = pokemon.base_stats["spe"] * 2
    speed += calculate_stats_from_evs(RANDOM_BATTLE_EVs) + RANDOM_BATTLE_IVs
    speed = (speed * pokemon.level) / 100
    speed += 5
    if Effect.SLOW_START in pokemon.effects:
        speed /= 2
    boost = boost_multiplier(pokemon, "spe")
    return speed * boost

def boost_multiplier(pokemon, stat_name):
    current_boost = pokemon.boosts[stat_name]
    bonus = 1 + 0.5 * abs(current_boost)
    if current_boost < 0:   # malus
        bonus = 1 / bonus
    return bonus

def i_am_faster(my_pokemon, opponent_pokemon):
    my_speed = my_pokemon.stats["spe"]
    opponent_max_speed = calculate_spe(opponent_pokemon)
    if my_speed >= opponent_max_speed:
        return True
    return False


def get_opponent_fnt_counter(battle):
    fnt_counter = 0
    for _, pkmn in battle.opponent_team.items():
        if pkmn.status == Status.FNT:
            fnt_counter += 1
    return fnt_counter


def calculate_damage(move, user_pokemon, target_pokemon, battle, i_am_attacking, rng_modifier=RNG_MEAN):
    # Base calculation
    damage = ((2 * user_pokemon.level) / 5) + 2
    move_base_power = move.base_power
    move_base_power = set_changeable_base_power(move, move_base_power, user_pokemon, target_pokemon)
    damage *= move_base_power
    damage = set_physical_or_special(damage, move, user_pokemon, target_pokemon)
    damage /= 50
    if damage != 0:
        damage += 2
    # Modifiers
    damage = set_burn_conditions(damage, move, user_pokemon)
    damage = set_weather_conditions(damage, move, battle)
    damage = set_screens(damage, move, battle, i_am_attacking)
    damage = handle_double_targets(damage, move, battle)
    damage = consider_items(damage, move, user_pokemon, target_pokemon)
    damage = set_stab(damage, move, user_pokemon)
    damage = handle_abilities(
        damage,
        move,
        move_base_power,
        user_pokemon,
        target_pokemon
        )
    damage = type_effectiveness_multiplier(damage, move, user_pokemon, target_pokemon)
    damage *= rng_modifier
    return damage


# For handling non-fixed damage moves (return, gyro ball, ...)
def set_changeable_base_power(move, move_base_power, user_pokemon, target_pokemon):
    if move.id == "return":
        move_base_power = 102
    elif move.id == "gyroball":
        user_speed = calculate_spe(user_pokemon)
        target_speed = calculate_spe(target_pokemon)
        move_base_power = min(150, (25 * target_speed / user_speed) + 1)
    elif move.id == "nightshade":
        move_base_power = user_pokemon.level
    elif move.id == "seismictoss":
        move_base_power = user_pokemon.level
    elif move.id == "facade":
        if (user_pokemon.status == Status.PAR or
                user_pokemon.status == Status.PSN or
                user_pokemon.status == Status.BRN or
                user_pokemon.status == Status.TOX):
            move_base_power *= 2
    elif move.id == "waterspout" or move.id == "eruption":
        move_base_power = 150 * calculate_current_hp(user_pokemon) / calculate_full_hp(user_pokemon)
        if move_base_power < 1:
            move_base_power = 1
    elif move.id == "grassknot":
        if target_pokemon.weight < 10:  # weight in kilograms
            move_base_power = 20
        elif target_pokemon.weight < 25:
            move_base_power = 40
        elif target_pokemon.weight < 50:
            move_base_power = 60
        elif target_pokemon.weight < 100:
            move_base_power = 80
        elif target_pokemon.weight < 200:
            move_base_power = 100
        else:
            move_base_power = 120
    elif move.id == "lowkick":
        if target_pokemon.weight <= 10:  # weight in kilograms
            move_base_power = 20
        elif target_pokemon.weight <= 25:
            move_base_power = 40
        elif target_pokemon.weight <= 50:
            move_base_power = 60
        elif target_pokemon.weight <= 100:
            move_base_power = 80
        elif target_pokemon.weight <= 200:
            move_base_power = 100
        else:
            move_base_power = 120
    return move_base_power

def set_physical_or_special(damage, move, user_pokemon, target_pokemon):
    if move.category == MoveCategory.PHYSICAL:
        damage *= (calculate_atk(user_pokemon) / calculate_def(target_pokemon))
        return damage
    elif move.category == MoveCategory.SPECIAL:
        if move.id == "psyshock":
            damage *= (calculate_spa(user_pokemon) / calculate_def(target_pokemon))
        else:
            damage *= (calculate_spa(user_pokemon) / calculate_spd(target_pokemon))
        return damage
    return 0

def set_burn_conditions(damage, move, user_pokemon):
    if move.category == MoveCategory.PHYSICAL and user_pokemon.status == Status.BRN:
        damage *= 0.5
    return damage

def set_screens(damage, move, battle, i_am_attacking):
    if i_am_attacking:
        if (move.category == MoveCategory.PHYSICAL and 
        SideCondition.REFLECT in battle.opponent_side_conditions):
            damage *= 0.5
        elif (move.category == MoveCategory.SPECIAL and
        SideCondition.LIGHT_SCREEN in battle.opponent_side_conditions):
            damage *= 0.5
    else:
        if (move.category == MoveCategory.PHYSICAL and 
        SideCondition.REFLECT in battle.side_conditions):
            damage *= 0.5
        elif (move.category == MoveCategory.SPECIAL and
        SideCondition.LIGHT_SCREEN in battle.side_conditions):
            damage *= 0.5
    return damage

def handle_double_targets(damage, move, battle):
    # TODO: implement spread damage
    return damage

def set_weather_conditions(damage, move, battle):
    if battle.weather == Weather.RAINDANCE:
        if move.type == PokemonType.WATER:
            damage *= 1.5
        elif move.type == PokemonType.FIRE:
            damage *= 1/1.5
        elif move.id == "solarbeam":
            damage *= 1/1.5
    elif battle.weather == Weather.SUNNYDAY:
        if move.type == PokemonType.FIRE:
            damage *= 1.5
        elif move.type == PokemonType.WATER:
            damage *= 1/1.5
    return damage

def consider_items(damage, move, user_pokemon, target_pokemon):
    if user_pokemon.item == "choiceband" and move.category == MoveCategory.PHYSICAL:
        damage *= 1.5
    if user_pokemon.item == "choicespecs" and move.category == MoveCategory.SPECIAL:
        damage *= 1.5
    if user_pokemon.item == "lifeorb":
        damage *= 1.3
    if user_pokemon.item == "expertbelt" and target_pokemon.damage_multiplier(move) > 1:
        damage * 1.2
    return damage

def set_stab(damage, move, user_pokemon):
    if move.type == user_pokemon.type_1 or move.type == user_pokemon.type_2:
        if user_pokemon.ability == "adaptability":
            damage *= 2
        else:
            damage *= 1.5
    return damage

def type_effectiveness_multiplier(damage, move, user_pokemon, target_pokemon):
    if user_pokemon.ability == "scrappy":
        mult_1 = move.type.damage_multiplier(target_pokemon.type_1, None)
        mult_2 = 1
        if target_pokemon.type_2 is not None:
            mult_2 = move.type.damage_multiplier(target_pokemon.type_2, None)
        if mult_1 == 0:
            mult_1 = 1
        if mult_2 == 0:
            mult_2 = 1
        return damage * mult_1 * mult_2
    type_effectiveness_mult = target_pokemon.damage_multiplier(move)
    damage *= type_effectiveness_mult
    return damage

def handle_abilities(damage, move, move_base_power, user_pokemon, target_pokemon):
    if user_pokemon.ability == "guts" and move.category == MoveCategory.PHYSICAL:
        if (user_pokemon.status == Status.PAR or
                user_pokemon.status == Status.PSN or
                user_pokemon.status == Status.SLP or
                user_pokemon.status == Status.TOX):
            damage *= 1.5
        elif user_pokemon.status == Status.BRN:
            damage *= 3     # x3 -> balancing with x0.5 of burn
    elif user_pokemon.ability == "hugepower" and move.category == MoveCategory.PHYSICAL:
        damage *= 2
    elif user_pokemon.ability == "purepower" and move.category == MoveCategory.PHYSICAL:
        damage *= 2 
    elif Effect.FLASH_FIRE in user_pokemon.effects and move.type == PokemonType.FIRE:
        damage *= 1.5
    elif user_pokemon.ability == "tintedlens" and target_pokemon.damage_multiplier(move) < 1:
        damage *= 2
    elif (user_pokemon.ability == "blaze" and
          user_pokemon.current_hp_fraction < (1/3) and
          move.type == PokemonType.FIRE):
        damage *= 1.5
    elif (user_pokemon.ability == "torrent" and
          user_pokemon.current_hp_fraction < (1/3) and
          move.type == PokemonType.WATER):
        damage *= 1.5
    elif (user_pokemon.ability == "overgrow" and
          user_pokemon.current_hp_fraction < (1/3) and
          move.type == PokemonType.GRASS):
        damage *= 1.5
    elif (user_pokemon.ability == "swarm" and
          user_pokemon.current_hp_fraction < (1/3) and
          move.type == PokemonType.BUG):
        damage *= 1.5
    elif user_pokemon.ability == "technician" and move_base_power <= 60:
        damage *= 1.5
    elif user_pokemon.ability == "slowstart":
        if Effect.SLOW_START in user_pokemon.effects and move.category == MoveCategory.PHYSICAL:
            damage *= 0.5
    elif user_pokemon.ability != "moldbreaker":
        if ((move.type == PokemonType.FIRE or move.type == PokemonType.ICE) and
             target_pokemon.ability == "thickfat"):
            damage *= 0.5
        elif move.type == PokemonType.GROUND and target_pokemon.ability == "levitate":
            return 0
        elif move.type == PokemonType.WATER and target_pokemon.ability == "waterabsorb":
            return 0
        elif move.type == PokemonType.WATER and target_pokemon.ability == "stormdrain":
            return 0
        elif move.type == PokemonType.WATER and target_pokemon.ability == "dryskin":
            return 0
        elif move.type == PokemonType.ELECTRIC and target_pokemon.ability == "voltabsorb":
            return 0
        elif move.type == PokemonType.ELECTRIC and target_pokemon.ability == "lightningrod":
            return 0
        elif move.type == PokemonType.ELECTRIC and target_pokemon.ability == "motordrive":
            return 0
        elif move.type == PokemonType.FIRE and target_pokemon.ability == "flashfire":
            return 0
        elif move.type == PokemonType.GRASS and target_pokemon.ability == "sapsipper":
            return 0
        elif target_pokemon.damage_multiplier(move) > 1 and target_pokemon.ability == "solidrock":
            damage *= 0.75
        elif target_pokemon.damage_multiplier(move) > 1 and target_pokemon.ability == "filter":
            damage *= 0.75
    return damage