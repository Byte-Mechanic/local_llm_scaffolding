# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

from ..context.manager import ContextManager
from ..llama.interface import LlamaInterface

import pathlib
import json
import sys
import importlib.util
import logging
logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')


class Tools:
    def __init__(self, llama_interface, context_manager):
        
        # Interfaces
        self.interfaces = {'llama':llama_interface,
                           'context':context_manager}
        
        # Init vars for tools loaded below.
        self.tool_definitions: list = []
        self.funct_map: dict = {}
        self.system_prompt_injections: list = []

        self.ignore_files: list = ['__pycache__', '__init__.py', 'handler.py', 
                                   'utils.py', 'tool_log.log']
        for tool_dir in (pathlib.Path(__file__).parent.resolve().iterdir()): #Add to config
            logger.info('Checking "{tool_dir}" for tools...')
            tool_name = tool_dir.name
            if tool_name in self.ignore_files:
                continue
            try:
                tool_module = self._load_tool_modules(tool_name, 
                            tool_dir.joinpath('tool.py'))
                logger.info(f'"{tool_name}" Found!')
            except Exception as e:
                logger.warning(f'Cannot load "{tool_name}" module.')
                logger.warning(f'Load Failure Reason:\n{e}')
                continue
            try:
                self.funct_map[tool_name] = tool_module.run
                logger.info(f'"{tool_name}" Loaded Successfully!')
                definition_path = tool_dir.joinpath('definition.json')
                with open(definition_path, 'r') as doc:
                    self.tool_definitions.append(json.load(doc))
                    logger.info(f'"{tool_name}" Definitions Loaded!')
                sys_inject_path = tool_dir.joinpath('system_prompt_injection.md')
                with open(sys_inject_path, 'r') as doc:
                    self.system_prompt_injections.append(doc.read())
            except Exception as e:
                logger.warning(f'run() missing from "{tool_name}" module.')
                logger.warning(f'Load Failure Reason:\n{e}')
                if tool_name in self.funct_map:
                    del self.funct_map[tool_name]
                del tool_module

    def _load_tool_modules(self, int_name: str, path: pathlib.Path):
        module = importlib.import_module(f".{int_name}.tool", package=__package__)
        return module
    def update_tool_schema(self, path: pathlib.Path) -> dict:
        with open(path.joinpath('definition.json'), 'r') as doc:
            return json.loads(doc.read())
    def execute_tool(self, tool: dict):
        ## Add type checking for input validation
        if isinstance(tool, dict):
            tool_result = {}
            
            funct_name = tool['function']['name']
            try:
                funct_args = json.loads(tool['function']['arguments'])
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Arguments could not be parsed by the JSON '
                             f'decoder.\nJSON: {tool['function']['arguments']}'
                             f'\nError: {e}')
                funct_args = (f'Arguments could not be parsed by'
                              f' JSON decoder. \nError: {e}')
            raw_tool_result = self.funct_map[funct_name](self.interfaces, 
                                                         **funct_args)
            tool_result = {'funct_name': funct_name,
                           'funct_args': funct_args,
                           'result': raw_tool_result}

            logger.info(f'Returning Tool Result:\n{json.dumps(tool_result, 
                        indent=4)}')
            return tool_result
        else:
            logger.critical(f'Tool call is not of ecpected type "dict":\n{
                            json.dumps(tool, indent=4)}')
            raise ValueError


