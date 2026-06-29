# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Handles all tool related tasks for the agent.

This module handles the loading of tool plugins upon initialization, preparing 
tool instructions to be sent to the context manager, and tool calling.

Usage:
    >>> tools = Tools(llama_interface,
    ...               context_manager)
    >>> tools.execute_tool(<TOOL_JSON_FROM_MODEL_OUTPUT>)
"""

from ..context.manager import ContextManager
from ..llama.interface import LlamaInterface

import pathlib
import json
import logging
import importlib

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

tool_path = pathlib.Path(__file__).resolve().parent #Add to ConfigManager

class Tools:
    def __init__(self, llama_interface, context_manager):
        # Interfaces
        if not isinstance(llama_interface, LlamaInterface):
            raise TypeError('Passed "llama_interface" is not of type '
                            '"LlamaInterface"')
        if not isinstance(context_manager, ContextManager):
            raise TypeError('Passed "context_manager" is not of type '
                            '"ContextManager"')
        self.interfaces = {'llama':llama_interface,
                           'context':context_manager}
        # Init vars for tools loaded below.
        self.tool_definitions: list = []
        self.funct_map: dict = {}
        self.system_prompt_injections: list = []
        self.ignore_files: list = ['__pycache__', '__init__.py', 'handler.py', 
                                   'utils.py', 'tool_log.log']
        for tool_dir in (tool_path.iterdir()):
            logger.info('Checking "{tool_dir}" for tools...')
            tool_name = tool_dir.name
            if tool_name in self.ignore_files:
                continue
            # Check for tool file
            try:
                tool_module = self._load_tool_modules(tool_name)
                logger.info(f'"{tool_name}" found.')
            except ModuleNotFoundError:
                logger.warning(f'Cannot load "{tool_name}" module.\n'
                               f'Reason: Module {tool_name} does not exist.')
                continue
            except Exception as e:
                logger.warning(f'Cannot load "{tool_name}" module.\n'
                               f'Reason: Unexpected exception occured:\n'
                               f'{e}')
                continue
            # Check for run()
            try:
                if not callable(tool_module.run):
                    raise AttributeError
                self.funct_map[tool_name] = tool_module.run
                logger.info(f'"{tool_name}.run" found. Added to funct_map.')
            except AttributeError:
                logger.warning(f'Cannot load "{tool_name}" module.\n'
                               f'Reason: Module {tool_name} has no callable '
                               f'attribute "run".')
            # Check definition.json
            try:
                definition_path = tool_dir.joinpath('definition.json')
                with open(definition_path, 'r') as doc:
                    self.tool_definitions.append(json.load(doc))
                    logger.info(f'"{tool_name}" Definitions Loaded!')
            except FileNotFoundError:
                logger.warning(f'Cannot load "{tool_name}" module.\n'
                               f'Reason: "definition.json" not found in tool '
                               f'directory.')
                if tool_name in self.funct_map:
                    del self.funct_map[tool_name]
                logger.warning(f'"{tool_name}.run" Removed from funct_map')
                continue
            except json.decoder.JSONDecodeError:
                logger.warning(f'Cannot load "{tool_name}" module.\n'
                               f'Reason: "definition.json" cannot be decoded by'
                               f' json lib.')
                if tool_name in self.funct_map:
                    del self.funct_map[tool_name]
                logger.warning(f'"{tool_name}.run" Removed from funct_map')
                continue
            # Check system_prompt_injection.md
            try: 
                sys_inject_path = tool_dir.joinpath('system_prompt_injection.md')
                with open(sys_inject_path, 'r') as doc:
                    self.system_prompt_injections.append(doc.read())
            except FileNotFoundError:
                logger.debug(f'"system_prompt_injection.md" not found in the'
                             f' tool path. This file is recommended, but not'
                             f' required.')
        self.send_instructions_to_context_mgr()

    def _load_tool_modules(self, int_name: str):
        module = importlib.import_module(f".{int_name}.tool", package=__package__)
        return module

    def send_instructions_to_context_mgr(self) -> None:
        if not isinstance(self.system_prompt_injections, list):
            raise TypeError
        if len(self.system_prompt_injections) >= 1:
            self.interfaces['context'].tool_instructions = (
                    self.system_prompt_injections)
        self.interfaces['context'].build_sys_prompt()

    def execute_tool(self, tool: dict):
        ## Validate input
        tool_shape = {'type', 'function','id'}
        funct_shape = {'name', 'arguments'}
        if not isinstance(tool, dict):
            logger.critical(f'Tool call is not of ecpected type "dict":\n{
                            json.dumps(tool, indent=4)}')
            raise ValueError
        if not tool_shape.issubset(tool.keys()):
            logger.critical(f'Tool schema not matching expected input.\n'
                            f'{json.dumps(tool, indent=4)}')
            raise KeyError
        if not funct_shape.issubset(tool['function'].keys()):
            logger.critical(f'Tool schema not matching expected input.\n'
                            f'{json.dumps(tool, indent=4)}')
            raise KeyError
        tool_result = {}
        funct_name: str = tool['function']['name']
        try:
            funct_args = json.loads(tool['function']['arguments'])
        except json.decoder.JSONDecodeError as e:
            raw_tool_result = (f'Your arguments could not be parsed by the '
                               f'JSON decoder.\nYour previous tool call: '
                               f'{tool}\nThe error: {e}\nCorrect your call and'
                               f' try again.')
            logger.error(f'Arguments could not be parsed by'
                         f' JSON decoder. \nError: {e}')
            return {'funct_name': 'ERROR',
                    'funct_args': 'ERROR',
                    'result': raw_tool_result}
        raw_tool_result = self.funct_map[funct_name](self.interfaces, 
                                                     **funct_args)
        tool_result = {'funct_name': funct_name,
                       'funct_args': funct_args,
                       'result': raw_tool_result}
        logger.info(f'Returning Tool Result:\n{json.dumps(tool_result, 
                    indent=4)}')
        return tool_result

