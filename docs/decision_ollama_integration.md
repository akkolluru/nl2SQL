# Architecture Decision: Ollama Integration

## Decision

The system uses Ollama as the LLM service provider instead of cloud-based APIs, allowing for local deployment and better privacy control.

## Rationale

- **Privacy**: Keeps sensitive data within organizational boundaries
- **Cost Control**: Avoids per-token charges from cloud providers
- **Customization**: Allows use of specific models tailored to SQL generation
- **Availability**: Operates independently of external service availability
- **Latency**: Potentially lower latency with local deployment

## Implementation

- HTTP client communication with Ollama API
- Configurable Ollama URL and model selection
- Asynchronous request handling
- Response cleaning and normalization

## Impact

- Requires Ollama to be deployed alongside the application
- Model quality depends on local model capabilities
- Lower operational costs for high-volume usage
- Better data privacy and security