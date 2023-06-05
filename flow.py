# Each Flow Entry has following components:
# - Match Fields: used to match againse packets: ingress port, packet headers, metadata from previous tables.
# - Priority: Precedence of the Flow Entry. The higher value, the earlier check
# - Counters: Number of packets matched,...
# - Instruction: Modify ACTION SET or PIPELINE Processing
# - Timeouts: [Unit: seconds] Switch automatic remove this FE after the given number of seconds from logged time.
#       + Hard Timeout: Log and Using FE's arrival time
#       + Idle Timeout: Log and Using last matched Packet's arrival time
# - Cookie: Chosen by the Controller. Not used when processing packets
# --> Match Fields and Priority used to identify a UNIQUE Flow Entry for the specified packet.
# The packet is match againse the table (all flows) and the highest priority matched flow entry
# is selected and Update counter for that FE + Apply Instruction Set.
# If there are many (with same priority) -> Selected FE is undefined.

# FE Removal: 3 ways
# - Request to Controller.
# - Switch Flow Expiry Mechanism: Automatic by Switch, using config in FE.
# - Optional Switch Eviction Mechanism: Ex: Reclaim resource

# FE Counters: Received Packets + Received Bytes + Duration [Seconds and Nanoseconds]

from instruction import InstructionBuilder, instruction2string, APPLY_ACTIONS_INS
from match import MatchBuilder, match2string


APPLY_ACTIONS_INS = "apply-actions"
CLEAR_ACTIONS_INS = "clear-actions"
WRITE_ACTIONS_INS = "write-actions"
GOTO_TABLE_INS = "go-to-table"


class FlowBuilder(object):
    def __init__(self) -> None:
        self.data = {}
        self.temp_instructions = []

    def set_generic_info(
        self,
        id: str,
        name: str = None,
        priority: int = None,
        idle_timeout: int = None,
        hard_timeout: int = None,
        cookie: int = None,
    ):
        if id is not None:
            self.data["id"] = id
        if name is not None:
            self.data["flow-name"] = name
        if priority is not None:
            self.data["priority"] = priority
        if idle_timeout is not None:
            self.data["idle-timeout"] = idle_timeout
        if hard_timeout is not None:
            self.data["hard-timeout"] = hard_timeout
        if cookie is not None:
            self.data["cookie"] = cookie
        # if cookie is None:
        #     cookie = time.time() * 1000
        # self.data["cookie"] = int(cookie)
        return self

    def create_match_builder(self) -> MatchBuilder:
        return MatchBuilder(owner=self)

    def create_instruction_builder(
        self, type: str = APPLY_ACTIONS_INS
    ) -> InstructionBuilder:
        return InstructionBuilder(type, owner=self)

    def build(self) -> "Flow":
        self.data["instructions"] = {"instruction": self.temp_instructions}
        return Flow(self.data)

    def owner_callback(self, data):
        if isinstance(data, MatchBuilder):
            self.data["match"] = data.build()
        elif isinstance(data, InstructionBuilder):
            inst = data.build()
            inst["order"] = len(self.temp_instructions)
            self.temp_instructions.append(inst)


def create_basic_flow(
    id: str,
    src_mac: str,
    dest_mac: str,
    port_out_number: int | str,
    *,
    name: str = None,
    priority: int = 0,
):
    return (
        FlowBuilder()
        .set_generic_info(id, name, priority, 0, 0)
        .create_match_builder()
        .add_ethernet_criterion(None, src_mac, dest_mac)
        .owner()
        .create_instruction_builder()
        .add_output_action(port_out_number)
        .owner()
        .build()
    )


def create_drop_flow(
    id: str,
    src_mac: str = None,
    dest_mac: str = None,
    *,
    name: str = None,
    priority: int = 0,
):
    return (
        FlowBuilder()
        .set_generic_info(id, name, priority, 0, 0)
        .create_match_builder()
        .add_ethernet_criterion(None, src_mac, dest_mac)
        .owner()
        .create_instruction_builder()
        .add_drop_action()
        .owner()
        .build()
    )


def create_lldp_flow(id, *, priority: int = 100):
    return (
        FlowBuilder()
        .set_generic_info(id, priority=priority)
        .create_match_builder()
        .add_ethernet_criterion(0x88CC)
        .owner()
        .create_instruction_builder()
        .add_output_action("CONTROLLER")
        .owner()
        .build()
    )


class Table(object):
    def __init__(self, data: dict) -> None:
        self.data = data
        self.id = data.get("id", None)
        self.name = data.get("name", self.id)

    def __repr__(self) -> str:
        ret = f"{'TABLE':>6} [{self.id:>4}]: "
        stat = self.data.get(
            "opendaylight-flow-table-statistics:flow-table-statistics", None
        )
        if stat is not None:
            ret += f'[Active Flows = {stat.get("active-flows", None)}] [PKT Looked Up = {stat.get("packets-looked-up", None)}] [PKT Matched = {stat.get("packets-matched", None)}] '
        if self.flows:
            ret += f'Flows: {", ".join([str(fid) for fid in sorted(self.flows)])}'
        # ret = f"=====================     TABLE {str(self.name):>13}     =====================\n"
        # ret += f"ID              : {self.id}\n"

        # stat = table.get(
        #     "opendaylight-flow-table-statistics:flow-table-statistics", None
        # )
        # if stat is not None:
        #     ret += f'Statistics      : [Active Flows = {stat.get("active-flows", None)}] [PKT Looked Up = {stat.get("packets-looked-up", None)}] [PKT Matched = {stat.get("packets-matched", None)}]\n'

        # ret += f'Flows           : {", ".join([str(fid) for fid in self.flows])}'
        return ret

    @property
    def flows(self):
        flows = {}
        for fitem in self.data.get("flow", []):
            flows[fitem["id"]] = Flow(fitem)
        return flows


class Flow(object):
    def __init__(self, data: dict) -> None:
        self.data = data
        self.id = data.get("id", None)
        self.name = data.get("flow-name", self.id)

    def __repr__(self) -> str:
        flow = self.data
        ret = f"-----  FLOW {self.name:>12}  -----\n"
        ret += f"ID           : {self.id}\n"
        ret += f"Priority     : {flow.get('priority', None)}\n"
        ret += f"Timeout      : [idle] {flow.get('idle-timeout', None)} / [hard] {flow.get('hard-timeout', None)}\n"
        statistics = flow.get("opendaylight-flow-statistics:flow-statistics", None)
        if statistics is not None:
            if "duration" in statistics:
                d = statistics["duration"]
                duration = d["second"] + d["nanosecond"] * 1e-9
            else:
                duration = None
            ret += f"Statistics   : [Packets = {statistics.get('packet-count', None)}] [Bytes = {statistics.get('byte-count', None)}] [Duration = {duration}s]\n"

        ret += f"Matches      : {match2string(flow.get('match', {}))}\n"

        ret += f"Instructions :\n"
        instructions = flow.get("instructions", None)
        if instructions:
            for ins in instructions.get("instruction", []):
                ret += f"+ {instruction2string(ins)}\n"
        return ret

    def to_dict(self):
        return self.data
