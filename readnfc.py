import sys
import os
import time
import nfc
import requests
import uuid

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import appsettings  # you shouldn't need to edit this file
import usersettings  # this is the file you might need to edit

# this function gets called when a NFC tag is detected
def touched(tag):
    global sonosroom_local

    if tag.ndef:
        for record in tag.ndef.records:
            try:
                receivedtext = record.text
            except:
                print("Error reading a *TEXT* tag from NFC.")
                return True

            receivedtext_lower = receivedtext.lower()

            print("")
            print("Read from NFC tag: " + receivedtext)

            servicetype = ""
            sonosinstruction = ""

            # check if a full HTTP URL read from NFC
            if receivedtext_lower.startswith('http'):
                servicetype = "completeurl"
                sonosinstruction = receivedtext

            # determine which music service read from NFC
            if receivedtext_lower.startswith('spotify'):
                servicetype = "spotify"
                sonosinstruction = "spotify/now/" + receivedtext

            if receivedtext_lower.startswith('tunein'):
                servicetype = "tunein"
                sonosinstruction = receivedtext

            if receivedtext_lower.startswith('favorite'):
                servicetype = "favorite"
                sonosinstruction = receivedtext

            if receivedtext_lower.startswith('amazonmusic:'):
                servicetype = "amazonmusic"
                sonosinstruction = "amazonmusic/now/" + receivedtext[12:]

            if receivedtext_lower.startswith('apple:'):
                servicetype = "applemusic"
                sonosinstruction = "applemusic/now/" + receivedtext[6:]

            if receivedtext_lower.startswith('applemusic:'):
                servicetype = "applemusic"
                sonosinstruction = "applemusic/now/" + receivedtext[11:]

            if receivedtext_lower.startswith('bbcsounds:'):
                servicetype = "bbcsounds"
                sonosinstruction = 'bbcsounds/play/' + receivedtext[10:]

            # check if a Sonos "command" or room change read from NFC
            if receivedtext_lower.startswith('command'):
                servicetype = "command"
                sonosinstruction = receivedtext[8:]

            if receivedtext_lower.startswith('room'):
                servicetype = "room"
                sonosroom_local = receivedtext[5:]
                print("Sonos room changed to " + sonosroom_local)
                return True

            # if no service or command detected, exit
            if servicetype == "":
                print("Service type not recognised. NFC tag text should begin spotify, tunein, amazonmusic, apple/applemusic, command or room.")
                if usersettings.sendanonymoususagestatistics == "yes":
                    r = requests.post(appsettings.usagestatsurl, data={'time': time.time(), 'value1': appsettings.appversion, 'value2': hex(uuid.getnode()), 'value3': 'invalid service type sent'})
                return True

            print("Detected " + servicetype + " service request")

            # build the URL we want to request
            if servicetype.lower() == 'completeurl':
                urltoget = sonosinstruction
            else:
                urltoget = usersettings.sonoshttpaddress + "/" + sonosroom_local + "/" + sonosinstruction

            # check Sonos API is responding
            try:
                r = requests.get(usersettings.sonoshttpaddress)
                r.raise_for_status()
            except requests.RequestException as e:
                print("Failed to connect to Sonos API at " + usersettings.sonoshttpaddress + ": " + str(e))
                return True

            # clear the queue for every service request type except commands
            if servicetype != "command":
                try:
                    print("Clearing Sonos queue")
                    r = requests.get(usersettings.sonoshttpaddress + "/" + sonosroom_local + "/clearqueue")
                    r.raise_for_status()
                except requests.RequestException as e:
                    print("Failed to clear Sonos queue: " + str(e))
                    return True

            # use the request function to get the URL built previously, triggering the Sonos
            try:
                print("Fetching URL via HTTP: " + urltoget)
                r = requests.get(urltoget)
                r.raise_for_status()
            except requests.RequestException as e:
                print("Error fetching URL via HTTP: " + str(e))
                return True

            print("Sonos API reports " + r.json().get('status', 'unknown status'))

            # put together log data and send (if given permission)
            if usersettings.sendanonymoususagestatistics == "yes":
                logdata = {
                    'time': time.time(),
                    'value1': appsettings.appversion,
                    'value2': hex(uuid.getnode()),
                    'actiontype': 'nfcread',
                    'value3': receivedtext,
                    'servicetype': servicetype,
                    'urltoget': urltoget
                }
                r = requests.post(appsettings.usagestatsurl, data=logdata)

    else:
        print("")
        print("NFC reader could not read tag. This can be because the reader didn't get a clear read of the card. If the issue persists then this is usually because (a) the tag is encoded (b) you are trying to use a mifare classic card, which is not supported or (c) you have tried to add data to the card which is not in text format. Please check the data on the card using NFC Tools on Windows or Mac.")
        if usersettings.sendanonymoususagestatistics == "yes":
            r = requests.post(appsettings.usagestatsurl, data={'time': time.time(), 'value1': appsettings.appversion, 'value2': hex(uuid.getnode()), 'value3': 'nfcreaderror'})

    return True

print("")
print("")
print("Loading and checking readnfc")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("")
print("SCRIPT")
print("You are running version " + appsettings.appversion + "...")

print("")
print("NFC READER")
print("Connecting to NFC reader...")
try:
    reader = nfc.ContactlessFrontend(usersettings.nfc_reader_path)
except IOError as e:
    print("... could not connect to reader")
    print("")
    print("You should check that the reader is working by running the following command at the command line:")
    print(">  python -m nfcpy")
    print("")
    print("If this reports that the reader is in use by readnfc or otherwise crashes out then make sure that you don't already have readnfc running in the background via pm2. You can do this by running:")
    print(">  pm2 status             (this will show you whether it is running)")
    print(">  pm2 stop readnfc       (this will allow you to stop it so you can run the script manually)")
    print("")
    print("If you want to remove readnfc from running at startup then you can do it with:")
    print(">  pm2 delete readnfc")
    print(">  pm2 save")
    print(">  sudo reboot")
    print("")
    sys.exit()

print("... and connected to " + str(reader))

print("")
print("SONOS API")
sonosroom_local = usersettings.sonosroom
print("API address set to " + usersettings.sonoshttpaddress)
print("Sonos room set to " + sonosroom_local)

print("Trying to connect to API ...")
try:
    r = requests.get(usersettings.sonoshttpaddress)
    r.raise_for_status()
    print("... and API responding")
except requests.RequestException as e:
    print("... but API did not respond: " + str(e) + ". This could be a temporary error so I won't quit, but carry on to see if it fixes itself")

print("")
print("OK, all ready! Present an NFC tag.")
print("")

if usersettings.sendanonymoususagestatistics == "yes":
    r = requests.post(appsettings.usagestatsurl, data={'time': time.time(), 'value1': appsettings.appversion, 'value2': hex(uuid.getnode()), 'value3': 'appstart'})

while True:
    reader.connect(rdwr={'on-connect': touched, 'beep-on-connect': False})
    time.sleep(0.1)