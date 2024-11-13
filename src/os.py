import platform


def get_os():
    """
    this function detects the OS the user is running and if Valorant is officially supported in said platform
    returns ["operating system" (string), "Runs Valorant" (bool)]
    """
    # handles windows operating systems
    if platform.system() == "Windows":
        return f"Windows {platform.win32_ver()[0]} {platform.win32_edition()} {platform.win32_ver()[1]}"
    # handles other operating systems, such as linux or macOS
    else:
        return "Non-Windows operating system"
