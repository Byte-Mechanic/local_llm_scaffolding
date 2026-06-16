# al-Agent-Scaffolding
# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Program entry point.

This file is meant as the initial entry point of the program. The run()
function acts to start the program.

Usage:
    >>> cd <dir with pyproject.toml>
    >>> pip install -e . # -e installs as editable. Omit it if you do not intend to
    >>>                   # modify the source.
    >>>  #start program
    >>> llm-scaffolding
"""

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
    """A set of shared interfaces, where only one instance is needed."""

    def __init__(self, llama_manager, config_manager):
        """Initializes the shared interfaces."""
        self.config_manager: ConfigManager = config_manager
        self.llama_interface: LlamaInterface = LlamaInterface(self.config_manager,
                                                              llama_manager)

def run():
    """Starts the program

    Instantiates the llama-server process, the shared interfaces, and defines
    the main agent, then kicks off the chat loop.
    """
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

