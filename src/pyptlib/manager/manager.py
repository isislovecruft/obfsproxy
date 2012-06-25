import os
import sys
import subprocess

class Manager:
  def __init__(self):
    os.environ['TOR_PT_STATE_LOCATION']='/'
    os.environ['TOR_PT_MANAGED_TRANSPORT_VER']='1'

  def launch(self, path):
    p=subprocess.Popen(['python', '-u', path], stdout=subprocess.PIPE)
    line=p.stdout.readline().strip()
    while line!=None and line !='':
      print(str(line))
      sys.stdout.flush()
      line=p.stdout.readline().strip()
    print('Done!')
