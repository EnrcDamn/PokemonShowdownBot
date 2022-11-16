import asyncio

from DumbBotTesting import AverageAI
from poke_env import ShowdownServerConfiguration, PlayerConfiguration


async def main():
    # We create a random player
    player = AverageAI(
        player_configuration=PlayerConfiguration("your_username", "your_password"),
        server_configuration=ShowdownServerConfiguration,
    )

    # Sending challenges to "your_username"
    # await player.send_challenges("your_username", n_challenges=30)

    # Accepting one challenge from any user
    # await player.accept_challenges(None, 1)

    # Accepting three challenges from "your_username"
    # await player.accept_challenges("your_username", 3)

    # Playing n games on the ladder
    await player.ladder(n_games=1)

    # Print the rating of the player and its opponent after each battle
    for i, battle in enumerate(player.battles.values()):
        if i == 0:
            first_rating = battle.rating
        last_rating = battle.rating
    print("#################################")
    print("Score *probably* updated to the latest battle, but might not have")
    print(f"REGISTERED RATING: {first_rating} → {last_rating}")


if __name__ == "__main__":

    asyncio.get_event_loop().run_until_complete(main())
