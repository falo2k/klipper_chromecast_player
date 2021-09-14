# Depends on pychromecast 1.0.1 for Python 2 support.  https://github.com/home-assistant-libs/pychromecast/tree/1686e69103413d07b73dac9b8c03f82f7f12014f
# Chromecast Media Data reference: https://developers.google.com/cast/docs/reference/messages#MediaData
# Supported media types for Chromecast: https://developers.google.com/cast/docs/media
import logging
import pychromecast
from pychromecast import Chromecast
import socket

class ChromecastPlayer:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.mutex = self.printer.get_reactor().mutex()
        self.reactor = self.printer.get_reactor()
        # Re-add this when local file hosting is worked out
        # self.web_server_port = config.getint('web_server_port',default=1982)

        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.connect(("8.8.8.8",80))
        # self.web_server_host = s.getsockname()[0]

        # self.gcode.register_command(
        #         "CAST_LOCAL",
        #         self.cmd_CAST_LOCAL,
        #         desc=self.cmd_CAST_LOCAL_help)

        self.gcode.register_command(
                "CAST_LIST",
                self.cmd_CAST_LIST,
                desc=self.cmd_CAST_LIST_help)
        self.gcode.register_command(
                "CAST_HTTP",
                self.cmd_CAST_HTTP,
                desc=self.cmd_CAST_HTTP_help)



    cmd_CAST_LIST_help = "Utility Function: List chromecasts discoverable by Klipper"
    def cmd_CAST_LIST(self, params):
        self.gcode.respond_info("Looking for Chromecasts on network ...")
        chromecasts = pychromecast.get_chromecasts()
        self.gcode.respond_info("")
        self.gcode.respond_info("Discovered Chromecasts:")
        self.gcode.respond_info("-----------------------")
        for cast in chromecasts:
            self.gcode.respond_info("{0} ({1}:{2})".format(cast.device.friendly_name, cast.host, cast.port))

    cmd_CAST_HTTP_help = "Send a URL to a HTTP hosted file to play on a Chromecast"
    def cmd_CAST_HTTP(self, params):
        # URL: The url to play
        # Media Type: https://developers.google.com/cast/docs/media
        # DEVICE_NAME: The name of the Chromecast device
        # DEVICE_ADDRESS: HOST:PORT
        # TIMEOUT: WHEN TO CUT SHORT
        # CAN I SELECT A START AND END TIME?
        url = params.get('URL','')
        device_name = params.get('DEVICE_NAME','')
        device_address = params.get('DEVICE_ADDRESS','')

        if url == '':
            self.gcode.respond_info('No URL provided')
            return

        if device_name == '' and device_address == '':
            self.gcode.respond_info('Either a DEVICE_NAME or DEVICE_ADDRESS ' \
                'must be provided')
            return
        self.gcode.respond_info(device_address)
        if device_address == '':
            try:
                self.gcode.respond_info('Sending {0} to {1}'.format(url, device_name))
                chromecasts = pychromecast.get_chromecasts()
                cast = next(cc for cc in chromecasts if cc.device.friendly_name == device_name)

                cast.wait()
                mc = cast.media_controller
                mc.play_media(url, None)
                mc.block_until_active()
                mc.play()
                # Pause for a second to let the chromecast state catch up
                self.pause(1.0)
                # while mc.status.player_is_playing:
                #     self._pause(.05)
            except:
                self.gcode.respond_info('Could not reach chromecast')
        else:
            try:
                self.gcode.respond_info('Sending {0} to {1}'.format(url, device_address))
                host = device_address.split(':')[0]
                if len(device_address.split(':')) > 1:
                    port = int(device_address.split(':')[1])
                else:
                    port = 8009
                cast = Chromecast(host=host, port=port)
                cast.wait()
                mc = cast.media_controller
                mc.play_media(url, None)
                mc.block_until_active()
                mc.play()
                # Pause for a second to let the chromecast state catch up
                self._pause(1.0)
                # while mc.status.player_is_playing:
                #     self._pause(.05)
            except:
                self.gcode.respond_info('Could not reach chromecast')



    # To Be Revisited.  Need to set up an async http server for the file
    # cmd_CAST_LOCAL_help = "Cast a local file to a device"
    # def cmd_CAST_LOCAL(self, params):
    #     # FILE: The filename of the local file to host and play
    #     # DEVICE_NAME: The name of the Chromecast device
    #     # DEVICE_ADDRESS: HOST:PORT
    #     # TIMEOUT: WHEN TO CUT SHORT
    #     # CAN I SELECT A START AND END TIME?
    #     #chromecasts = pychromecast.get_chromecasts()
    #     #cast = next(cc for cc in chromecasts if cc.device.friendly_name == "Study Speakers")
    #     cast = Chromecast(host='192.168.1.115',port=8009)

    #     # chromecasts, browser = pychromecast.get_listed_chromecasts(['Study Speakers'])
    #     # #pychromecast.discovery.stop_discovery(browser)

    #     # cast = chromecasts[0]
    #     cast.wait()
    #     mc = cast.media_controller
    #     #mc.play_media('http://{0}:{1}/RuleBritannia.mp3'.format(self.web_server_host,self.web_server_port),'audio/mp3')
    #     mc.play_media('ftp://{0}:{1}/RuleBritannia.mp3'.format('192.168.1.2',21),'audio/mp3')
    #     mc.block_until_active()
    #     logging.debug("============Playback Starting")
    #     mc.play()
    #     # Pause for a second to let the chromecast state catch up
    #     self._pause(1.0)
    #     while mc.status.player_is_playing:
    #         self._pause(.05)
    #     logging.debug("============Playback completed")


    def _pause(self, time=0.):
        eventtime = self.reactor.monotonic()
        end  = eventtime + time
        while eventtime < end:
            eventtime = self.reactor.pause(eventtime + .05)


def load_config(config):
    return ChromecastPlayer(config)

