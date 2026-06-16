# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Manages a specific agent's context.

This module manages a specific agent instances' context, exposing an interface
for adding assistant, user, and tool messages as well as exposing functions to
compress or 'compact' the context when it hits a limit.

Usage:
    >>> context = ContextManager(llama_interface, context_prefix)
    >>> context.add_user_msg(input("--> "))
"""

import logging
import json
import copy
import pprint
import datetime
import pathlib
from ..llama.interface import LlamaInterface, GenerationResult

logger = logging.getLogger(__name__)
logger.info(f'Logger {logger.name} Initiated.')

proj_root = pathlib.Path(__file__).resolve().parent.parent
sys_prompt_file = 'config/agent/system_prompt.md' # get from config after config
sys_memory_file = 'config/agent/memory.md'        # refactor
compaction_file = 'context/general_compaction.md'
user = 'user'
log_wd = 120

class ContextManager:
    """A single agent's context"""

    def __init__(self, llama_interface: LlamaInterface, context: list|None = None):
        """Initializes a single agent's context.

        Sets up the context with predefined variables probed by other parts of
        the program. Takes in a starting context for added flexibility.

        Args:
            context:
                Optional starting context, structured in the typical OAI [{'role',
                'content':}] schema
        """
        if context:
            self.full_context: list[dict] = context
        else:
            self.full_context: list[dict] = [] ### Add preconfig Sys-prompt-
                                               ### Here
        self.llama_interface: LlamaInterface = llama_interface
        self.working_context: list[dict] = copy.deepcopy(self.full_context)
        self.ctx_token_limit: int = 0
        self.ctx_tokens_used: int = 0
        self.retain_reasoning: bool = True
        self.compact_chunks: dict = {}
        self.tool_instructions: list = []
        self.system_prompt: dict = {'role':'system','content':''}
        logger.info(f'Logger initialized with context:\n'
                    f'{pprint.pformat(self.working_context, width=log_wd)}')

    def build_sys_prompt(self) -> None:
        """Builds the system prompt.

        Builds the system prompt by making the nessesary substitutions, adding
        the tool instructions based on what's been loaded, and wraps it in the
        message dict and adds to the contexts.
        """
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
        self.working_context = copy.deepcopy(self.full_context)
        logger.info(f'System Prompt built:\n'
                    f'{pprint.pformat(self.system_prompt, width=log_wd)}')

    def add_user_msg(self, msg) -> None:
        """Adds a 'user' message to the context

        Args:
            msg:
                The string sent by the user.
        """
        message: dict = {'role': 'user',
                   'content': msg}
        logger.info(f'Adding User Message:\n'
                    f'{pprint.pformat(message, width=log_wd)}')
        self.full_context.append(message)
        self.working_context.append(message)
        self.post_add()

    def add_assistant_msg(self, msg: GenerationResult) -> None:
        """Adds an 'assistant' message to the context

        Args:
            msg:
                The resulting GenerationResult from the call to LlamaManager's
                generate_local.
        """
        message: dict = {'content': msg['response'],
                               'role': msg['role']}
        if msg['tools']:
            message['tool_calls'] = msg['tools']
        if self.retain_reasoning == True:
            message['reasoning_content'] = msg['reasoning']
        logger.info(f'Adding Assistant Message:\n'
                    f'{pprint.pformat(message, width=log_wd)}')
        self.full_context.append(message)
        self.working_context.append(message)
        self.post_add()

    def add_tool_msg(self, tool, tool_result):
        """Adds a 'tool' message to the context.

        Args:
            tool:
                the raw tool information sent when the model requested the call.
            tool_result:
                The raw tool result from execution.
        """
        message: dict = {'role': 'tool',
                         'tool_call_id': tool['id'],
                         'content': (json.dumps(tool_result)
                                     if not isinstance(tool_result, str)
                                     else tool_result)}
        logger.info(f'Adding Tool Message:\n'
                    f'{pprint.pformat(message, width=log_wd)}')
        self.full_context.append(message)
        self.working_context.append(message)
        self.post_add()

    def post_add(self):
        """A stub method for post-processing after message additions."""
        ## update ctx_tokens_used + ctx_tokens_limit, kick off compaction if 
        ## needed, and update the working_context
        logger.info(f'working_context Updated:\n'
                    f'{pprint.pformat(self.working_context, width=log_wd)}')
        if self.llama_interface.default_model != '':
            self.ctx_tokens_used = self.llama_interface.count_tokens(self.working_context)

    def compact_context(self) -> None:
        """Compacts the context.

        Separates the context into the current system prompt, and last 2
        messages, compacts the rest in-between, then adds the message compaction
        to the system prompt and reconstructs the message history into the
        working_context. It also detects if compaction was previously performed.
        """
        logger.info(f'Starting Context Compaction...')
        llama = self.llama_interface
        first_chunk = False
        # Register compaction chunk in self.compact_chunks
        ctx_range: tuple = (self.full_context.index(self.working_context[1]),
                            self.full_context.index(self.working_context[-2]))
        if self.compact_chunks:
            comp_keys = list(self.compact_chunks.keys())
            comp_keys.sort()
            chunk = comp_keys[-1]+1
            self.compact_chunks[chunk] = ctx_range
        else:
            first_chunk = True
            chunk = 0
            self.compact_chunks[chunk] = ctx_range
        # Generate stats
        before_tokens = llama.count_tokens(self.working_context)
        # strip data not to be compacted
        if self.working_context[0]['role'] == 'system':
            sys_prompt = self.working_context.pop(0)
            logger.info(f'System prompt preserved:\n'
                        f'{pprint.pformat(sys_prompt, width=log_wd)}')
        else:
            sys_prompt = {'role':'system',
                          'content':'You are a helpful AI assistant.'}
            logger.info(f'No system prompt detected. Using default:\n'
                        f'{pprint.pformat(sys_prompt, width=log_wd)}')
        if len(self.working_context) > 2:
            last_msgs: list[dict] = []
            last_msgs.append(self.working_context.pop(-2))
            last_msgs.append(self.working_context.pop(-1))
            logger.info(f'Last messages preserved:\n'
                        f'{pprint.pformat(last_msgs, width=log_wd)}')
        else:
            logger.info('Context cannot be compacted.')
            # revert
            self.working_context = copy.deepcopy(self.full_context)
            return
        # COMPACTION
        with open(proj_root.joinpath(compaction_file), 'r') as doc:
            compact_prompt = [{'role':'system',
                              'content':doc.read()},
                              {'role':'user',
                               'content':json.dumps(self.working_context, 
                                                   indent=4)}]
        response = llama.chat_completions(model = 'mini_thinking',
                                         context = compact_prompt,
                                         tools = None,
                                         caching = False)
        logger.info(f'Compaction:\n{pprint.pformat(response, width=log_wd)}')
        # add to system prompt
        if first_chunk == True:
            compact_msg = (f'\n-----------------------------------------------\n'
                           f'The conversation has been compacted and the\n'
                           f'context you need to continue is provided below:\n\n'
                           f'Chunk 0:\n'
                           f'{response['response']}\n')
        else:
            compact_msg = (f'Chunk {chunk}:\n'
                           f'{response['response']}\n')
        sys_prompt['content'] += compact_msg
        # rebuild the context
        new_context = [sys_prompt]
        if len(last_msgs) == 2:
            new_context.extend([last_msgs[-2],last_msgs[-1]])
        logger.info(f'Post-Compaction Context:\n'
                    f'{pprint.pformat(new_context, width=log_wd)}')
        # Apply to the working context
        self.working_context = copy.deepcopy(new_context)
        # Log stats
        after_tokens = llama.count_tokens(new_context)
        logger.info(f'Compaction Complete [{before_tokens}->{after_tokens}]')

    def compact_tool_use(self):
        """A stub method for compacting tool use specifically."""
        pass

