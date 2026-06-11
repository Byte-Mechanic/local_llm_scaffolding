# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

import json
import logging
import logging.config
import pathlib
import datetime

pkg_root = pathlib.Path(__file__).resolve().parent.parent
logger_config_path = pkg_root.joinpath('config/agent/logger_config.json')
session_stamp = datetime.datetime.now().strftime('%m-%d-%Y-%H:%M:%S')

with open(logger_config_path, 'r') as doc:
    logger_config = json.load(doc)

logger_config['handlers']['agent_file']['filename'] = logger_config['handlers']['agent_file']['filename'].format(
        PROJ_ROOT = str(pkg_root),
        SESSION = session_stamp
        )
logger_config['handlers']['tool_file']['filename'] = logger_config['handlers']['tool_file']['filename'].format(
        PROJ_ROOT = str(pkg_root),
        SESSION = session_stamp
        )
logger_config['handlers']['llama_file']['filename'] = logger_config['handlers']['llama_file']['filename'].format(
        PROJ_ROOT = str(pkg_root),
        SESSION = session_stamp
        )
logger_config['handlers']['context_file']['filename'] = logger_config['handlers']['context_file']['filename'].format(
        PROJ_ROOT = str(pkg_root),
        SESSION = session_stamp
        )

logging.config.dictConfig(logger_config)
