from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI

class MyStaticTopo(Topo):
    def build(self):
        # Add 1 Switch
        s1 = self.addSwitch('s1')
        
        # Add 3 Hosts
        h1 = self.addHost('h1', ip='10.0.0.1')
        h2 = self.addHost('h2', ip='10.0.0.2')
        h3 = self.addHost('h3', ip='10.0.0.3')

        # Connect them to specific switch ports
        # h1 -> Port 1, h2 -> Port 2, h3 -> Port 3
        self.addLink(h1, s1, port2=1)
        self.addLink(h2, s1, port2=2)
        self.addLink(h3, s1, port2=3)

if __name__ == '__main__':
    topo = MyStaticTopo()
    # RemoteController tells Mininet to look for POX (default port 6633)
    net = Mininet(topo=topo, controller=RemoteController)
    net.start()
    CLI(net)
    net.stop()
