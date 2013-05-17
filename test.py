#! /usr/bin/env python
# coding=utf-8

# Copyright (c) 2013, Tomáš Pospíšek and individual contributors.
# see LICENSE for the license

import argparse
import random
import copy
import subprocess
import time
import select

# add your mesh implementation to this array
implementations = [ './meshnode.py' ]

BASE_PORT = 3333

# must not have a trailing newline
THE_MESSAGE = "detachement and love"

be_verbose = False

class MeshNode(object):
   def __init__(self, port, is_sink=False, is_source=False):
      self.is_source  = is_source
      self.is_sink    = is_sink
      self.port       = port

      self.executable = get_random( implementations )

      command = [ self.executable ]
      if self.is_source:
        command += [ '-q' ]
      elif self.is_sink:
        command += [ '-z' ]

      command += [ str(port) ]

      env=None
      if be_verbose: env={"BE_VERBOSE": "1"}

      if self.is_source:
        self.proc = subprocess.Popen( command, env=env, stdin =subprocess.PIPE )
      elif self.is_sink:
        self.proc = subprocess.Popen( command, env=env, stdout=subprocess.PIPE )
      else:
        self.proc = subprocess.Popen( command, env=env )


def dbg(message):
   if be_verbose: print "Test: " + message

# return random index in array
#
def random_index( array ):
  return random.randint( 0, len(array) - 1)


# return and random element from array
# no checks are performed
#
def get_random(array):
  return array[random_index(array)]

# return and remove random element from array
# no checks are performed
#
def pop_random(array):
  return array.pop(random_index(array))


def add_new_source_to(nodes, port):
  nodes.append( MeshNode( port, is_source=True ))

def add_new_sink_to(nodes, port):
  nodes.append( MeshNode( port, is_sink=True   ))

def add_new_intermediate_to(nodes, port):
  nodes.append( MeshNode( port                 ))

# construct 'util' command
#
def cmd( args ):
  command = [ './util.py' ]
  if be_verbose: command += [ '-v' ]
  return command + args

def connect( node1, node2 ):
  subprocess.call( cmd([ 'connect', str(node1.port), str(node2.port) ]))

def connect_to_random_node( nodes_connected, node ):
  connect( get_random(nodes_connected), node)
  
# send message through mesh
#
def send( message, port ):
  command = cmd([ 'pipe', str(port), "1" ]) # 1 == target
  dbg("sende an %d: %s" % (port, message)) 
  proc = subprocess.Popen( command, stdin=subprocess.PIPE )
  proc.stdin.write( message + "\n") # match readline in receive
  proc.stdin.flush()
  proc.stdin.close()
  dbg("warte, weiss nicht warum")
  time.sleep(1) # why is this necessary?
  proc.terminate()
  proc.wait()
  

# receive message at one mesh sink
#
def receive( nodes_sink ):
  sink_stdouts = map( lambda sink: sink.proc.stdout, nodes_sink )
  ready = select.select( sink_stdouts, [], [], 3 ) # wait 3s
  if len(ready[0]) > 0:
    return ready[0][0].readline().rstrip("\n") # match write + "\n" in send
  else:
    return ""


# main()
if __name__ == '__main__':
  #
  parser = argparse.ArgumentParser(description='Mesh network test harness. ' +
                                               'Please edit the variable "implementations" ' +
					       'at the top of this file to test with additional' +
					       'mesh implementations.')

  parser.add_argument('-v',              help='be verbose',       dest='be_verbose', action='store_true')
  parser.add_argument('n_intermediates', help="connecting nodes", type=int, nargs='?', default=1)
  parser.add_argument('n_sources',       help="source nodes",     type=int, nargs='?', default=1)
  parser.add_argument('n_sinks',         help="sink nodes",       type=int, nargs='?', default=1)

  args = parser.parse_args()

  be_verbose = args.be_verbose

  nodes_all          = []
  nodes_source       = []
  nodes_sink         = []
  nodes_intermediate = []

  dbg("erstelle Knoten")

  port = BASE_PORT
  for i in range(args.n_sources      ): add_new_source_to(       nodes_source      , port); port += 1
  for i in range(args.n_sinks        ): add_new_sink_to(         nodes_sink        , port); port += 1
  for i in range(args.n_intermediates): add_new_intermediate_to( nodes_intermediate, port); port += 1 

  nodes_all = nodes_source + nodes_sink + nodes_intermediate

  dbg("warte auf Start der Knoten")
  time.sleep(1)

  dbg("verbinde Knoten miteinander")

  nodes_to_connect = copy.copy(nodes_all)

  # initial node
  nodes_connected  = [ pop_random(nodes_to_connect) ]
  for i in range(len(nodes_to_connect)):
      connect_to_random_node( nodes_connected, pop_random(nodes_to_connect) )

  ### do random other interconnects: TODO ##

  dbg("sende Daten durch Netz")
  send( THE_MESSAGE, get_random(nodes_source).port )

  dbg("warte, dass Daten Netz durchqueren")
  time.sleep(1)

  dbg(u"empfange und überprüfe Daten")
  exit_code = 127 # fail
  message = receive( nodes_sink )
  if message == THE_MESSAGE:
    print "Test passed"
    exit_code = 0
  else:
    print "Test failed"
    print "Expected: " + THE_MESSAGE
    print "Received: " + message

  dbg("beende Knoten")
  for node in nodes_all:
      node.proc.terminate()
      node.proc.wait()

  exit(exit_code)
