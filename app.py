from nettopo import NetworkTopology
from netconfig import NetworkConfig
from connector import Connector
from node import Host, Switch, Port, parse_port_list
from flow import Table, Flow
from command import CommandParser
import json


def parse_dict(type: str, data: dict):
    try:
        if type == "host":
            return Host(data)
        elif type == "switch":
            return Switch(data)
        elif type == "table":
            return Table(data)
        elif type == "flow":
            return Flow(data)
        elif type == "port":
            return Port(data)
    except:
        pass
    return None


class App(object):
    def __init__(
        self,
        server_ip="192.168.1.6",
        server_port=8181,
        auth: tuple = None,
        content_type="application/json",
    ) -> None:
        self.connector = Connector(server_ip, server_port, auth, content_type)
        self.topology = NetworkTopology(self.connector)
        self.config = NetworkConfig(self.connector)
        self._start()

    def _create_app_command_parser(self):
        command_parser = CommandParser()
        command_parser.register(
            "print",
            self.print,
            {
                "active_port": {
                    "default": True,
                    "dtype": bool,
                    "description": "True if want to print active ports only. [Default: True]. [Used in `ports`].",
                },
                "node": {
                    "default": None,
                    "description": "The node name. [Used in `tables`, `flows`, `object`]. [Required in `tables`, `flows`].",
                },
                "table": {
                    "default": None,
                    "dtype": int,
                    "description": "The table id. [Used in `flows`, `object`]. [Required in `flows`].",
                },
                "flow": {
                    "default": None,
                    # "description": "The flow id. [Used in `object`].",
                },
                "datastore": {
                    "default": "operational",
                    "description": "The datastore want to retrive object. Used in `print liveobject`. VALUES: 'operational' [Default], 'config'",
                },
                "": {
                    "name": "type",
                    "description": "Object want to prints. VALUES: hosts, switches, tables, ports, flows, object, liveobject.",
                },
            },
            "Print network details",
        )
        # a = (
        #     "path",
        #     self.set_path,
        #     {
        #         "": {
        #             "dtype": "list",
        #             "name": "nodes",
        #             "description": "The list of node names in path. Must begin and end with hosts.",
        #         },
        #         "table": {
        #             "default": "0",
        #             "description": "The switch's table used to update into. [Default 0]",
        #         },
        #         "priority": {
        #             "default": 5,
        #             "dtype": int,
        #             "description": "The priority of this path. [Default 5]",
        #         },
        #     },
        # )
        command_parser.register(
            "path",
            self.extract_shortest_path,
            {
                "source": {"description": "The node name for the source of the path."},
                "destination": {
                    "description": "The node name for the destination of the path."
                },
                "throughs": {
                    "dtype": list,
                    "default": None,
                    "description": "The nodes that the path must through. [Default: None]",
                },
                "blocks": {
                    "dtype": list,
                    "default": None,
                    "description": "The nodes that the path must NOT through. [Default: None]",
                },
                "cutoff": {
                    "dtype": int,
                    "default": None,
                    "description": "The length limit for the path. [Default: None]",
                },
                "": {
                    "name": "type",
                    "default": "",
                    "description": "Set this value to `set` to update current path to controller. [Default: None]. VALUES: set",
                },
                "table": {
                    "dtype": int,
                    "default": 0,
                    "description": "Table to update this path. [Default: 0]. [Only used with `set`]",
                },
                "priority": {
                    "dtype": int,
                    "default": 5,
                    "description": "Priority for this path. [Default: 5]. [Only used with `set`]",
                },
            },
            "Print shortest path between two nodes with some criterions.",
        )
        command_parser.register(
            "shell",
            self.start_shell,
            {
                "": {
                    "name": "type",
                    "description": "Kind of shell want to open. VALUES: 'path' [for updating paths], 'weight' [for BATCH updating link's weight]",
                }
            },
            "Open shell for updating paths or updating links weights",
        )
        command_parser.register(
            "flow",
            self.set_flow,
            {
                "": {
                    "name": "type",
                    "description": "Type of instruction: `drop`, `output`. [DEFAULT: `drop`]",
                    "default": "drop",
                },
                "node": {"description": "Node Name want to work on. [Required]"},
                "src": {"description": "Source node for get MAC.", "default": ""},
                "dest": {
                    "description": "Destination node for get MAC.",
                    "default": "",
                },
                "priority": {
                    "dtype": int,
                    "default": 5,
                    "description": "Priority for of this flow. [Default: 5].",
                },
                "table": {
                    "description": "Table ID want to work on. [DEFAULT: 0]",
                    "default": 0,
                    "dtype": int,
                },
            },
        )
        command_parser.register(
            "delete",
            self.delete_flows,
            {
                "node": {
                    "description": "Node Name want to work on. [Required]. [Use '*' for all nodes]",
                },
                "table": {
                    "description": "Table ID want to work on. [DEFAULT: 0]",
                    "default": 0,
                    "dtype": int,
                },
                "flow": {
                    "description": "Flow ID want to delete. [DEFAULT: None]. [Require in delete one flow]",
                    "default": None,
                },
                # "directly": {
                #     "description": "True if want to delete directly in switch. False if want to delete just on controller config datastore. [DEFAULT: False]",
                #     "default": False,
                #     "dtype": bool,
                # },
            },
            "Remove flows/tables in config datastore. May raise Error if the flows are in operational datastore",
        )
        command_parser.register(
            "delete-directly",
            self.delete_flows_directly,
            {
                "node": {
                    "description": "Node Name want to work on. [Required]. [Use '*' for all nodes]",
                },
                "table": {
                    "description": "Table ID want to work on. [DEFAULT: 0]",
                    "default": 0,
                    "dtype": int,
                },
                "flow": {
                    "description": "Flow ID want to delete. [DEFAULT: None]. [Not used with `priority`]",
                    "default": None,
                },
                # "priority": {
                #     "description": "Priority match. [DEFAULT: None].",
                #     "default": None,
                #     "dtype": int,
                # },
                "strict": {
                    "description": "True if want to delete only if match exactly. [DEFAULT: False]. [Not used with `priority`]",
                    "default": False,
                    "dtype": int,
                },
            },
            "Remove flows/tables in switch directly, with some criterions",
        )
        command_parser.register(
            "refresh", self.topology.refresh, {}, "Updating topology from Server."
        )
        return command_parser

    def set_flow(self, type: str = "drop", **kwargs):
        if type == "drop":
            try:
                node_id = self.topology.get_id_from_names(kwargs["node"])[0]
                src = None
                if kwargs["src"] != "":
                    src = self.topology.get_node_from_names(kwargs["src"])[0]
                    if src.type == "host":
                        src = src.mac

                dest = None
                if kwargs["dest"] != "":
                    dest = self.topology.get_node_from_names(kwargs["dest"])[0]
                    if dest.type == "host":
                        dest = dest.mac
                self.config.set_drop_flow(
                    node_id, kwargs["table"], src, dest, kwargs["priority"]
                )
            except Exception as ex:
                print(f":: fail to set flow on {node_id}: {ex}")
        pass

    def _set_path(self, nodes: list[str], table: int | str = 0, priority: int = 5):
        if not self.topology.is_valid_path(*nodes):
            raise Exception("INVALID PATH")
        else:
            nodes = self.topology.get_node_from_names(*nodes)
            # print(nodes)
            try:
                self.config.set_path(*nodes, table=table, priority=priority)
                # print(":: Set path successfully")
            except Exception as ex:
                raise

    def extract_shortest_path(
        self,
        type: str = "",
        **kwargs
        # source: str,
        # destination: str,
        # throughs: list[str] = None,
        # blocks: list[str] = None,
        # cutoff: int = None,
    ):
        length, path = self.topology.find_shortest_path(
            kwargs["source"],
            kwargs["destination"],
            kwargs["throughs"],
            kwargs["blocks"],
            kwargs["cutoff"],
        )
        print(f":: [{length}]", *path if path is not None else "None")
        if "set" in type and path is not None:
            self._set_path(path, kwargs["table"], kwargs["priority"])

    def _set_weights(self, edge_weights: list[tuple]) -> int:
        count = 0
        for ew in edge_weights:
            try:
                self.topology.set_weight(ew[0], ew[1], int(ew[2]))
                count += 1
            except Exception as e:
                print(f":: set weight fail for link {ew}: {e}")
        return count

    def _start_shell_for_update_path(self):
        print("|| ======== Shell for updating Paths ========")
        print("|| Enter the path, each node separate by space ' '. One path per line.")
        #  or id (Ex: openflow:1), first match the id.
        print("|| Each node is identified by name (Ex: H01 or s1)")
        print(
            "|| Type 'priority <priority>' for set priority for following paths, default: 5"
        )
        print(
            "|| Type 'table <table index>' for set table for following paths, default: 0"
        )
        print(
            "|| Type 'sh <command>' for run outer level commands. Ex: sh print switches"
        )
        # print("Type 'file <path>' for updating from file, with same format")
        print("|| Type 'end' or 'exit' for exiting.")
        priority = 5
        table = 0
        while True:
            enter = input("|| >> ")
            comm = enter.lower()
            if comm in ["exit", "end"]:
                break
            elif comm.startswith("sh"):
                self.comparser.run(comm[3:])
            elif comm.startswith("priority"):
                try:
                    priority = int(enter[9:])
                    print("|| :: priority =", priority)
                except:
                    print("|| :: set priority fail")
            elif comm.startswith("table"):
                try:
                    table = int(enter[6:])
                except:
                    print("|| :: set table fail")
            else:
                try:
                    self._set_path(enter.split(" "), table=table, priority=priority)
                except Exception as ex:
                    print(f"|| :: update path fail: {ex}")

    def _start_shell_for_update_weights(self):
        print("|| ======== Shell for updating Links' Weights ========")
        print(
            "|| Enter nodes' names and weight (int), separate by space ' '. One link per one line."
        )
        print("|| In case you want to reset one link weight, just set it to 1.")
        print("|| Type 'file <path>' for updating from file, with same format")
        print(
            "|| Type 'sh <command>' for run outer level commands. Ex: sh print switches"
        )
        print(
            "|| Type 'dump <path>' for dumping configs to file, with same format, then update and exit."
        )
        print("|| Type 'end' for updating, 'exit' for canceling.")
        print(
            "|| NOTE: This shell just updating the offline topology, and only update after `end` command."
        )
        updates = []
        ### Get Inputs
        while True:
            enter = input("|| >> ")
            comm = enter.lower()
            if comm == "end":
                break
            elif comm == "exit":
                updates.clear()
                break
            elif comm.startswith("sh"):
                self.comparser.run(comm[3:])
            elif comm.startswith("file "):
                filepath = enter[5:]
                with open(filepath, "r") as file:
                    updates.extend(file.readlines())
            elif comm.startswith("dump "):
                filepath = enter[5:]
                with open(filepath, "w") as file:
                    file.writelines([l + "\n" for l in updates])
                    # updates.extend(file.readlines())
                break
            else:
                updates.append(enter)
        ### Update on Graph
        data = []
        for enter in updates:
            inps = enter.split(" ")
            if len(inps) < 3:
                continue
            n1, n2, w = inps[:3]
            if w[-1] == "\n":
                w = w[:-1]
            data.append((n1, n2, w))
        if len(data) > 0:
            count = self._set_weights(data)
            print(f":: updating successfully {count}/{len(data)}")
        # # self.print_graph()
        # print(":: updating shortest paths with priority 2...")
        # stp = self.topology.get_hosts_shortest_path()
        # for path in stp.values():
        #     self._set_path(path, priority=2, table=0)

    def delete_flows_directly(
        self,
        node: str = "*",
        table: int = 0,
        flow: str = None,
        # priority: int = None,
        strict=False,
    ):
        if node == "*":
            sws = self.topology.get_objects("switch")
            for sw in sws:
                try:
                    self.config.delete_flows_in_switch(sw.id, list(sw.active_tables))
                    print(f":: cleared all tables in switch {sw.name} [{sw.id}]")
                    # self.config.delete_flows_with_criterion_in_switch(
                    #     sw.id, list(sw.active_tables), priority=priority
                    # )
                    # print(
                    #     f":: cleared all tables with priority {priority} in switch {sw.name} [{sw.id}]"
                    # )
                except Exception as ex:
                    print(
                        f":: fail to clear tables in switch {sw.name} [{sw.id}]. Exception: {ex}"
                    )
                # if priority is None:
                self.config.set_lldp_flow_in_switch(sw.id, 0)
            return
        node_id = self.topology.get_id_from_names(node)[0]
        type, obj = self.connector.get_object(
            node_id, table, flow, datastore="operational"
        )
        try:
            if type == "flow":
                self.config.delete_flows_in_switch(
                    node_id, table, parse_dict(type, obj), strict=strict
                )
            elif type == "table":
                self.config.delete_flows_in_switch(node_id, table)
                # self.config.delete_flows_with_criterion_in_switch(
                #     node_id, table, priority=priority
                # )
        except Exception as ex:
            print(
                f":: fail to clear {type} directly in switch {node} [{node_id}]. Exception: {ex}"
            )

    def delete_flows(self, node: str = "*", table: int = 0, flow: str = None):
        if node == "*":
            sws = self.topology.get_objects("switch")
            for sw in sws:
                for table_id in sw.active_tables:
                    try:
                        self.config.delete_flows(sw.id, table_id)
                        print(
                            f":: cleared table {table_id} for switch {sw.name} [{sw.id}]"
                        )
                    except Exception as ex:
                        print(
                            f":: fail to clear table {table_id} for switch {sw.name} [{sw.id}]. Exception: {ex}"
                        )
        else:
            try:
                node_id = self.topology.get_id_from_names(node)[0]
                self.config.delete_flows(node_id, table, flow)
            except Exception as ex:
                print(
                    f":: fail to clear flows for switch {node} [{node_id}]. Exception: {ex}"
                )

    # def reset_switches(self):
    #     sws = self.topology.get_objects("switch")
    #     for sw in sws:
    #         for table_id in sw.active_tables:
    #             self.config.delete_flows_in_switch(sw.id, table_id)
    #             print(f":: Reset table {table_id} in switch {sw.name} [{sw.id}]")

    def print(self, type: str, **kwargs):
        node_id = self.topology.get_id_from_names(kwargs.get("node", None))[0]
        if type.startswith("gr"):
            self.topology.print_graph()
        elif type.startswith("ho"):
            self.topology.print_hosts()
        elif type.startswith("sw"):
            self.topology.print_switches()
        elif type.startswith("po"):
            self.topology.print_ports(node_id, kwargs["active_port"])
        elif type.startswith("ta"):
            if node_id is None:
                print(f":: invalid node name {kwargs['node']}")
            else:
                self.topology.print_tables(node_id)
        elif type.startswith("fl"):
            if node_id is None:
                print(f":: invalid node name {kwargs['node']}")
            else:
                self.topology.print_flows(node_id, kwargs["table"])
        elif type.startswith("ob"):
            if node_id is None:
                print(f":: invalid node name {kwargs['node']}")
            else:
                self.topology.print_object(node_id, kwargs["table"], kwargs["flow"])
        elif type.startswith("li"):
            if node_id is None:
                print(f":: invalid node name {kwargs['node']}")
            else:
                print(
                    parse_dict(
                        self.connector.get_object(
                            node_id,
                            kwargs["table"],
                            kwargs["flow"],
                            datastore=kwargs["datastore"],
                        )
                    )
                )
            # self.topology.print_object(kwargs["node"], kwargs["table"], kwargs["flow"])

    def start_shell(self, type: str):
        if type == "path":
            self._start_shell_for_update_path()
        elif type == "weight":
            self._start_shell_for_update_weights()

    def _start(self):
        print("================== SDN Application ==================")
        self.comparser = self._create_app_command_parser()
        while True:
            inp = input(">> ")
            if inp.startswith("exit"):
                break
            mess = self.comparser.run(inp)
            if mess:
                print(f":: {mess}")

    # def print_graph(self):
    #     print("======== Network Graph ========")
    #     for u, v, i in sorted(self.topology.graph.edges.data("w"), key=lambda x: x[0]):
    #         print(f"Link from {u:>5} to {v:>5} has weight: {i}")

    # def print_hosts(self):
    #     for host in self.topology.get_objects("host", is_sorted=True):
    #         print(host)

    # def print_switches(self):
    #     for switch in self.topology.get_objects("switch", is_sorted=True):
    #         print(switch)

    # def print_ports(self, live_only=False):
    #     ports = self.topology.get_objects("port", is_sorted=True)
    #     if live_only:
    #         ports = [p for p in ports if p.peer is not None]
    #     print(parse_port_list(ports))

    # def print_tables(self, switch_id: str):
    #     print(f":: TABLES FOR {switch_id}:")
    #     for table in self.topology.get_objects("table", switch_id, is_sorted=True):
    #         print(table)

    # def print_flows(self, switch_id: str, table_id: str):
    #     print(f":: SWITCH {switch_id}:")
    #     print(f":: TABLE {table_id}:")
    #     for flow in self.topology.get_objects(
    #         "flow", switch_id, table_id, is_sorted=True
    #     ):
    #         print(flow)

    # def print_object(self, node_id=None, table_id=None, flow_id=None):
    #     print(self.topology.get_object(node_id, table_id, flow_id))

    # def print_live_object(
    #     self, node_id, table_id=None, flow_id=None, *, datastore="operational"
    # ):
    #     type, obj = self.connector.get_object(
    #         node_id, table_id, flow_id, datastore=datastore
    #     )
    #     print(parse_dict(type, obj))


if __name__ == "__main__":
    app = App()
