#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Player Plugin for Enigma2
Main plugin entry point and initialization
"""

from Plugins.Plugin import PluginDescriptor
from . import __version__, __description__


def main(session, **kwargs):
    """Main plugin entry point"""
    from .ui.main_screen import SubtitlePlayerMainScreen
    session.open(SubtitlePlayerMainScreen)


def Plugins(**kwargs):
    """Plugin descriptor for Enigma2"""
    return [
        PluginDescriptor(
            name="Subtitle Player",
            description=__description__,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="subtitle_icon.png",
            fnc=main
        ),
        PluginDescriptor(
            name="Subtitle Player",
            description=__description__,
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main
        )
    ]