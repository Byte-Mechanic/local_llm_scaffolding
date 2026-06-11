# Copyright (c) 2024 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""Spawns and manages a llama-server instance

Meant to be used as a context manager, to help manage
a llama-server instance. This should only be used once
for the main loop. If multiple models are needed to be
loaded in parallel, refer to the config manager.

Example:
    >>> from llama.manager import LlamaManager
    >>> with LlamaManager(config) as llama_server:
    ... #Do work
"""

import subprocess
import threading
import time
import pathlib
import logging

logger = logging.getLogger(__name__)
pkg_root = pathlib.Path(__file__).resolve().parent.parent

class LlamaManager:
    """
    Manages the `llama-server` process

    Keeps track of the llama-server process state and
    catches/recovers from unexpected errors.
    """

    def __init__(self, config: ConfigManager) -> None:
        """Initialize the manager, preconfiguring variables

        Args:
            config (ConfigManager): a ConfigManager class instance
        """    
        #Main Process
        self._process: subprocess.Popen = None
        #States
        self._server_is_ready: bool = False
        self._model_loaded: bool = False
        self._loaded_model: str = None
        self._avg_gpu_vram: int = None
        #Config Variables
        self.server_path: str = pkg_root.joinpath(config.server_exec).resolve()
        self.server_args: list = config.server_args
        self.server_port: str = config.server_port
        self.server_ip: str = config.server_ip
        #Locks

        self._state_lock = threading.Lock()
        
        logger.info(f'Llama Server Loaded (with):\n\tPATH: {self.server_path}'
                    f'\n\tARGS: [{self.server_args}]')
    def __enter__(self) -> None:
        """Starts the server"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the server and startup script"""
        self.stop()
        subprocess.run(['pkill', '-9', 'llama'])
        return False

    def _read_logs(self):
        """Toggles server readiness based on server stdout"""
        time.sleep(1)
        while self._process.poll() == None:
            log_line = self._process.stdout.readline()
            with self._state_lock:
                if f'router server is listening on http://{self.server_ip}:{self.server_port}' in log_line:
                    self._server_is_ready = True
            logger.info(f'LLAMA_INSTANCE_STDOUT : \n{log_line.replace('\n', '')}')
        while self._process.poll() == 1:
            time.sleep(0.5)
            line = self._process.stdout.readline()
            logger.info(f'LLAMA_INSTANCE_STDOUT : \n{line.replace('\n', '')}')

    def _gpu_usage(self) -> None:
        """DEPRECATED: Tracks GPU usage to check for models failing to unload"""
        avg_usage: list = []
        gpu_usage: int = None
        for y in range(5):
            time.sleep(1)
            start_idx = None
            output = subprocess.run(
                    ['rocm-smi'], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True
                    )
            for x in output.stdout.split('\n'):
                if start_idx is not None:
                    if x.find('%') != -1:
                        gpu_usage = int(x[start_idx:start_idx+4].strip().replace('%',''))
                        continue
                find_idx = x.find('VRAM%')
                if find_idx != -1:
                    start_idx = find_idx
            avg_usage.append(gpu_usage)
            ##What happens if you cannot find the gpu vram usage?
        with self._state_lock:
            self._avg_gpu_vram = sum(avg_usage)/len(avg_usage)


        return
    def start(self) -> None:
        """Start the server

        Builds the command list from the config class that was passed in and
        starts the logging thread to determine when the server is ready to
        accept requests.

        Raises:
            TimeoutError: if the server takes too long to be ready.
        """
        server_command_list = [str(self.server_path)]
        server_command_list.extend(self.server_args)
        server_command_list.extend([
            '--host', 
            f'{self.server_ip}', 
            '--port', 
            f'{self.server_port}'
            ])
        self._process = subprocess.Popen(
                server_command_list, 
                cwd=pkg_root,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
                )
        _log_thread = threading.Thread(target=self._read_logs, daemon=True)
        _log_thread.start()
        for x in range(5):
            time.sleep(2)
            with self._state_lock:
                if self._server_is_ready:
                    break
        else:
            if not self._server_is_ready:
                self._process.kill()
                raise TimeoutError
    
    def stop(self) -> None:
        """Stops the server"""
        if self._process.poll() is None:
            self._process.kill()

