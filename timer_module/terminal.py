from abc import ABC


class ANSICode(ABC):
    def __init__(self):
        self.value: str


class ResetANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[0m"


class RedANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[31m"


class GreenANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[32m"


class YellowANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[33m"


class BlueANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[34m"


class MagentaANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[35m"


class CyanANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[36m"


class WhiteANSI(ANSICode):
    def __init__(self):
        self.value: str = "\033[37m"


class Terminal:
    def __init__(self, ansi_color: ANSICode = WhiteANSI()):
        self.ansi_color = ansi_color
        self.ansi_reset = ResetANSI()

    def write(self, text: str):
        string = "{}{}{}"
        ansi_color_val = self.ansi_color.value
        ansi_reset_val = self.ansi_reset.value
        string = string.format(ansi_color_val, text, ansi_reset_val)
        print(string)

    def set_ansi_color(self, ansi_color: ANSICode):
        self.ansi_color = ansi_color
