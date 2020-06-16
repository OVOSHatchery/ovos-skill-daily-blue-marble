from adapt.intent import IntentBuilder
from os.path import dirname, join
import requests
from tempfile import gettempdir
from mycroft import MycroftSkill, intent_file_handler, intent_handler
import requests
import random
from datetime import datetime, timedelta
from mycroft.skills.core import resting_screen_handler
from lingua_franca.format import nice_date


class EPICSkill(MycroftSkill):

    def initialize(self):
        self.add_event('skill-nasa-epic.jarbasskills.home',
                       self.handle_homescreen)

    # homescreen
    def handle_homescreen(self, message):
        self.gui.show_url("http://epic.gsfc.nasa.gov/",
                          override_idle=True)

    # idle screen
    def update_picture(self):
        try:
            today = datetime.now().replace(hour=12, second=0, minute=0,
                                           microsecond=0)
            if not self.settings.get("ts"):
                self.settings["ts"] = (today - timedelta(days=1)).timestamp()
            if today.timestamp() != self.settings["ts"] or\
                    not self.settings.get('imgLink'):
                url = "https://epic.gsfc.nasa.gov/api/natural"

                self.settings["raw_data"] = requests.get(url).json()
                self.settings["ts"] = today.timestamp()

        except Exception as e:
            self.log.exception(e)

        response = random.choice(self.settings["raw_data"])

        url = "https://epic.gsfc.nasa.gov/epic-archive/jpg/" + response["image"] + ".jpg"
        self.gui['imgLink'] = self.settings['imgLink'] = url

        for k in response:
            if k in ['identifier', 'version', 'image']:
                continue
            self.settings[k] = response[k]
            self.gui[k] = response[k]
        date = datetime.strptime(self.settings["date"],
                                 '%Y-%m-%d %H:%M:%S')
        self.settings["spoken_date"] = self.settings["gui"] = nice_date(date,
                                                                     lang=self.lang)
        self.gui['title'] = response['date']

    @resting_screen_handler("E.P.I.C")
    def idle(self, message):
        self.update_picture()
        self.gui.show_image(self.settings["imgLink"],
                            fill='PreserveAspectFit')

    # intents
    @intent_file_handler("epic_website.intent")
    def handle_website_epic_intent(self, message):
        self.handle_homescreen(message)

    @intent_file_handler("about.intent")
    def handle_about_epic_intent(self, message):
        # TODO better picture
        epic = join(dirname(__file__), "ui", "images", "epic.png")
        self.gui.show_image(epic, override_idle=True, fill='PreserveAspectFit')
        self.speak_dialog("aboutEPIC")

    @intent_file_handler("earth_from_space.intent")
    def handle_epic_intent(self, message):
        # TODO picture selection
        self.update_picture()
        self.speak_dialog("EPIC", {"date": self.settings["spoken_date"]})
        self.gui.show_image(self.settings["imgLink"],
                            override_idle=True,
                            title=self.settings["date"],
                            caption=self.settings["caption"],
                            fill='PreserveAspectFit')


def create_skill():
    return EPICSkill()

