```python?code_reference&code_event_index=2
# SDN Mininet Static Routing Project

## 1. Problem Statement & Objective
The goal of this project is to implement an SDN-based static routing solution using Mininet and the POX OpenFlow controller to solve the "Orange Problem". Instead of relying on traditional MAC learning, the controller explicitly programs the switch's flow tables using match-action rules based on IPv4 destination addresses.

**Topology:**
* 1 OpenFlow Switch (`s1`)
* 3 Hosts (`h1`, `h2`, `h3`) connected to specific switch ports.
* Controller: POX (Remote Controller)

**Controller Logic:**
* **ARP Handling:** Floods ARP packets to allow host discovery.
* **Forwarding:** Installs static paths for allowed hosts (`h1` and `h2`).
* **Filtering:** Explicitly drops traffic destined for blocked hosts (`h3`).

## 2. Setup and Execution Steps

### Prerequisites
* WSL / Linux Environment
* Mininet
* POX Controller

### Execution
1. **Start the POX Controller:**
   Navigate to the POX directory and run the custom static routing module.
   ```
```text?code_stdout&code_event_index=2
File generated

```bash
   cd ~/pox
   ./pox.py log.level --INFO static
   ```

2. **Start the Mininet Topology:**
   In a separate terminal, launch the custom topology script.
   ```bash
   sudo python3 topo.py
   ```

## 3. Expected Output & Validation Scenarios

### Scenario 1: Allowed vs. Blocked Traffic (Filtering/Firewall)
* **Allowed:** Traffic between `h1` and `h2` is permitted. The controller installs a flow rule directing traffic to the correct output port.
  * Command: `h1 ping -c 3 h2`
  * Result: 0% packet loss.
* **Blocked:** Traffic destined for `h3` (`10.0.0.3`) is explicitly dropped by a high-priority controller rule with no actions.
  * Command: `h1 ping -c 3 h3`
  * Result: 100% packet loss.

### Scenario 2: Normal vs. Failure (Link Down)
* **Normal:** `h2 ping -c 3 h1` succeeds.
* **Failure:** Disconnecting the link (`link s1 h2 down`) results in unreachable destination. Reconnecting the link (`link s1 h2 up`) immediately restores communication based on the established controller rules.

### Scenario 3: Performance Observation
* **Throughput:** Bandwidth between hosts is measured using `iperf` (TCP) or `iperfudp` (UDP) to observe network performance under the SDN rules.
  * Command: `iperfudp 10M h1 h2`

### Scenario 4: Regression Testing
* Deleting all flow rules from the switch (`sh sudo ovs-ofctl del-flows s1`) clears the switch memory. Initiating a new ping forces the controller to process `PacketIn` events again, successfully reinstalling the exact same static routing rules without requiring a system restart.


## 4. References
* POX Controller Documentation: https://noxrepo.github.io/pox-doc/html/
* Mininet Walkthrough: http://mininet.org/walkthrough/
* OpenFlow Specification (Match-Action rules)

---

## 5. Source Code

### `topo.py`
```python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI

class MyStaticTopo(Topo):
    def build(self):
        
        s1 = self.addSwitch('s1')
        
      
        h1 = self.addHost('h1', ip='10.0.0.1')
        h2 = self.addHost('h2', ip='10.0.0.2')
        h3 = self.addHost('h3', ip='10.0.0.3')

       
        # h1 -> Port 1, h2 -> Port 2, h3 -> Port 3
        self.addLink(h1, s1, port2=1)
        self.addLink(h2, s1, port2=2)
        self.addLink(h3, s1, port2=3)

if __name__ == '__main__':
    topo = MyStaticTopo()
  
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, port=6633))
    net.start()
    CLI(net)
    net.stop()
```

### `static.py` (POX Controller)
```python
from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class StaticSwitch (object):
  def __init__ (self, connection):
    self.connection = connection
    connection.addListeners(self)

  def _handle_PacketIn (self, event):
    packet = event.parsed
    
  
    if packet.type == packet.ARP_TYPE:
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
        return

    
    ip = packet.find('ipv4')
    if ip is None:
        return

    dst_ip = str(ip.dstip)

   
    if dst_ip == "10.0.0.3":
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(dl_type = 0x0800, nw_dst = ip.dstip)
        msg.priority = 20  # Higher priority to ensure it gets checked first
       
        self.connection.send(msg)
        log.info("BLOCKED PATH: Dropping traffic to %s", dst_ip)
        return

  
    routing_table = {
        "10.0.0.1": 1,
        "10.0.0.2": 2
    }

    if dst_ip in routing_table:
        out_port = routing_table[dst_ip]
        
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(dl_type = 0x0800, nw_dst = ip.dstip)
        msg.actions.append(of.ofp_action_output(port = out_port))
        msg.priority = 10
        self.connection.send(msg)
        
        msg_out = of.ofp_packet_out()
        msg_out.data = event.ofp
        msg_out.actions.append(of.ofp_action_output(port = out_port))
        self.connection.send(msg_out)
        
        log.info("SUCCESS PATH: Installed rule for %s out port %d", dst_ip, out_port)

def launch ():
  def start_switch (event):
    StaticSwitch(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
```
