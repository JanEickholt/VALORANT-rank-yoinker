class Rank:
    def __init__(self, api, log, content, ranks_before):
        self.api = api
        self.log = log
        self.ranks_before = ranks_before
        self.content = content
        self.requestMap = {}

    def get_request(self, puuid):
        if puuid in self.requestMap:
            return self.requestMap[puuid]

        response = self.api.fetch("pd", f"/mmr/v1/players/{puuid}", "get")
        self.requestMap[puuid] = response
        return response

    def invalidate_cached_responses(self):
        self.requestMap = {}

    # in future rewrite this code
    def get_rank(self, puuid, season_id):
        response = self.get_request(puuid)
        final = {
            "rank": None,
            "rr": None,
            "leaderboard": None,
            "peak_rank": None,
            "wr": None,
            "number_of_games": 0,
            "peak_rank_act": None,
            "peak_rank_ep": None,
            "status_good": None,
            "status_code": None,
        }
        try:
            if response.ok:
                r = response.json()
                rank_tier = r["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][
                    season_id
                ]["CompetitiveTier"]
                if int(rank_tier) >= 21:

                    final["rank"] = rank_tier
                    final["rr"] = r["QueueSkills"]["competitive"][
                        "SeasonalInfoBySeasonID"
                    ][season_id]["RankedRating"]
                    final["leaderboard"] = r["QueueSkills"]["competitive"][
                        "SeasonalInfoBySeasonID"
                    ][season_id]["LeaderboardRank"]
                elif int(rank_tier) not in (0, 1, 2):
                    final["rank"] = rank_tier
                    final["rr"] = r["QueueSkills"]["competitive"][
                        "SeasonalInfoBySeasonID"
                    ][season_id]["RankedRating"]
                    final["leaderboard"] = 0

                else:
                    final["rank"] = 0
                    final["rr"] = 0
                    final["leaderboard"] = 0

            else:
                self.log("failed getting rank")
                self.log(response.text)
                final["rank"] = 0
                final["rr"] = 0
                final["leaderboard"] = 0
        except TypeError:
            final["rank"] = 0
            final["rr"] = 0
            final["leaderboard"] = 0
        except KeyError:
            final["rank"] = 0
            final["rr"] = 0
            final["leaderboard"] = 0
        max_rank = final["rank"]
        max_rank_season = season_id
        seasons = r["QueueSkills"]["competitive"].get("SeasonalInfoBySeasonID")
        if seasons is not None:
            for season in r["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"]:
                if (
                    r["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][season][
                        "WinsByTier"
                    ]
                    is not None
                ):
                    for win_by_tier in r["QueueSkills"]["competitive"][
                        "SeasonalInfoBySeasonID"
                    ][season]["WinsByTier"]:
                        if season in self.ranks_before:
                            if int(win_by_tier) > 20:
                                win_by_tier = int(win_by_tier) + 3
                        if int(win_by_tier) > max_rank:
                            max_rank = int(win_by_tier)
                            max_rank_season = season
            final["peak_rank"] = max_rank
        else:
            final["peak_rank"] = max_rank
        try:
            wins = r["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][season_id][
                "NumberOfWinsWithPlacements"
            ]
            total_games = r["QueueSkills"]["competitive"]["SeasonalInfoBySeasonID"][
                season_id
            ]["NumberOfGames"]
            final["number_of_games"] = total_games
            try:
                wr = int(wins / total_games * 100)

            # no loses
            except ZeroDivisionError:
                wr = 100

        # haven't played this season, no data?
        except (KeyError, TypeError):
            wr = "N/a"

        final["wr"] = wr
        final["status_good"] = response.ok
        final["status_code"] = response.status_code

        # peak rank act and ep
        peak_rank_act_ep = self.content.get_act_episode_from_act_id(max_rank_season)
        final["peak_rank_act"] = peak_rank_act_ep["act"]
        final["peak_rank_ep"] = peak_rank_act_ep["episode"]
        return final
