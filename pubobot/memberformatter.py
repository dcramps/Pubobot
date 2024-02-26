import discord
from typing import List, OrderedDict, Dict, Tuple

def format_list(players: List[Tuple[discord.Member, List[str]]], mention = False) -> str:
    escaped_names = [get_player_string(player, mention) for player in players]
    return ", ".join(escaped_names)

def format_team(prefix: str, players: List[discord.Member], ranks: Dict[int, str], mention = False):
    team = format_list(players, ranks, mention)
    return f"{prefix} {team}"

def format_unpicked(prefix: str, unpicked: OrderedDict):
    return "Unpicked: " + ", ".join(
        [f"{k}. {v.nick if v.nick else v.name}" for k, v in unpicked.items()]
    )


### Utility Functions

def get_player_string(player: Tuple[discord.Member, List[str]], mention) -> str:
    return f"{player[0].mention if mention else get_player_name(player[0])} {get_decorations(player[1])}" 

def get_player_name(player: discord.Member) -> str:
    return (player.nick if player.nick else player.name).replace("`", r"\`")

def get_decorations(decorations: List[str]):
    if len(decorations):
        return f"[{', '.join(decorations)}]"
    return None