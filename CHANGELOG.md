# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The creation of tools
- Tool server following the MCP protocol
- The creation of agents
- A chat functionality with an agent
- Context tool configuration for an agent
- Instruction configuration for an agent
- Support for multiple model providers (configurable)
- Model selection per agent
- A user interface
- Performance monitoring using Elastic APM

#### TODO

- [ ] [1] middleware, intercept messages and save them in the store
- [ ] [1] Cleanup store
- [x] [1] Fix dynamic tool loading
- [x] [1] Logging
- [x] [1] Global error handling
- [ ] [1] RAG support with vector db, think of how to seperate data from tenants/environments
- [ ] [1] Support for different providers
- [ ] [1] More reliable configuration
- [x] [2] APM
- [ ] [3] UI
