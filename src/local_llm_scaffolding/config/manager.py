# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Manages the program configuration.

This module loads configs, creates configs when not present, and exposes them
so other modules can access what they need.

Usage:
    >>> config = ConfigManager()
    >>> # Access config:
    >>> ip = config.server_ip
"""

import json
import pathlib

file_path: pathlib.Path = pathlib.Path(__file__).resolve().parent
pkg_root: pathlib.Path = file_path.parent

class ConfigManager:
    """Handles the program's configuration"""

    def __init__(self) -> None:
        """Initializes a configuration.

        Initializes a configuration instance. only one should exist in the
        whole program.
        """
        self.config_file: pathlib.Path = file_path.joinpath('cfg.json')
        if self.config_file.is_file() == False:
            with open(self.config_file, 'w') as doc:
                default_data = {
                        'general': {
                            'logger_config': str(file_path.joinpath(
                                'agent/logger_config.json')),
                            'user': 'Name Here'
                            },
                        'server': {
                            'ip': '0.0.0.0',
                            'port': '8080',
                            'exec': str(pkg_root.joinpath(
                                'llama/llama.cpp.sh')),
                            'args': ['--models-preset', 
                                     str(pkg_root.joinpath(
                                         'llama/models/config.ini')),
                                     '--models-max', '1',
                                     '-ngl', '99', 
                                     '-ctk', 'q8_0', 
                                     '-ctv', 'q8_0', 
                                     '-np', '1',
                                     ]
                            },
                        'agent': {
                            'system_prompt': str(file_path.joinpath(
                                'agent/system_prompt.md')),
                            'memory_file': str(file_path.joinpath(
                                'agent/memory.md'))
                            },
                        'context': {
                            'placeholder': None
                            }
                        }
                doc.write(json.dumps(default_data))
        with open(self.config_file, 'r') as config_file:
            self.load_config(json.loads(config_file.read()))
    def load_config(self, config_file):
        """Loads the program's configuration from what was initialized.

        Args:
            config_file:
                The configuration data loaded either from a file or from
                defaults in the initialization.
        """
        ## General
        general_config: dict = config_file['general']
        self.general_logger_config: pathlib.Path = general_config['logger_config']
        self.general_user: str = general_config['user']
        ## Server
        server_config: dict = config_file['server']
        self.server_ip: str = server_config['ip']
        self.server_port: str = server_config['port']
        self.server_exec: pathlib.Path = server_config['exec']
        self.server_args: list = server_config['args']
        ##Agent
        agent_config: dict = config_file['agent']
        self.agent_system_prompt: pathlib.Path = agent_config['system_prompt']
        self.agent_memory_file: pathlib.Path = agent_config['memory_file']
        ##Context
        ##WIP
                
