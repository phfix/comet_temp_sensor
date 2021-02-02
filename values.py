#
# Read current measured values example
#
# Requirements: Python 3.8 ( www.python.org )
#               Wx7xx device with firmware version 10-0-0-6 or higher
#
#  Purpose of this example is demonstration of communication with Wx7xx device(s).
#  It is not intended to be used in production environment without further changes.
#

#connection parameters
#TCP_IP = '192.168.1.213'
TCP_IP = '192.168.3.1'
TCP_PORT = 502

import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_IP, TCP_PORT))

try:
    req = struct.pack('12B', 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x01, 0x03, 0x9C, 0x40, 0x00, 0x04)
    #send ModbusTCP request
    sock.send(req)
    '''
    Modbus TCP request:
       0x00 0x00 0x00 0x00 - transaction ID + protocol ID
       0x00 0x06           - length of following bytes
       0x01                - unit ID
       0x03                - function code (read holding registers)
       0x9C 0x40           - register address (from manual - 0x9C40=channel 1)
       0x00 0x04           - number of registers (reading of four measured values)
    '''

    #read ModbusTCP response
    rcv = sock.recv(64)
    print(rcv)
    #decode response
    out = struct.unpack(">IHccchhhh", rcv)
    print("Channel 1:", out[5]/10,
          "\nChannel 2:", out[6]/10,
          "\nChannel 3:", out[7]/10,
          "\nChannel 4:", out[8])
    '''
    Modbus TCP response:
       0x00 0x00 0x00 0x00 - (I integer 4) transaction ID + protocol ID
       0x00 0x0B           - (H unsigned short 2) length of following bytes
       0x01                - (c- char 1) unit ID
       0x03                - (c )function code (read holding registers)
       0x08                - (c) bytes count (=4x2*Byte)
       0x00 0xF8 0x01 0x97 0x00 0x69 0x82 0xCB - response data
          0x00 0xF8 = 248    = 24.8°C - (h - short 2)(temperature)
          0x01 0x97 = 407    = 40.7%RH (relative humidity)
          0x00 0x69 = 105    = 10.5°C (dew point)
          0x82 0xCB = -32053 = Error 53 (n/a)
    '''
    
finally:
    sock.close()
