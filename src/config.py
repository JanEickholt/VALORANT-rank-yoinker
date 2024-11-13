import json
from io import TextIOWrapper
from json import JSONDecodeError
import requests
import os

from src.constants import DEFAULT_CONFIG


def apply_defaults(cls):
    for name, value in DEFAULT_CONFIG.items():
        setattr(cls, name, value)
    return cls


@apply_defaults
class Config:
    def __init__(self, log):
        self.log = log

        if not os.path.exists("config.json"):
            self.log("config.json not found, creating new one")
            with open("config.json", "w") as file:
                config = self.config_dialog(file)

        try:
            with open("config.json") as file:
                self.log("config opened")
                config = json.load(file)

                # getting the keys in the file
                keys = [k for k in config.keys()]

                # getting the keys in the self.default
                default_keys = [k for k in DEFAULT_CONFIG.keys()]

                # comparing the keys in the file to the keys in the default and returning the missing keys
                missing_keys = list(filter(lambda x: x not in keys, default_keys))

                if len(missing_keys) > 0:
                    self.log("config.json is missing keys")
                    with open("config.json", "w") as w:
                        self.log(f"missing keys: " + str(missing_keys))
                        for key in missing_keys:
                            config[key] = DEFAULT_CONFIG[key]

                        self.log("Successfully added missing keys")
                        json.dump(config, w, indent=4)

        except JSONDecodeError:
            self.log("invalid file")
            with open("config.json", "w") as file:
                config = self.config_dialog(file)
        finally:
            config = DEFAULT_CONFIG | config
            for name, value in config.items():
                setattr(self, name, value)

            self.log(f"config class dict: {self.__dict__}")
            self.log(f"got cooldown with value '{self.cooldown}'")

            # if the user manually entered a wrong name into the config file,
            # this will be the default until changed by the user.
            if not self.weapon_check(config["weapon"]):
                self.weapon = "vandal"
            else:
                self.weapon = config["weapon"]

    @staticmethod
    def weapon_check(name):
        if name in [
            weapon["displayName"]
            for weapon in requests.get("https://valorant-api.com/v1/weapons").json()[
                "data"
            ]
        ]:
            return True
        else:
            return False

    def get_feature_flag(self, key):
        return self.__dict__.get("flags", DEFAULT_CONFIG["flags"]).get(
            key, DEFAULT_CONFIG["flags"][key]
        )

    def get_table_flag(self, key):
        return self.__dict__.get("table", DEFAULT_CONFIG["flags"]).get(
            key, DEFAULT_CONFIG["table"][key]
        )

    def config_dialog(self, file_to_write: TextIOWrapper):
        self.log("color config prompt called")
        json_to_write = DEFAULT_CONFIG

        json.dump(json_to_write, file_to_write, indent=4)
        return json_to_write
