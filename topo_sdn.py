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
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    info('*** Adding server and client container\n')
    client = net.addDocker('client', ip='172.16.0.1/24', dimage="client-image")
    server = net.addDocker('server', ip='172.16.1.1/24', dimage="server-image",
                        ports=[80], port_bindings={80: 8080},
                        volumes=["/home/ADMR-S/Documents/Advanced_Computer_Networks/tp2/containernet/custom/volumes/media:/var/www/html/media"])
                        
    #h1 = net.addHost('h1', cls=Host, ip='10.0.1.1', defaultRoute=None)
    #h2 = net.addHost('h2', cls=Host, ip='10.0.2.1', defaultRoute=None)

    info( '*** Add links\n')
    s1s3 = {'bw':1,'delay':'10ms'}
    net.addLink(s1, s3, intfName1='s1-eth1',intfName2='s3-eth1', cls=TCLink , **s1s3)
    s1s2 = {'bw':5,'delay':'10ms'}
    net.addLink(s1, s2, intfName1='s1-eth2',intfName2='s2-eth1', cls=TCLink , **s1s2)
    s2s3 = {'bw':5,'delay':'10ms'}
    net.addLink(s2, s3,  intfName1='s2-eth2',intfName2='s3-eth2', cls=TCLink , **s2s3)   

    net.addLink(client, s1, intfName1='d1-eth0',intfName2='s1-eth3')
    net.addLink(server, s3, intfName1='d2-eth0',intfName2='s3-eth3')
    
    info( '*** Add phys interfaces to switches \n')
    #Intf('eth1',node=h1)
    #Intf('eth2',node=h2)
    #s1.attach('s1-eth3')
    #s3.attach('s3-eth3')

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])

    info( '*** Post configure switches and hosts\n')
    client.cmd("ip link set d1-eth0 up")
    client.cmd("ip route add 172.16.1.0/24 dev d1-eth0")
    server.cmd("ip link set d2-eth0 up")
    server.cmd("ip route add 172.16.0.0/24 dev d2-eth0")
    
    #h1.cmd("ip addr add 172.16.0.254/24 brd + dev eth1")
    #h1.cmd("echo 1 >/proc/sys/net/ipv4/ip_forward")
    #h1.cmd("route add -net 172.16.1.0/24 gw 10.0.2.1 h1-eth0")

    #h2.cmd("ip addr add 172.16.1.254/24 brd + dev eth2")
    #h2.cmd("echo 1 >/proc/sys/net/ipv4/ip_forward")
    #h2.cmd("route add -net 172.16.0.0/24 gw 10.0.1.1 h2-eth0")

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
