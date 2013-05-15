#! /usr/bin/env python
# coding=utf-8
import argparse
import socket
import struct
import sys


def connect_package(host, port):
    content = struct.pack('!4sH122s', socket.inet_aton(host), port, "\0"*122)
    packet = struct.pack('!HBc128s', 1, 0, 'N', content)
    return packet


def connect_local_nodes(port1, port2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port1))
    s.sendall(connect_package('127.0.0.1', port2))
    s.close()

def send_data_packet(s, target, packet_nr):
    packet = struct.pack('!HBc128s', packet_nr, target, 'C', " " * 128)
    s.sendall(packet)
    d = s.recv(132)

def pipe(s, target):
    eof = False
    packet_nr = 0
    while not eof:
	data = sys.stdin.read(128)
	if data == "":
	    eof = True
	    break
        packet = struct.pack('!HBc128s', packet_nr, target, 'C', data)
        s.sendall(packet)
        d = s.recv(132)
	packet_nr += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mesh network test util')
    subparsers = parser.add_subparsers(help='commands', dest='command')

    target_port_parser = argparse.ArgumentParser(add_help=False)
    target_port_parser.add_argument('connect_port', type=int)

    connect_parser = subparsers.add_parser('connect', help='connect 2 nodes', parents=[target_port_parser])
    connect_parser.add_argument('target_port', type=int)

    connect_line_parser = subparsers.add_parser('connect_line', help='n nodes in a line', parents=[target_port_parser])
    connect_line_parser.add_argument('node_count', type=int)

    send_packet_parser = subparsers.add_parser('send_packet', help='send a packet to a node', parents=[target_port_parser])
    send_packet_parser.add_argument('target', help=u'0 für quelle 1 für ziel', type=int)
    send_packet_parser.add_argument('packet_nr', help='Paket Nummer', type=int)

    send_packets_parser = subparsers.add_parser('send_packets', help='n packets to a node', parents=[target_port_parser])
    send_packets_parser.add_argument('target', help=u'0 für quelle 1 für ziel', type=int)
    send_packets_parser.add_argument('packet_nr', help='erste Paket Nummer', type=int)
    send_packets_parser.add_argument('packet_count', help='anzahl Pakete', type=int)

    send_packets_parser = subparsers.add_parser('pipe', help='send stdin to a node', parents=[target_port_parser])
    send_packets_parser.add_argument('target', help=u'0 für quelle 1 für ziel', type=int)

    args = parser.parse_args()

    if args.command == 'connect':
        connect_local_nodes(args.connect_port, args.target_port)
    elif args.command == 'connect_line':
        for i in range(args.node_count - 1):
            connect_local_nodes(args.connect_port + i, args.connect_port + i + 1)
    elif args.command == 'send_packet':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', args.connect_port))
        send_data_packet(s, args.target, args.packet_nr)
        s.close()
    elif args.command == 'send_packets':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', args.connect_port))
        for i in range(args.packet_count):
            send_data_packet(s, args.target, args.packet_nr + i)
        s.close()
    elif args.command == 'pipe':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', args.connect_port))
        pipe(s, args.target)
        s.close()