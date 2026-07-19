# Local-LLM-Scaffolding

> Disclaimer: This is a solo learning project, 
> not ready for contributions yet.

This LLM Scaffolding project Is meant to be local-first, private, while also trying to achieve close to Anthropic and Openai class performance in web research, memory management, and tool use. This project also has the constraint of limiting myself to 16gb of vram (and 32gb of system ram). Making something powerful that can run on a majority of consumer gaming hardware.

## Current Status:
[07/18/2026] - The main loop is functional, the web_fetch, web_search, and bash is functional. Chats are not saved. Streaming is off. Basic chat compaction is functional.

For roadmap details, jump to the end of the readme.

## Usage:

*WORK IN PROGRESS*

As of right now, there is no official UI, as i am trying to finalize the backend to get the loop to a stable and predictable state. The entry point for the program is:

`src/local_llm_scaffolding/main.py`

### For Web Search
You will need to setup a docker or podman instance of searxng running locally, currently it looks at `http://0.0.0.0:8888/`, with no exposed config for changing where it points yet.

### You will need to create/modify a few files to run successfully:

#### memory.md
 * You'll need a memory file in `/src/local_llm_scaffolding/config/agent/` named `memory.md`.
    - This is a memory file injected raw into the system prompt, this will be depreciated in the future for a more dynamic memory system.

#### cfg.json
 * after first launch, a config file will be created with default parameters, if one is not found. Here is an example of the config and the definitions if you would like to modify and test:
```json
{
"general": {
    "logger_config": "agent/logger_config.json", 
    "user": "Name Here"
    }, 
"server": {
    "ip": "0.0.0.0", 
    "port": "8080", 
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

 - logger_config: Specifies the location of the logger configuration file. Leave as default.
 - user: The name the llm will refer to the user as.
 - ip: the ip used to communicate with the llama-server instance.
 - port: the port used to communicate with the llama-server instance.
 - exec: the location of the llama-server binary or launch script.
 - args: a list of arguments to be fed to llama-server. It will be used in a subprocess call, so keep that in mind when it comes to formatting.
 - system_prompt: Location of your system prompt file.
 - memory_file: Location of your memory file.

#### Llama.cpp
Inside the `llama/build/` directory, sits an `update.sh` script. This is meant to just build the llama.cpp llama-server binary and it's dependencies, move them to the `llama/build/bin` folder, and clean up the build files. This will be the binary that the program will use, but all thats needed is for you to build.
> Comments have been added to the file to denote where you can modify build flags for your hardware configuration.

#### Models
Models need to be placed into the `llama/models/` directory. *I* am using the Qwen3.6/3.5 models, just because they seem more competant for tool calling, but realistically you can use whichever. just note that my prompts and tooling methods are tailored to those models.

After copying the `.gguf` to the models folder, you need to modify the `llama/models/config.ini` with your model's preferred parameters. there are 4 model specs in there by default, it has not been added yet, but there's meant to be a thinking and non-thinking varient for a 'default' (main chat) model, and a 'mini' (tool-use/agentic) model.

Currently it only uses the `default_thinking` model.

If you wish for one model to share all tasks, just make the directories all point to the same model.

## TODO/Milestones:
 - [ ] [by 07/21/26] Complete file_edit tool
        - Experimenting with a new (to me) architecture for iteration, to be
          extended to the web_search tool.
 - [ ] [by 07/26/26] Optimize web_search tool
        - web_search does not give the model a choice on what enters it's
          context. This initial implementation was meant to be naive, but i'm
          at the point where it needs to be expanded in order to keep context
          tight.
 - [ ] [by 07/27/26] Role-based colors
        - For easy separation in the terminal, easier on the eyes and user
          friendly.
 - [ ] [by 08/10/26] Tests
        - Need tests for sanity check. The program is getting large enough to
          warrent the need for testing. The context manager is especially
          important, i need to know that objects are being added to context
          properly, and if related logic changes that it's working.

 - [ ] []
