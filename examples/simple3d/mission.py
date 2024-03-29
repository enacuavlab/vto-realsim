#!/usr/bin/python3

import threading
import socket
import time
import threading

import numpy as np

from vehicle import Vehicle

#------------------------------------------------------------------------------
#telloFreq = 10
#telloFreq = 5
telloFreq = 5

H_max = 1.2

#V_coef = 0.8 # to be tuned with repealance
#V_coef = 1.0
#V_coef = 1.2
#V_coef = 1.4
V_coef = 1.6

#W_coef = 0.6
#W_coef = 0.4
W_coef = 0.2

#------------------------------------------------------------------------------
def compute_flow(vehicles):

  flow_vels = np.zeros([len(vehicles),3])

  V_sink    = np.zeros([len(vehicles),2]) # Velocity induced by sink element
  V_source  = np.zeros([len(vehicles),2]) # Velocity induced by source elements
  V_sum     = np.zeros([len(vehicles),2]) # V_gamma + V_sink + V_source
  V_flow    = np.zeros([len(vehicles),2]) # Normalized velocity inversly proportional to magnitude
  V_norm2    = 0

  W_sink     = 0
  W_source   = 0
  W_sum      = 0
  W_flow    = np.zeros([len(vehicles)]) # Vertical velocity component (to be used in 3-D scenarios)

  for f,vehicle in enumerate(vehicles):

    # Cartesian velocity reprsentation by 2D sink
    # (Velocity induced by 2D point sink, eqn. 10.2 & 10.3 in Katz & Plotkin:)
    V_sink[f,0] = (-vehicle.sink_strength*(vehicle.position[0]-vehicle.goal[0]))/\
                  (2*np.pi*((vehicle.position[0]-vehicle.goal[0])**2+(vehicle.position[1]-vehicle.goal[1])**2))
    V_sink[f,1] = (-vehicle.sink_strength*(vehicle.position[1]-vehicle.goal[1]))/\
                  (2*np.pi*((vehicle.position[0]-vehicle.goal[0])**2+(vehicle.position[1]-vehicle.goal[1])**2))


    # Velocity induced by 3-D point sink. Katz&Plotkin Eqn. 3.25
    W_sink = (-vehicle.sink_strength*(vehicle.position[2]-vehicle.goal[2]))/\
      (4*np.pi*(((vehicle.position[0]-vehicle.goal[0])**2+(vehicle.position[1]-vehicle.goal[1])**2+(vehicle.position[2]-vehicle.goal[2])**2)**1.5))


    othervehicleslist = vehicles[:f] + vehicles[f+1:]
    for othervehicle in othervehicleslist:
      # Cartesian velocity reprsentation by 2D source
      V_source[f,0] += (othervehicle.source_strength*(vehicle.position[0]-othervehicle.position[0]))/\
                       (2*np.pi*((vehicle.position[0]-othervehicle.position[0])**2+(vehicle.position[1]-othervehicle.position[1])**2))
      V_source[f,1] += (othervehicle.source_strength*(vehicle.position[1]-othervehicle.position[1]))/\
                       (2*np.pi*((vehicle.position[0]-othervehicle.position[0])**2+(vehicle.position[1]-othervehicle.position[1])**2))

      W_source += (othervehicle.source_strength*(vehicle.position[2]-othervehicle.position[2]))/\
        (4*np.pi*((vehicle.position[0]-othervehicle.position[0])**2+(vehicle.position[1]-othervehicle.position[1])**2+(vehicle.position[2]-othervehicle.position[2])**2)**(3/2))

    # Total velocity induced :
    V_sum = V_sink + V_source

    V_norm2 = (V_sum[f,0]**2 + V_sum[f,1]**2)

    # Flow velocity inversely proportional to velocity magnitude:
    V_flow = V_sum/(V_coef*V_norm2)

    W_sum = W_sink + W_source
    W_flow[f] = -0.5 if ((abs(vehicle.velocity[0])+abs(vehicle.velocity[1]))<0.3) else (W_sum/W_coef)  # apply vertical correction, when moving horizontal else go down

    print(str(vehicle.ID)+" "+str(W_flow[f]))

    W_flow[f] = np.clip(W_flow[f],0.0, H_max) if W_flow[f] > 0 else np.clip(W_flow[f],-H_max, 0.0) 

    flow_vels[f,:] = [V_flow[f,0],V_flow[f,1],W_flow[f]]

  return flow_vels


#------------------------------------------------------------------------------
class Thread_mission(threading.Thread):

  def __init__(self,quitflag,mobiles):
    threading.Thread.__init__(self)
    self.quitflag = quitflag
    self.mobiles = mobiles
    self.suspend = True
    self.telloPeriod = 1/telloFreq
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


  def send_command(self,droneID,cmdstr):
    if (droneID != 0): self.sock.sendto(cmdstr.encode(encoding="utf-8"),self.mobiles[droneID][2])
    else: 
      cmd = cmdstr.encode(encoding="utf-8")
      for ac in self.mobiles:
        if (self.mobiles[ac][0]) and (ac != 888): self.sock.sendto(cmd,self.mobiles[ac][2])



  def run(self):

    while (self.suspend): time.sleep(self.telloPeriod)

    self.send_command(0,'command')
#    self.send_command(0,'streamon')
#    time.sleep(1)
    self.send_command(0,'takeoff')
    time.sleep(8)
    self.send_command(0,'up 150')
    time.sleep(7)

    self.guidanceLoop() # drone should be flying to have position from optitrack
    self.send_command(0,'land')



  def guidanceLoop(self):
    unvalidcpt = 0
    loop_incr = 0

    flyings=[]
    for elt in self.mobiles:
      if (elt!=888): flyings.append(Vehicle(elt))

    try: 

      while not self.quitflag and loop_incr < 15000 and not (self.suspend):
        loop_incr = loop_incr + 1
        starttime = time.time()

        if (self.mobiles[888][0]):               # check suspended position capture for real target 
          if not (self.mobiles[888][1].valid):
            unvalidcpt = unvalidcpt+1
            if unvalidcpt == 10: break
            else: continue
          else: unvalidcpt= 0

        for elt in self.mobiles:
          if (elt != 888):
            for v in flyings:
              if (v.ID == elt):
                offset = self.mobiles[elt][1]
                offsettarget = self.mobiles[888][1]
                v.update(offset.position,offset.velocity,offset.heading,offsettarget.position,5)

        flow_vels = compute_flow(flyings)
 
        i = 0
        for elt in self.mobiles:
          if (elt != 888):
            for v in flyings:
              if (v.ID == elt):
                cmd=v.apply_flow(flow_vels[i])
                i=i+1
                if (self.mobiles[v.ID][0]): self.send_command(v.ID,'rc {} {} {} {}'.format(cmd[0],cmd[1],cmd[2],cmd[3]))
                else: self.mobiles[v.ID][1].appliedspeed = cmd
 
        time.sleep(self.telloPeriod-(time.time()-starttime))

    finally: 
      print("Thread_mission stop")


  def trigger(self):
    if self.suspend: self.suspend = False
    else: self.suspend = True
