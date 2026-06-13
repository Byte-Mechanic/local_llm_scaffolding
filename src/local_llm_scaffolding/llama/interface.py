# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Interfaces with the llama-server instance

Used as an interface for llama-server. Used for any interaction
with the server.

Example:
    >>> from llama.interface import LlamaInterface
    >>> interface = LlamaInterface(config, server_mgr)
    >>> interface.count_tokens(context)
    >>> response = interface.chat_completions(model=model,
    ...                                     context=context,
    ...                                     tools=tools)
"""

import requests
from typing import Literal, TypedDict
import logging
import traceback
import time
import json

from ..config.manager import ConfigManager
from ..llama.manager import LlamaManager

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

class GenerationResult(TypedDict):
    """final return type for chat completions"""

    role: str
    response: str
    reasoning: str
    finish_reason: Literal['stop', 'length', 'content_filter', 'null', 'tool']
    stats: dict
    tools: list|None

class LlamaInterface:
    """Sends requests to the llama-server instance

    Used to send requests to the llama-server interface, creating a
    unified interface that any module can import and use.
    """
    def __init__(self, config: ConfigManager, server_manager: LlamaManager):
        """Initialize the interface

        Args:
            config (ConfigManager): the ConfigManager instance used
            server_manager (LlamaManager): The LlamaManager instance used

        Raises:
            TimeoutError: If the server takes too long to get ready
        """
        self.server = config.server_ip
        self.port = config.server_port
        for _try in range(3):
            time.sleep(_try)
            if server_manager._server_is_ready == True:
                self.models = self._generate_model_list()
                break
        else:
            raise TimeoutError('Could not generate LLM model map.')
        self.cur_model: str = ''
    
    def _generate_model_list(self) -> list:
        """Generates a list of the models specified in the server config"""
        raw_models = requests.get(f'http://{self.server}:{self.port}/models')
        raw_models.raise_for_status()
        models = [model['id'] for model in raw_models.json()['data']]
        print(models)
        return models
    
    def get_health(self) -> dict:
        raw_health = requests.get(f'http://{self.server}:{self.port}/health')
        raw_health.raise_for_status()
        return raw_health.json()

    
    def count_tokens(self, context: list[dict]) -> int:
        """Counts the tokens in a message used for a request (list of dicts)

        Args:
            context (list[dict]): the context of the conversation

        Returns:
            int: the token count of the context provided
        """
        response = requests.post((f'http://{self.server}:{self.port}'
                                  f'/v1/messages/count_tokens'),
                                 json={'model':self.cur_model,
                                     'messages':context})
        response.raise_for_status()
        return int(response.json()['input_tokens'])

    def tokenize(self, content: str) -> int:
        """Counts the tokens in a string of text.

        Args:
            content (str): The string of text to be evaluated

        Returns:
            int: the token count of the content provided.
        """
        response = requests.post((f'http://{self.server}:{self.port}'
                                 f'/tokenize'),
                                 json={'model':self.cur_model,
                                       'content':content})
        response.raise_for_status()
        return len(response.json()['tokens'])

    def get_props(self):
        """Get the full properties of the model that is loaded.

        Returns:
            dict: server properties
        """
        models = requests.get(f'http://{self.server}:{self.port}/models')
        models.raise_for_status()
        for mod in models.json()['data']:
            if mod['status']['value'] == 'loaded':
                props = mod['status']['preset'].split('\n')
                prop_dict = {}
                prop_dict['model'] = mod['id']
                for prop in props:
                    if '=' not in prop:
                        continue
                    prop_split = prop.split('=')
                    propk = prop_split[0].strip()
                    propv = prop_split[1].strip()
                    try:
                        prop_dict[propk] = json.loads(propv)
                    except json.decoder.JSONDecodeError:
                        prop_dict[propk] = str(propv)
                logger.info(f'Requested model props:\n'
                            f'{json.dumps(prop_dict, indent=4)}')
                return prop_dict
        else:
            return {'model': 'unloaded'}

    def chat_completions_streaming(self,
                                   context: list[dict],
                                   tools: list[dict],
                                   thinking: bool) -> None:
        ### Work In Progress, dont mind me
        pass

    def chat_completions(self,
                         model: str,
                         context: list[dict],
                         tools: list[dict]|None,
                         caching: bool = True) -> GenerationResult:
        """Sends a request to run inference

        Sends a non-streaming inference request with the provided context,
        tools, and model

        Args:
            model (str): Model name (usually using the index from the model list)
            context (list[dict]): context of the conversation
            tools (list[dict]): llm tool definitions (OpenAI Schema)
            Caching (bool): Whether to keep the generation cache or not

        Returns:
            GenerationResult: the full generated response from the llm

        Raises:
            HTTPError: If the http request returns a 4xx or 5xx code
            KeyError: If the output from the llm does not match the expected schema
        """
        try:
            response = requests.post((f'http://{self.server}:{self.port}'
                                      f'/v1/chat/completions'),
                                     json={
                                         'model': model,
                                         'messages': context,
                                         'tools': tools,
                                         'cache_prompt': caching,
                                         'parallel_tool_calls': True}
                                     )
            response.raise_for_status()
        except:
            r_json = response.json()
            if 'error' in r_json:
                logger.critical(f"Generation failed. "
                                f"[{r_json['error']['code']}] - "
                                f"{r_json['error']['message']}")
            else:
                logger.critical(f"Generation failed. Unexpected Response:\n"
                                f"{json.dumps(r_json, indent=4)}")
        try:
            choice = response.json()['choices'][0]
            message = choice['message']
            gen = GenerationResult(
                    role = message['role'],
                    response = message['content'],
                    reasoning = (message['reasoning_content']
                                 if 'reasoning_content' in message else ''),
                    finish_reason = choice['finish_reason'],
                    stats = response.json()['usage'],
                    tools = (message['tool_calls']
                             if 'tool_calls' in message else None)
                    )
            logger.info(f'Response Generated:\n{gen}')
            self.cur_model = model
            return gen
        except KeyError:
            logger.critical('Unable to create [GenerationResult]. Detailed '
                            'error below.'
                            '\n--------\n'
                            f'{traceback.format_exc()}'
                            '\n--------\n'
                            f'{json.dumps(response.json(), indent=4)}'
                            '\n--------')


