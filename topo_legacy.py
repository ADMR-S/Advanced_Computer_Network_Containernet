#!/usr/bin/python

from mininet.net import Containernet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Containernet( topo=None,
                   build=False,
                   xterms=True)
                   #ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    
    info( '*** Add switches\n')
    r2 = net.addHost('r2', cls=Node, ip='0.0.0.0')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    r1 = net.addHost('r1', cls=Node, ip='0.0.0.0')
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3 = net.addHost('r3', cls=Node, ip='0.0.0.0')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')

    info( '*** Add hosts\n')
    info('*** Adding server and client container\n')
    client = net.addDocker('client', ip='172.16.0.1/24', dimage="client-image")
    server = net.addDocker('server', ip='172.16.1.1/24', dimage="server-image",
                        ports=[80], port_bindings={80: 8080},
                        volumes=["/home/ADMR-S/Documents/Advanced_Computer_Networks/tp2/containernet/custom/volumes/media:/var/www/html/media"])
    
    #info( '*** Add phys interfaces to routers \n')
    #Intf('eth1',node=r1)
    #Intf('eth2',node=r3)1

    info( '*** Add links\n')
    r3r1 = {'bw':1,'delay':'10ms'}
    net.addLink(r3, r1, intfName1='r3-eth1',intfName2='r1-eth1', cls=TCLink , **r3r1)
    r1r2 = {'bw':5,'delay':'10ms'}
    net.addLink(r1, r2, intfName1='r1-eth0',intfName2='r2-eth0', cls=TCLink , **r1r2)
    r2r3 = {'bw':5,'delay':'10ms'}
    net.addLink(r2, r3, intfName1='r2-eth1',intfName2='r3-eth0', cls=TCLink , **r2r3)
    
    net.addLink(client, r1, intfName1='d1-eth0',intfName2='r1-eth2')
    net.addLink(server, r3, intfName1='d2-eth0',intfName2='r3-eth2')
    net.addLink(server, r3, intfName1='dash-eth0',intfName2='r3-eth3')


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')

    info( '*** Post configure switches and hosts\n')
    
    r1.cmd("ifconfig r1-eth2 0")
    r1.cmd("ip addr add 172.16.0.254/24 brd + dev r1-eth2")
    r1.cmd("ifconfig r1-eth1 0")
    r1.cmd("ip addr add 10.0.3.1/24 brd + dev r1-eth1")
    r1.cmd("ifconfig r1-eth0 0")
    r1.cmd("ip addr add 10.0.1.1/24 brd + dev r1-eth0")
    r1.cmd("route add default gw 10.0.3.3 r1-eth1")
    r1.cmd("echo 1 >/proc/sys/net/ipv4/ip_forward")

    r1.cmd("ip route add 172.16.1.2 via 10.0.1.2 dev r1-eth0") #ajout route client vers serveur DASH

    r2.cmd("ifconfig r2-eth0 0")
    r2.cmd("ip addr add 10.0.1.2/24 brd + dev r2-eth0")
    r2.cmd("ifconfig r2-eth1 0")
    r2.cmd("ip addr add 10.0.2.2/24 brd + dev r2-eth1")
    r2.cmd("route add -net 172.16.1.0/24 gw 10.0.2.3 r2-eth1")
    r2.cmd("route add -net 172.16.0.0/24 gw 10.0.1.1 r2-eth0")
    r2.cmd("echo 1 >/proc/sys/net/ipv4/ip_forward")

    r2.cmd("ip route add 172.16.1.2 via 10.0.2.3 dev r2-eth1") #ajout route serveur vers client DASH
    
    
    #r2.cmd("ip route add 172.16.0.1/24 via 10.0.1.1 dev r2-eth0 table 100") #Ajout d'une table pour PBR
    #r2.cmd("ip rule add from 172.16.1.2 table 100") #Ajout d'une rèlge pour diriger le trafic DASH

    r3.cmd("ifconfig r3-eth2 0")
    r3.cmd("ip addr add 172.16.1.254/24 brd + dev r3-eth2")
    r3.cmd("ifconfig r3-eth1 0")
    r3.cmd("ip addr add 10.0.3.3/24 brd + dev r3-eth1")
    r3.cmd("ifconfig r3-eth0 0")
    r3.cmd("ip addr add 10.0.2.3/24 brd + dev r3-eth0")
    r3.cmd("route add default gw 10.0.3.1 r3-eth1")
    r3.cmd("echo 1 >/proc/sys/net/ipv4/ip_forward")

    r3.cmd("ip addr add 172.16.1.253/24 dev r3-eth3") #ajout d'une interface pour l'IP secondaire DASH
    r3.cmd("ip link set r3-eth3 up")
    #r3.cmd("ip route add 172.16.1.2 via 172.16.1.253 dev r3-eth3") #connection r3-serveur sur IP DASH
    r3.cmd("ip route add default via 10.0.2.2 dev r3-eth0 table 200") #Ajout d'une table pour PBR
    r3.cmd("ip rule add from 172.16.1.2 table 200") #Ajout d'une rèlge pour diriger le trafic DASH

    client.cmd("ip link set d1-eth0 up")
    client.cmd("ip route add 172.16.1.0/24 via 172.16.0.254")
    server.cmd("ip link set d2-eth0 up")
    server.cmd("ip route add 172.16.0.0/24 via 172.16.1.254")

    server.cmd("ip addr add 172.16.1.2/24 dev dash-eth0") #ajout d'une adresse IP secondaire pour DASH
    server.cmd("ip link set dash-eth0 up") #activer la nouvelle interface 
    client.cmd("ip route add 172.16.1.2 via 172.16.0.254") #ajout d'une route côté client pour DASH


    CLI(net)
    net.stop()
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
