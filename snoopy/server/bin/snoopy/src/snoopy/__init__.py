"""Main snoopy package."""

# Logging configuration
import logging
#logging.basicConfig(level=logging.DEBUG)
#log = logging.getLogger(name='snoopy')

import os
import sys
from collections import OrderedDict
from ConfigParser import ConfigParser


SRCDIR = os.path.dirname(__file__)


class PluginRegistry(object):
    """Handles the loading and management of plug-ins.
        Plug-ins register in this registry by importing an instance of this
        class and decorating a callable with the `add()` method. Plug-ins are
        loaded from the directory specified in the `pluginsdir` variable. Once
        loaded, plug-ins are stored in the `self.plugins` dictionary.

        When loaded, the `self.plugins` dictionary has the following layout:

            self.plugins[groupname][plugin] = options

        where `groupname` is the group name specified as the first parameter to
        `add()`, `plugin` is the plug-in callable decorated with `add()` and
        `options` is a dictionary of the plug-in's name and title and any other
        keyword arguments to `add()`."""

    pluginsdir = 'plugins'
    """The directory from where plug-ins are loaded, relative to this file."""

    def __init__(self):
        self.plugins = {}

    def add(self, group, name, title, **options):
        """Decorator used by plug-ins to register with this registry.
            :param group: Name of the group that the decorated plug-in belongs
                to. This is the key under `self.plugins` that the plug-in is
                stored.
            :param name: The plug-in's internal (JSON-friendly) name.
            :param title: The plug-in's external (display-friendly) name.
            :param options: All keyword arguments (and name and title) are
                stored as plug-in options."""
        options.update(dict(name=name, title=title))
        if group not in self.plugins:
            self.plugins[group] = OrderedDict()
        def plugin_decorator(plugin):
            logging.debug('Registering plug-in: %r', plugin)
            self.plugins[group][plugin] = options
            return plugin
        return plugin_decorator

    def collect(self):
        """Collect plug-ins from the `plugins` directory."""
        for fname in os.listdir(os.path.join(SRCDIR, self.pluginsdir)):
            parts = fname.split(os.extsep)
            if parts[-1] != 'py' or fname.startswith('__') or len(parts) != 2:
                continue # Not a valid Python file to import
            __import__('snoopy.%s.%s' % (self.pluginsdir, parts[0]))

pluginregistry = PluginRegistry()


class Config(object):
    def __init__(self):
        self._parser = ConfigParser()
        # Prevent the parser from changing the case of option names:
        self._parser.optionxform = str

    def __getitem__(self, secname):
        if secname not in self._parser.sections():
            return {}
        section = self._parser._sections[secname].copy()
        if '__name__' in section:
            del section['__name__']
        return section

    def from_file(self, fname):
        self._parser.read(fname)
        self._post_load()
        logging.debug('configuration loaded from %r', fname)
        return self._parser._sections

    def from_sysargv(self):
        if len(sys.argv) > 1:
            return self.from_file(sys.argv[1])

    def _post_load(self):
        parser = self._parser
        for section in parser.sections():
            for key in parser.options(section):
                val = parser.get(section, key)
                if val.lower() in ('true', 'false'):
                    parser.set(section, key, val.lower() == 'true')

config = Config()
