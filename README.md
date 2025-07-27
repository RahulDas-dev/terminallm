# TerminalLM

TerminalLM is a Toy Python application that provides an agent-based interface for interacting with LLMs directly from your terminal. The agent can perform various software engineering tasks such as reading files ~~writing files~~, ~~Editing Existing File~~, executing shell commands, and managing directories, all powered by LLM reasoning.

## Overview

This project serves as a demonstration of how Claude code or Gemini CLI works, developed purely for educational and demonstration purposes. The codebase is highly motivated by Gemini CLI's architecture and functionality (https://github.com/google-gemini/gemini-cli.git). While the core functionality is similar to these commercial tools, the codebase is designed to be easily extensible, allowing developers to add new tools, capabilities, or integrate with different LLM providers as needed.

## Features

- Support for multiple LLM providers including OpenAI, Azure, Google Vertex AI, and AWS Bedrock
- Built-in tool system for file operations, directory management, and shell command execution
- Available LLM-accessible tools:
  - File tools: Reading files, writing files, Editing files and file globbing
  - Directory tools: Listing directory contents 
  - Shell tools: Executing shell commands
- Event Based Communication Agent and Console ~~and SDK Logger~~

## Supported Models

TerminalLM supports any model that LiteLLM can connect to

## Development

Requires Python 3.13 or higher.

```bash
# Clone the repository
git clone https://github.com/yourusername/terminallm.git
cd terminallm

uv sync 
```

## Usage

```bash
# Basic usage with default settings
uv run main.py or python main.py

# Specify a different LLM model
python main.py --model gpt-4o

# Enable debug mode
python main.py --debug

# Specify a target directory
python main.py --target-dir /path/to/your/project --task Write a suitable readme.md for the project
```

## Configuration

The application can be configured through command-line arguments or environment variables. Create a `.env` file in the project root to set environment variables. Kidly Check `.env.example`.

TerminalLM uses LiteLLM as its LLM client, which means it can be configured to work with any LLM provider supported by LiteLLM through the appropriate environment variables. This provides extensive flexibility for connecting to different models across various providers.

