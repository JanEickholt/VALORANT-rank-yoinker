import asyncio
import os
import socket
import sys
import time
import traceback

import urllib3
from colr import color as colr
from InquirerPy import inquirer
from rich.console import Console as RichConsole

from src.chatlogs import ChatLogging
from src.colors import Colors
from src.config import Config
from src.configurator import configure
from src.constants import *
from src.content import Content
from src.errors import Error
from src.loadouts import Loadouts
from src.logs import Logging
from src.names import Names
from src.player_stats import PlayerStats
from src.presences import Presences
from src.rank import Rank
from src.api import Api
from src.rpc import Rpc
from src.server import Server
from src.states.coregame import Coregame
from src.states.menu import Menu
from src.states.pregame import Pregame
from src.table import Table
from src.websocket import Ws
from src.os import get_os
import src.stats as stats

from src.account_manager.account_manager import AccountManager
from src.account_manager.account_config import AccountConfig
from src.account_manager.account_auth import AccountAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.system(f"title VALORANT rank yoinker v{VERSION}")

server = ""


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


try:
    Logging = Logging()
    log = Logging.log

    # os logging
    log(f"Operating system: {get_os()}\n")

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--config":
            configure()
            run_app = inquirer.confirm(
                message="Do you want to run vRY now?", default=True
            ).execute()
            if run_app:
                os.system("cls")
            else:
                os._exit(0)
        else:
            os.system("cls")
    except Exception as e:
        print("Something went wrong while running configurator!")
        log("configurator encountered an error")
        log(str(traceback.format_exc()))
        input("press enter to exit...\n")
        os._exit(1)

    ChatLogging = ChatLogging()
    chat_log = ChatLogging.chat_log

    acc_manager = AccountManager(log, AccountConfig, AccountAuth, NUMBER_TO_RANKS)

    ErrorSRC = Error(log, acc_manager)

    Api.check_version(VERSION, Api.copy_run_update_script)
    Api.check_status()
    Requests = Api(VERSION, log, ErrorSRC)

    cfg = Config(log)

    content = Content(Requests, log)

    rank = Rank(Requests, log, content, BEFORE_ASCENDANT_SEASONS)
    pstats = PlayerStats(Requests, log, cfg)

    names_class = Names(Requests, log)

    presences = Presences(Requests, log)

    menu = Menu(Requests, log, presences)
    pregame = Pregame(Requests, log)
    coregame = Coregame(Requests, log)

    Server = Server(log, ErrorSRC)
    Server.start_server()

    agent_dict = content.get_all_agents()

    map_info = content.get_all_maps()
    map_urls = content.get_map_urls(map_info)
    map_splashes = content.get_map_splashes(map_info)

    current_map = coregame.get_current_map(map_urls, map_splashes)

    colors = Colors(HIDE_NAMES, agent_dict, AGENT_COLOR_LIST)

    loadouts_class = Loadouts(Requests, log, colors, Server, current_map)
    table = Table(cfg, chat_log, log)

    if cfg.get_feature_flag("discord_rpc"):
        rpc = Rpc(map_urls, GAMEMODES, colors, log)
    else:
        rpc = None

    Wss = Ws(
        Requests.lockfile, Requests, cfg, colors, HIDE_NAMES, chat_log, Server, rpc
    )
    log(f"VALORANT rank yoinker v{VERSION}")

    VALO_API_SKINS = requests.get("https://valorant-api.com/v1/weapons/skins")
    game_content = content.get_content()
    season_id = content.get_latest_season_id(game_content)
    previous_season_id = content.get_previous_season_id(game_content)
    last_game_state = ""

    print("\nvRY Mobile", color(f"- {get_ip()}:{cfg.port}", fore=(255, 127, 80)))

    print(
        color(
            "\nVisit https://vry.netlify.app/matchLoadouts to view full player inventories\n",
            fore=(255, 253, 205),
        )
    )
    chat_log(
        color(
            "\nVisit https://vry.netlify.app/matchLoadouts to view full player inventories\n",
            fore=(255, 253, 205),
        )
    )

    richConsole = RichConsole()

    first_time = True
    first_print = True
    while True:
        table.clear()
        table.set_default_field_names()
        table.reset_runtime_col_flags()

        try:
            if first_time:
                run = True
                while run:
                    while True:
                        presence = presences.get_presence()
                        # wait until your own valorant presence is initialized
                        if presences.get_private_presence(presence):
                            break
                        time.sleep(5)
                    if cfg.get_feature_flag("discord_rpc"):
                        rpc.set_rpc(presences.get_private_presence(presence))
                    game_state = presences.get_game_state(presence)
                    if game_state:
                        run = False
                    time.sleep(2)
                log(f"first game state: {game_state}")
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                previous_game_state = game_state
                game_state = loop.run_until_complete(
                    Wss.recconect_to_websocket(game_state)
                )
                # we invalidate the cached responses when going from any state to menus
                if previous_game_state != game_state and game_state == "MENUS":
                    rank.invalidate_cached_responses()
                log(f"new game state: {game_state}")
                loop.close()
            first_time = False
        except TypeError:
            raise Exception("Game has not started yet!")
        if True:
            log(f"getting new {game_state} scoreboard")
            last_game_state = game_state
            game_state_dict = {
                "INGAME": color("In-Game", fore=(241, 39, 39)),
                "PREGAME": color("Agent Select", fore=(103, 237, 76)),
                "MENUS": color("In-Menus", fore=(238, 241, 54)),
            }

            if (not first_print) and cfg.get_feature_flag("pre_cls"):
                os.system("cls")

            is_leaderboard_needed = False

            private_presence = presences.get_private_presence(presence)
            if (
                private_presence["provisioningFlow"] == "CustomGame"
                or private_presence["partyState"] == "CUSTOM_GAME_SETUP"
            ):
                gamemode = "Custom Game"
            else:
                gamemode = GAMEMODES.get(private_presence["queueId"])

            heartbeat_data = {
                "time": int(time.time()),
                "state": game_state,
                "mode": gamemode,
                "puuid": Requests.puuid,
                "players": {},
            }

            if game_state == "INGAME":
                coregame_stats = coregame.get_coregame_stats()
                if not coregame_stats:
                    continue
                player_dict = coregame_stats["Players"]
                # data for chat to function
                presence = presences.get_presence()
                party_members = menu.get_party_members(Requests.puuid, presence)
                party_members_list = [a["Subject"] for a in party_members]

                players_data = {}
                players_data.update({"ignore": party_members_list})
                for player in player_dict:
                    if player["Subject"] == Requests.puuid:
                        if cfg.get_feature_flag("discord_rpc"):
                            rpc.set_data({"agent": player["CharacterID"]})
                    players_data.update(
                        {
                            player["subject"]: {
                                "team": player["TeamID"],
                                "agent": player["CharacterID"],
                                "streamer_mode": player["player_identity"]["Incognito"],
                            }
                        }
                    )
                Wss.set_player_data(players_data)

                try:
                    server = GAMEPODS[coregame_stats["GamePodID"]]
                except KeyError:
                    server = "New server"
                presences.wait_for_presence(names_class.get_players_puuid(player_dict))
                names = names_class.get_names_from_puuids(player_dict)
                loadouts_arr = loadouts_class.get_match_loadouts(
                    coregame.get_coregame_match_id(),
                    player_dict,
                    cfg.weapon,
                    VALO_API_SKINS,
                    names,
                )
                loadouts = loadouts_arr[0]
                loadouts_data = loadouts_arr[1]
                is_range = False
                players_loaded = 1

                heartbeat_data["map"] = (map_urls[coregame_stats["MapID"].lower()],)
                with richConsole.status("Loading Players...") as status:
                    party_obj = menu.get_party_json(
                        names_class.get_players_puuid(player_dict), presence
                    )
                    player_dict.sort(
                        key=lambda players: players["PlayerIdentity"].get(
                            "AccountLevel"
                        ),
                        reverse=True,
                    )
                    player_dict.sort(
                        key=lambda players: players["TeamID"], reverse=True
                    )
                    party_count = 0
                    party_num = 0
                    party_icons = {}
                    last_team_boolean = False
                    last_team = "Red"

                    already_played_with = []
                    stats_data = stats.read_data()

                    for p in player_dict:
                        if p["Subject"] == Requests.puuid:
                            allyTeam = p["TeamID"]
                    for player in player_dict:
                        status.update(
                            f"Loading players... [{players_loaded}/{len(player_dict)}]"
                        )
                        players_loaded += 1

                        if player["Subject"] in stats_data.keys():
                            if (
                                player["Subject"] != Requests.puuid
                                and player["Subject"] not in party_members_list
                            ):
                                curr_player_stat = stats_data[player["Subject"]][-1]
                                i = 1
                                while (
                                    curr_player_stat["match_id"] == coregame.match_id
                                    and len(stats_data[player["Subject"]]) > i
                                ):
                                    i += 1
                                    curr_player_stat = stats_data[player["Subject"]][-i]
                                if curr_player_stat["match_id"] != coregame.match_id:
                                    # checking for party members and self players
                                    times = 0
                                    m_set = ()
                                    for m in stats_data[player["Subject"]]:
                                        if (
                                            m["match_id"] != coregame.match_id
                                            and m["match_id"] not in m_set
                                        ):
                                            times += 1
                                            m_set += (m["match_id"],)
                                    if not player["PlayerIdentity"]["Incognito"]:
                                        already_played_with.append(
                                            {
                                                "times": times,
                                                "name": curr_player_stat["name"],
                                                "agent": curr_player_stat["agent"],
                                                "time_diff": time.time()
                                                - curr_player_stat["epoch"],
                                            }
                                        )
                                    else:
                                        if player["TeamID"] == allyTeam:
                                            team_string = "your"
                                        else:
                                            team_string = "enemy"
                                        already_played_with.append(
                                            {
                                                "times": times,
                                                "name": agent_dict[
                                                    player["CharacterID"].lower()
                                                ]
                                                + " on "
                                                + team_string
                                                + " team",
                                                "agent": curr_player_stat["agent"],
                                                "time_diff": time.time()
                                                - curr_player_stat["epoch"],
                                            }
                                        )

                        party_icon = ""
                        # set party pre-mate icon
                        for party in party_obj:
                            if player["Subject"] in party_obj[party]:
                                if party not in party_icons:
                                    party_icons.update(
                                        {party: PARTY_ICON_LIST[party_count]}
                                    )
                                    # party icon
                                    party_icon = PARTY_ICON_LIST[party_count]
                                    party_num = party_count + 1
                                    party_count += 1
                                else:
                                    # party icon
                                    party_icon = party_icons[party]
                        player_rank = rank.get_rank(player["Subject"], season_id)
                        previous_player_rank = rank.get_rank(
                            player["Subject"], previous_season_id
                        )

                        if player["Subject"] == Requests.puuid:
                            if cfg.get_feature_flag("discord_rpc"):
                                rpc.set_data(
                                    {
                                        "rank": player_rank["rank"],
                                        "rank_name": colors.escape_ansi(
                                            NUMBER_TO_RANKS[player_rank["rank"]]
                                        )
                                        + " | "
                                        + str(player_rank["rr"])
                                        + "rr",
                                    }
                                )

                        player_stats = pstats.get_stats(player["Subject"])
                        hs = player_stats["hs"]
                        kd = player_stats["kd"]

                        player_level = player["PlayerIdentity"].get("AccountLevel")

                        if player["PlayerIdentity"]["Incognito"]:
                            name_color = colors.get_color_from_team(
                                player["TeamID"],
                                names[player["Subject"]],
                                player["Subject"],
                                Requests.puuid,
                                agent=player["CharacterID"],
                                party_members=party_members_list,
                            )
                        else:
                            name_color = colors.get_color_from_team(
                                player["TeamID"],
                                names[player["Subject"]],
                                player["Subject"],
                                Requests.puuid,
                                party_members=party_members_list,
                            )
                        if last_team != player["TeamID"]:
                            if last_team_boolean:
                                table.add_empty_row()
                        last_team = player["TeamID"]
                        last_team_boolean = True
                        if player["PlayerIdentity"]["HideAccountLevel"]:
                            if (
                                player["Subject"] == Requests.puuid
                                or player["Subject"] in party_members_list
                                or not HIDE_LEVELS
                            ):
                                player_color = colors.level_to_color(player_level)
                            else:
                                player_color = ""
                        else:
                            player_color = colors.level_to_color(player_level)

                        # agent
                        agent = colors.get_agent_from_uuid(
                            player["CharacterID"].lower()
                        )
                        if agent == "" and len(player_dict) == 1:
                            is_range = True

                        # name
                        name = name_color

                        # skin
                        skin = loadouts[player["Subject"]]

                        # rank
                        rank_name = NUMBER_TO_RANKS[player_rank["rank"]]
                        if cfg.get_feature_flag("aggregate_rank_rr") and cfg.table.get(
                            "rr"
                        ):
                            rank_name += f" ({player_rank['rr']})"

                        # rank rating
                        rr = player_rank["rr"]

                        # short peak rank string
                        peak_rank_act = f" (e{player_rank['peak_rank_ep']}a{player_rank['peak_rank_act']})"
                        if not cfg.get_feature_flag("peak_rank_act"):
                            peak_rank_act = ""

                        # peak rank
                        peak_rank = (
                            NUMBER_TO_RANKS[player_rank["peak_rank"]] + peak_rank_act
                        )

                        # previous rank
                        previous_rank = NUMBER_TO_RANKS[previous_player_rank["rank"]]

                        # leaderboard
                        leaderboard = player_rank["leaderboard"]

                        hs = colors.get_gradient(hs)
                        wr = (
                            colors.get_gradient(player_rank["wr"])
                            + f" ({player_rank['number_of_games']})"
                        )

                        if int(leaderboard) > 0:
                            is_leaderboard_needed = True

                        # level
                        level = player_color
                        table.add_row_table(
                            [
                                party_icon,
                                agent,
                                name,
                                skin,
                                rank_name,
                                rr,
                                peak_rank,
                                previous_rank,
                                leaderboard,
                                hs,
                                wr,
                                kd,
                                level,
                            ]
                        )

                        heartbeat_data["players"][player["Subject"]] = {
                            "puuid": player["Subject"],
                            "name": names[player["Subject"]],
                            "partyNumber": party_num if party_icon != "" else 0,
                            "agent": agent_dict[player["CharacterID"].lower()],
                            "rank": player_rank["rank"],
                            "peakRank": player_rank["peak_rank"],
                            "peakRankAct": peak_rank_act,
                            "rr": rr,
                            "kd": player_stats["kd"],
                            "headshotPercentage": player_stats["hs"],
                            "winPercentage": f"{player_rank['wr']} ({player_rank['number_of_games']})",
                            "level": player_level,
                            "agentImgLink": loadouts_data["Players"][
                                player["Subject"]
                            ].get("Agent", None),
                            "team": loadouts_data["Players"][player["Subject"]].get(
                                "Team", None
                            ),
                            "sprays": loadouts_data["Players"][player["Subject"]].get(
                                "Sprays", None
                            ),
                            "title": loadouts_data["Players"][player["Subject"]].get(
                                "Title", None
                            ),
                            "playerCard": loadouts_data["Players"][
                                player["Subject"]
                            ].get("PlayerCard", None),
                            "weapons": loadouts_data["Players"][player["Subject"]].get(
                                "Weapons", None
                            ),
                        }

                        stats.save_data(
                            {
                                player["Subject"]: {
                                    "name": names[player["Subject"]],
                                    "agent": agent_dict[player["CharacterID"].lower()],
                                    "map": current_map,
                                    "rank": player_rank["rank"],
                                    "rr": rr,
                                    "match_id": coregame.match_id,
                                    "epoch": time.time(),
                                }
                            }
                        )

            elif game_state == "PREGAME":
                already_played_with = []
                pregame_stats = pregame.get_pregame_stats()
                if not pregame_stats:
                    continue
                try:
                    server = GAMEPODS[pregame_stats["GamePodID"]]
                except KeyError:
                    server = "New server"
                player_dict = pregame_stats["AllyTeam"]["Players"]
                presences.wait_for_presence(names_class.get_players_puuid(player_dict))
                names = names_class.get_names_from_puuids(player_dict)
                players_loaded = 1
                with richConsole.status("Loading Players...") as status:
                    presence = presences.get_presence()
                    party_obj = menu.get_party_json(
                        names_class.get_players_puuid(player_dict), presence
                    )
                    party_members = menu.get_party_members(Requests.puuid, presence)
                    party_members_list = [a["Subject"] for a in party_members]
                    player_dict.sort(
                        key=lambda players: players["PlayerIdentity"].get(
                            "AccountLevel"
                        ),
                        reverse=True,
                    )
                    party_count = 0
                    party_icons = {}
                    for player in player_dict:
                        status.update(
                            f"Loading players... [{players_loaded}/{len(player_dict)}]"
                        )
                        players_loaded += 1
                        party_icon = ""

                        for party in party_obj:
                            if player["Subject"] in party_obj[party]:
                                if party not in party_icons:
                                    party_icons.update(
                                        {party: PARTY_ICON_LIST[party_count]}
                                    )
                                    # party icon
                                    party_icon = PARTY_ICON_LIST[party_count]
                                    party_num = party_count + 1
                                else:
                                    # party icon
                                    party_icon = party_icons[party]
                                party_count += 1
                        player_rank = rank.get_rank(player["Subject"], season_id)
                        previous_player_rank = rank.get_rank(
                            player["Subject"], previous_season_id
                        )

                        if player["Subject"] == Requests.puuid:
                            if cfg.get_feature_flag("discord_rpc"):
                                rpc.set_data(
                                    {
                                        "rank": player_rank["rank"],
                                        "rank_name": colors.escape_ansi(
                                            NUMBER_TO_RANKS[player_rank["rank"]]
                                        )
                                        + " | "
                                        + str(player_rank["rr"])
                                        + "rr",
                                    }
                                )

                        player_stats = pstats.get_stats(player["Subject"])
                        hs = player_stats["hs"]
                        kd = player_stats["kd"]

                        player_level = player["PlayerIdentity"].get("AccountLevel")
                        if player["PlayerIdentity"]["Incognito"]:
                            name_color = colors.get_color_from_team(
                                pregame_stats["Teams"][0]["TeamID"],
                                names[player["Subject"]],
                                player["Subject"],
                                Requests.puuid,
                                agent=player["CharacterID"],
                                party_members=party_members_list,
                            )
                        else:
                            name_color = colors.get_color_from_team(
                                pregame_stats["Teams"][0]["TeamID"],
                                names[player["Subject"]],
                                player["Subject"],
                                Requests.puuid,
                                party_members=party_members_list,
                            )

                        if player["PlayerIdentity"]["HideAccountLevel"]:
                            if (
                                player["Subject"] == Requests.puuid
                                or player["Subject"] in party_members_list
                                or not HIDE_LEVELS
                            ):
                                player_color = colors.level_to_color(player_level)
                            else:
                                player_color = ""
                        else:
                            player_color = colors.level_to_color(player_level)
                        if player["CharacterSelectionState"] == "locked":
                            agent_color = color(
                                str(agent_dict.get(player["CharacterID"].lower())),
                                fore=(255, 255, 255),
                            )
                        elif player["CharacterSelectionState"] == "selected":
                            agent_color = color(
                                str(agent_dict.get(player["CharacterID"].lower())),
                                fore=(128, 128, 128),
                            )
                        else:
                            agent_color = color(
                                str(agent_dict.get(player["CharacterID"].lower())),
                                fore=(54, 53, 51),
                            )

                        # agent
                        agent = agent_color

                        # name
                        name = name_color

                        # rank
                        rank_name = NUMBER_TO_RANKS[player_rank["rank"]]
                        if cfg.get_feature_flag("aggregate_rank_rr") and cfg.table.get(
                            "rr"
                        ):
                            rank_name += f" ({player_rank['rr']})"

                        # rank rating
                        rr = player_rank["rr"]

                        # short peak rank string
                        peak_rank_act = f" (e{player_rank['peak_rank_ep']}a{player_rank['peak_rank_act']})"
                        if not cfg.get_feature_flag("peak_rank_act"):
                            peak_rank_act = ""
                        # peak rank
                        peak_rank = (
                            NUMBER_TO_RANKS[player_rank["peak_rank"]] + peak_rank_act
                        )

                        # previous rank
                        previous_rank = NUMBER_TO_RANKS[previous_player_rank["rank"]]

                        # leaderboard
                        leaderboard = player_rank["leaderboard"]

                        hs = colors.get_gradient(hs)
                        wr = (
                            colors.get_gradient(player_rank["wr"])
                            + f" ({player_rank['number_of_games']})"
                        )

                        if int(leaderboard) > 0:
                            is_leaderboard_needed = True

                        # level
                        level = player_color

                        table.add_row_table(
                            [
                                party_icon,
                                agent,
                                name,
                                "",
                                rank_name,
                                rr,
                                peak_rank,
                                previous_rank,
                                leaderboard,
                                hs,
                                wr,
                                kd,
                                level,
                            ]
                        )

                        heartbeat_data["players"][player["Subject"]] = {
                            "name": names[player["Subject"]],
                            "partyNumber": party_num if party_icon != "" else 0,
                            "agent": agent_dict[player["CharacterID"].lower()],
                            "rank": player_rank["rank"],
                            "peakRank": player_rank["peak_rank"],
                            "peakRankAct": peak_rank_act,
                            "level": player_level,
                            "rr": rr,
                            "kd": player_stats["kd"],
                            "headshotPercentage": player_stats["hs"],
                            "winPercentage": f"{player_rank['wr']} ({player_rank['numberofgames']})",
                        }

            if game_state == "MENUS":
                already_played_with = []
                player_dict = menu.get_party_members(Requests.puuid, presence)
                names = names_class.get_names_from_puuids(player_dict)
                players_loaded = 1
                with richConsole.status("Loading Players...") as status:
                    # sort players by levels
                    player_dict.sort(
                        key=lambda players: players["PlayerIdentity"].get(
                            "AccountLevel"
                        ),
                        reverse=True,
                    )
                    seen = []
                    for player in player_dict:

                        if player not in seen:
                            status.update(
                                f"Loading players... [{players_loaded}/{len(player_dict)}]"
                            )
                            players_loaded += 1
                            party_icon = PARTY_ICON_LIST[0]
                            player_rank = rank.get_rank(player["Subject"], season_id)
                            previous_player_rank = rank.get_rank(
                                player["Subject"], previous_season_id
                            )
                            if player["Subject"] == Requests.puuid:
                                if cfg.get_feature_flag("discord_rpc"):
                                    rpc.set_data(
                                        {
                                            "rank": player_rank["rank"],
                                            "rank_name": colors.escape_ansi(
                                                NUMBER_TO_RANKS[player_rank["rank"]]
                                            )
                                            + " | "
                                            + str(player_rank["rr"])
                                            + "rr",
                                        }
                                    )

                            player_stats = pstats.get_stats(player["Subject"])
                            hs = player_stats["hs"]
                            kd = player_stats["kd"]

                            player_level = player["PlayerIdentity"].get("AccountLevel")
                            player_color = colors.level_to_color(player_level)

                            # agent
                            agent = ""

                            # name
                            name = color(names[player["Subject"]], fore=(76, 151, 237))

                            # rank
                            rank_name = NUMBER_TO_RANKS[player_rank["rank"]]
                            if cfg.get_feature_flag(
                                "aggregate_rank_rr"
                            ) and cfg.table.get("rr"):
                                rank_name += f" ({player_rank['rr']})"

                            # rank rating
                            rr = player_rank["rr"]

                            # short peak rank string
                            peak_rank_act = f" (e{player_rank['peak_rank_ep']}a{player_rank['peak_rank_act']})"
                            if not cfg.get_feature_flag("peak_rank_act"):
                                peak_rank_act = ""

                            # peak rank
                            peak_rank = (
                                NUMBER_TO_RANKS[player_rank["peak_rank"]]
                                + peak_rank_act
                            )

                            # previous rank
                            previous_rank = NUMBER_TO_RANKS[
                                previous_player_rank["rank"]
                            ]

                            # leaderboard
                            leaderboard = player_rank["leaderboard"]

                            hs = colors.get_gradient(hs)
                            wr = (
                                colors.get_gradient(player_rank["wr"])
                                + f" ({player_rank['number_of_games']})"
                            )

                            if int(leaderboard) > 0:
                                is_leaderboard_needed = True

                            # level
                            level = player_color

                            table.add_row_table(
                                [
                                    party_icon,
                                    agent,
                                    name,
                                    "",
                                    rank_name,
                                    rr,
                                    peak_rank,
                                    previous_rank,
                                    leaderboard,
                                    hs,
                                    wr,
                                    kd,
                                    level,
                                ]
                            )

                            heartbeat_data["players"][player["Subject"]] = {
                                "name": names[player["Subject"]],
                                "rank": player_rank["rank"],
                                "peakRank": player_rank["peakrank"],
                                "peakRankAct": peak_rank_act,
                                "level": player_level,
                                "rr": rr,
                                "kd": player_stats["kd"],
                                "headshotPercentage": player_stats["hs"],
                                "winPercentage": f"{player_rank['wr']} ({player_rank['numberofgames']})",
                            }

                    seen.append(player["Subject"])

            title = game_state_dict.get(game_state)
            if title is None:
                time.sleep(9)
            if server != "":
                table.set_title(
                    f"VALORANT status: {title} {colr('- ' + server, fore=(200, 200, 200))}"
                )
            else:
                table.set_title(f"VALORANT status: {title}")
            server = ""
            if title is not None:
                if cfg.get_feature_flag("auto_hide_leaderboard") and (
                    not is_leaderboard_needed
                ):
                    table.set_runtime_col_flag("Pos.", False)

                if game_state == "MENUS":
                    table.set_runtime_col_flag("Party", False)
                    table.set_runtime_col_flag("Agent", False)
                    table.set_runtime_col_flag("Skin", False)

                if game_state == "INGAME":
                    if is_range:
                        table.set_runtime_col_flag("Party", False)
                        table.set_runtime_col_flag("Agent", False)

                # we don't to show the RR column if the "aggregate_rank_rr" feature flag is True.
                table.set_runtime_col_flag(
                    "RR",
                    cfg.table.get("rr")
                    and not cfg.get_feature_flag("aggregate_rank_rr"),
                )

                table.set_caption(f"VALORANT rank yoinker v{VERSION}")
                Server.send_payload("heartbeat", heartbeat_data)
                table.display()
                first_print = False

                if cfg.get_feature_flag("last_played"):
                    if len(already_played_with) > 0:
                        print("\n")
                        for played in already_played_with:
                            print(
                                f"Already played with {played['name']} (last {played['agent']}) {stats.convert_time(played['time_diff'])} ago. (Total played {played['times']} times)"
                            )
                            chat_log(
                                f"Already played with {played['name']} (last {played['agent']}) {stats.convert_time(played['time_diff'])} ago. (Total played {played['times']} times)"
                            )
                already_played_with = []
        if cfg.cooldown == 0:
            input("Press enter to fetch again...")
        else:
            pass
except KeyboardInterrupt:
    os._exit(0)
except:
    log(traceback.format_exc())
    print(
        color(
            "The program has encountered an error. If the problem persists, please reach support"
            f" with the logs found in {os.getcwd()}\\logs",
            fore=(255, 0, 0),
        )
    )
    chat_log(
        color(
            "The program has encountered an error. If the problem persists, please reach support"
            f" with the logs found in {os.getcwd()}\\logs",
            fore=(255, 0, 0),
        )
    )
    input("press enter to exit...\n")
    os._exit(1)
