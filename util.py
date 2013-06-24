#! /usr/bin/env python
# coding=utf-8
import argparse
import socket
import struct
import sys
import select

be_verbose = False

def dbg(message):
    if be_verbose: sys.stderr.write("Util: " + message + "\n")

def connect_package(host, port):
    content = struct.pack('!4sH122s', socket.inet_aton(host), port, "\0"*122)
    packet  = struct.pack('!HBc128s', 1, 0, 'N', content)
    return packet


def connect_local_nodes(port1, port2):
    dbg("verbinde %d mit %d" % (port1, port2))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port1))
    s.sendall(connect_package('127.0.0.1', port2))
    s.close()

def send_data_packet_on_socket(s, target, packet_nr, data):
    packet = struct.pack('!HBc128s', packet_nr, target, 'C', data)
    s.sendall(packet)
    ready = select.select( [ s ], [], [], 3 ) # wait 3s
    if len(ready[0]) > 0:
        ok_data = s.recv(132)
        if len(ok_data) != 132:
          return False
        ok_id, ok_target, ok_type, ok_content = struct.unpack('!HBc128s', ok_data)
        return ok_id == packet_nr and ok_target == target and ok_type == 'O'
    return False

def send_data_packet(port, target, packet_nr, data):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    ret = send_data_packet_on_socket(s, target, packet_nr, data)
    s.close()
    return ret

def send_data_packets(port, target, count, packet_nr, data):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    for i in range(count):
        send_data_packet_on_socket(s, target, packet_nr + i, data)
    s.close()

def pipe(port, target, first_packet_nr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    packet_nr = first_packet_nr
    while True:
        data = sys.stdin.read(128)
        if data == "":
            break
        dbg( "pipe Daten: " + data )
        packet = struct.pack('!HBc128s', packet_nr, target, 'C', data)
        s.sendall(packet)
        d = s.recv(132)
        packet_nr += 1
    s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mesh network test util')
    parser.add_argument('-v', help='be verbose', dest='be_verbose', action='store_true')

    subparsers = parser.add_subparsers(help='commands', dest='command')

    target_port_parser = argparse.ArgumentParser(add_help=False)
    target_port_parser.add_argument('connect_port', type=int)

    connect_parser = subparsers.add_parser(      'connect',      help=u'2 Knoten verbinden',       parents=[target_port_parser])
    connect_parser.add_argument(                 'target_port',                                    type=int)

    connect_line_parser = subparsers.add_parser( 'connect_line', help=u'N Knoten hintereinander',  parents=[target_port_parser])
    connect_line_parser.add_argument(            'node_count',                                     type=int)

    send_packet_parser = subparsers.add_parser(  'send_packet',  help=u'Paket an Knoten schicken', parents=[target_port_parser])
    send_packet_parser.add_argument(             'target',       help=u'0 für Quelle 1 für Ziel',  type=int)
    send_packet_parser.add_argument(             'packet_nr',    help=u'Paket Nummer',             type=int)

    send_packets_parser = subparsers.add_parser( 'send_packets', help=u'n Pakete an Knoten',       parents=[target_port_parser])
    send_packets_parser.add_argument(            'target',       help=u'0 für Quelle 1 für Ziel',  type=int)
    send_packets_parser.add_argument(            'packet_nr',    help=u'erste Paketnummer',        type=int)
    send_packets_parser.add_argument(            'packet_count', help=u'Anzahl Pakete',            type=int)

    send_packets_parser = subparsers.add_parser( 'pipe',         help=u'Stdin an Knoten schicken', parents=[target_port_parser])
    send_packets_parser.add_argument(            'target',       help=u'0 für Quelle 1 für Ziel',  type=int)
    send_packets_parser.add_argument(            'packet_nr',    help=u'erste Paketnummer',        type=int, nargs='?', default=0)

    args = parser.parse_args()

    be_verbose = args.be_verbose

    if args.command == 'connect':
        connect_local_nodes(args.connect_port, args.target_port)
    elif args.command == 'connect_line':
        for i in range(args.node_count - 1):
            connect_local_nodes(args.connect_port + i, args.connect_port + i + 1)
    elif args.command == 'send_packet':
        send_data_packet(args.connect_port, args.target, args.packet_nr, " " * 128)
    elif args.command == 'send_packets':
        send_data_packets(args.connect_port, args.target, args.packet_count, args.packet_nr, " " * 128)
    elif args.command == 'pipe':
        pipe(args.connect_port, args.target, args.packet_nr)
