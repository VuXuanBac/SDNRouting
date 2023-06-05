import networkx as nx


class NetworkGraph(object):
    def __init__(self, links: list[tuple]) -> None:
        g = nx.Graph()
        g.add_edges_from(links, w=1)  # default weight is 1
        self.graph = g

    def set_weight(self, src: str, dest: str, weight: int = 1):
        try:
            self.graph.edges[src, dest]["w"] = weight
        except:
            pass

    # def print_edges(self):
    #     for u, v, i in self.graph.edges.data("w"):
    #         print(u, v, i)

    def set_weights(self, edge_weights: list[tuple]):
        for ew in edge_weights:
            try:
                self.graph.edges[ew[0], ew[1]]["w"] = int(ew[2])
            except:
                pass

    def shortest_path_subgraph(self, nodes: list[str] = None, node_match_func=None):
        if nodes is None:
            nodes = [n for n in self.graph.nodes if node_match_func(n)]
            print(nodes)
        stp = nx.shortest_path(self.graph, weight="w", method="dijkstra")
        ret = {}
        for src, dest_path in stp.items():
            if src in nodes:
                for dest, path in dest_path.items():
                    if dest in nodes and (dest, src) not in ret:
                        ret[(src, dest)] = path
                ret.pop((src, src), None)
        return ret

    def get_shortest_path(self, src_id=None, dest_id=None) -> dict[tuple, list]:
        stp = nx.shortest_path(
            self.graph, src_id, dest_id, weight="w", method="dijkstra"
        )
        ret = {}
        if src_id is None and dest_id is None:
            for src, dest_path in stp.items():
                for dest, path in dest_path.items():
                    ret[(src, dest)] = path
                ret.pop((src, src), None)
        elif dest_id is None:
            for dest, path in stp.items():
                ret[(src_id, dest)] = path
            ret.pop((src_id, src_id), None)
        elif src_id is None:
            for src, path in stp.items():
                ret[(src, dest_id)] = path
            ret.pop((dest_id, dest_id), None)
        else:
            ret[(src_id, dest_id)] = stp
        return ret
