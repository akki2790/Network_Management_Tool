

from pox.core import core
import pox


from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.util import str_to_bool, dpid_to_str

import pox.openflow.libopenflow_01 as of

import time
import random
log = core.getLogger("iplb")

FLOW_IDLE_TIMEOUT = 10
FLOW_MEMORY_TIMEOUT = 60 * 5



class MemoryIngress (object):
  
  def __init__ (self, server, first_packet, c_port):
    self.server = server
    self.first_packet = first_packet
    self.c_port = c_port
    self.refresh()

  def refresh (self):
    self.timeout = time.time() + FLOW_MEMORY_TIMEOUT

  @property
  def check_expiry (self):
    return time.time() > self.timeout

  @property
  def key1 (self):
    eth_packet = self.first_packet
    ip_fld = eth_packet.find('ipv4')
    tcp_fld = eth_packet.find('tcp')

    return ip_fld.srcip,ip_fld.dstip,tcp_fld.srcport,tcp_fld.dstport

  @property
  def key2 (self):
    eth_packet = self.first_packet
    ip_fld = eth_packet.find('ipv4')
    tcp_fld = eth_packet.find('tcp')

    return self.server,ip_fld.srcip,tcp_fld.dstport,tcp_fld.srcport


class iplb (object):
 

  def __init__ (self, connection, service_ip, servers = []):
    self.service_ip = IPAddr(service_ip)
    self.servers = [IPAddr(a) for a in servers]
    self.con = connection
    self.mac = self.con.eth_addr
    self.live_servers = {} # IP -> MAC,port

    try:
      self.log = log.getChild(dpid_to_str(self.con.dpid))
    except:
        
      self.log = log

    self.outstanding_probes = {} # IP -> expire_time

     
    self.probe_cycle_time = 5

     
    self.arp_timeout = 3

    
    self.memory = {} # (srcip,dstip,srcport,dstport) -> MemoryIngress

    self._do_probe()  

  def _do_expire (self):
    
    t = time.time()

    # Expire probes
    for ip,expire_at in self.outstanding_probes.items():
      if t > expire_at:
        self.outstanding_probes.pop(ip, None)
        if ip in self.live_servers:
          self.log.warn("Server %s down", ip)
          del self.live_servers[ip]

    # Expire old flows
    c = len(self.memory)
    self.memory = {k:v for k,v in self.memory.items()
                   if not v.check_expiry}
    if len(self.memory) != c:
      self.log.debug("Expired %i flows", c-len(self.memory))

  def _do_probe (self):
    """
    check if server's still up
    """
    self._do_expire()

    server = self.servers.pop(0)
    self.servers.append(server)

    a = arp()
    a.hwtype = a.HW_TYPE_ETHERNET
    a.prototype = a.PROTO_TYPE_IP
    a.opcode = a.REQUEST
    a.hwdst = ETHER_BROADCAST
    a.protodst = server
    a.hwsrc = self.mac
    a.protosrc = self.service_ip
    e = ethernet(type=ethernet.ARP_TYPE, src=self.mac,
                 dst=ETHER_BROADCAST)
    e.set_payload(r)
    #self.log.debug("ARPing for %s", server)
    msg = of.ofp_packet_out()
    msg.data = e.pack()
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    msg.in_port = of.OFPP_NONE
    self.con.send(msg)

    self.outstanding_probes[server] = time.time() + self.arp_timeout

    core.callDelayed(self._probe_wait_time, self._do_probe)

  @property
  def _probe_wait_time (self):
     
    a = self.probe_cycle_time / float(len(self.servers))
    a = max(.25, a) # Cap it at four per second
    return a

  def _pick_server (self, key, inport):
     
    return random.choice(self.live_servers.keys())

  def _handle_PacketIn (self, event):
    inport = event.port
    packet = event.parsed

    def drop ():
      if event.ofp.buffer_id is not None:
        # Kill the buffer
        msg = of.ofp_packet_out(data = event.ofp)
        self.con.send(msg)
      return None

    tcp_fld = packet.find('tcp')
    if not tcp_fld:
      arpp = packet.find('arp')
      if arpp:
        #  
        if arpp.opcode == arpp.REPLY:
          if arpp.protosrc in self.outstanding_probes:
            #  
            del self.outstanding_probes[arpp.protosrc]
            if (self.live_servers.get(arpp.protosrc, (None,None))
                == (arpp.hwsrc,inport)):
              #  
              pass
            else:
              #  
              self.live_servers[arpp.protosrc] = arpp.hwsrc,inport
              self.log.info("Server %s up", arpp.protosrc)
        return

      #  
      return drop()

     
    
    ip_fld = packet.find('ipv4')

    if ip_fld.srcip in self.servers:
       

      key = ip_fld.srcip,ip_fld.dstip,tcp_fld.srcport,tcp_fld.dstport
      entry = self.memory.get(key)

      if entry is None:
        # We either didn't install it, or we forgot about it.
        self.log.debug("No client for %s", key)
        return drop()

      # Refresh time timeout and reinstall.
      entry.refresh()

      #self.log.debug("Install reverse flow for %s", key)

      # Install reverse table entry
      mac,port = self.live_servers[entry.server]

      actions = []
      actions.append(of.ofp_action_dl_addr.set_src(self.mac))
      actions.append(of.ofp_action_nw_addr.set_src(self.service_ip))
      actions.append(of.ofp_action_output(port = entry.c_port))
      match = of.ofp_match.from_packet(packet, inport)

      msg = of.ofp_flow_mod(command=of.OFPFC_ADD,
                            idle_timeout=FLOW_IDLE_TIMEOUT,
                            hard_timeout=of.OFP_FLOW_PERMANENT,
                            data=event.ofp,
                            actions=actions,
                            match=match)
      self.con.send(msg)

    elif ip_fld.dstip == self.service_ip:
      # Ah, it's for our service IP and needs to be load balanced

      # Do we already know this flow?
      key = ip_fld.srcip,ip_fld.dstip,tcp_fld.srcport,tcp_fld.dstport
      entry = self.memory.get(key)
      if entry is None or entry.server not in self.live_servers:
        # Don't know it (hopefully it's new!)
        if len(self.live_servers) == 0:
          self.log.warn("No servers")
          return drop()

        # Pick a server for this flow
        server = self._pick_server(key, inport)
        self.log.debug("Directing traffic towards %s", server)
        entry = MemoryIngress(server, packet, inport)
        self.memory[entry.key1] = entry
        self.memory[entry.key2] = entry
   
      # Update timestamp
      entry.refresh()

      # Set up table entry towards selected server
      mac,port = self.live_servers[entry.server]

      actions = []
      actions.append(of.ofp_action_dl_addr.set_dst(mac))
      actions.append(of.ofp_action_nw_addr.set_dst(entry.server))
      actions.append(of.ofp_action_output(port = port))
      match = of.ofp_match.from_packet(packet, inport)

      msg = of.ofp_flow_mod(command=of.OFPFC_ADD,
                            idle_timeout=FLOW_IDLE_TIMEOUT,
                            hard_timeout=of.OFP_FLOW_PERMANENT,
                            data=event.ofp,
                            actions=actions,
                            match=match)
      self.con.send(msg)


# Remember which DPID we're operating on (first one to connect)
target_switch_dpid = None

def launch (ip, servers):
  servers = servers.replace(","," ").split()
  servers = [IPAddr(x) for x in servers]
  ip = IPAddr(ip)

  # Boot up ARP Responder
  from proto.arp_responder import launch as arp_launch
  arp_launch(eat_packets=False,**{str(ip):True})
  import logging
  logging.getLogger("proto.arp_responder").setLevel(logging.WARN)

  def _handle_ConnectionUp (event):
    global target_switch_dpid
    if target_switch_dpid is None:
      log.info("IP Load Balancer Up.")
      core.registerNew(iplb, event.connection, IPAddr(ip), servers)
      target_switch_dpid = event.dpid

    if target_switch_dpid != event.dpid:
      log.warn("Ignoring switch %s", event.connection)
    else:
      log.info("Load Balancing on switch %s", event.connection)

      # Gross hack
      core.iplb.con = event.connection
      event.connection.addListeners(core.iplb)


  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
