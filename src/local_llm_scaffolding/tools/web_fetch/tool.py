# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

from ..utils import fetch_link_md
from local_llm_scaffolding.llama.interface import LlamaInterface
import json
import logging

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')


def run(llama_interface: LlamaInterface, url: str) -> str:
    return fetch_link_md(url)
