# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import logging
from subprocess import run
from time import time


class TR_SysCommandPlugin(octoprint.plugin.SettingsPlugin,
                          octoprint.plugin.TemplatePlugin,
                          octoprint.plugin.SimpleApiPlugin,
                          octoprint.plugin.RestartNeedingPlugin):

    def __init__(self):
        self.logger = logging.getLogger("octoprint.plugins.TR_SysCommand")
        return

    def get_template_configs(self):
        return [
            # We bind to the settings to allow us to show a settings page to the user
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            over_command="exit 0",
            under_command="exit 0",
            either_command="exit 0"
        )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            TR_SysCommand=dict(
                displayName="Tr_syscommand Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="AlexVerrico",
                repo="Octoprint-TR_SysCommand",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/AlexVerrico/Octoprint-TR_SysCommand/archive/{target_version}.zip"
            )
        )

    #########################
    # SimpleApiPlugin Mixin #
    #########################
    # Function to return a list of commands that we accept through the POST endpoint of the API for this plugin
    def get_api_commands(self):
        return dict(
            run_over_command=[],
            run_under_command=[],
            run_either_command=[]
        )

    # Function for OctoPrint to call when a request is sent to the POST endpoint of the API for this plugin
    def on_api_command(self, command, data, heater_id='T', current_temp='50.0', set_temp='25.0'):
        # If the command sent to the API is 'run_command'
        if command == 'run_over_command':
            with open('{basefolder}/over_temp_output.log'.format(basefolder=self.get_plugin_data_folder()), 'a') as f:
                cmd = str(self._settings.get(['over_command']))
                if '{heater_id}' in cmd:
                    cmd = cmd.replace('{heater_id}', heater_id)
                if '{current_temp}' in cmd:
                    cmd = cmd.replace('{current_temp}', str(current_temp))
                if '{set_temp}' in cmd:
                    cmd = cmd.replace('{set_temp}', str(set_temp))

                f.write('#######################################################################{t}:\n{d}\n\n\n\n'
                        .format(t=time(),
                                d=run(cmd, shell=True, capture_output=True)
                                .stdout
                                .decode()
                                )
                        )
            return '', 200

        if command == 'run_under_command':
            cmd = str(self._settings.get(['under_command']))
            if '{heater_id}' in cmd:
                cmd = cmd.replace('{heater_id}', heater_id)
            if '{current_temp}' in cmd:
                cmd = cmd.replace('{current_temp}', str(current_temp))
            if '{set_temp}' in cmd:
                cmd = cmd.replace('{set_temp}', str(set_temp))
            with open('{basefolder}/under_temp_output.log'.format(basefolder=self.get_plugin_data_folder()), 'a') as f:
                f.write('#######################################################################{t}:\n{d}\n\n\n\n'
                        .format(t=time(),
                                d=run(cmd, shell=True, capture_output=True)
                                .stdout
                                .decode()
                                )
                        )
            return '', 200

        if command == 'run_either_command':
            cmd = str(self._settings.get(['either_command']))
            if '{heater_id}' in cmd:
                cmd = cmd.replace('{heater_id}', heater_id)
            if '{current_temp}' in cmd:
                cmd = cmd.replace('{current_temp}', str(current_temp))
            if '{set_temp}' in cmd:
                cmd = cmd.replace('{set_temp}', str(set_temp))
            with open('{basefolder}/either_output.log'.format(basefolder=self.get_plugin_data_folder()), 'a') as f:
                f.write('#######################################################################{t}:\n{d}\n\n\n\n'
                        .format(t=time(),
                                d=run(cmd, shell=True, capture_output=True)
                                .stdout
                                .decode()
                                )
                        )
            return '', 200
        return 'unknown command', 400

    ####################
    # Custom functions #
    ####################

    def over_temp_runaway(self, heater_id, set_temp, current_temp):
        self.logger.critical("Over temp thermal runaway detected on heater {h}. Set temp {s}, current temp {c}"
                             .format(h=heater_id, s=set_temp, c=current_temp))
        self.on_api_command('run_over_command', {}, heater_id=heater_id, set_temp=set_temp, current_temp=current_temp)
        return

    def under_temp_runaway(self, heater_id, set_temp, current_temp):
        self.logger.critical("under temp thermal runaway detected on heater {h}. Set temp {s}, current temp {c}"
                             .format(h=heater_id, s=set_temp, c=current_temp))
        self.on_api_command('run_under_command', {}, heater_id=heater_id, set_temp=set_temp, current_temp=current_temp)
        return

    def runaway(self, heater_id, set_temp, current_temp):
        self.logger.critical("Thermal runaway detected on heater {h}. Set temp {s}, current temp {c}"
                             .format(h=heater_id, s=set_temp, c=current_temp))
        self.on_api_command('run_either_command', {}, heater_id=heater_id, set_temp=set_temp, current_temp=current_temp)
        return


__plugin_pythoncompat__ = ">=3.5,<4"  # only python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = TR_SysCommandPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.plugin.ThermalRunaway.over_runaway_triggered": __plugin_implementation__.over_temp_runaway,
        "octoprint.plugin.ThermalRunaway.under_runaway_triggered": __plugin_implementation__.under_temp_runaway,
        "octoprint.plugin.ThermalRunaway.runaway_triggered": __plugin_implementation__.runaway
    }
