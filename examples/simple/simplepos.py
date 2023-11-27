#!/usr/bin/python3

import threading,queue,time,argparse
import numpy as np

import sys
sys.path.append("/home/pprz/Projects/vto-realsim/natnet-utilities")

acId = 123   # Rigid body tracked id
optiFreq = 20 # Check that optitrack stream at least with this value
printFreq = 10
printPeriod = 1 / printFreq 

------------------------------------------------------------------------------
class Thread_print(threading.Thread):
  def __init__(self,quitflag,mobiles):
    threading.Thread.__init__(self)
    self.quitflag = quitflag

  def run(self):
    while (self.suspend): time.sleep(self.printFreq)
    try:
      while not self.quitflag and not (self.suspend):
        starttime = time.time()
        curr = threadMotion.rigidBodyDict[acId]
        print(curr.valid) 
        #,curr.position,curr.velocity,curr.heading,curr.quaternion)
        time.sleep(printPeriod-(time.time()-starttime))
    finally:
      print("Thread_print stop")
 
#------------------------------------------------------------------------------
class Flag(threading.Event):
  def __bool__(self):
    return self.is_set()

#------------------------------------------------------------------------------
def main(bodies):
  flag = Flag()
  if len(bodies):
    try:
      threadMotion = Thread_natnet(flag,bodies,optiFreq)
      threadMotion.start()
      threadPrint = Thread_print(flag,threadMotion)
      threadPrint.start()
    except ValueError as msg:
      print(msg)
      exit()
      
#------------------------------------------------------------------------------
if __name__=="__main__":
  main(Rigidbody(acId))
