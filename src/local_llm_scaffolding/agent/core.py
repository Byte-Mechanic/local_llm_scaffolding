# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Holds the state, owned objects, and orchestrates an agent instance.

This module is inteded to hold, and spawn everything an agent instance needs,
and hold its state within instances of its 'owned' objects as well as within
itself.

Usage:
    >>> with LlamaManager(config) as llama_server:
    >>>     shared_interfaces = SharedInterfaces(llama_server, config)
    >>>     agent = Agent(shared_interfaces, model = 'model')
    >>>     while True:
    >>>         agent.turn(input('--> '))

"""

import json
import logging
from ..tools.handler import Tools
from ..llama.interface import LlamaInterface, GenerationResult
from ..context.manager import ContextManager
from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')
print(__name__)


class Agent:
    """A single LLM Agent"""

    def __init__(self, shared_interfaces, model: str = '') -> None:
        """Initialize the agent instance.

        Initializes the agent instance, and collects all other interfaces it 
        needs.

        Args:
            shared_interfaces:
                Shared interfaces (containing the global LlamaInterface, and 
                ConfigManager)
            model:
                The model string to send to the LlamaInterface in order to
                request the response from a certain model alias.
        """
        self.model: str = model
        self.config_manager: ConfigManager = shared_interfaces.config_manager
        self.llama_interface: LlamaInterface = shared_interfaces.llama_interface
        self.context_manager: ContextManager = ContextManager(self.llama_interface)
        self.tools: Tools = Tools(self.llama_interface, self.context_manager)
        self.llama_interface.default_model = model

    def handle_tools(self, tools: list[dict]) -> None:
        """Handles tool execution.

        Handles tool execution if it is detected in the turn, will loop until
        all tools are called and adds the results to the context via the linked
        ContextManager

        Args:
            tools:
                a list of dicts directly pulled from the model's response.
        """
        for tool in tools:
            print(f'\tCalling [{tool["function"]["name"]}]\n'
                  f'\t\tWith Args: [{tool["function"]["arguments"]}]...')
            tool_result: dict = self.tools.execute_tool(tool)
            self.context_manager.add_tool_msg(tool, tool_result['result'])
            print(f'\t\t\tRESULT:'
                  f'\n\t\t\t[{json.dumps(tool_result, indent=4)}]')

    def turn(self, msg):
        """Orchestrates the agent's turn.

        Orchestrates the agents turn in the conversation, detects tools in the 
        response, calls the handler on them, runs another generation, and keeps 
        looping until the model does not output any more tool calls. in each 
        loop, the generation response is sent to be added into the context via
        the ContextManager.

        Args:
            msg:
                The message sent by the user.
        """
        self.context_manager.add_user_msg(msg)
        response = self.generate_local()
        while response['tools']:
            self.context_manager.add_assistant_msg(response)
            print(f'\nASSISTANT:\n{response["response"]}')
            self.handle_tools(response['tools'])
            response = self.generate_local()
        self.context_manager.add_assistant_msg(response)
        print(f'\nASSISTANT:\n{response["response"]}')

    def generate_local(self) -> GenerationResult:
        """Generates a single response

        Sets the model if not already set (based on auto-detected aliases),
        generates the response, handles any generation failures it can handle,
        and returns a GenerationResult object.

        Returns:
            A TypedDict with the keys:
                role: 
                    The direct role value from the llama-server response
                response:
                    The direct response value from the llama-server response
                reasoning:
                    The direct reasoning_content value from the llama-server 
                    response
                finish_reason:
                    The direct finish_reason value from the llama-server 
                    response, unless the server returns an error for context
                    length, then the value is 'length' to match the same
                    corresponding finish_reason.
                stats:
                    The direct usage dict from the llama-server response.
                status:
                    Explicitly indicates a successful or failed generation.
                tools:
                    The available tools schema/definitions built and passed by
                    the Tools object.
        """
        logger.info(f'Sending message context:\n'
                    f'{json.dumps(self.context_manager.working_context, indent=4)}')
        if self.model:
            mod = self.model
        else:
            mod = self.llama_interface.models[1]
        generation = self.llama_interface.chat_completions(
                model=mod,
                context=self.context_manager.working_context,
                tools=self.tools.tool_definitions if self.tools else None)
        if 'length' in generation['finish_reason']:
            self.context_manager.compact_context()
            return self.generate_local()
        else:
            logger.info(f'Returning Generation Result:\n{json.dumps(generation, indent=4)}')
            return generation        
