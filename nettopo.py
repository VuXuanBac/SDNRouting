from node import Switch, Host, Node
from flow import Table, Flow
from connector import Connector
from node import parse_port_list
import networkx as nx
import networkx.classes.function as nxfunc
import networkx.algorithms.simple_paths as nxpath
import json


class NetworkTopology(object):
    def __init__(self, connector: Connector) -> None:
        self.connector = connector
        self.refresh()

    def refresh(self):
        topology = self.connector.get_objects("topo")[1][0]
        switches = self.connector.get_objects("switch")[1]
        with open("topology.json", "w") as file:
            json.dump(topology, file)
        with open("nodes.json", "w") as file:
            json.dump(switches, file)
        nodes = NetworkTopology._extract_nodes(topology, switches)

        links = []
        for node in nodes.values():
            for peer in node.peers.values():
                links.append((node.name, peer.name))
        # self.netgraph = NetworkGraph(links)
        graph = nx.Graph()
        graph.add_edges_from(links, w=1)

        self.graph = graph
        self.nodes = nodes

        ret = {}
        for id, node in nodes.items():
            ret[node.name] = id
        self.mappings_node_id_name = ret

    def get_id_from_names(self, *node_names):
        return [self.mappings_node_id_name.get(n, None) for n in node_names]

    def get_node_from_names(self, *node_names):
        return [
            self.nodes.get(self.mappings_node_id_name.get(n, None), None)
            for n in node_names
        ]

    def set_weight(self, src: str, dest: str, weight: int = 1):
        self.graph.edges[src, dest]["w"] = weight

    def get_hosts_shortest_path(self) -> dict[tuple, list]:
        hosts = [n for n in self.graph.nodes if n.startswith(("H", "h"))]
        stp = nx.shortest_path(self.graph, weight="w", method="dijkstra")
        ret = {}
        for src, dest_path in stp.items():
            if src in hosts:
                for dest, path in dest_path.items():
                    if dest in hosts and (dest, src) not in ret:
                        ret[(src, dest)] = path
                ret.pop((src, src), None)
        return ret

    def find_shortest_path(
        self,
        src: str,
        dest: str,
        throughs: set = None,
        blocks: set = None,
        cutoff: int = None,
    ):
        throughs = set(throughs if throughs is not None else [])
        blocks = set(blocks if blocks is not None else [])
        for path in nxpath.shortest_simple_paths(self.graph, src, dest, weight="w"):
            if blocks.intersection(path):
                continue
            if throughs.difference(path):
                continue
            if cutoff and nxfunc.path_weight(self.graph, path, weight="w") > cutoff:
                break
            return nxfunc.path_weight(self.graph, path, weight="w"), path
        return None, None

    def is_valid_path(self, *path) -> bool:
        return nxfunc.is_path(self.graph, path)

    @staticmethod
    def _extract_nodes(topology: dict, switches: dict):
        ret = {}
        for ni in topology.get("node", {}):
            id = ni["node-id"]
            if "host" in id:
                ret[id] = Host(ni)

        for nd in switches:
            id = nd["id"]
            ret[id] = Switch(nd)

        for link in topology.get("link", {}):
            # id = link['link-id']
            src_id, src_port = link["source"].values()
            dest_id, dest_port = link["destination"].values()
            ret[src_id].set_peer(src_port, ret[dest_id], dest_port)
            ret[dest_id].set_peer(dest_port, ret[src_id], src_port)
        return ret

    def get_object(self, node_id=None, table_id=None, flow_id=None):
        if node_id is None or node_id not in self.nodes:
            return self
        node = self.nodes[node_id]
        if table_id is None or node.type == "host":
            return node
        table = node.tables.get(table_id, None)
        if table is None:
            return node
        flows = table.flows
        if flow_id is None or flow_id not in flows:
            return table
        return flows[flow_id]

    def get_objects(
        self,
        level: str = "topo",
        node_id: str = None,
        table_id: str = None,
        *,
        is_sorted: bool = False,
    ):
        nodes = self.nodes
        sorted_by_name_func = lambda n: n.name
        if "topo" in level or "node" in level:
            return (
                sorted(nodes.values(), key=sorted_by_name_func)
                if is_sorted
                else nodes.values()
            )
        if "host" in level:
            ret = [node for node in nodes.values() if node.type == "host"]
            return sorted(ret, key=sorted_by_name_func) if is_sorted else ret
        if "switch" in level:
            ret = [node for node in nodes.values() if node.type == "switch"]
            return sorted(ret, key=sorted_by_name_func) if is_sorted else ret
        if "port" in level:
            ret = [port for node in nodes.values() for port in node.ports.values()]
            return sorted(ret, key=sorted_by_name_func) if is_sorted else ret

        node = nodes.get(node_id, None)
        if node is None or node.type != "switch":
            return []

        if "table" in level:
            ret = node.active_tables.values()
            return sorted(ret, key=sorted_by_name_func) if is_sorted else ret

        table = node.tables.get(table_id, None)
        if table is None:
            return []

        ret = table.flows.values()
        return sorted(ret, key=sorted_by_name_func) if is_sorted else ret

    def print_graph(self):
        print("======== Network Graph ========")
        for u, v, i in sorted(
            self.graph.edges.data("w"), key=lambda x: (x[0], x[1], x[2])
        ):
            print(f"{u:<5} <--> {v:>5} [weight: {i}]")
        print(
            f":: Total: {self.graph.number_of_nodes()} Nodes, {self.graph.number_of_edges()} Edges."
        )

    def print_hosts(self):
        for host in self.get_objects("host", is_sorted=True):
            print(host)

    def print_switches(self):
        for switch in self.get_objects("switch", is_sorted=True):
            print(switch)

    def print_ports(self, node_id: str = None, live_only: bool = False):
        if node_id is None:
            ports = self.get_objects("port", is_sorted=True)
            if live_only:
                ports = [p for p in ports if p.peer is not None]
        else:
            node = self.get_object(node_id)
            ports = (
                sorted(node.ports.values(), key=lambda p: p.name)
                if node is not None
                else []
            )
        print(parse_port_list(ports))

    def print_tables(self, switch_id: str):
        print(f":: TABLES FOR {switch_id}:")
        for table in self.get_objects("table", switch_id, is_sorted=True):
            print(table)

    def print_flows(self, switch_id: str, table_id: str):
        print(f":: SWITCH {switch_id}:")
        print(f":: TABLE {table_id}:")
        for flow in self.get_objects("flow", switch_id, table_id, is_sorted=True):
            print(flow)

    def print_object(self, node_id=None, table_id=None, flow_id=None):
        print(self.get_object(node_id, table_id, flow_id))
