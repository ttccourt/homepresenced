import subprocess
import datetime
import yaml
import dweepy
from time import sleep

CONFIG_FILE_PATH = '/etc/homepresenced/homepresenced.yaml'



class Occupant:
        def __init__(self, name, mac):
                self.name = name
                self.mac = mac
                self.lastPresent = None

        def registerPresence(self):
                self.lastPresent = datetime.datetime.now()



with open(CONFIG_FILE_PATH) as f:
        # load configuration into conf dictionary
        conf = yaml.safe_load(f)

        # replace yaml-style occupant listings with instances of Occupant object
        for i, occupant in enumerate(conf['occupants']):
                conf['occupants'][i] = Occupant(occupant['name'], occupant['mac'])



try:
        while True:
                occupancy_report = {}  # data sent to dweepy about occupant presence

                # perform network scan. this takes time so it's more efficient to do it once per loop, rather than once per occupant per loop
                arp_scan = str(subprocess.check_output("sudo arp-scan -l", shell=True))

                for occupant in conf['occupants']:
                        if occupant.mac in arp_scan:
                                occupant.registerPresence()  # register occupant as CURRENTLY present if mac is in scan

                        # should the occupant be MARKED as present (taking into account the 'grace period')?
                        presence = datetime.datetime.now() - occupant.lastPresent < datetime.timedelta(minutes=conf['presence_grace_period']) if occupant.lastPresent else None

                        # format time of last CURRENT presence. if not set (==None) then use "never"
                        lastPresent = occupant.lastPresent.strftime(conf['time_format']) if occupant.lastPresent else "never"

                        print(f"Occupant {occupant.name}'s device is {'PRESENT' if presence else 'ABSENT' if presence == False else 'UNSEEN'} (last present: {lastPresent})")

                        # add to dictionary that will be sent to dweepy
                        occupancy_report[occupant.name] = {
                                'presence': presence,
                                'lastPresent': lastPresent
                        }

                dweepy.dweet_for(conf['dweet_thing'], occupancy_report)



# catch keyboard ctrl+c interrupt signals and exit cleanly
except KeyboardInterrupt:
        exit()
