import requests as rq
import json


def make_request(method, endpoint, headers, auth, data=None):
    if method == "GET":
        try:
            response = rq.get(endpoint, headers=headers, auth=auth)
        except rq.exceptions.RequestException as e:
            raise Exception(f"Error on GET: {e}")
    elif method == "PUT":
        try:
            # print(data)
            response = rq.put(endpoint, headers=headers, data=data, auth=auth)
        except rq.exceptions.RequestException as e:
            raise Exception(f"Error on PUT: {e}")
    elif method == "POST":
        try:
            # print(data)
            response = rq.post(endpoint, headers=headers, data=data, auth=auth)
        except rq.exceptions.RequestException as e:
            raise Exception(f"Error on POST: {e}")
    elif method == "DELETE":
        try:
            # print(endpoint)
            response = rq.delete(endpoint, headers=headers, auth=auth)
        except rq.exceptions.RequestException as e:
            raise Exception(f"Error on DELETE: {e}")
    else:
        raise NotImplemented(f"Method {method} not implemented.")

    if response.status_code == 404:
        raise Exception(f"404. Endpoint not found: {endpoint}")

    # Consider any status other than 2xx an error
    if not response.status_code // 100 == 2:
        raise Exception(f"Unexpected Response {format(response)}")

    return response


class Connector(object):
    """
    APIs From: [OpenDayLight Plugin](https://docs.opendaylight.org/projects/openflowplugin/en/latest/users/operation.html)
    """

    def __init__(
        self,
        server_ip="192.168.1.6",
        server_port=8181,
        auth: tuple = None,
        content_type="application/json",
    ) -> None:
        if auth is None:
            auth = ("admin", "admin")
        self.server = f"http://{server_ip}:{server_port}"
        self.auth = auth
        self.headers = {"Content-type": content_type}

    def get(self, endpoint: str):
        print(f"... GET: {endpoint} ...")
        response = make_request(
            "GET", self.server + endpoint, headers=self.headers, auth=self.auth
        )
        return json.loads(response.text)

    def put(self, endpoint: str, data: dict):
        print(f"... PUT: {endpoint} ...")
        return make_request(
            "PUT",
            self.server + endpoint,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(data),
        )

    def post(self, endpoint: str, data: dict):
        print(f"... POST: {endpoint} ...")
        return make_request(
            "POST",
            self.server + endpoint,
            headers=self.headers,
            auth=self.auth,
            data=json.dumps(data),
        )

    def delete(self, endpoint: str):
        print(f"... DELETE: {endpoint} ...")
        return make_request(
            "DELETE", self.server + endpoint, headers=self.headers, auth=self.auth
        )

    # def get_topology(self):
    #     endpoint = "/restconf/operational/network-topology:network-topology/"
    #     return self.get(endpoint)["network-topology"]["topology"][0]

    # def get_nodes(self):
    #     endpoint = "/restconf/operational/opendaylight-inventory:nodes/"
    #     return self.get(endpoint)["nodes"]["node"]

    def get_object(
        self, node_id, table_id=None, flow_id=None, *, datastore="operational"
    ) -> tuple[str, object]:
        """
        Retrieve one object from OPERATIONAL/CONFIG DATASTORE:
        - A Switch Node [requires `node_id`]
        -- A Switch Port [requires `node_id` and `port_id`]
        - A Switch Table [requires `node_id` and `table_id`]
        - A Flow Entry [requires `node_id` and `table_id` and `flow_id`]
        Return first matched object's dict data (with its type: switch, table, flow] or print exception for invalid requests.
        """
        if "conf" in datastore:
            datastore = "config"
        else:
            datastore = "operational"

        endpoint = f"/restconf/{datastore}/opendaylight-inventory:nodes"
        try:
            if node_id is None:
                return "None", None

            endpoint += f"/node/{node_id}"
            if table_id is None:  # and port_id is None:
                return "switch", self.get(endpoint)["node"][0]

            # if port_id is not None:
            #     return self.get(endpoint + f"node-connector/{port_id}")[
            #         "node-connector"
            #     ][0]

            endpoint += f"/table/{table_id}"
            if flow_id is None:
                return "table", self.get(endpoint)["flow-node-inventory:table"][0]

            endpoint += f"/flow/{flow_id}"
            return "flow", self.get(endpoint)["flow-node-inventory:flow"][0]
        except Exception as e:
            print(e)
            return "None", None

    def get_objects(
        self, level: str = "topo", node_id=None, table_id=None
    ) -> tuple[str, list]:
        """
        Retrieves objects in a level and return a list of them
        - "topo" [Topology: Nodes, Links,...]
        - "switch" or "node" [Switches]
        - "port" or "connector" [Switch Ports, requires `node_id`]
        - "table" [Switch Flow Table, requires `node_id`]
        - "flow" [Flows in Switch Table, requires `node_id` and `table_id`]

        Return objects and their type: "topo", "node", "port", "table", "flow"
        """
        if "topo" in level:
            endpoint = "/restconf/operational/network-topology:network-topology/"
            return "topo", self.get(endpoint)["network-topology"]["topology"]

        if "switch" in level or "node" in level:
            endpoint = "/restconf/operational/opendaylight-inventory:nodes/"
            return "switch", self.get(endpoint)["nodes"].get("node", [])
        if node_id is None:
            return "None", []

        endpoint = f"/restconf/operational/opendaylight-inventory:nodes/node/{node_id}"
        if "port" in level or "connector" in level:
            return "port", self.get(endpoint)["node"].get("node-connector", [])

        if "table" in level:
            return "table", self.get(endpoint)["node"].get(
                "flow-node-inventory:table", []
            )

        if table_id is None:
            return "None", []

        endpoint += f"/table/{table_id}"
        if "flow" in level:
            return "flow", self.get(endpoint)["flow-node-inventory:table"].get(
                "flow", []
            )
