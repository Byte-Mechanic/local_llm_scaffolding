# Copyright (c) 2024 Byte-Mechanic
# SPDX-License-Identifier: MIT

import pytest
import context
from llama.interface import LlamaInterface
import re

def test_server_correct_port_correct():
    interface = LlamaInterface()
    interface.server = '0.0.0.0'
    interface.port = '8090'
    assert interface.validate_server() == True

def test_server_incorrect_port_correct():
    interface = LlamaInterface()
    interface.server = '0.111.9.0'
    interface.port = '8090'
    with pytest.raises(ValueError, match='Llama server.*is down'):
        interface.validate_server()

def test_server_correct_port_incorrect():
    interface = LlamaInterface()
    interface.server = '0.0.0.0'
    interface.port = '1111'
    with pytest.raises(ValueError, match='Port.*is closed'):
        interface.validate_server()

def test_server_get_props():
    interface = LlamaInterface()
    props = interface.get_props()
    assert isinstance(props, dict)
