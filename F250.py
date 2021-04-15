import serial
import re
import time

#The F250 operates with a range of 4-wire Pt100 (100 Ohm), Pt25.5 (25.5 Ohm) and Pt10 (10 Ohm)
#Platinum Resistance Thermometers (PRT) to provide temperature measurement in °C, °F, K (Kelvin) plus
#resistance in Ohms.

expects= [
    (r"(?P<input>[ABD])\s*E.\s*(?P<error>\d?)","error"),
    (r"(?P<status>[PRUZ])(?P<code>\d)","status"),
    (r"(?P<input>[ABD])(?P<sign>-*)\s*(?P<value>\d*\.\d+)(?P<unit>[KCFR])(?P<channel>\d\d)*","temp")
]

class F250:
    def __init__(self, port):
        self.portname = port
        self.current_output=""
        self.display=False
        self.re_strings=[]
        for e in expects:
            self.re_strings.append(e[0])

    def connect(self,portname=None):
        """
            As supplied by the factory, unless requested otherwise, the RS232C interface is configured as follows:
            19,200 Baud
            8 Character bits
            No Parity
            2 Stop Bits
        """
        if portname is not None:
            self.portname=portname
        self.port=serial.Serial(port=self.portname, baudrate=19200, timeout=10,parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS)
        pass


    def send_command(self,command):
        """ All commansds must be delimited with a line feed character (ASCII 0AH), that is the last character of a
            command string sent to the F250 must be the line feed (LF) character. 
            Following is a list of the commands that can be sent to the F250: all are single letters which may be
            followed by up to 2 single digit parameters, with the exception of the switchbox commands which have 2
            alphabetical characters followed by 2 digits. 
        """
        self.port.write((command+"\n").encode("utf8"))
        
    def send_command_expect_response(self,command,responses):

        self.send_command(command)

        response=self.expect()
        #while True:
        #    index,re= response
        #    if index<0:
        #        break 
        #    _,response_type= expects[index]
        #    if response_type in response:
        #        return response
        #    response=self.expect()


    def receive(self):
        """ All data returned is terminated with a carriage return/line (CR LF) feed sequence
            A standard reading returned form PRT input A or B is 11 characters long, e.g. ‘A962.000C\r\n’, where ‘\r’
            represents a carriage return and ‘\n’ a line feed. When reading Ohms in high resolution, the reading will
            be 12 characters long, e.g. ‘A200.1234R\r\n’.
            When the ‘M’ command is used to return a reading with the switchbox channel number, the complete
            reading will be 13 characters long for a standard reading, or 14 characters long when reading Ohms in
            high resolution, e.g. ‘A962.000C00\r\n’, ‘A200.1234R01\r\n’. When the ‘M’ command is used to return the
            switchbox channel number and differential mode is selected (A-B), the reading will indicate both A and B
            channel numbers, e.g. ‘D100.345C0015’ where ‘D’ is differential mode, ‘100.345’ is the temperature
            difference in degrees Celsius, ‘00’ is the channel selected on switchbox A and ‘15’ is the channel selected
            on switchbox B. 
        """
        
        return self.port.read_until() #expected=LF

    def expect( self, timeout=60 ):
            current_buffer_output = self.current_output
            # This function needs all regular expressions to be in the form of a
            # list, so if the user provided a string, let's convert it to a 1
            # item list.
            if not isinstance(self.re_strings, list):
                return (-1,"Not valid list of expects")
            if len(self.re_strings) == 0:
                return (-1,"Not valid list of expects")
                
            # to avoid looping in recv_ready()
            base_time = time.time()
            # Loop until one of the expressions is matched or loop forever if
            # nothing is expected (usually used for exit)
            wait=True
            match=None
            re_index=-1
            while wait:
                # check current buffer conted
                for re_index,re_string in enumerate(self.re_strings):
                    match=re.search( re_string,str(current_buffer_output), re.MULTILINE) #re.DOTALL
                    if match:
                        wait=False
                        break

                if not wait:
                    break
            
                current_buffer=""
                # avoids paramiko hang when recv is not ready yet
                while time.time() < (base_time + timeout):
                    # Read some of the output
                    current_buffer =  self.port.read_until().decode('utf8')
                    if "\n" in current_buffer:
                        break


                # If we have an empty buffer, then the SSH session has been closed
                if len(current_buffer) == 0:
                    break


                # Display the current buffer in realtime if requested to do so
                # (good for debugging purposes)
                if self.display:
                    print("Received:",current_buffer)


                # Add the currently read buffer to the output
                self.current_output += current_buffer
                current_buffer_output = self.current_output

            # Grab the first pattern that was matched
            if match is not None:
                startpos= match.regs[0][0]
                endpos= match.regs[0][1]
                found_pattern = self.current_output[startpos:endpos]
                # eat all data including match
                self.current_output =self.current_output[endpos:]

                return (re_index,found_pattern)

            return (-1,"Not expected")

    def read_response(self,timeout,store):
        read_more=True
        while read_more:
            index,match_string=self.expect()
            match_string=str(match_string)
            if index<0:
                #print("expect timout?",command)
               # response["Timeout"]=index
                return (-1,"Not expected")
            m,action=expects[index]
            #print("-->\n","RESPONSE", index, action, m, match_string)
            if action == "error":
                match=re.search(expects[index][0],match_string,re.MULTILINE)
                if match:
                    #response["input"]=str(match.group('input'))
                    #response["errorcode"]=str(match.group('code'))
                    print("Error received:",str(match.group('input')),int(match.group('errorcode')))
            if action == "status":
                match=re.search(expects[index][0],match_string,re.MULTILINE)
                if match:
                    #status=str(match.group('status'))
                    #response[status]=int(match.group('code'))
                    print("Status received:",str(match.group('status')),int(match.group('code')))
            if action == "temp":
                match=re.search(expects[index][0],match_string,re.MULTILINE)
                if match:
                    sign=1
                    reading=match.groupdict()
                    if "sign" in reading and reading["sign"]=="-":
                        sign=-1
                    temp=float(reading["value"])
                    temp*= sign
                    input= str(reading["input"])
                    print("Temp reading", input,temp)
                    #skip info about unit, and switchbox channels
                    d={}
                    d["name"]="FK250/" + input
                    d["valuef"]=temp
                    d["errorcode"]=""
                    store(d)
                

        return (-1,"Not expected")
                
        
    def setup(self):
        """
        An, where n = 0, 1, 2, 3 or 4
        Parameters: n = 0 selects PRT A
        n = 1 selects PRT B
        n = 2 selects PRT A - B (differential)
        n = 3 selects alternate mode (A then B)
        n = 4 cancels continuous output 

        Ma, where a = @, A,B,C,D,I,J,K or L
        Parameters a = @ cancels continuous output
        a = A sets PRT to A and sends data when reading available.
        a = B sets PRT to B and sends data when reading available.
        a = C sets PRT to A-B and sends data when reading available.
        a = D sets PRT alternately to A then B and sends data when reading available.
        a = I sets PRT to A and sends data with channel number when reading available.
        a = J sets PRT to B and sends data with channel number when reading available.
        a = K sets PRT to A-B and sends data with channel number when reading available.
        a = L sets PRT alternately to A then B and sends data with channel number when reading
        available
        """

        #verfiy contact
        self.send_command_expect_response("?Z",["status"])
        # cleare Z ?
        #self.send_command("Z") #Toggles the Z function. dont use
        
        # Send "R1"  for high resolution
        self.send_command("R1")
        # send data from A and B input (no switchbox channel)
        self.send_command("A3")
        # switchbox
        #self.send_command("SA00")
        #self.send_command("SB00")


    def error_code_decode(self,code):
        """10. Error Codes
        Error codes can be generated by the F250 for a variety of reasons as follows.
        Code Meaning / Cause
        E1 Balance error / No PRT, PRT open circuit / Ratio over range.
        E2 Temperature over range / PRT at temperature outside limits of conversion
        table.
        E3 No "A" ROM calibration/ No ROM calibration on selected Input or Channel
        E4 IEEE or RS232 error / Unrecognized instruction sent
        E5 IEEE or RS232 error / Illegal argument sent
        E6 RAM failure
        E7 Data validation error in CAL ROM “A” or “B” - PRT calibration invalid
        E8 Unable to track temperature change / temperature change too large
        E9 Conversion table too big (more than 395 points)/ Resistance range too great
        E10 Unable to create resistance/temperature conversion table.
        E11 Unable to create resistance/temperature conversion table. 
          Received: BE- 1  
        """
        pass



if __name__ == "__main__":
    device= F250("COM3")
    device.connect()
    device.setup()
    for x in range(100):
        r=device.expect()
        #print(r)