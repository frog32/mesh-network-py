#! /usr/bin/env python
# coding=utf-8
from datetime import datetime
from twisted.internet import reactor, protocol, task
from struct import pack, unpack
from socket import inet_ntoa
from random import randint
from os     import environ
import argparse
import sys


PACKAGE_FORMAT = '!HBc128s'

class MeshNodeProtocol(protocol.Protocol):

    def dataReceived(self, data):
        self.mesh_node.handle_packet(data, self)

    def connectionMade(self):
        self.mesh_node = self.factory.mesh_node
        self.mesh_node.add_neighbor(self)

    def connectionLost(self, reason):
        self.mesh_node.remove_neighbor(self)

    def send_packet(self, packet):
        self.transport.write(packet)


class MeshNode(object):
    def __init__(self, port, is_sink, is_source, be_verbose):
        self.is_source         = is_source
        self.is_sink           = is_sink
        self.factory           = protocol.ServerFactory()
        self.factory.protocol  = MeshNodeProtocol
        self.factory.mesh_node = self
        self.port              = port
        self.be_verbose        = be_verbose
        reactor.listenTCP(port, self.factory)

        self.neighbors        = {}
        self.valid_routes     = {}
        self.neighbor_id      = 0
        self.package_tracker  = {}
        self.confirmed_routes = {}

        self.dbg("erstellt")

    def dbg( self, string ):
        if self.be_verbose:
            node_type = ' '
            if self.is_sink:     node_type = 'Z'
            elif self.is_source: node_type = 'Q'
            sys.stderr.write( ("Knoten %s %d: " % (node_type, self.port)) + string + "\n")

    def clean_package_tracker(self, packet_id):
        if packet_id in self.package_tracker:
            try:
                del self.valid_routes[self.package_tracker[packet_id][1]]
            except KeyError:
                pass
            del self.package_tracker[packet_id]

    def add_neighbor(self, node):
        self.neighbors[self.neighbor_id] = node
        node.neighbor_id = self.neighbor_id
        self.dbg( "Verbindung von Nachbar mit ID %s empfangen" % node.neighbor_id )
        self.neighbor_id += 1

    def remove_neighbor(self, node):
        del self.neighbors[node.neighbor_id]
        for target in self.valid_routes.keys():
            if self.valid_routes[target] == node:
                del self.valid_routes[target]

        self.dbg( "Verbindung zu  Nachbar mit ID %s geschlossen" % node.neighbor_id )

    def handle_packet(self, data, source):
        packet_id, target, packet_type, content = unpack(PACKAGE_FORMAT, data)
        self.dbg( "Paket Typ %s mit ID %s erhalten" % (packet_type, packet_id) )
        if packet_type == 'C':
            self.dbg( "Paket Inhalt: %s" % content )
            if self.is_sink and target == 1 or self.is_source and target == 0:
                # Paket is angekommen
                sys.stdout.write( content )
                sys.stdout.flush()
                packet = pack(PACKAGE_FORMAT, packet_id, target, 'O', ' ' * 128)
                source.send_packet(packet)
                return

            if packet_id in self.package_tracker:
                # Paket schon gesehen -> verwerfen
                return

            # Daten übermitteln
            if target in self.valid_routes:
                # Route existiert
                self.valid_routes[target].send_packet(data)
            else:
                # Route existiert nicht
                self.dbg( 'Route existiert nicht' )
                for neighbor_id, neighbor in self.neighbors.items():
                    if neighbor_id != source.neighbor_id:
                        neighbor.send_packet(data)

            self.package_tracker[packet_id] = (source.neighbor_id, target)
            reactor.callLater(0.1, self.clean_package_tracker, packet_id)

        elif packet_type == 'O':
            # Bestätigung übermitteln
            self.dbg( "Bestaetigung für Paket %s erhalten" % packet_id )
            if packet_id not in self.package_tracker:
                #raise Exception("Bestätigung für Paket %s jedoch kein Paket vorhanden" % packet_id)
                print >> stderr, Exception("Bestätigung für Paket %s jedoch kein Paket vorhanden" % packet_id)
            # Knoten könnte schon wieder disconnected sein todo
            package_tracker_entry = self.package_tracker[packet_id]
            source_id = package_tracker_entry[0]
            self.valid_routes[package_tracker_entry[1]] = source
            # aus Paket Tracker löschen
            del self.package_tracker[packet_id]
            self.neighbors[source_id].send_packet(data)

        elif packet_type == 'N':
            # neuer Mesh Knoten
            factory = protocol.ClientFactory()
            factory.protocol = MeshNodeProtocol
            factory.mesh_node = self
            host, port, crap = unpack('!4sH122s', content)
            host = inet_ntoa(host)
            self.dbg( "erstelle neue Verbindung zu Knoten %s:%d" % (host,port))
            reactor.connectTCP(host, port, factory)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='mesh network node',
                                     epilog='set the environment variable BE_VERBOSE to enable debugging output')

    parser.add_argument('port', type=int)
    parser.add_argument('-z', dest='is_sink',    action='store_true', help='is the sink'  )
    parser.add_argument('-q', dest='is_source',  action='store_true', help='is the source')

    args = parser.parse_args()

    m = MeshNode(args.port,
                 is_sink=args.is_sink, is_source=args.is_source,
                 be_verbose=('BE_VERBOSE' in environ))

    reactor.run()
