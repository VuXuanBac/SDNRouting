# How to run

## OpenDaylight

### Running

```CMD
cd distribute...
bin\start
```

### Stop and Exit

```CMD
bin\stop
```

## Network in Mininet

### Create

- Use Available Topology

```CMD
sudo mn --controller=remote,ip=192.168.1.6 --switch=ovsk,protocols=OpenFlow13 --mac --topo=torus,3,3
```

- Use Custom Topology
  
```CMD
sudo mn --custom ~/custom/sdntopo.py --topo topo --controller=remote,ip=192.168.1.6 --switch=ovsk,protocols=OpenFlow13 --mac
```

- `--mac`: User-friendly MAC for Hosts. Use this, or you will know why.
- `--topo`: Set topology for the network.
- `--controller`: Type of Controller. Here, use remote controller running at IPv4: 192.168.1.6.
- `--switch`: Type of Switch. Here, use OpenFlow13 Switch (ovsk : Open vSwitch, protocols=OpenFlow13)
- `--custom`: Path to Python file config topology. See [Syntax](https://mininet.org/walkthrough/#custom-topologies)

### Done

After exiting, run following command for cleaning:

```CMD
sudo mn -c
```

## Some commands on Mininet

### View Flows on Switch in mininet

- Dump all

```CMD
dpctl dump-flows -O OpenFlow13
```

- View flows on one switch [s1]
  - `sh`: run outer shell command
  - `ovs-vsctl`: config Open vSwitch

```CMD
sh ovs-ofctl dump-flows [s1] -O OpenFlow13
```

### Reset state in database: Remove all flows in switches

```CMD
sh ovs-vsctl emer-reset
```

- `emer-reset`: reset Switches to known good state.

## The APP

- Requires Packages: [requests](https://pypi.org/project/requests/), [networkx](https://networkx.org/).
- The code is not good at first look. So don't look.

```CMD
python app.py
```
