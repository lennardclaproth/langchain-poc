# OCTOBOX Agentic

## Setting up development environment

make sure you have a virtual environment. Please refer to the [pydoc](https://docs.python.org/3/library/venv.html).

You can also run one of the following commands. Make sure you are in the **root** of the project.

```bash
python -m venv .venv
py -m venv .venv
```

To activate this environment you can use the following command or the equivalent of your OS

```bash
.\.venv\Scripts\Activate.ps1
```

To install the dependencies run the following commands.

```bash
python -m pip install -e ./agent-store
python -m pip install -e ./agent-engine
```

To run a ollama instance run the following command.

```bash
docker compose up -d
```

to install a model run the following command.

```bash
docker exec <container_name_or_id> ollama pull <model>
```

## Server configuration

[container-toolkit-installation-guide-nvidia](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
[docker-installation-guide-ubuntu](https://docs.docker.com/engine/install/ubuntu/)

for gpu support in ollama on docker make sure you enable the **--gpus=all** flag when running the ollama container or add the **gpus: all** to the docker-compose.yml
