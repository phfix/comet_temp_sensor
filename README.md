# comet_temp_sensor


This Python package is designed to collect data from the Wi-Fi device W0741 from Comet Systems (https://www.cometsystem.com/) and store it in SQLite3 database files.

It also collects data from an F250 Mk II reference temperature device connected via a serial port.

The code is provided as-is without any warranties.

# Usage:

## create venv

```bash
py -m venv venv
```

## Activate the virtual environment

```bash
.\venv\Scripts\activate
```

## Install required Python packages
```bash
pip install -r reqirements.txt
```


## Configure Database Creation Schedule

In the `main.py` file, you can configure when new database files are created by editing the scheduling section. The relevant code snippet is:

```python
# Schedule database creation
# schedule.every().day.at("00:00").do(new_database)  # Midnight
schedule.every().day.at("06:00").do(new_database)  # 6:00 AM
# schedule.every().day.at("12:00").do(new_database)  # Noon
schedule.every().day.at("18:00").do(new_database)  # 6:00 PM
# schedule.every(60).minutes.do(new_database)       # Every 60 minutes
```
### What to Edit:
1. Time of Day: Uncomment or modify the lines to set the desired times for database creation (e.g., "00:00" for midnight, "12:00" for noon).
2. Frequency: You can also schedule database creation at regular intervals, such as every 60 minutes, by uncommenting the relevant line.
This allows you to control how often new database files are created to suit your data collection needs. 

## Connect the Comet device
Ensure you have network access to the device and know the ip address or dns name.
For more information about the devices, refer to the official documentation of Comet Systems.

# Configure Threads for Your Devices

In the `main.py` file, you need to configure the threads to match your specific devices. This is done in the section where threads are created for each device. The relevant code snippet is:

```python
threadlist = []
# Prepare one thread for each device
t = threading.Thread(target=measure_ref_temp, args=[keep_running, file_name_manager, 2], name="FK250")
t.daemon = True  # Stop this thread if the main program exits
threadlist.append(t)

t = threading.Thread(target=measure_temp, args=[keep_running, file_name_manager, Sensor('192.168.25.22', ["Slot1T", "Slot1B", "Slot2T", "Slot2B"]), 10], name="W0741_20280027")
t.daemon = True
threadlist.append(t)

t = threading.Thread(target=measure_temp, args=[keep_running, file_name_manager, Sensor('192.168.25.20', ["Slot3T", "Slot3B", "Slot4T", "Slot4B"]), 10], name="W0741_20280028")
t.daemon = True
threadlist.append(t)

t = threading.Thread(target=measure_temp, args=[keep_running, file_name_manager, Sensor('192.168.25.21', ["Slot5T", "Slot5B", "Slot6T", "Slot6B"]), 10], name="W0741_20280029")
t.daemon = True
threadlist.append(t)

t = threading.Thread(target=measure_temp, args=[keep_running, file_name_manager, Sensor('192.168.25.23', ["Slot7T", "Slot7B", "Slot8T", "Slot8B"]), 10], name="W0741_21280122")
t.daemon = True
threadlist.append(t)

t = threading.Thread(target=measure_temp, args=[keep_running, file_name_manager, Sensor('192.168.25.24', ["Slot9T", "Slot9B", "Temp1", "Temp2"]), 10], name="W0741_21280123")
t.daemon = True
threadlist.append(t)
```

### What to Edit:
1. IP Addresses: Replace the IP addresses (e.g., '192.168.25.22') with the IP addresses of your devices.
Sensor Slots: Update the slot names (e.g., ["Slot1T", "Slot1B", "Slot2T", "Slot2B"]) to match the configuration of your sensors.
2. Thread Names: Modify the thread names (e.g., "W0741_20280027") to reflect the identifiers of your devices.
3. Reference Device: If you are using a reference temperature device (e.g., FK250), ensure the measure_ref_temp thread is configured correctly.

### Why This is Important:
Each thread corresponds to a specific device and its configuration. By editing this section, you ensure that the program communicates with the correct devices and collects data from the appropriate sensors.

If you add or remove devices, you must update this section to reflect the changes.
