import base64
import json
import time


class Presences:
    def __init__(self, api, log):
        self.api = api
        self.log = log

    @staticmethod
    def decode_presence(private):
        if private and "{" not in str(private):
            presence_dict = json.loads(base64.b64decode(str(private)).decode())
            if presence_dict.get("isValid"):
                return presence_dict
        return {
            "isValid": False,
            "partyId": 0,
            "partySize": 0,
            "partyVersion": 0,
        }

    def get_presence(self):
        presences = self.api.fetch(
            url_type="local", endpoint="/chat/v4/presences", method="get"
        )
        return presences["presences"]

    def get_game_state(self, presences):
        return self.get_private_presence(presences)["sessionLoopState"]

    def get_private_presence(self, presences):
        for presence in presences:
            if presence["puuid"] == self.api.puuid:
                if (
                    presence.get("championId")
                    or presence.get("product") == "league_of_legends"
                ):
                    return None
                else:
                    return json.loads(base64.b64decode(presence["private"]))

    def wait_for_presence(self, players_uuids):
        while True:
            presence = self.get_presence()
            for puuid in players_uuids:
                if puuid not in str(presence):
                    time.sleep(1)
                    continue
            break
