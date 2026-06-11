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
    def __init__(self,  
                 tool_handler: Tools,
                 context_manager: ContextManager,
                 llama_interface: LlamaInterface,
                 system_prompt: str|None = None, 
                 model: str = 'unkn'
                 ) -> None:
        self.model: str = model
        self.tools: Tools|None = tool_handler
        self.llama_interface: LlamaInterface = llama_interface
        self.context_manager: ContextManager = context_manager
        if system_prompt:
            self.context_manager.full_context.append({'role':'system',
                                                    'content':system_prompt})
    def add_assistant_msg(self, msg: GenerationResult) -> None:
        self.context_manager.add_assistant_msg(msg)
    def add_user_msg(self, msg) -> None:
        self.context_manager.add_user_msg(msg)
    def add_tool_msg(self, tool, tool_result) -> None:
        self.context_manager.add_tool_msg(tool, tool_result)
    def generate_local(self) -> GenerationResult:
        logger.info(f'Sending message context:\n'
                    f'{json.dumps(self.context_manager.working_context, indent=4)}')
        generation = self.llama_interface.chat_completions(
            model=self.llama_interface.models[1],
            context=self.context_manager.working_context,
            tools=self.tools.tool_definitions if self.tools else None)
        logger.info(f'Returning Generation Result:\n{json.dumps(generation, indent=4)}')
        return generation        
