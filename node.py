from flow import Table


class Port(object):
    def __init__(
        self,
        owner: "Node",
        id: str,
        name: str = None,
        port_number: int = None,
        mac: str = None,
        state: str = None,
        statistics: dict = None,
    ) -> None:
        self.id = id
        self.port_number = port_number
        self.name = name
        self.mac = mac
        self.state = state
        self.statistics = statistics
        self.peer = None
        self.owner = owner

    def __repr__(self) -> str:
        peer_name = "None" if self.peer is None else self.peer.name
        return f'[{("unk" if self.port_number is None else str(self.port_number)):^9}] : {self.name:<10}: {self.mac} : {peer_name:>10} : {self.state}'


def parse_port_list(ports: dict[Port] | list[Port]) -> str:
    ret = (
        f"         #      |   Name    |        MAC        |    Peer    |    State   \n"
    )
    pps = ports.values() if isinstance(ports, dict) else ports
    ret += "\n".join([f"   {port}" for port in sorted(pps, key=lambda p: p.name)])
    return ret


class Node(object):
    def __init__(
        self,
        id: str,
        node_type: str = "switch",
        name=None,
        ip=None,
        ports=None,
        data: dict = None,
    ) -> None:
        self.id = id
        self.type = node_type
        self.name = name
        self.ip = ip
        self.ports = ports
        self.data = data

    def set_peer(self, at_port_id: str, peer_node: "Node", peer_port_id: str):
        if self.ports is not None:
            self.ports[at_port_id].peer = peer_node.ports[peer_port_id]

    def get_port_for_peer(self, peer_id: str) -> Port:
        # print("find port with peer", peer_id)
        for port in self.ports.values():
            if port.peer is not None and port.peer.owner.id == peer_id:
                return port
        return None

    @property
    def peers(self):
        ret = {}
        for port_id, port in self.ports.items():
            if port.peer is not None:
                ret[port_id] = port.peer.owner
        return ret

    def __repr__(self) -> str:
        return f"{self.type.upper():>6} [{self.name}]: [ID = {self.id:>5}] [IPv4 = {self.ip}] Ports: {[p.name for p in sorted(self.ports.values(), key=lambda x: x.name)]}"
        # ret = f"=====================     {self.type.upper()} {self.name:>15}     =====================\n"
        # ret += f"ID              : {self.id}\n"
        # ret += f"IPv4 Address    : {self.ip}\n"
        # ret += f"Ports           :\n"
        # ret += parse_port_list(self.ports)
        # return ret


class Host(Node):
    def __init__(self, data: dict) -> None:
        id = data.get("node-id", None)
        if id is None or "host" not in id:
            raise Exception("[data] is not a HOST data")

        addrs = data["host-tracker-service:addresses"]
        if len(addrs) > 1:
            print("WARNING: Host connected many ports:", addrs)

        name = f"h{id[-2:]}"
        ip = addrs[0]["ip"]
        self.mac = addrs[0]["mac"]
        port_id = data["termination-point"][0]["tp-id"]
        is_active = data["host-tracker-service:attachment-points"][0]["active"]
        ports = {
            port_id: Port(
                self,
                port_id,
                f"{name}:unk",
                0,
                self.mac,
                ("active" if is_active else "inactive"),
                None,
            )
        }
        super().__init__(id, "host", name, ip, ports, data)


class Switch(Node):
    def __init__(self, data: dict) -> None:
        id = data.get("id", None)
        if id is None:
            raise Exception("[data] is not a SWITCH data")
        name = data["flow-node-inventory:description"]
        ip = data["flow-node-inventory:ip-address"]

        ports = {}
        for conn in data["node-connector"]:
            ports[conn["id"]] = self._parse_port(conn)

        super().__init__(id, "switch", name, ip, ports, data)

    def _parse_port(self, data: dict):
        id = data.get("id", None)
        port_number = data.get("flow-node-inventory:port-number", None)
        mac = data.get("flow-node-inventory:hardware-address", None)
        name = data.get("flow-node-inventory:name", None)
        state = ", ".join(
            [k for k, v in data.get("flow-node-inventory:state", {}).items() if v]
        )
        statistics = data.get(
            "opendaylight-port-statistics:flow-capable-node-connector-statistics", None
        )
        # endpoint = info['address-tracker:addresses'][0]['id']
        return Port(self, id, name, port_number, mac, state, statistics)

    @property
    def active_tables(self) -> dict[str, Table]:
        raw_table = self.data.get("flow-node-inventory:table", [])
        ret = {}
        for item in raw_table:
            if "flow" in item:
                ret[item["id"]] = Table(item)
        return ret

    @property
    def tables(self) -> dict[str, Table]:
        raw_table = self.data.get("flow-node-inventory:table", [])
        ret = {}
        for item in raw_table:
            ret[item["id"]] = Table(item)
        return ret
