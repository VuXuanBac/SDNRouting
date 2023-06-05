################################ INSTRUCTION ########################################
# INSTRUCTION: instructions are attached to a flow entry and describe the OpenFlow processing that
# happens when a packet matches the flow entry.

# An instruction either
# + Modifies pipeline processing: Directing the packet to another flow table, or
# + Contains a set of actions to add to the action set
# + Contains a list of actions to apply immediately to the packet.

# Instruction Type:
# - Apply Actions <actions>: Apply <actions> immediately and AT SAME TIME, does not change ACTION SET
# - Clear Actions: Clears all the ACTION SET immediately.
# - Write Actions <actions>: Merge <actions> to current ACTION SET, overwrite for same type action.
# - GoTo Table <table_id>: Go to Table with id <table_id> [Move Forward Only]

# Instruction Set in each FE contains <= 1 instruction of each type, and applied in following order
# Apply -> Clear -> Write -> GoTo Table

################################## ACTION ######################################
# ACTION: an operation that forwards the packet to a port or modifies the packet, such as decrementing the TTL field. Actions may be specified as part of the instruction set associated with a
# flow entry or in an action bucket associated with a group entry. Actions may be accumulated in
# the Action Set of the packet or applied immediately to the packet.

# ACTION SET: a set of actions associated with the packet that are accumulated while the packet
# is processed by each table and that are executed when the instruction set instructs the packet to
# exit the processing pipeline.

# Apply Actions in Action Set in following orders [regardless of the added order]:
#       Copy TTL inwards -> Pop -> Push (MPLS -> PBB -> VLAN)
#       -> Copy TTL outwards -> Decrement TTL -> Set Fields
#       -> QOS -> Group -> Output -> DROP [default]

# Action Type:
# - Output: Forward a packet to a specified Port.
# - Drop:
# - Change TTL: Modify (Set/Decrement) TPv4 TTL, IPv6 Hop Limit, MPLS TTL

# <actions> in Apply Actions Instruction is an ordered list. Each action is applied in order.

APPLY_ACTIONS_INS = "apply-actions"
CLEAR_ACTIONS_INS = "clear-actions"
WRITE_ACTIONS_INS = "write-actions"
GOTO_TABLE_INS = "go-to-table"


class InstructionBuilder(object):
    def __init__(self, type: str = APPLY_ACTIONS_INS, owner=None) -> None:
        self._owner = owner
        self.type = type
        if type in [APPLY_ACTIONS_INS, CLEAR_ACTIONS_INS, WRITE_ACTIONS_INS]:
            self.data = []  # Action Lists
            self.ins_group = 1
        elif type in [GOTO_TABLE_INS]:
            self.data = None
            self.ins_group = 2
        else:
            raise Exception(
                f"Instruction type {type} not found. Used predefined values only."
            )

    def new_instance(self, type: str = APPLY_ACTIONS_INS):
        self._owner.owner_callback(self)
        return InstructionBuilder(type, owner=self._owner)

    def owner(self):
        self._owner.owner_callback(self)
        return self._owner

    # @staticmethod
    # def from_dict(info: dict):
    #     for k, v in info.items():
    #         if k in InstructionBuilder.name_key_map.values():
    #             ret = InstructionBuilder(k)
    #             if "action" in v:
    #                 ret.data = v["action"]
    #             elif "table_id" in v:
    #                 ret.data = v["table_id"]
    #             return ret
    #     return None

    def add_table_id(self, table_id: str | int):
        if self.ins_group == 2:
            self.data = table_id
        return self

    def add_output_action(self, output_to: int | str, max_length: int = 65535):
        if self.ins_group == 1:
            self.data.append(
                {
                    "order": len(self.data),
                    "output-action": {
                        "output-node-connector": str(output_to),
                        "max-length": max_length,
                    },
                }
            )
        return self

    def add_drop_action(self):
        if self.ins_group == 1:
            self.data.append({"order": len(self.data), "drop-action": {}})
        return self

    def add_decrease_network_ttl_action(self):
        if self.ins_group == 1:
            self.data.append({"order": len(self.data), "dec-nw-ttl": {}})
        return self

    def add_set_network_ttl_action(self, ttl: int):
        if self.ins_group == 1:
            self.data.append(
                {"order": len(self.data), "set-nw-ttl-action": {"nw-ttl": ttl}}
            )
        return self

    def add_loopback_action(self):
        if self.ins_group == 1:
            self.data.append({"order": len(self.data), "loopback-action": {}})
        return self

    def add_set_next_hop_action(self, addr: str):
        if self.ins_group == 1:
            if "." in addr:
                d = {
                    "order": len(self.data),
                    "set-next-hop-action": {"ipv4-address": addr},
                }
            else:
                d = {
                    "order": len(self.data),
                    "set-next-hop-action": {"ipv6-address": addr},
                }
            self.data.append(d)
        return self

    def build(self) -> dict:
        if self.ins_group == 1:
            return {self.type: {"action": self.data}}
        elif self.ins_group == 2:
            return {self.type: {"table_id": self.data}}

    # def _parse_action(action: dict, key_value_sep: str) -> str:
    #         actstr = ""
    #         ind = None
    #         for name, data in action.items():
    #             if name == "order":
    #                 ind = data
    #             elif "action" in name:
    #                 actstr = Instruction._parse_names[name]
    #                 for k, v in data.items():
    #                     if k in Instruction._parse_names:
    #                         actstr += f"[{Instruction._parse_names[k]}{key_value_sep}{v}]"
    #         return f"{ind}: {actstr}"

    # def parse(self, item_sep="\n", key_value_sep=" = ") -> str:
    #         ret = f"{Instruction._parse_names[self.type]}"
    #         if self.ins_group == 2:  # goto table
    #             ret += self.data
    #         elif self.ins_group == 1:
    #             ret += item_sep.join(
    #                 [
    #                     Instruction._parse_action(action, key_value_sep)
    #                     for action in sorted(self.data, key=lambda action: action["order"])
    #                 ]
    #             )
    #         return ret


_parse_names = {
    APPLY_ACTIONS_INS: "APPLY ACTIONS",
    CLEAR_ACTIONS_INS: "CLEAR ACTIONS",
    WRITE_ACTIONS_INS: "WRITE ACTIONS",
    GOTO_TABLE_INS: "GO TO TABLE",
    "loopback-action": "LOOP BACK",
    "output-action": "OUTPUT",
    "drop-action": "DROP",
    "set-next-hop-action": "SET NEXT HOP",
    "dec-nw-ttl": "DECREMENT TTL",
    "set-nw-ttl-action": "SET TTL",
    "output-node-connector": "To",
    "max-length": "Max Length",
    "nw-ttl": "TTL",
    "ipv4-address": "Address",
    "ipv6-address": "Address",
}


def action2string(action: dict, key_value_sep: str) -> str:
    ind, actstr = None, ""
    for name, data in action.items():
        if name == "order":
            ind = data
        elif "action" in name:
            actstr = _parse_names[name]
            for k, v in data.items():
                if k in _parse_names:
                    actstr += f" [{_parse_names[k]}{key_value_sep}{v}] "
    return f"[{ind:>2}]: {actstr}"


def instruction2string(instruction: dict, item_sep="\n\t", key_value_sep=" = ") -> str:
    # print(instruction)
    ind, insstr = None, ""
    for k, v in instruction.items():
        if k == "order":
            ind = v
        elif k in [APPLY_ACTIONS_INS, WRITE_ACTIONS_INS, CLEAR_ACTIONS_INS]:
            action_list = v.get("action", [])
            insstr = f"{_parse_names[k]}:{item_sep}"
            insstr += item_sep.join(
                [
                    action2string(action, key_value_sep)
                    for action in sorted(
                        action_list, key=lambda action: action.get("order", None)
                    )
                ]
            )
        elif k in [GOTO_TABLE_INS]:
            insstr = f"{_parse_names[k]} {v}"

    return f"[{ind:>2}]: {insstr}"
