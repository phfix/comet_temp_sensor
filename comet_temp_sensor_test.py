import socket
from comet_temp_sensor import Sensor

s = Sensor('192.168.3.1',["Top1","Bot1","Top2","Bot2"])

try:
    s.open()
    # Read inf
    snr=s.getSerialNumber()
    print("Serial", snr)
   
    r= s.getSelectedData([0,1,2,3])
    print(r)

"""
    # More examples
    print("int:",s.getInt(0x9C40))
    print("int32:",s.getInt32(0x9C68))
    print("float", s.getFloat(0x9C78 ))
    r=s.getReadings(0)
    r=s.getReadings(1)
    r=s.getReadings(2)
    r=s.getReadings(3)
    print(r)
""""

except  socket.error as e:
    print("Sensor communication error: ",e, s.ip)
else:
    pass
finally:
    s.close()

