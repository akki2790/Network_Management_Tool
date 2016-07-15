#!/usr/bin/python

"""
Script created by VND - Visual Network Description (SDN version)
"""
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink

def topology():
    "Create a network."
    net = Mininet( controller=RemoteController, link=TCLink, switch=OVSKernelSwitch )

    print "*** Creating nodes"
    c1 = net.addController( 'c1', controller=RemoteController, ip='127.0.0.1', port=6633 )
    s1 = net.addSwitch( 's1', listenPort=6634, mac='00:00:00:00:00:01' )
    
    h1 = net.addHost( 'h1', mac='00:00:00:00:00:11', ip='10.0.0.1/8' )
    h2 = net.addHost( 'h2', mac='00:00:00:00:00:12', ip='10.0.0.2/8' )
    h3 = net.addHost( 'h3', mac='00:00:00:00:00:13', ip='10.0.0.3/8' )
    h4 = net.addHost( 'h4', mac='00:00:00:00:00:14', ip='10.0.0.4/8' )
    h5 = net.addHost( 'h5', mac='00:00:00:00:00:15', ip='10.0.0.5/8' )
    h6 = net.addHost( 'h6', mac='00:00:00:00:00:16', ip='10.0.0.6/8' )
    h7 = net.addHost( 'h7', mac='00:00:00:00:00:17', ip='10.0.0.7/8' )
    h8 = net.addHost( 'h8', mac='00:00:00:00:00:18', ip='10.0.0.18/8' )

    print "*** Creating links"
    net.addLink(h8, s1, 0, 8)
    net.addLink(h7, s1, 0, 7)
    net.addLink(h6, s1, 0, 6)
    net.addLink(h5, s1, 0, 5)
    net.addLink(h4, s1, 0, 4)
    net.addLink(h3, s1, 0, 3)
    net.addLink(h2, s1, 0, 2)
    net.addLink(h1, s1, 0, 1)

    print "*** Starting network"
    net.build()
    s1.start( [c1] )
    c1.start()

    print "*** Running CLI"
    CLI( net )

    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    topology()

