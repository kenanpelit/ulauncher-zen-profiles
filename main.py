"""
Zen Browser Profile Selector Extension for Ulauncher
Author: Kenan Pelit <kenanpelit@gmail.com>
Version: 1.0.0
License: MIT
"""

import os
import logging
import subprocess
import configparser
from typing import List, Optional

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.cache/ulauncher_zen_profiles.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ZenProfileExtension(Extension):
    """Main extension class for Zen Profile Selector"""
    
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        logger.info("Zen Profile Extension initialized")

class KeywordQueryEventListener(EventListener):
    """Handles the keyword query events"""
    
    def __init__(self):
        super().__init__()
        self.profiles: List[str] = []
        logger.debug("KeywordQueryEventListener initialized")

    def get_profiles(self, config_folder: str) -> List[str]:
        """
        Read and parse profiles from profiles.ini
        
        Args:
            config_folder: Path to the Zen configuration folder
            
        Returns:
            List of profile names
        """
        try:
            config_folder = os.path.expanduser(config_folder)
            profiles_ini = os.path.join(config_folder, 'profiles.ini')
            logger.debug(f"Reading profiles from: {profiles_ini}")

            if not os.path.exists(profiles_ini):
                logger.error(f"profiles.ini not found at: {profiles_ini}")
                return []

            config = configparser.ConfigParser()
            config.read(profiles_ini)

            profiles = []
            for section in config.sections():
                if section.startswith('Profile') and 'Name' in config[section]:
                    profile_name = config[section]['Name']
                    profiles.append(profile_name)
                    logger.debug(f"Found profile: {profile_name}")

            logger.info(f"Total profiles found: {len(profiles)}")
            return profiles

        except Exception as e:
            logger.exception("Error reading profiles:")
            return []

    def on_event(self, event: KeywordQueryEvent, extension: Extension) -> RenderResultListAction:
        """
        Handle the keyword query event
        
        Args:
            event: The keyword query event
            extension: The extension instance
            
        Returns:
            Action to render the result list
        """
        try:
            # Get and filter profiles
            query = event.get_argument() or ""
            if not self.profiles:
                config_folder = extension.preferences['zen_folder']
                self.profiles = self.get_profiles(config_folder)

            filtered_profiles = self.profiles
            if query:
                query = query.strip().lower()
                filtered_profiles = [p for p in self.profiles if query in p.lower()]
                logger.debug(f"Filtered profiles for '{query}': {filtered_profiles}")

            # Create result items
            items = []
            for profile in filtered_profiles:
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=profile,
                    description=f"Launch Zen with {profile} profile",
                    on_enter=ExtensionCustomAction(profile)
                ))

            # Add default item if no profiles found
            if not items:
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name='No profiles found',
                    description='Check your Zen profiles folder path',
                    on_enter=ExtensionCustomAction('')
                ))

            return RenderResultListAction(items)

        except Exception as e:
            logger.exception("Error handling query event:")
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Error occurred',
                    description=str(e),
                    on_enter=ExtensionCustomAction('')
                )
            ])

class ItemEnterEventListener(EventListener):
    """Handles the item enter events"""

    def on_event(self, event: ItemEnterEvent, extension: Extension) -> None:
        """
        Handle the item enter event
        
        Args:
            event: The item enter event
            extension: The extension instance
        """
        try:
            profile = event.get_data()
            if not profile:  # Skip if no profile selected
                return

            cmd = extension.preferences['zen_cmd']
            logger.info(f"Launching Zen with profile: {profile}")
            subprocess.Popen(
                [cmd, '-p', profile],
                start_new_session=True
            )

        except Exception as e:
            logger.exception("Error launching Zen:")

if __name__ == '__main__':
    try:
        logger.info("Starting Zen Profile Extension")
        ZenProfileExtension().run()
    except Exception as e:
        logger.exception("Failed to start extension")

