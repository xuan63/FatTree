#!/usr/bin/python
#-*- coding:utf8 -*-
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import logging
import os

logging.basicConfig(filename='./fattree.log', level=logging.INFO)
logger = logging.getLogger(__name__)


class Fattree(Topo):
    logger.debug("Class Fattree")
    CoreSwitchList = []
    AggSwitchList = []
    EdgeSwitchList = []
    HostList = []

    def __init__(self, k):
        logger.debug("Class Fattree init")
        self.pod = k
        self.iCoreLayerSwitch = (k/2)**2
        self.iAggLayerSwitch = k*k/2
        self.iEdgeLayerSwitch = k*k/2
        self.iHost = k**3/4

        #Init Topo
        Topo.__init__(self)

    def createTopo(self):
        self.createCoreLayerSwitch(self.iCoreLayerSwitch)
        self.createAggLayerSwitch(self.iAggLayerSwitch)
        self.createEdgeLayerSwitch(self.iEdgeLayerSwitch)
        self.createHost(self.iHost, self.pod)

    def _addSwitch(self, number, level, switch_list):
        for x in xrange(1, number+1):
            PREFIX = str(level) + "00"
            if x >= int(10):
                PREFIX = str(level) + "0"
            switch_list.append(self.addSwitch('s' + PREFIX + str(x)))

    def createCoreLayerSwitch(self, NUMBER):
        logger.debug("Create Core Layer")
        self._addSwitch(NUMBER, 1, self.CoreSwitchList)


    def createAggLayerSwitch(self, NUMBER):
        logger.debug("Create Aggregation Switch")
        self._addSwitch(NUMBER, 2, self.AggSwitchList)


    def createEdgeLayerSwitch(self, NUMBER):
        logger.debug("Create Edge Switch")
        self._addSwitch(NUMBER, 3, self.EdgeSwitchList)

    def createHost(self, NUMBER, pod):
        mount = 1
        for p in xrange(0, pod):
            for w in xrange(pod/2, pod):
                for h in xrange(2, pod/2+2):
                    Host = self.addHost('h{}'.format(mount), ip = '%d.%d.%d.0/16' % (p,w,h))
                    self.HostList.append(Host)
                    mount += 1


    """
    Add Link
    """
    def createLink(self, bw_c2a=0.2, bw_a2e=0.1, bw_h2a=0.5):
        logger.debug("Add link Core to Agg.")
        for i in xrange(self.pod**2/4):
            x = i/(self.pod/2) 
            mount = 0
            for j in xrange(self.pod):
                up = self.CoreSwitchList[i]
                down = self.AggSwitchList[x + mount*(self.pod/2)]
                # self.addLink(up, down, bw=bw_c2a)
                self.addLink(up, down)
                mount += 1


        logger.debug("Add link Agg to Edge.")        
        for i in xrange(self.pod**2/2):
            x = i/(self.pod/2)
            for j in xrange(self.pod/2):
                up = self.AggSwitchList[i]
                down = self.EdgeSwitchList[x*(self.pod/2) + j]
                # self.addLink(up, down, bw=bw_a2e)
                self.addLink(up, down)

        logger.debug("Add link Edge to Host.")
        x = 0
        for i in xrange(self.pod**2/2):
            for j in xrange(self.pod/2):
                up = self.EdgeSwitchList[i]
                down = self.HostList[x*(self.pod/2) + j]
                # self.addLink(up, down, bw=bw_h2a)
                self.addLink(up, down)
            x += 1

    def set_ovs_protocol_13(self,):
        self._set_ovs_protocol_13(self.CoreSwitchList)
        self._set_ovs_protocol_13(self.AggSwitchList)
        self._set_ovs_protocol_13(self.EdgeSwitchList)

    def _set_ovs_protocol_13(self, sw_list):
            for sw in sw_list:
                cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % sw
                os.system(cmd)

def createTopo(k):
    logging.debug("LV1 Create Fattree")
    topo = Fattree(k)
    topo.createTopo()
    topo.createLink()
    logging.debug("LV1 Start Mininet")
    net = Mininet(topo, build=False, link=TCLink, autoSetMacs=True)
    net.addController('Controller',controller=RemoteController, ip='127.0.0.1', port=6633)
    net.start()
    '''
        Set OVS's protocol as OF13
    '''
    topo.set_ovs_protocol_13()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    if os.getuid() != 0:
        logger.debug("You are NOT root")
    elif os.getuid() == 0:
        createTopo(4)