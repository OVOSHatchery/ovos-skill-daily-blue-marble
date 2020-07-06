from adapt.intent import IntentBuilder
from os.path import dirname, join
import requests
from tempfile import gettempdir
from mycroft import MycroftSkill, intent_file_handler, intent_handler
from requests_cache import CachedSession
import random
import time
from datetime import datetime, timedelta
from mycroft.skills.core import resting_screen_handler
from lingua_franca.format import nice_date
import tempfile
from os.path import join, exists
from PIL import Image
from io import BytesIO
from mycroft.util import create_daemon


class DailyBlueMarbleSkill(MycroftSkill):

    def initialize(self):
        self.session = CachedSession(backend='memory',
                                     expire_after=timedelta(hours=3))
        self.add_event('skill-blue-marble.jarbasskills.home',
                       self.handle_homescreen)
        create_daemon(self.update_picture) # cache for speedup

    # homescreen
    def handle_homescreen(self, message):
        self.gui.show_url("http://epic.gsfc.nasa.gov/",
                          override_idle=True)

    # idle screen
    def _create_gif(self):
        urls = []

        for picture in self.settings["raw_data"]:
            url = "https://epic.gsfc.nasa.gov/epic-archive/jpg/" + \
                  picture["image"] + ".jpg"
            urls.append(url)

        urls.reverse()

        # once a day only
        path = join(tempfile.gettempdir(), str(datetime.now().date()) + ".gif")
        if not exists(path):
            images = []
            for url in urls:
                response = self.session.get(url)
                img = Image.open(BytesIO(response.content))
                images.append(img)
            images[0].save(path,
                           save_all=True, append_images=images[1:],
                           optimize=True, loop=0)

        return path

    def update_picture(self):
        try:
            url = "https://epic.gsfc.nasa.gov/api/natural"

            self.settings["raw_data"] = self.session.get(url).json()

        except Exception as e:
            self.log.exception(e)

        response = self.settings["raw_data"][-1]

        url = "https://epic.gsfc.nasa.gov/epic-archive/jpg/" + response["image"] + ".jpg"
        self.gui['imgLink'] = self.settings['imgLink'] = url

        for k in response:
            if k in ['identifier', 'version', 'image']:
                continue
            self.settings[k] = response[k]
            self.gui[k] = response[k]
        self.settings["spoken_date"] = self.gui["spoken_date"] = \
            nice_date(datetime.today(), lang=self.lang)
        self.gui['title'] = response['date']
        self.settings["animation"] = self.gui["animation"] = self._create_gif()
        self.set_context("BlueMarble")
        return self.gui['imgLink']

    @resting_screen_handler("BlueMarble")
    def idle(self, message):
        self.update_picture()
        self.gui.show_animated_image(self.gui["animation"],
                                     fill='PreserveAspectFit')

    # intents
    @intent_file_handler("epic_website.intent")
    def handle_website_epic_intent(self, message):
        self.handle_homescreen(message)

    @intent_file_handler("about.intent")
    def handle_about_epic_intent(self, message):
        epic = join(dirname(__file__), "ui", "images", "epic.jpg")
        self.gui.show_image(epic, override_idle=True, fill='PreserveAspectFit')
        self.speak_dialog("aboutEPIC")

    @intent_file_handler("location.intent")
    def handle_location_epic_intent(self, message):
        image = random.choice(["L1.jpeg","distance.jpg" ])
        epic = join(dirname(__file__), "ui", "images", image)
        self.gui.show_image(epic, override_idle=True, fill='PreserveAspectFit')
        self.speak_dialog("location")

    @intent_file_handler("earth_from_space.intent")
    def handle_epic_intent(self, message):
        self.update_picture()
        self.speak_dialog("EPIC", {"date": self.settings["spoken_date"]})
        self.gui.show_image(self.settings["imgLink"],
                            override_idle=True,
                            title=self.settings["date"],
                            caption=self.settings["caption"],
                            fill='PreserveAspectFit')

    @intent_handler(IntentBuilder("AnimateBlueMarbleIntent")
                    .require("animate").optionally("picture")
                    .require("BlueMarble"))
    def handle_animate(self, message):
        self.speak_dialog("animation")
        self.idle(message)


def create_skill():
    return DailyBlueMarbleSkill()

