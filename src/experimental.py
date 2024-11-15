import requests


class Experimental:
    def __init__(self, log):
        self.log = log

    def get_views(self, name: str):
        response_views = requests.get(
            f"https://tracker.gg/valorant/profile/riot/{name.split('#')[0]}%23{name.split('#')[1]}/overview"
        ).text
        try:
            result = response_views.split("views")[1].split(">")[-1]
            int(result)
            self.log(f"retrieved views {result}, {name}")
            return int(result)
        except ValueError:
            self.log(f"retrieved None views , {name}")
            return None
