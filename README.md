# <span style="color:green">Local-LLM-Scaffolding</span>

Disclaimer: This is a solo project and I'm not accepting pull requests or feature requests
My Python-Based local LLM Scaffolding. Meant to be used as a testing ground for new ideas and getting the most out of smaller open models.

## Project Info

OS: Linux
Language: Python
LM Target: Model-agnostic
GPU VRAM Limitation: 16G
Testing LM: Qwen3.6 27B UD-IQ3_XXS (unsloth quant)

## Usage:

*WORK IN PROGRESS*

As of right now, there is no official UI, as i am trying to finalize the backend to get the loop to a stable and predictable state. The entry point for the program is:

`src/local-llm-scaffolding/chatflow.py`

### You will need to create/modify a few files to run successfully:
 * You'll need a memory file in `/src/local-llm-scaffolding/agent/` named `memory.md`.
    - This is a memory file injected raw into the system prompt, this will be depreciated in the future for a more dynamic memory system.

 * after first launch, a config file will be created with default parameters, alternatively, you *can* create one. it needs to be named `cfg.json` and located in `/src/local-llm-scaffolding/config/`. Heres a template:

```json
{
"general": {
    "logger_config": "agent/logger_config.json", 
    "user": "Name Here"
    }, 
"server": {
    "ip": "0.0.0.0", 
    "port": "8090", 
    "exec": "./llama/llama.cpp.sh", 
    "args": ["--models-preset", "llama/models/config.ini",
        "--models-max", "1", 
        "-ngl", "99", 
        "-ctk", "q8_0", 
        "-ctv", "q8_0", 
        "-np", "1"]
        }, 
"agent": {
    "system_prompt": "agent/system_prompt.md", 
    "memory_file": "agent/memory.md"
    }, 
"context": {
    "placeholder": null
    }
}
```

 - logger_config - Specifies the location of the logger configuration file. Leave as default.
 - user - The name the llm will refer to the user as.
 - ip - the ip used to communicate with the llama-server instance.
 - port - the port used to communicate with the llama-server instance.
 - exec - the location of the llama-server binary or launch script.
 - args - a list of arguments to be fed to llama-server. It will be used in a subprocess call, so keep that in mind when it comes to formatting.
 - system_prompt - Location of your system prompt file.
 - memory_file - Location of your memory file.

## TODO:
- [ ] Fix imports and dependencies from switching to src project structure.
- [ ] Logging consistancy.
- [ ] Verify tool functionality.
- [ ] Verify chat loop functionality.
- [ ] Verify diagnostic functionality.
