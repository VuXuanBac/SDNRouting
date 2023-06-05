from mininet.topo import Topo


class MyTopo(Topo):
    "Simple topology example."

    def __init__(self):
        "Create custom topo."

        Topo.__init__(self)

        # Add hosts and switches
        h1 = self.addHost("h01")
        h2 = self.addHost("h02")
        h3 = self.addHost("h03")
        h4 = self.addHost("h04")
        h5 = self.addHost("h05")
        h6 = self.addHost("h06")
        h7 = self.addHost("h07")
        h8 = self.addHost("h08")
        h9 = self.addHost("h09")
        h10 = self.addHost("h10")

        # Them cac switch
        s1 = self.addSwitch("s01")
        s2 = self.addSwitch("s02")
        s3 = self.addSwitch("s03")
        s4 = self.addSwitch("s04")
        s5 = self.addSwitch("s05")
        s6 = self.addSwitch("s06")
        s7 = self.addSwitch("s07")
        s8 = self.addSwitch("s08")
        s9 = self.addSwitch("s09")
        s10 = self.addSwitch("s10")

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s4)
        self.addLink(h4, s6)
        self.addLink(h5, s5)
        self.addLink(h6, s5)
        self.addLink(h7, s9)
        self.addLink(h8, s7)
        self.addLink(h9, s10)
        self.addLink(h10, s10)

        self.addLink(s1, s2)
        self.addLink(s1, s4)
        self.addLink(s1, s5)
        self.addLink(s1, s9)
        self.addLink(s2, s3)
        self.addLink(s3, s4)
        self.addLink(s3, s5)
        self.addLink(s3, s7)
        self.addLink(s3, s10)
        self.addLink(s4, s6)
        self.addLink(s5, s8)
        self.addLink(s5, s9)
        self.addLink(s6, s7)
        self.addLink(s7, s8)
        self.addLink(s7, s10)
        self.addLink(s8, s9)
        self.addLink(s9, s10)


topos = {"topo": (lambda: MyTopo())}
