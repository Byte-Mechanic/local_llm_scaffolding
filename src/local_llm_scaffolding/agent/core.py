# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

import json
import logging
from ..tools.handler import Tools
from ..llama.interface import LlamaInterface, GenerationResult
from ..context.manager import ContextManager

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')
print(__name__)


class Agent:
    def __init__(self, shared_interfaces, model: str|None = None) -> None:
        
        self.model: str = model
        
        self.config_manager: ConfigManager = shared_interfaces.config_manager
        self.llama_interface: LlamaInterface = shared_interfaces.llama_interface

        self.context_manager: ContextManager = ContextManager(self.llama_interface)
        self.tools: Tools = Tools(self.llama_interface, self.context_manager)
        
        self.llama_interface.default_model = model

    def add_assistant_msg(self, msg: GenerationResult) -> None:
        self.context_manager.add_assistant_msg(msg)
    def add_user_msg(self, msg) -> None:
        self.context_manager.add_user_msg(msg)
    def add_tool_msg(self, tool, tool_result) -> None:
        self.context_manager.add_tool_msg(tool, tool_result)
    def generate_local(self) -> GenerationResult:
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
