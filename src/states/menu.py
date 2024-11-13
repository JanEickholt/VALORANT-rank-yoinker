class Menu:
    def __init__(self, api, log, presences):
        self.api = api
        self.log = log
        self.presences = presences

    def get_party_json(self, game_players_puuid, presences_dict):
        party_json = {}
        for presence in presences_dict:
            if presence["puuid"] in game_players_puuid:
                decoded_presence = self.presences.decode_presence(presence["private"])
                if decoded_presence["isValid"]:
                    if decoded_presence["partySize"] > 1:
                        try:
                            party_json[decoded_presence["partyId"]].append(presence["puuid"])
                        except KeyError:
                            party_json.update({decoded_presence["partyId"]: [presence["puuid"]]})

        # remove non-in-game parties from with one player in game
        parties_to_delete = []
        for party in party_json:
            if len(party_json[party]) == 1:
                parties_to_delete.append(party)
        for party in parties_to_delete:
            del party_json[party]

        self.log(f"retrieved party json: {party_json}")
        return party_json

    def get_party_members(self, self_puuid, presences_dict):
        res = []
        for presence in presences_dict:
            if presence["puuid"] == self_puuid:
                decoded_presence = self.presences.decode_presence(presence["private"])
                if decoded_presence["isValid"]:
                    party_id = decoded_presence["partyId"]
                    res.append({"Subject": presence["puuid"], "PlayerIdentity": {
                        "AccountLevel": decoded_presence["accountLevel"]}})
        for presence in presences_dict:
            decoded_presence = self.presences.decode_presence(presence["private"])
            if decoded_presence["isValid"]:
                if decoded_presence["partyId"] == party_id and presence["puuid"] != self_puuid:
                    res.append({"Subject": presence["puuid"], "PlayerIdentity": {
                        "AccountLevel": decoded_presence["accountLevel"]}})
        self.log(f"retrieved party members: {res}")
        return res
