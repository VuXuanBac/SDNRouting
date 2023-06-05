# __all__ = ["create_match", "parse_match"]


class MatchBuilder(object):
    def __init__(self, owner=None) -> None:
        self.data = {}
        self._owner = owner

    def add_ingress_port_criterion(self, in_port=None, in_physical_port=None):
        if in_port is not None:
            self.data["in-port"] = in_port
        if in_physical_port is not None:
            self.data["in-phy-port"] = in_physical_port
        return self

    def add_ethernet_criterion(
        self, ether_type=None, ether_src_addr=None, ether_dest_addr=None
    ):
        ether_dict = {}
        if ether_src_addr is not None:
            ether_dict["ethernet-source"] = {"address": ether_src_addr}
        if ether_dest_addr is not None:
            ether_dict["ethernet-destination"] = {"address": ether_dest_addr}
        if ether_type is not None:
            ether_dict["ethernet-type"] = {"type": ether_type}
        self.data["ethernet-match"] = ether_dict
        return self

    def add_layer3_criterion(
        self, l3_protocol="ipv4", l3_src_addr=None, l3_dest_addr=None
    ):
        if l3_protocol is not None:
            if l3_protocol in ["ipv4", "ipv6"]:
                if l3_src_addr is not None:
                    self.data[f"{l3_protocol}-source"] = l3_src_addr
                if l3_dest_addr is not None:
                    self.data[f"{l3_protocol}-destination"] = l3_dest_addr
            else:
                self.data["ip-match"] = {"ip-protocol": l3_protocol}
        return self

    def add_layer4_criterion(
        self, l4_protocol="tcp", l4_src_port=None, l4_dest_port=None
    ):
        if l4_protocol in ["tcp", "udp", "sctp"]:
            if l4_src_port is not None:
                self.data[f"{l4_protocol}-source-port"] = l4_src_port
            if l4_dest_port is not None:
                self.data[f"{l4_protocol}-destination-port"] = l4_dest_port
        return self

    def add_icmp_criterion(self, icmp_version=None, icmp_type=None, icmp_code=None):
        if "6" in str(icmp_version):
            icmp_version = "icmpv6"
        else:
            icmp_version = "icmpv4"

        icmp_dict = {}
        if icmp_type is not None:
            icmp_dict[f"{icmp_version}-type"] = icmp_type
        if icmp_code is not None:
            icmp_dict[f"{icmp_version}-code"] = icmp_code
        self.data[f"{icmp_version}-match"] = icmp_dict
        return self

    def build(self) -> dict:
        return self.data

    def owner(self):
        self._owner.owner_callback(self)
        return self._owner


_parse_names = {
    "in-port": "Port In",
    "in-phy-port": "Port In [Physical]",
    "ethernet-source": "Source [Ethernet]",
    "ethernet-destination": "Destination [Ethernet]",
    "ethernet-type": "Ethernet Frame Type",
    "ip-protocol": "IP Protocol",
    "ipv4-source": "Source [IPv4]",
    "ipv4-destination": "Destination [IPv4]",
    "ipv6-source": "Source [IPv6]",
    "ipv6-destination": "Destination [IPv6]",
    "udp-source-port": "Source [UDP]",
    "udp-destination-port": "Destination [UDP]",
    "tcp-source-port": "Source [TCP]",
    "tcp-destination-port": "Destination [TCP]",
    "sctp-source-port": "Source [SCTP]",
    "sctp-destination-port": "Destination [SCTP]",
    "icmpv4-type": "ICMPv4 Type",
    "icmpv4-code": "ICMPv4 Code",
    "icmpv6-type": "ICMPv6 Type",
    "icmpv6-code": "ICMPv6 Code",
}

# def create_match(
#     in_port=None,
#     in_physical_port=None,
#     ether_type=None,
#     ether_src_addr=None,
#     ether_dest_addr=None,
#     l3_protocol=None,
#     l3_src_addr=None,
#     l3_dest_addr=None,
#     l4_protocol=None,
#     l4_src_port=None,
#     l4_dest_port=None,
#     icmp_version=None,
#     icmp_type=None,
#     icmp_code=None,
# ) -> dict:
#     ret = {}
#     if in_port is not None:
#         ret["in-port"] = in_port
#     if in_physical_port is not None:
#         ret["in-phy-port"] = in_physical_port
#     ########### ETHERNET MATCH ###########
#     ether_dict = {}
#     if ether_src_addr is not None:
#         ether_dict["ethernet-source"] = ether_src_addr
#     if ether_dest_addr is not None:
#         ether_dict["ethernet-destination"] = ether_dest_addr
#     if ether_type is not None:
#         ether_dict["ethernet-type"] = {"type": ether_type}
#     ret["ethernet-match"] = ether_dict

#     if l3_protocol is not None:
#         if l3_protocol in ["ipv4", "ipv6"]:
#             if l3_src_addr is not None:
#                 ret[f"{l3_protocol}-source"] = l3_src_addr
#             if l3_dest_addr is not None:
#                 ret[f"{l3_protocol}-destination"] = l3_dest_addr
#         else:
#             ret["ip-match"] = {"ip-protocol": l3_protocol}

#     if l4_protocol in ["tcp", "udp", "sctp"]:
#         if l4_src_port is not None:
#             ret[f"{l4_protocol}-source-port"] = l4_src_port
#         if l4_dest_port is not None:
#             ret[f"{l4_protocol}-destination-port"] = l4_dest_port

#     if icmp_version in ["icmpv4", "icmpv6"]:
#         icmp_dict = {}
#         if icmp_type is not None:
#             icmp_dict[f"{icmp_version}-type"] = icmp_type
#         if icmp_code is not None:
#             icmp_dict[f"{icmp_version}-code"] = icmp_code
#         ret[f"{icmp_version}-match"] = icmp_dict

#     return ret


def match2string(data: dict, item_sep="\n\t", key_value_sep=" = ") -> str:
    converted = {}
    for k, v in data.items():
        if k in ["ethernet-match", "ip-match", "icmpv4-match", "icmpv6-match"]:
            converted.update(v)
        else:
            converted.update({k: v})

    if "ethernet-type" in converted:
        converted["ethernet-type"] = hex(converted["ethernet-type"].get("type", 0))

    return item_sep + item_sep.join(
        [f"{_parse_names.get(k, k)}{key_value_sep}{v}" for k, v in converted.items()]
    )
