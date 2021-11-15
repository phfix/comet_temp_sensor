import sqlite3
from sqlite3 import Error
from comet_temp_sensor import Sensor
import socket
from time import sleep
from F250 import  F250
import threading
import datetime
import schedule
import time

max_timeout=60

# extract time exakt data

# select strftime('%Y-%m-%d %H:%M:%f' ,timestamp), name, valuef from temperature_readings;


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print("Sqlite3 version:",sqlite3.version)
        thread=threading.current_thread()
        print(f"{thread.name} Open database file {db_file} ")
    except Error as e:
        print(e)
    finally:
        pass

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)
        raise


def open_db(database_path):
    #database = "C:/Users/Dammdata/Documents/temperature_cal.db"
    # C:\Users\Dammdata\Documents\LSDATA
    database= database_path

    sql_create_temperarure_table = """ CREATE TABLE IF NOT EXISTS temperature_readings (
                                        id integer PRIMARY KEY,
                                        timestamp DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                                        name text NOT NULL,
                                        -- value integer,
                                        -- value32 integer,
                                         valuef float,
                                         errorcode integer
                                        
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_temperarure_table)

    else:
        print("Error! cannot create the database connection.")

    return conn


def create_temperature_reading(conn, args):
    """
    Create a new project into the temperatur_readings table
    :param conn:
    :param temperatur_readings:
    :return: temperatur_readings id
    """
    sql = ''' INSERT INTO temperature_readings(name, valuef, errorcode)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    #cur.execute(sql, [name,value, value32, valuef, errorcode])
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid

def measure_temp_inner(keep_running,filename_manager,sensors,delta_time):
    current_file_name=filename_manager.get_filename()
    try:
        sensors.open()
    except socket.error as e:
        print("Sensor communication error -open: ", e)
        return
    except socket.timeout as e:
        print("Sensor timeout error: ", e)
        return
    except Exception as e:
        print("Exception",e)
   
    read_data=True
    db = open_db(current_file_name)
    while read_data and keep_running():
        try:
            r = sensors.getSelectedData([0, 1,2,3])
        except socket.error as e:
            print("Sensor communication error get data: ", e)
            read_data=False
            break
        except socket.timeout as e:
            print("Sensor timeout error: ", e)
            read_data=False
            break
        except Exception as e:
            print("Exception",e)
            read_data=False
            break

        else:
            for d in r:
                #print("temp reading error:", sensors.get_error_message(d["errorcode"]))
                create_temperature_reading(
                    db, [d["name"], d["valuef"], d["errorcode"]])
                if d["errorcode"] != 0:
                    print(f'{d["name"] } ** ERROR ** {d["errorcode"]}' )
                else:
                    print(f'{d["name"]} {d["valuef"]:.3f}')
            new_filename=filename_manager.wait_for_new_filename(current_file_name,delta_time)
            if new_filename is not None:
                #db.close()?
                db = open_db(new_filename)
                current_file_name=new_filename
    db.close()
    sensors.close()

def measure_temp(keep_running,filename_manager,sensors,delta_time):
    while keep_running():
        try:
            measure_temp_inner(keep_running,filename_manager,sensors,delta_time)
        except Exception as e:
            print("Exception:",e)
        finally:
            print("Wait before retry..")
            time.sleep(10)
            print("Retry")
        
    thread=threading.current_thread()
    print(f"Exit thread: {thread.name}")


def measure_ref_temp(keep_running,file_name_manager,delta_time):
    current_file_name= file_name_manager.get_filename()
    db=open_db(current_file_name)
  

      
    
    device= F250("COM8") # Input! COMX where X is integer. May occassionally need to be changed to successfully connect. Previous values: COM3, COM4, COM8.
    device.connect()
    device.setup(keep_running)
    #print("Start processs f250")
    while keep_running():
        # new database?
        new_filename=file_name_manager.wait_for_new_filename(current_file_name,delta_time)
        if new_filename is not None:
            #db.close()
            db=open_db(new_filename)
            current_file_name=new_filename
        #print("read response f250")
        d=device.read_response(max_timeout,keep_running)
        if d is not None:
            create_temperature_reading(db, [d["name"], d["valuef"], d["errorcode"]])
        else:
            print("F250 no data")
        #print(r) #printout
    device.disconnect()
    db.close()
    thread=threading.current_thread()
    print(f"Exit thread: {thread.name}")


def measure_dummy(keep_running,file_name_manager):
    current_file_name= file_name_manager.get_filename()
    db=open_db(current_file_name)
  

    def save_temp(d):
        create_temperature_reading(db, [d["name"], d["valuef"], d["errorcode"]])
        
    
  
    while keep_running():
        # new database?
        new_filename=file_name_manager.is_new_filename(current_file_name)
        if new_filename is not None:
            db.close()
            db=open_db(new_filename)
            current_file_name=new_filename
        d= {"name": "dummy", "valuef":123.4, "errorcode":0}
        save_temp(d)
        time.sleep(2)
   
    db.close()
    thread=threading.current_thread()
    print(f"Exit thread: {thread.name}")


def measure_dummy2(keep_running,filename_manager,sensors,delta_time):
    current_file_name=filename_manager.get_filename()
    db = open_db(current_file_name)
    while keep_running():
        d= {"name": "dummy2", "valuef":123.4, "errorcode":0}
        create_temperature_reading(
                    db, [d["name"], d["valuef"], d["errorcode"]])

        new_filename=filename_manager.wait_for_new_filename(current_file_name,delta_time)
        if new_filename is not None:
            db = open_db(new_filename)
            current_file_name=new_filename
    db.close()
    thread=threading.current_thread()
    print(f"Exit thread: {thread.name}")


class FileNameManager():
    def __init__(self):
        self.cond=cond = threading.Condition()
    
    def create_new_filename(self):
        ts= datetime.datetime.now()
        return f"C:/Users/Dammdata/Documents/tempkalibrering/temperature_{ts.year:4d}{ts.month:02d}{ts.day:02d}_{ ts.hour:02d}{ts.minute:02d}{ts.second:02d}.db"
        #return f"C:/Users/Dammdata/Documents/8_slot_data/temperatur/temperature_{ts.year:4d}{ts.month:02d}{ts.day:02d}_{ ts.hour:02d}{ts.minute:02d}{ts.second:02d}.db"
        #return f"temperature_{ts.year:4d}{ts.month:02d}{ts.day:02d}_{ ts.hour:02d}{ts.minute:02d}{ts.second:02d}.db"

    def set_new_filename(self,name):
        self.cond.acquire()
        self.filename=name
        self.cond.notify_all()
        self.cond.release()

    def get_filename(self):
        self.cond.acquire()
        filename=self.filename
        self.cond.release()
        return filename

    def is_new_filename(self,old_filename):
            """ check if new filename
                returns None if not new filename
            Args:
                old_filename (string): the current file name used by the thread
                
            """
            def test():
                return old_filename!=self.filename
            new_filename=None
            self.cond.acquire()
            is_new_filename=test()
            if is_new_filename:
                new_filename=self.filename
            self.cond.release()
            return new_filename
            
    def wait_for_new_filename(self,old_filename,timeout):
        """ wait for an updated filenam. Returns None if timeout

        Args:
            old_filename (string): the current file name used by the thread
            timeout (float): timeout time in seconds
        """
        def test():
            return old_filename!=self.filename
        new_filename=None
        self.cond.acquire()
        is_new_filename=self.cond.wait_for(test,timeout)
        if is_new_filename:
            new_filename=self.filename
        self.cond.release()
        return new_filename

    
def make_database(file_name_manager):
    file_name=file_name_manager.create_new_filename()
    db= open_db(file_name)
    db.close()
    file_name_manager.set_new_filename(file_name)


if __name__ == '__main__':
    # maka a new database if it it a new day...
    file_name_manager=FileNameManager()
    make_database(file_name_manager)
    keep_running_flag=True

    def keep_running():
        return keep_running_flag
   
    threadlist=[]
    # prepare one thread for each device
    t=threading.Thread( target=measure_ref_temp, args=[keep_running,file_name_manager,2], name="FK250")
#    t1=threading.Thread( target=measure_dummy, args=[keep_running,file_name_manager], name="dummy FK250")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    t=threading.Thread(target=measure_temp, args=[keep_running,file_name_manager,Sensor('192.168.25.22', ["Slot1T", "Slot1B", "Slot2T", "Slot2B"]),10], name="W0741_20280027")
    #t2=threading.Thread(target=measure_dummy2, args=[keep_running,file_name_manager,Sensor('192.168.0.49', ["S0", "S1", "S2", "S3"]),2], name="w741.49")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    t=threading.Thread(target=measure_temp, args=[keep_running,file_name_manager,Sensor('192.168.25.20', ["Slot3T", "Slot3B", "Slot4T", "Slot4B"]),10], name="W0741_20280028")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    t=threading.Thread(target=measure_temp, args=[keep_running,file_name_manager,Sensor('192.168.25.21', ["Slot5T", "Slot5B", "Slot6T", "Slot6B"]),10], name="W0741_20280029")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    t=threading.Thread(target=measure_temp, args=[keep_running,file_name_manager,Sensor('192.168.25.23', ["Slot7T", "Slot7B", "Slot8T", "Slot8B"]),10], name="W0741_21280122")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    t=threading.Thread(target=measure_temp, args=[keep_running,file_name_manager,Sensor('192.168.25.24', ["Slot9T", "Slot9B", "Temp1", "Temp2"]),10], name="W0741_21280123")
    t.daemon=True # Stop this thread if main exits
    threadlist.append(t)

    # start the threads
    for x in threadlist:
        x.start()

    def new_database():
        make_database(file_name_manager)

    # use main thread to trigg new databases
    #schedule.every().day.at("00:00").do(new_database)
    schedule.every().day.at("06:00").do(new_database)
    #schedule.every().day.at("12:00").do(new_database)
    schedule.every().day.at("18:00").do(new_database)
    #schedule.every(60).minutes.do(new_database)
    try:
        while True:
            delay = schedule.idle_seconds()
            if delay is None:
                break
            elif delay>0:
                time.sleep(delay)
            schedule.run_pending()
            
    except KeyboardInterrupt:
        print ("keyboard interupt")
    except Exception as e: 
        print("Exception:", e)
    finally:
        print(f"Stopping threads (wait {max_timeout+1} seconds to allow all threads to exit")
        keep_running_flag=False
        #time.sleep(max_timeout+1)
        for x in threadlist:
            x.join()

    print("Program exit")
    exit()



    #measure_temp(5)
