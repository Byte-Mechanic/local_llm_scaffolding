# Copyright (c) 2024 Byte-Mechanic
# SPDX-License-Identifier: MIT

import sys
import pathlib
import context
from agent.tools.bash.tool import run as bash_tool
import pytest

fake_dirs = [
        './tests/test_dir/', 
        './tests/test_dir/dir1/', 
        './tests/test_dir/dir2/', 
        './tests/test_dir/dir2/dir21/', 
        './tests/test_dir/dir2/dir22/', 
        './tests/test_dir/dir3/'
        ]

def build_fake_dir_tree():
    for dir_ in fake_dirs:
        pathlib.Path.mkdir(dir_)

def delete_fake_dir_tree():
    fake_dirs.reverse()
    for dir_ in fake_dirs:
        pathlib.Path.rmdir(dir_)

@pytest.fixture(autouse=True, scope="module")
def cleanup():
    yield
    delete_fake_dir_tree()

build_fake_dir_tree()
cleanup()


def test_bash_allowlist_tree():
    expected = """├── dir1
├── dir2
│   ├── dir21
│   └── dir22
└── dir3
""" 
    test_result = bash_tool(
            ['tree', 
             str(pathlib.Path('./tests/test_dir/').resolve())]
            )
    assert expected in test_result

def test_bash_allowlist_ls():
    pass

def test_bash_allowlist_touch():
    pass

def test_bash_allowlist_mkdir():
    pass

def test_bash_allowlist_cat():
    pass

def test_bash_allowlist_head():
    pass

def test_bash_allowlist_tail():
    pass

def test_bash_allowlist_wc():
    pass

def test_bash_allowlist_pwd():
    pass

def test_bash_allowlist_stat():
    pass

def test_bash_allowlist_file():
    pass

def test_bash_allowlist_grep():
    pass

def test_bash_allowlist_find():
    pass

def test_bash_allowlist_ps():
    pass

def test_bash_allowlist_pgrep():
    pass

