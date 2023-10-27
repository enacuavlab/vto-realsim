#!/usr/bin/python3

import socket
import threading
import time
import sys

tello_cmd_port =  8889
tello_cmd_ip = '192.168.1.68'

tello_cmd_add = (tello_cmd_ip,tello_cmd_port)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#------------------------------------------------------------------------------
def periodic(timer_runs):
  while timer_runs.is_set():
    sock.sendto('battery?'.encode(encoding="utf-8"),tello_cmd_add)
    print("send battery req")
    time.sleep(1)

#------------------------------------------------------------------------------
def recv(timer_runs):
  while timer_runs.is_set():
    try:
      data, server = sock.recvfrom(1518)
      res = (data.decode(encoding="utf-8")).strip()
      if ((res != 'ok') and (res != 'nok')): print('bat '+res)
    except Exception:
      print ('\nExit . . .\n')
      break

#------------------------------------------------------------------------------
if __name__=="__main__":

  timer_runs = threading.Event()
  timer_runs.set()

  recvThread = threading.Thread(target=recv, args=(timer_runs,))
  recvThread.start()

  time.sleep(2.0)
  sock.sendto('command'.encode(encoding="utf-8"),tello_cmd_add)

  timerThread = threading.Thread(target=periodic, args=(timer_runs,))
  timerThread.start()

  sock.sendto('takeoff'.encode(encoding="utf-8"),tello_cmd_add)

  time.sleep(7)
  sock.sendto('land'.encode(encoding="utf-8"),tello_cmd_add)

  timer_runs.clear()
