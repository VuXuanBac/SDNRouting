from node import Switch, Host, Node, Port
from flow import (
    Table,
    Flow,
    FlowBuilder,
    create_basic_flow,
    create_lldp_flow,
    create_drop_flow,
)
from connector import Connector
import json

# def parse_dict(type: str, data: dict):
#     try:
#         if type == "host":
#             return Host(data)
#         elif type == "switch":
#             return Switch(data)
#         elif type == "table":
#             return Table(data)
#         elif type == "flow":
#             return Flow(data)
#         elif type == "port":
#             return Port(data)
#     except:
#         pass
#     return None


class NetworkConfig(object):
    def __init__(self, connector: Connector) -> None:
        self.connector = connector

    def set_path(self, *nodes: Node, table: int = 0, priority: int = 5):
        if len(nodes) < 2 or nodes[0].type != "host" or nodes[-1].type != "host":
            raise Exception("INVALID PATH: TERMINALS MUST BE HOSTS")
        src_mac, dest_mac = nodes[0].mac, nodes[-1].mac
        src_name, dest_name = nodes[0].name, nodes[-1].name

        for ind, node in enumerate(nodes[1:-1], 1):  # set flow for each switch
            port_prev = node.get_port_for_peer(nodes[ind - 1].id)
            port_next = node.get_port_for_peer(nodes[ind + 1].id)
            if port_next is None or port_prev is None:
                raise Exception("INVALID PATH: PORT NOT FOUND")
            flow_forward = create_basic_flow(
                f"{src_name}-{dest_name}-go",
                src_mac,
                dest_mac,
                port_next.port_number,
                priority=priority,
            )
            flow_backward = create_basic_flow(
                f"{src_name}-{dest_name}-back",
                dest_mac,
                src_mac,
                port_prev.port_number,
                priority=priority,
            )
            self.set_flow(node.id, table, flow_forward)
            self.set_flow(node.id, table, flow_backward)

    def set_drop_flow(
        self, node_id: str, table_id: str, src_mac: str, dest_mac: str, priority: int
    ):
        return self.set_flow(
            node_id,
            table_id,
            create_drop_flow("drop", src_mac, dest_mac, priority=priority),
        )

    def set_lldp_flow_in_switch(self, node_id: str, table_id: str):
        return self.set_flow_in_switch(node_id, table_id, create_lldp_flow("hello"))

    def set_flow_in_switch(self, node_id: str, table_id: str, flow: Flow):
        """
        Add Flow directly in Switch
        [RPC Example](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html#example-of-flow-programming-by-using-rpc-operation)
        Do not set `flow.id` because it will add flow.id in datastore to switch instead of add new.
        Do not need `flow.name` as well, see the reason here. [How Flow ID Match](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html#flow-id-match-function)
        """
        ep = f"/restconf/operations/sal-flow:add-flow"
        flow_dict = flow.to_dict()
        flow_dict["table_id"] = table_id
        flow_dict[
            "node"
        ] = f"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='{node_id}']"
        flow_dict.pop("id", None)  # remove "id" if present, else return None
        self.connector.post(ep, {"input": flow_dict})

    def delete_flows_with_criterion_in_switch(
        self,
        node_id: str | list[str],
        table_id: int | list[int],
        **kwargs
        # strict: bool = True,
    ):
        """
        Remove Flows directly in Switch with some set fields. Ex: priority. Do not set `id` or `name` or `statistics`.

        This function can delete flows on multiple nodes and multiple tables. Each call will use a flow with set fields

        [RPC Example](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html#deleting-flows-from-switch-using-rpc-operation)
        """
        ep = f"/restconf/operations/sal-flow:remove-flow"
        flow_dict = {"strict": False}
        for key, value in kwargs.items():
            if key in [
                "id",
                "name",
                "opendaylight-flow-statistics:flow-statistics",
            ]:  # do not use this value
                continue
            if value is not None:
                flow_dict[key] = value

        if isinstance(node_id, str):
            node_id = [node_id]
        if isinstance(table_id, (int, str)):
            table_id = [table_id]

        for ni in node_id:
            for ti in table_id:
                flow_dict["table_id"] = ti
                flow_dict[
                    "node"
                ] = f"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='{ni}']"
                print(json.dumps(flow_dict))
                a = input("Continue ? ")
                if len(a) > 1:
                    self.connector.post(ep, {"input": flow_dict})
                else:
                    return

    def delete_flows_in_switch(
        self,
        node_id: str | list[str],
        table_id: int | list[int],
        flow: Flow = None,
        strict: bool = True,
    ):
        """
        Remove Flows directly in Switch.
        - flow: Need a Flow object to match, not just flow.id as delete in controller config datastore. None if delete all flows in table
        - strict: True if want to delete only if Flow object match exactly with Flow record saved in Switch

        This function can delete flows on multiple nodes and multiple tables. Each call will use the set `flow`.

        [RPC Example](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html#deleting-flows-from-switch-using-rpc-operation)
        Do not set `flow.id`
        Do not need `flow.name` as well, see the reason here. [How Flow ID Match](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html#flow-id-match-function)
        """
        ep = f"/restconf/operations/sal-flow:remove-flow"
        if flow is not None:
            flow_dict = flow.to_dict()
            flow_dict["strict"] = strict
        else:
            flow_dict = {"strict": False}
        flow_dict.pop("id", None)  # remove "id" if present, else return None
        flow_dict.pop("opendaylight-flow-statistics:flow-statistics", None)

        if isinstance(node_id, str):
            node_id = [node_id]
        if isinstance(table_id, (int, str)):
            table_id = [table_id]

        for ni in node_id:
            for ti in table_id:
                flow_dict["table_id"] = ti
                flow_dict[
                    "node"
                ] = f"/opendaylight-inventory:nodes/opendaylight-inventory:node[opendaylight-inventory:id='{ni}']"
                # print(json.dumps(flow_dict))
                self.connector.post(ep, {"input": flow_dict})

    def set_flow(self, node_id: str, table_id: str, flow: Flow):
        ep = f"/restconf/config/opendaylight-inventory:nodes/node/{node_id}/flow-node-inventory:table/{table_id}/flow/{flow.id}"
        flow_dict = flow.to_dict()
        flow_dict["table_id"] = table_id
        self.connector.put(ep, {"flow-node-inventory:flow": [flow_dict]})

    def delete_flows(self, node_id: str, table_id: str, flow_id: str = None):
        # "/restconf/config/opendaylight-inventory:nodes/node/{id}/flow-node-inventory:table/{id}/flow/{id}""
        if flow_id is not None:
            ep = f"/restconf/config/opendaylight-inventory:nodes/node/{node_id}/table/{table_id}/flow/{flow_id}"
        else:
            ep = f"/restconf/config/opendaylight-inventory:nodes/node/{node_id}/table/{table_id}"
        self.connector.delete(ep)

    # def print_live_object(
    #     self, node_id, table_id=None, flow_id=None, *, datastore="operational"
    # ):
    #     type, obj = self.connector.get_object(
    #         node_id, table_id, flow_id, datastore=datastore
    #     )
    #     print(parse_dict(type, obj))
