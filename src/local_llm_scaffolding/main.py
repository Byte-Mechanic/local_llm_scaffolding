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

config: ConfigManager = ConfigManager()

user: str = config.general_user
sys_prompt_path: pathlib.Path = file_path.joinpath(config.agent_system_prompt)
sys_memory_path: pathlib.Path = file_path.joinpath(config.agent_memory_file)


def turn(main_agent: Agent, context: ContextManager, msg: str) -> None:
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
    print(f'[{context.ctx_tokens_used}]')

def run():
    #  Clear Screen.
    print('\x1B[2J'.encode('utf-8').decode('unicode-escape'))
    #  Start context manager loop
    #  Starts server, defines main agent, starts main chat loop.
    with LlamaManager(config) as llama_server: 
        llama = LlamaInterface(config, llama_server)
        context = ContextManager(llama)
        tools = Tools(llama, context)
        #  Load Memory Document
        with open(sys_memory_path, 'r') as doc:
            system_memory: str = doc.read()

        #  Load System Prompt and make the necessary substitutions, injecting
        #  the memory document, current date, and the user name.
        with open(sys_prompt_path, 'r') as doc:
            system_prompt: str = doc.read()
            cur_date: str = datetime.datetime.strftime(datetime.datetime.now(), 
                                                  '%A %B %d, %Y. %I:%M %p')
            system_prompt = system_prompt.replace('$DATE', cur_date)
            system_prompt = system_prompt.replace('$MEMORY', system_memory)
            system_prompt = system_prompt.replace('$USER', user)
            tool_instruct_buffer = ''
            for instruct in tools.system_prompt_injections:
                tool_instruct_buffer += f'\n{instruct}'
            system_prompt = system_prompt.replace('$TOOLS', tool_instruct_buffer)

        main_agent = Agent(
                system_prompt = system_prompt,
                model = 'Local',
                tool_handler = tools,
                llama_interface=llama,
                context_manager = context)
        while True:
            turn(main_agent, context, input('--> '))

