from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class StaticSwitch (object):
  def __init__ (self, connection):
    self.connection = connection
    connection.addListeners(self)

  def _handle_PacketIn (self, event):
    packet = event.parsed
    
    # --- ADD THIS NEW BLOCK FOR ARP ---
    # If it's an ARP packet, flood it out all ports so hosts can find each other
    if packet.type == packet.ARP_TYPE:
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
        return
    # ----------------------------------

    # The rest of your existing IPv4 logic
    ip = packet.find('ipv4')
    if ip is None:
        return

    # Static Mapping: Destination IP -> Output Port
    routing_table = {
        "10.0.0.1": 1,
        "10.0.0.2": 2,
        "10.0.0.3": 3
    }

    dst_ip = str(ip.dstip)

    # --- THIS BLOCK MUST BE HERE TO DROP H3 TRAFFIC ---
    if dst_ip == "10.0.0.3":
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(dl_type = 0x0800, nw_dst = ip.dstip)
        msg.priority = 20  
        # No actions appended means the switch will DROP the packet
        self.connection.send(msg)
        log.info("BLOCKED PATH: Dropping traffic to %s", dst_ip)
        return
    # --------------------------------------------------

def launch ():
  def start_switch (event):
    StaticSwitch(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
