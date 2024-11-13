class PlayerStats:
    def __init__(self, api, log, config):
        self.api = api
        self.log = log
        self.config = config

    # in future rewrite this code
    def get_stats(self, puuid):
        if not self.config.get_table_flag("headshot_percent") and not self.config.get_table_flag("kd"):
            return {
                "kd": "N/a",
                "hs": "N/a"
            }

        response = self.api.fetch('pd',
                                  f"/mmr/v1/players/{puuid}/competitiveupdates?startIndex=0&endIndex=1&queue=competitive",
                                  "get")
        try:
            r = self.api.fetch('pd', f"/match-details/v1/matches/{response.json()['Matches'][0]['MatchID']}",
                               "get")

            # too old match
            if r.status_code == 404:
                return {
                    "kd": "N/a",
                    "hs": "N/a"
                }

            total_hits = 0
            total_headshots = 0
            for rround in r.json()["roundResults"]:
                for player in rround["playerStats"]:
                    if player["subject"] == puuid:
                        for hits in player["damage"]:
                            total_hits += hits["legshots"]
                            total_hits += hits["bodyshots"]
                            total_hits += hits["headshots"]
                            total_headshots += hits["headshots"]

            for player in r.json()["players"]:
                if player["subject"] == puuid:
                    kills = player["stats"]["kills"]
                    deaths = player["stats"]["deaths"]

            if deaths == 0:
                kd = kills
            elif kills == 0:
                kd = 0
            else:
                kd = round(kills / deaths, 2)
            final = {
                "kd": kd,
                "hs": "N/a"
            }

            # no hits
            if total_hits == 0:
                return final
            hs = int((total_headshots / total_hits) * 100)
            final["hs"] = hs
            return final

        # no matches
        except IndexError:
            return {
                "kd": "N/a",
                "hs": "N/a"
            }
