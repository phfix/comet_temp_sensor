from datetime import datetime

import socket
import struct

TCP_IP = '192.168.3.1'
TCP_PORT = 502


def bcdDigits(c):
    return ''.join("{:02x}".format(c))


def getaddr(ch, offset, size):
    return 0x9C40+offset+ch*size


def get_type_from_code(code):
    codes = {
        0x0001: "W0710",
        0x0002: "W0741",
        0x0003: "W3710",
        0x0004: "W3711",
        0x0005: "W3721",
        0x0007: "W7710",
        0x0008: "W4710",
        0x0009: "W5714",
        0x000B: "W0711"
    }
    if code in codes:
        return codes[code]
    return f"Type{code}"


def getErrorMessage(code):
    if code == 0:
        return "Ok"
    messages = {
        1: "A/D converter for measurement from Pt1000 probes is under lower limit. It is likely that temperature probe is shorted.",
        2: "A/D converter for measurement from Pt1000 probes is above high limit. It is likely that temperature probe is not connected, or cable is damaged.",
        3: "Measured value is outside expected range.",
        4: "The source value for computed value (dew point) is not available.",
        10: "Communication error with internal CO2 sensor.",
        11: "Measurement error from internal CO2 sensor. One of reasons for this error is an insufficient voltage from power source.",
        15: "Communication error with relative humidity sensor inside Digi probe. It is likely that relative humidity sensor is damaged.",
        16: "Measurement error from relative humidity sensor.",
        20: "Unable to read calibration constants from internal barometric pressure sensor.",
        21: "Measurement error at internal barometric pressure sensor.",
        30: "Communication error with internal A/D converter.",
        35: "Measured value from Digi probe is not available. It is likely that Digi probe is not connected.",
        36: "During Digi probe detection procedure was returned CRC error of memory for calibration data.",
        37: "Unknow type of Digi probe.",
        38: "Communication error with memory for calibration data inside Digi probe. It is likely that Digi probe is not connected properly, or probe is damaged.",
        39: "Memory for calibration data inside Digi probe have wrong CRC.",
        40: "Connected type of Digi probe is not same as was detected probe.",
        50: "Device configuration for channel is damaged.",
        52: "Measured value cannot be shown due to overflow during conversion.",
        53: "Value is not available. This error is shown at disabled channels or when value was not measured yet. CO2 concentration is available 15 sec after device start-up.",
        55: "This error is related to values transferred via Modbus TCP. It signalises overflow of Modbus register.",
    }
    if code in messages:
        return "E" + str(code) + ": " + messages[code]

    return "E" + str(code) + ": Unknown (May relate to error 35 or 53. " + messages[35] + messages[53] + ")"


class Sensor:
    def __init__(self, ip=TCP_IP, names=[]):
        self.ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.registers = {
            0x9C27:  "internal acoustic signalisation",
            0x9C28:  "optical LED signalisation",
            0x9C29:  "RSSI value",
            0x9C2A:  "configuration error",
            0x9C2B:  "system alarm - measurement error ",
            0x9C2C:  "low voltage of RTC battery"
        }
        self.names = names
        self.channelsstart = [0x9C40, 0x9C41, 0x9C42,
                              0x9C43, 0x9C44, 0x9C45, 0x9C46, 0x9C47]
        self.name = ip

    def set_device_name(self, name):
        self.name = name

    def open(self):
        self.sock.connect((self.ip, TCP_PORT))
        snr = self.getSerialNumber()
        typename= self.get_type_name()

        print("Serial", snr)
        self.set_device_name(f"{typename}_{snr}")

    def close(self):
        self.sock.close()

    def getName(self, channel):
        if channel < len(self.names):
            return self.name+"/"+str(channel)+"."+self.names[channel]
        else:
            return self.name+"/"+str(channel)

    def getSerialNumber(self):
        return bcdDigits(self.getInt(0x9c22))+bcdDigits(self.getInt(0x9c23))+bcdDigits(self.getInt(0x9c24)) + bcdDigits(self.getInt(0x9c25))

    def get_device_type(self):
        return self.getInt(0x9C26)

    def get_type_name(self):
        return get_type_from_code(self.get_device_type())

    def getStr(self, addr):
        c = self.getInt(addr)
        return ''.join("{:c}{:c}".format(c & 0xff, (c >> 8) & 0xff))

    def getInt(self, adress):
        l = 1
        req = struct.pack('>LHccHH', 0, 6, chr(1).encode(
            'ascii'), chr(3).encode('ascii'), adress, l)
        # send ModbusTCP request
        self.sock.send(req)
        # read ModbusTCP response
        rcv = self.sock.recv(64)
        # decode response
        out = struct.unpack(">IHccch", rcv)
        return out[5]

    def getInt32(self, adress):
        l = 2
        req = struct.pack('>LHccHH', 0, 6, chr(1).encode(
            'ascii'), chr(3).encode('ascii'), adress, l)
        # send ModbusTCP request
        self.sock.send(req)
        # read ModbusTCP response
        rcv = self.sock.recv(64)
        # decode response
        out = struct.unpack(">IHccci", rcv)
        return out[5]

    def getFloat(self, adress):
        l = 2
        req = struct.pack('>LHccHH', 0, 6, chr(1).encode(
            'ascii'), chr(3).encode('ascii'), adress, l)
        # send ModbusTCP request
        self.sock.send(req)
        # read ModbusTCP response
        rcv = self.sock.recv(64)
        # decode response
        original = bytearray(rcv[-4:])
        original[0::2], original[1::2] = original[1::2], original[0::2]
        return struct.unpack('<f', original)[0]

    def getErrorCode(self, value):
        r = value
        if r < -32000:
            return abs(r+32000)
        return 0

    def get_error_message(self,code):
        return getErrorMessage(code)
        
    def getReadings(self, ch):
        d = {}
        addr = self.channelsstart[ch]
        d["name"] = self.getName(ch)
        d["value"] = self.getInt(addr+0)
        d["alarm1"] = self.getInt(addr+8)
        d["alarm2"] = self.getInt(addr+16)
        d["unit"] = self.getStr(addr+24)
        d["decimals"] = self.getInt(addr+32)
        d["value32"] = self.getInt32(getaddr(ch, 40, 2))
        d["valuef"] = self.getFloat(getaddr(ch, 56, 2))
        d["min"] = self.getInt(addr+72)
        d["max"] = self.getInt(addr+80)
        d["error"] = self.getErrorCode(d["value"])
        return d

    def getSelectedData(self, channellist):
        result = []
        for ch in channellist:
            d = {}
            addr = self.channelsstart[ch]
            d["name"] = self.getName(ch)
            #
            # d["value32"]=self.getInt32(getaddr(ch,40,2))
            d["valuef"] = self.getFloat(getaddr(ch, 56, 2))
            d["value"] = self.getInt(addr+0)
            d["errorcode"] = self.getErrorCode(d["value"])
            # d["errormessage"]=getErrorMessage(d["errorcode"])
            result.append(d)
        return result
