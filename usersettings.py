from config.config_manager import get_config

# Fetch the address for node-sonos-http-api from environment variables
sonoshttpaddress = get_config('NODE_SONOS_URL') or 'http://localhost:5005'

# Fetch the name of the Sonos room from environment variables
sonosroom = get_config('PLAYER_ROOM') or 'Garden'

# Send anonymous usage statistics
sendanonymoususagestatistics = "no"

# Fetch the NFC reader path from environment variables
#if you are getting erros saying your nfc reader can not be found do the following:
#type lsusb into a terminal on your raspberry pi and enter
#in the output, find your nfc reader and copy the hex code next to it
#(for example, the ACR122U it is 072f:2200)
#then replace "usb" with "usb:072f:2200"
#(or whatever lsusb outputted for your nfc reader)
nfc_reader_path = get_config('NFC_READER_PATH') or 'usb'