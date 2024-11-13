from colr import color
from src.constants import TIER_DICT
import re


class Colors:
    def __init__(self, hide_names, agent_dict, agent_color_list):
        self.hide_names = hide_names
        self.agent_dict = agent_dict
        self.tier_dict = TIER_DICT
        self.agent_color_list = agent_color_list

    def get_color_from_team(self, team, name, player_puuid, self_puuid, agent=None, party_members=None):
        orig_name = name
        if agent is not None:
            if self.hide_names:
                if agent != "":
                    name = self.agent_dict[agent.lower()]
                else:
                    name = "Player"
        if team == 'Red':
            if player_puuid not in party_members:
                team_color = color(name, fore=(238, 77, 77))
            else:
                team_color = color(orig_name, fore=(238, 77, 77))
        elif team == 'Blue':
            if player_puuid not in party_members:
                team_color = color(name, fore=(76, 151, 237))
            else:
                team_color = color(orig_name, fore=(76, 151, 237))
        else:
            team_color = ''
        if player_puuid == self_puuid:
            team_color = color(orig_name, fore=(221, 224, 41))
        return team_color

    def get_rgb_color_from_skin(self, skin_id, valo_api_skins):
        for skin in valo_api_skins.json()["data"]:
            if skin_id == skin["uuid"]:
                return self.tier_dict[skin["contentTierUuid"]]

    @staticmethod
    def level_to_color(level):
        if level >= 400:
            return color(level, fore=(102, 212, 212))
        elif level >= 300:
            return color(level, fore=(207, 207, 76))
        elif level >= 200:
            return color(level, fore=(71, 71, 204))
        elif level >= 100:
            return color(level, fore=(241, 144, 54))
        elif level < 100:
            return color(level, fore=(211, 211, 211))

    def get_agent_from_uuid(self, agent_uuid):
        agent = str(self.agent_dict.get(agent_uuid))
        if self.agent_color_list.get(agent.lower()):
            agent_color = self.agent_color_list.get(agent.lower())
            return color(agent, fore=agent_color)
        else:
            return agent

    @staticmethod
    def get_gradient(number):
        try:
            number = int(number)
        except ValueError:
            return color("N/a", fore=(46, 46, 46))
        dark_red = (64, 15, 10)
        yellow = (140, 119, 11)
        green = (18, 204, 25)
        white = (255, 255, 255)
        gradients = {
            (0, 25): (dark_red, yellow),
            (25, 50): (yellow, green),
            (50, 100): (green, white)
        }
        f = []
        for gradient in gradients:
            if gradient[0] <= number <= gradient[1]:
                for rgb in range(3):
                    if gradients[gradient][0][rgb] > gradients[gradient][1][rgb]:
                        first_higher = True
                    else:
                        first_higher = False
                    if first_higher:
                        offset = gradients[gradient][0][rgb] - gradients[gradient][1][rgb]
                    else:
                        offset = gradients[gradient][1][rgb] - gradients[gradient][0][rgb]
                    if first_higher:
                        f.append(int(gradients[gradient][0][rgb] - offset * number / gradient[1]))
                    else:
                        f.append(int(offset * number / gradient[1] + gradients[gradient][0][rgb]))
                return color(number, fore=f)

    @staticmethod
    def escape_ansi(line):
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)
