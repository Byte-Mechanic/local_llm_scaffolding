# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

import logging
import json
import copy
import datetime
import pathlib
from ..llama.interface import LlamaInterface, GenerationResult

logger = logging.getLogger(__name__)
logger.info(f'Logger {logger.name} Initiated.')

proj_root = pathlib.Path(__file__).resolve().parent.parent
sys_prompt_file = 'config/agent/system_prompt.md' # get from config after config
sys_memory_file = 'config/agent/memory.md'        # refactor
user = 'user'


class ContextManager:
    def __init__(self, llama_interface: LlamaInterface, context: list|None = None):
        if context:
            self.full_context: list[dict] = context
        else:
            self.full_context: list[dict] = [] ### Add preconfig Sys-prompt-
                                               ### Here

        self.llama_interface: LlamaInterface = llama_interface
        self.working_context: list = []
        self.ctx_token_limit: int = 0
        self.ctx_tokens_used: int = 0
        self.retain_reasoning: bool = True
        self.tool_instructions = []
        self.system_prompt = {'role':'system','content':''}
    def build_sys_prompt(self) -> None:
        # Load external files
        with open(proj_root.joinpath(sys_prompt_file), 'r') as doc:
            sys_prompt = doc.read()
        with open(proj_root.joinpath(sys_memory_file), 'r') as doc:
            sys_memory = doc.read()
        tool_instruction_buff = ''
        for instruction in self.tool_instructions:
            tool_instruction_buff += f'\n{instruction}'
        # Substitutions
        datetime_now: str = datetime.datetime.strftime(datetime.datetime.now(),
                                                       '%A %B %d, %Y. %I:%M%p')
        sys_prompt = sys_prompt.replace('$DATE', datetime_now)
        sys_prompt = sys_prompt.replace('$MEMORY', sys_memory)
        sys_prompt = sys_prompt.replace('$USER', user)
        sys_prompt = sys_prompt.replace('$TOOLS', tool_instruction_buff)
        self.system_prompt['content'] = sys_prompt
        for msg in self.full_context:
            if 'role' not in msg:
                continue
            if msg['role'] is 'system':
                msg['content'] = self.system_prompt
        else:
            self.full_context.insert(0, self.system_prompt)

    def add_user_msg(self, msg) -> None:
        message: dict = {'role': 'user',
                   'content': msg}
        logger.info(f'Adding User Message:\n'
                    f'{json.dumps(message, indent=4)}')
        self.full_context.append(message)
        self.post_add()
    def add_assistant_msg(self, msg: GenerationResult) -> None:
        message: dict = {'content': msg['response'],
                               'role': msg['role']}
        if msg['tools']:
            message['tool_calls'] = msg['tools']
        if self.retain_reasoning == True:
            message['reasoning_content'] = msg['reasoning']
        logger.info(f'Adding Assistant Message:\n'
                    f'{json.dumps(message, indent=4)}')
        self.full_context.append(message)
        self.post_add()
    def add_tool_msg(self, tool, tool_result):
        message: dict = {'role': 'tool',
                         'tool_call_id': tool['id'],
                         'content': (json.dumps(tool_result)
                                     if not isinstance(tool_result, str)
                                     else tool_result)}
        logger.info(f'Adding Tool Message:\n'
                    f'{json.dumps(message, indent=4)}')
        self.full_context.append(message)
        self.post_add()
    def post_add(self):
        ## update ctx_tokens_used + ctx_tokens_limit, kick off compaction if 
        ## needed, and update the working_context
        self.working_context = copy.deepcopy(self.full_context)
        logger.info(f'working_context Updated:\n'
                    f'{json.dumps(self.working_context, indent=4)}')
        if self.llama_interface.cur_model != '':
            self.ctx_tokens_used = self.llama_interface.count_tokens(self.working_context)
    def compact_context(self):
        pass
    def compact_tool_use(self):
        pass

