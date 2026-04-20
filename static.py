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

   
    routing_table = {
        "10.0.0.1": 1,
        "10.0.0.2": 2,
        "10.0.0.3": 3
    }

    dst_ip = str(ip.dstip)

 
    if dst_ip == "10.0.0.3":
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(dl_type = 0x0800, nw_dst = ip.dstip)
        msg.priority = 20  
       
        self.connection.send(msg)
        log.info("BLOCKED PATH: Dropping traffic to %s", dst_ip)
        return
  

def launch ():
  def start_switch (event):
    StaticSwitch(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
