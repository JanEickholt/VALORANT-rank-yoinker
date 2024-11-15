import glob
import os
import time


class Logging:
    # log_file_opened is a variable that keeps track of the log file status.
    # it is initialized as False to represent the log file wasn't open.
    def __init__(self):
        self.log_file_opened = False

    # `log_string` is a string that is the log message that will be written to the log file.
    def log(self, log_string: str):
        logs_directory = os.getcwd() + "/logs"

        if not os.path.exists(logs_directory):
            os.mkdir(logs_directory)

        log_files = glob.glob(r"logs/log-*.txt")

        # the log file numbers are extracted from the filenames
        log_file_numbers = [int(file[9:-4]) for file in log_files]

        # if log_file_numbers list is empty, append the value 0 to it.
        # this ensures that the list always contains at least one value.
        if not log_file_numbers:
            log_file_numbers.append(0)

        log_file_name = f"logs/log-{max(log_file_numbers) + 1 if not self.log_file_opened else max(log_file_numbers)}.txt"

        with open(log_file_name, "a" if self.log_file_opened else "w") as log_file:
            self.log_file_opened = True

            current_time = time.strftime(
                "%Y.%m.%d-%H.%M.%S", time.localtime(time.time())
            )
            log_file.write(
                f"[{current_time}] {log_string.encode('ascii', 'replace').decode()}\n"
            )
