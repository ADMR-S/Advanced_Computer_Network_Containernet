#!/usr/bin/python
# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.packet import ethernet,ipv4, ipv6,tcp
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()
clientIP_str = "172.16.0.1"
serverIP_str = "172.16.1.1"
#clientIP_str = "10.0.1.1"
#serverIP_str = "10.0.2.1"

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}

  # AJOUT TP3
  def http_via_s2(self, packet, packet_in):
    dpid = dpid_to_str(self.connection.dpid)

    if dpid == "00-00-00-00-00-01":
      if packet_in.in_port == 3:
        self.resend_packet(packet_in, 2)
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type
        msg.match.in_port = 3
        msg.match.nw_proto = 6
        msg.match.tp_dst = 80
        msg.match.dl_type = ethernet.IP_TYPE
        msg.actions.append(of.ofp_action_output(port=2))
        self.connection.send(msg)

      elif packet_in.in_port == 2:
        self.resend_packet(packet_in, 3)
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type
        msg.match.in_port = 2
        msg.match.nw_proto = 6
        msg.match.tp_src = 80
        msg.match.dl_type = ethernet.IP_TYPE
        msg.actions.append(of.ofp_action_output(port=3))
        self.connection.send(msg)

      elif dpid == "00-00-00-00-00-02":
        if packet_in.in_port == 1:
          self.resend_packet(packet_in, 2)
          msg = of.ofp_flow_mod()
          msg.match.dl_type = packet.type
          msg.match.in_port = 1
          msg.actions.append(of.ofp_action_output(port=2))
          self.connection.send(msg)

        elif packet_in.in_port == 2:
          self.resend_packet(packet_in, 1)
          msg = of.ofp_flow_mod()
          msg.match.dl_type = packet.type
          msg.match.in_port = 2
        
          msg.actions.append(of.ofp_action_output(port=1))
          self.connection.send(msg)
        
        elif dpid == "00-00-00-00-00-03":
          if packet_in.in_port == 2:
            self.resend_packet(packet_in, 3)
            msg = of.ofp_flow_mod()
            msg.match.dl_type = packet.type
            msg.match.in_port = 2
            msg.actions.append(of.ofp_action_output(port=3))
            self.connection.send(msg)
          
          elif packet_in.in_port == 3:
            self.resend_packet(packet_in, 2)
            msg = of.ofp_flow_mod()
            msg.match.dl_type = packet.type
            msg.match.in_port = 3
            msg.actions.append(of.ofp_action_output(port=2))
            self.connection.send(msg)

  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """

    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).
        
  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """

    # """ # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #
    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    # print "Src: ",str(packet.src),":", packet_in.in_port,"Dst:", str(packet.dst)
    
    if packet.src not in self.mac_to_port:
        print("Learning that " + str(packet.src) + " is attached at port " + str(packet_in.in_port))
        self.mac_to_port[packet.src] = packet_in.in_port
    # self.mac_to_port ... <add or update entry>

    # if the port associated with the destination MAC of the packet is known:
    if packet.dst in self.mac_to_port:
      # Send packet out the associated port
      print(str(packet.dst) + " destination known. only send message to it")
      self.resend_packet(packet_in, self.mac_to_port[packet.dst])

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      # log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      print(str(packet.dst) + " not known, resend to everybody")
      self.resend_packet(packet_in, of.OFPP_ALL)
            
  def act_like_routers_in_legacy_case (self, packet, packet_in):
    log.debug("Packet captured by first time by switch %s at input port %d" % (dpid_to_str(self.connection.dpid), packet_in.in_port))
    
    #if captured at s1
    if dpid_to_str(self.connection.dpid) == "00-00-00-00-00-01": 
      if packet_in.in_port == 3 :
        log.debug("We send out directly packet to s3 via port 1")
        self.resend_packet(packet_in, 1)          
        log.debug("Installing flow ...")
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type
        msg.match.in_port = packet_in.in_port
        msg.actions.append(of.ofp_action_output(port=1))
        self.connection.send(msg)

      if packet_in.in_port == 1 :
        log.debug("We send out directly packet to h1 via port 3")
        self.resend_packet(packet_in, 3)
        log.debug("Installing flow ...")
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type
        msg.match.in_port = packet_in.in_port
        msg.actions.append(of.ofp_action_output(port=3))
        self.connection.send(msg)

    #if captured at s3 
    if dpid_to_str(self.connection.dpid) == "00-00-00-00-00-03" :
      if packet_in.in_port == 3 :
        log.debug("We send out directly packet to s1 via port 1")
        self.resend_packet(packet_in, 1)          
        log.debug("Installing flow ...")
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type        
        msg.match.in_port = packet_in.in_port
        msg.actions.append(of.ofp_action_output(port=1))
        self.connection.send(msg)
        
      if packet_in.in_port == 1 :
        log.debug("We send out directly packet to h2 via port 3")
        self.resend_packet(packet_in, 3)
        log.debug("Installing flow ...")
        msg = of.ofp_flow_mod()
        msg.match.dl_type = packet.type 
        msg.match.in_port = packet_in.in_port
        msg.actions.append(of.ofp_action_output(port=3))
        self.connection.send(msg)     

  def http_packet(self, packet): # to identify a HTTP packet
    http_pkt = 0 
    if packet.type == ethernet.IP_TYPE:
      ipv4_packet = packet.find("ipv4") 
      #Ajout TP3
      if ipv4_packet is None:
        ipv6_packet = packet.find("ipv6")
        if ipv6_packet is None:
          log.warning("Ignoring incomplete packet")
          return
        else :
          if ipv6_packet.protocol == ipv6.TCP_PROTOCOL:
            tcp_segment = ipv6_packet.find("tcp")
            if tcp_segment.dstport == 80 or tcp_segment.srcport == 80 :
              http_pkt = 1
      elif ipv4_packet.protocol == ipv4.TCP_PROTOCOL:
        tcp_segment = ipv4_packet.find("tcp")
        if tcp_segment.dstport == 80 or tcp_segment.srcport == 80 :
          http_pkt = 1
    print("HTTP packet: ", http_pkt)
    return http_pkt  

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.
    
    print(packet)

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    #self.act_like_hub(packet, packet_in)
    #self.act_like_switch(packet, packet_in)

    #MODIF TP3
    if self.http_packet(packet):
      self.http_via_s2(packet, packet_in)
    else:
      self.act_like_routers_in_legacy_case(packet, packet_in)
   
def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
