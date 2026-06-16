# al-Agent-Scaffolding
# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

from .agent.core import Agent
from .tools.handler import Tools
from .llama.interface import LlamaInterface
from .config.manager import ConfigManager
from .llama.manager import LlamaManager
from .context.manager import ContextManager
import logging
import datetime
import pathlib
import json

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

file_path: pathlib.Path = pathlib.Path(__file__).resolve().parent

class SharedInterfaces:
    def __init__(self, llama_manager, config_manager):
        self.config_manager: ConfigManager = config_manager
        self.llama_interface: LlamaInterface = LlamaInterface(self.config_manager,
                                                              llama_manager)

def run():
    #  Clear Screen.
    print('\x1B[2J'.encode('utf-8').decode('unicode-escape'))
    
    config = ConfigManager()
    with LlamaManager(config) as llama_server: 
        shared_interfaces = SharedInterfaces(llama_server, config)
        main_agent = Agent(
                shared_interfaces,
                model = 'default_thinking')
        while True:
            main_agent.turn(input('--> '))

