

import pytest
import socket
from comet_temp_sensor import Sensor

def test_read_sensor():
    s = Sensor('192.168.3.1',["Top1","Bot1","Top2","Bot2"])
    ok=False
    try:
        s.open()
        # Read inf
        snr=s.getSerialNumber()
        r= s.getSelectedData([0,1,2,3])
        ok=True

    except  socket.error as e:
        print("Sensor communication error: ",e, s.ip)
    else:
        pass
    finally:
        s.close()

    assert ok
