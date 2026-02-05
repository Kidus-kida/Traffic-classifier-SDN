#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel, info
import time
import subprocess

def run_traffic():
    setLogLevel('info')
    
    info('*** Creating network\n')
    net = Mininet(topo=SingleSwitchTopo(3),
                  controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
                  switch=OVSSwitch,
                  autoSetMacs=True)
    
    info('*** Starting network\n')
    net.start()
    
    h1, h2, h3 = net.get('h1', 'h2', 'h3')
    
    info('*** Running D-ITG receiver on h2\n')
    h2.cmd('ITGRec &')
    time.sleep(2)
    
    info('*** Generating HTTP traffic from h1 to h2\n')
    for _ in range(3):
        h1.cmd('curl -s 10.0.0.2 > /dev/null')
        time.sleep(2)
    
    info('*** Generating DNS requests from h1 to h2\n')
    for _ in range(5):
        h1.cmd('dig @10.0.0.2 google.com')
        time.sleep(1)
        
    info('*** Generating SSH attempts from h3 to h2\n')
    for _ in range(3):
        h3.cmd('ssh -o ConnectTimeout=2 10.0.0.2 "exit" 2>/dev/null')
        time.sleep(2)
    
    info('*** Waiting for dashboard to capture data...\n')
    time.sleep(30)
    
    info('*** Stopping network\n')
    h2.cmd('pkill ITGRec')
    net.stop()

if __name__ == '__main__':
    run_traffic()
