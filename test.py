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
from string import find
import util

# add path to your mesh implementation to this array. One per line makes enable/disable easy
implementations = [ ]
implementations += [ './meshnode.py' ]

BASE_PORT = 3333

PACKAGE_CONTENT_LENGTH = 128

# must not have a trailing newline
THE_MESSAGE = "detachement and love"

PASSED    = 0
FAILED    = 127

be_verbose = False
be_verbose_nodes = False

class MeshNode(object):
   def __init__(self, port, is_sink=False, is_source=False):
      self.is_source  = is_source
      self.is_sink    = is_sink
      self.port       = port

      self.executable = get_random( implementations )

      command = [ self.executable ]

      command += [ str(port) ]

      if self.is_source:
        command += [ '-q' ]
      elif self.is_sink:
        command += [ '-z' ]

      env=None
      if be_verbose_nodes: env={"BE_VERBOSE": "1"}

      if self.is_source or self.is_sink:
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

def connect( node1, node2 ):
  util.connect_local_nodes(node1.port, node2.port)

def connect_to_random_node( nodes_connected, node ):
  connect( get_random(nodes_connected), node)
  
# send message through mesh
#
def send( target, message, port, packet_nr ):
  return util.send_data_packet(port, target, packet_nr, message + "\n")

# receive message at one mesh sink
#
def receive( node_sink ):
  sink_stdouts = [ node_sink.proc.stdout ]
  ret = []
  ready = select.select( sink_stdouts, [], [], 0 ) # dont wait
  while len(ready[0]) > 0:
    package_content = ready[0][0].read(PACKAGE_CONTENT_LENGTH)
    end = find(package_content, "\n")
    ret.append( package_content[0:end] )  # remove "\n": match write + "\n" in send
    ready = select.select( sink_stdouts, [], [], 0 )
  return ret


def test_send_receive(target, sources, sinks):
  exit_code = PASSED

  dbg("sende Daten durch Netz in Richung " + str(target))
  ok_received = []
  for i in range(args.n_messages):
      ok_received.append( send( target, THE_MESSAGE + str(i), get_random(sources).port, i ) )

  dbg("warte, dass Daten Netz durchqueren")
  time.sleep(2)

  dbg("empfange und ueberpruefe Daten")
  messages = []
  for sink in sinks:
    messages.extend( receive( sink ) )

  for i in range(args.n_messages):

    needed_message = THE_MESSAGE + str(i)
    message_found = False

    for msg in messages:
      if msg == needed_message:
        message_found = True
        break

    if message_found == False:
      print "Failed to find message '" + needed_message + "'"
      exit_code = FAILED

    if ok_received[i] == False:
      print "Failed to receive OK packet for C packet with ID " + str(i)
      exit_code = FAILED

  if exit_code == FAILED:
    print "I've received to following messages:"
    for msg in messages:
      print msg

  return exit_code

# main()
if __name__ == '__main__':
  #
  parser = argparse.ArgumentParser(description='Mesh network test harness. ' +
                                               'Please edit the variable "implementations" ' +
					       'at the top of this file to test with ' +
					       'additional/alternative mesh implementations.')

  parser.add_argument('-v',              help='be verbose for test steps',       dest='be_verbose', action='store_true')
  parser.add_argument('-V',              help='be verbose for mesh nodes',       dest='be_verbose_nodes', action='store_true')
  parser.add_argument('n_intermediates', help="connecting nodes",      type=int, nargs='?', default=1)
  parser.add_argument('n_sources',       help="source nodes",          type=int, nargs='?', default=1)
  parser.add_argument('n_sinks',         help="sink nodes",            type=int, nargs='?', default=1)
  parser.add_argument('n_messages',      help="# of messages to send", type=int, nargs='?', default=1)

  args = parser.parse_args()

  be_verbose = args.be_verbose
  be_verbose_nodes = args.be_verbose_nodes
  util.be_verbose = be_verbose

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

  sleeptime = len(nodes_all)/15 + 2
  dbg("warte auf Start der Knoten: " + str(sleeptime) + "s")
  time.sleep(sleeptime)

  dbg("verbinde Knoten miteinander")

  nodes_to_connect = copy.copy(nodes_all)

  # initial node
  nodes_connected  = [ pop_random(nodes_to_connect) ]
  for i in range(len(nodes_to_connect)):
      connect_to_random_node( nodes_connected, pop_random(nodes_to_connect) )
  dbg("warte bis alles verbunden ist: 2s")
  time.sleep(2)

  ### do random other interconnects: TODO ##

  exit_code = test_send_receive(1, nodes_source, nodes_sink)
  if exit_code == PASSED:
    exit_code = test_send_receive(0, nodes_sink, nodes_source)

  dbg("beende Knoten")
  for node in nodes_all:
      node.proc.terminate()
      node.proc.wait()

  if exit_code == FAILED:
    print "Test failed"
  else:
    print "Test passed"

  exit(exit_code)
