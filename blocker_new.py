# --ports=80
from pox.core import core 

block_ports_list = set()   #intiate a set in which port numbers will be added

def block_checker (event):
	tcp_hdr = event.parsed.find('tcp')  #find tcp header
	if not tcp_hdr: return # Not TCP   	#if no tcp header is found, skip
	if tcp_hdr.srcport in block_ports_list or tcp_hdr.dstport in block_ports_list:  #block traffic even if one port is blocked
   	 	core.getLogger("port blocker").info("Blocked TCP from %s to %s",tcp_hdr.srcport, tcp_hdr.dstport) #display blocking info
		event.halt = True 
def unblock (*ports):
	block_ports_list.difference_update(ports) #return set with given ports removed from the set
def block (*ports):
	block_ports_list.update(ports)			# add given ports to set
def launch (ports = ''):
	block_ports_list.update(int(x) for x in ports.replace(",", " ").split())   #take in multiple ports argument seprated by ,
	core.Interactive.variables['block'] = block 
	core.Interactive.variables['unblock'] = unblock
	core.openflow.addListenerByName("PacketIn", block_checker)

