# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

from pathlib import Path
import subprocess
import logging
from local_llm_scaffolding.llama.interface import LlamaInterface

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

sandbox_dir = Path('/home/reggie/')
BWRAP_PREFIX = [
    'bwrap',
    '--ro-bind', '/usr', '/usr',
    '--ro-bind', '/bin', '/bin',
    '--ro-bind', '/lib', '/lib',
    '--ro-bind', '/lib64', '/lib64',
    '--ro-bind', '/etc/ld.so.cache', '/etc/ld.so.cache',
    '--proc', '/proc',
    '--dev', '/dev',
    '--tmpfs', '/tmp',
    '--bind', str(sandbox_dir), '/workspace',
    '--unshare-net',
    '--unshare-pid',
    '--chdir', '/workspace',
    '--die-with-parent',
    '--',
]

allowlist = ['tree', 'ls', 'touch', 'mkdir', 'cat', 'head', 'tail', 'wc', 
             'pwd', 'stat', 'file', 'grep', 'find', 'ps', 'pgrep'] 
denied_char = ['|','>','<','||','|&']
py_exec = ['python','python3']
def command_filter(commands: list[str]) -> str|None:
    if commands[0] in py_exec:
        return None
    for command in commands:
        ## Path Guardrails
        if '/' in command or command.startswith('.'):
            cmd_path = Path(command).resolve()
            if not cmd_path.is_relative_to(sandbox_dir):
                return (f'ERROR: "{command}" directory access is denied. you'
                        f' can only work within "{sandbox_dir}".')
        ## Formatting Check
        if command == '':
            return 'ERROR: Command contains empty strings'
        if ' ' in command:
            return (f'ERROR: "{command}" not valid. spaces present in the'
                    f' command. Each command and argument needs to be split'
                    f' and spearate elements in the list.')
        if command in denied_char:
            return (f'ERROR: {command}: You cannot use any of the following'
                    f' characters in your command:\n{denied_char}')
        ## Binary Guardrails
    else:
        if commands[0] not in allowlist:
            return (f'"{command}" execution is denied. Only the following'
                    f' binaries are allowed:\n{allowlist}')
        return None

def run(llama_interface: LlamaInterface, commands: list) -> str:
    logger.info(f'Bash tool executed with the command ([{commands}])')
    _filter = command_filter(commands)
    if commands[0] in py_exec:
        logger.info(f'Python execution detected.. Diverting to BWRAP execution..')
        result = subprocess.run(BWRAP_PREFIX+commands, 
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                cwd=sandbox_dir,
                                shell=False, 
                                text=True,
                                timeout=300)
        result = result.stdout
        logger.info(f'Python Execution Result:\n{result}')
        return result
    elif not _filter:
        result = subprocess.run(commands, 
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT,
                                cwd=sandbox_dir,
                                shell=False, 
                                text=True,
                                timeout=300)
        result = result.stdout
        logger.info(f'Bash Execution Result:\n{result}')
        return result
    else:
        return _filter
