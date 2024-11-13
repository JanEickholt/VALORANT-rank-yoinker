import requests


class Names:
    def __init__(self, api, log):
        self.api = api
        self.log = log

    @staticmethod
    def get_players_puuid(players):
        return [player["Subject"] for player in players]

    def get_name_from_puuid(self, puuid):
        response = requests.put(self.api.pd_url + "/name-service/v2/players", headers=self.api.get_headers(),
                                json=[puuid], verify=False)
        return response.json()[0]["GameName"] + "#" + response.json()[0]["TagLine"]

    def get_multiple_names_from_puuid(self, puuids):
        response = requests.put(self.api.pd_url + "/name-service/v2/players", headers=self.api.get_headers(),
                                json=puuids, verify=False)

        if 'errorCode' in response.json():
            self.log(f'{response.json()["errorCode"]}, new token retrieved')
            response = requests.put(self.api.pd_url + "/name-service/v2/players",
                                    headers=self.api.get_headers(refresh=True), json=puuids, verify=False)

        name_dict = {player["Subject"]: f"{player['GameName']}#{player['TagLine']}"
                     for player in response.json()}
        return name_dict

    def get_names_from_puuids(self, players):
        players_puuid = []
        for player in players:
            players_puuid.append(player["Subject"])
        return self.get_multiple_names_from_puuid(players_puuid)
