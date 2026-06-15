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

def turn(main_agent: Agent, msg: str) -> None:
    """Manages the flow of a chat turn."""

    logger.info(f'USER INPUT: "{msg}"')
    main_agent.add_user_msg(msg)
    response = main_agent.generate_local()
    #  Loop on tool calls.
    if response['tools']:
        # Loops over tool calls. Needed for back-to-back tool calling, handling
        # all tool calls until the agent no longer needs tools.
        while response['tools']:
            main_agent.add_assistant_msg(response)
            print(f'ASSISTANT:\n{response["response"]}')
            # Loops over all tool calls in the response, needed in the case of
            # parallel tool calls
            for tool in response['tools']:
                print(f'\tCalling [{tool["function"]["name"]}] \n\t\twith '
                      f'args: [{tool["function"]["arguments"]}]...')
                tool_result = main_agent.tools.execute_tool(tool)
                main_agent.add_tool_msg(tool, tool_result['result'])
                logger.info(f'Tool Result:\n{json.dumps(tool_result, indent=4)}')
                print(f'\t\tResult:\n\t\t{str(tool_result["result"])[:50]}...')
            response = main_agent.generate_local()
    #  Print assistant message, add response to context.
    print(f'ASSISTANT:\n{response["response"]}')
    main_agent.add_assistant_msg(response)

def run():
    #  Clear Screen.
    print('\x1B[2J'.encode('utf-8').decode('unicode-escape'))
    #  Start context manager loop
    #  Starts server, defines main agent, starts main chat loop.
    config = ConfigManager()
    with LlamaManager(config) as llama_server: 
        shared_interfaces = SharedInterfaces(llama_server, config)
        main_agent = Agent(
                shared_interfaces,
                model = 'default_thinking')
        while True:
            turn(main_agent, input('--> '))

