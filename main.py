import os
import re
import subprocess
import configparser
import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

# Logging ayarları
logging.basicConfig(filename='~/.cache/ulauncher_zen_profiles.log',
                   level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class ZenProfileExtension(Extension):
    def __init__(self):
        super(ZenProfileExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

class KeywordQueryEventListener(EventListener):
    def __init__(self):
        super(KeywordQueryEventListener, self).__init__()
        self.profiles = []

    def get_profiles(self, config_folder):
        try:
            logging.debug(f"Reading profiles from: {config_folder}")
            config = configparser.ConfigParser()
            profiles_ini = os.path.join(config_folder, 'profiles.ini')
            logging.debug(f"Profiles.ini path: {profiles_ini}")
            
            if not os.path.exists(profiles_ini):
                logging.error(f"profiles.ini not found at {profiles_ini}")
                return []
                
            config.read(profiles_ini)
            logging.debug(f"Sections in profiles.ini: {config.sections()}")
            
            regex = r'^Profile.*$'
            profiles = []
            for p in config.sections():
                if 'Name' in config[p] and re.search(regex, p, re.IGNORECASE):
                    profile_name = config[p]['Name']
                    logging.debug(f"Found profile: {profile_name}")
                    profiles.append(profile_name)
            
            return profiles
        except Exception as e:
            logging.error(f"Error reading profiles: {str(e)}")
            return []

    def on_event(self, event, extension):
        try:
            query = event.get_argument()
            logging.debug(f"Query received: {query}")
            
            if not query or len(self.profiles) == 0:
                config_folder = os.path.expanduser(extension.preferences['zen_folder'])
                logging.debug(f"Config folder: {config_folder}")
                self.profiles = self.get_profiles(config_folder)
                logging.debug(f"Found profiles: {self.profiles}")
            
            profiles = self.profiles.copy()
            if query:
                query = query.strip().lower()
                profiles = [p for p in profiles if query in p.lower()]
                logging.debug(f"Filtered profiles: {profiles}")

            entries = []
            for profile in profiles:
                entries.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=profile,
                    description=f"Launch Zen with {profile} profile",
                    on_enter=ExtensionCustomAction(profile, keep_app_open=False)
                ))
            
            if not entries:
                entries.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name='No profiles found',
                    description='Make sure your profiles.ini path is correct',
                    on_enter=ExtensionCustomAction('', keep_app_open=False)
                ))
            
            return RenderResultListAction(entries)
            
        except Exception as e:
            logging.error(f"Error in on_event: {str(e)}")
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Error occurred',
                    description=str(e),
                    on_enter=ExtensionCustomAction('', keep_app_open=False)
                )
            ])

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        try:
            profile = event.get_data()
            cmd = extension.preferences['zen_cmd']
            logging.debug(f"Launching Zen with profile: {profile}")
            logging.debug(f"Command: {cmd} -p {profile}")
            subprocess.Popen([cmd, '-p', profile], start_new_session=True)
        except Exception as e:
            logging.error(f"Error launching Zen: {str(e)}")

if __name__ == '__main__':
    ZenProfileExtension().run()

