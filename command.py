DEFAULT_ARGUMENT_KEY = ""
LIST_SEPARATOR = ","
DATA_TYPE_KEY = "dtype"
DESCRIPTION_KEY = "description"
DEFAULT_ARGUMENT_NAME_KEY = "name"
DEFAULT_VALUE_KEY = "default"


class CommandParser(object):
    def __init__(self) -> None:
        self.commands = {
            "help": {
                DEFAULT_ARGUMENT_KEY: {
                    DEFAULT_ARGUMENT_NAME_KEY: "command",
                    DATA_TYPE_KEY: str,
                    DEFAULT_VALUE_KEY: None,
                    DESCRIPTION_KEY: "Print this dialog",
                }
            }
        }
        self.callers = {"help": self.print_help}
        self.command_desc = {"help": ""}

    def print_help(self, command: str = None):
        if command in self.commands:
            commands = {command: self.commands[command]}
        else:
            commands = self.commands
        for command, infos in commands.items():
            print(f"COMMAND [{command}]: {self.command_desc[command]}")
            for k, inf in infos.items():
                print(f"-- [{k}]: {inf[DESCRIPTION_KEY]}")

    def register(
        self,
        command_type: str,
        caller: object,
        arg_infos: dict[str, dict],
        description: str = "",
    ):
        infos = {}
        infos.update(arg_infos)
        for arg, info in arg_infos.items():
            if DATA_TYPE_KEY not in info:
                infos[arg][DATA_TYPE_KEY] = str
            elif info[DATA_TYPE_KEY] in [list, "list"] and arg != DEFAULT_ARGUMENT_KEY:
                infos[arg][DATA_TYPE_KEY] = lambda inp: inp.split(LIST_SEPARATOR)
            if DESCRIPTION_KEY not in info:
                infos[arg][
                    DESCRIPTION_KEY
                ] = f"[Data Type: {infos[arg][DATA_TYPE_KEY]}]. [Default = {info.get(DEFAULT_VALUE_KEY, '')}]"
            # if "default" not in info:
            #     infos[arg]["default"] = None
        # for arg in args:
        #     if arg not in arg_infos:
        #         infos[arg] = {"dtype": str}
        self.commands[command_type] = infos
        self.callers[command_type] = caller
        self.command_desc[command_type] = description

    def run(self, input: str):
        try:
            command, kwargs = self.parse(input)
            # print(command, kwargs)
            self.callers[command](**kwargs)
        except Exception as ex:
            return str(ex)

    def parse(self, input: str):
        inps = input.split(" ")
        ret_type = inps[0]
        if ret_type not in self.commands:
            raise Exception(f"Invalid Command Type: {inps[0]}")
        infos = self.commands[ret_type]
        ret_args = {}
        for a in inps[1:]:
            if "=" in a:
                arg_name, arg_value = a.split("=", 2)
                if arg_name in infos:
                    ret_args[arg_name] = infos[arg_name][DATA_TYPE_KEY](arg_value)
            elif DEFAULT_ARGUMENT_KEY in infos:
                converter = infos[DEFAULT_ARGUMENT_KEY][DATA_TYPE_KEY]
                if converter in ["list", list]:
                    ret_args.setdefault(DEFAULT_ARGUMENT_KEY, []).append(a)
                else:
                    ret_args[DEFAULT_ARGUMENT_KEY] = converter(a)
        try:
            for arg in infos:
                if arg not in ret_args:
                    ret_args[arg] = infos[arg][DEFAULT_VALUE_KEY]
        except:
            raise Exception(
                f"Invalid Command Arguments: argument [{arg}] is required in command [{ret_type}]"
            )
        if DEFAULT_ARGUMENT_KEY in ret_args:
            # remove item with key DEFAULT_ARGUMENT_KEY and replace by its DEFAULT_ARGUMENT_NAME_KEY item. Ex: {"": "Hello"} -> {"type": "Hello"}
            default_value = ret_args.pop(DEFAULT_ARGUMENT_KEY)
            ret_args[
                infos[DEFAULT_ARGUMENT_KEY].get(DEFAULT_ARGUMENT_NAME_KEY, "type")
            ] = default_value
        return ret_type, ret_args
