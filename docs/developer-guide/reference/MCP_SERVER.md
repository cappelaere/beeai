# RealtyIQ MCP Server

## Overview

The RealtyIQ MCP (Model Context Protocol) Server exposes all 16 tools for property, agent, auction, and bidding data via the MCP protocol, enabling AI assistants and agents to interact with the RealtyIQ API.

## Quick Start

### Start the Server

```bash
# Make sure environment variables are set
source dev-setup.sh

# Start the MCP server
python mcp_server.py
```

Expected output:
```
🚀 RealtyIQ MCP Server starting on port 8001
📊 Registered 16 tools:

  Core Tools:
    • list_properties
    • list_agents_summary

  Tier 1 - Property & Reference Data:
    • get_property_detail
    • list_property_types
    • list_asset_types
    • get_auction_types
    • get_site_detail
    • property_count_summary

  Tier 2 - Auctions & Bids:
    • auction_dashboard
    • auction_bidders
    • auction_total_bids
    • bid_history
    • auction_watchers
    • admin_dashboard
    • property_registration_graph

  Utility:
    • list_available_tools

📖 See docs/tools.md for detailed documentation
```

## Configuration

### Server Settings

The server runs on:
- **Protocol**: `streamable-http`
- **Port**: `8001`
- **Host**: `0.0.0.0` (allows external connections)

### Environment Variables

The MCP server requires the same environment variables as the tools:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_URL` | Yes | - | Base URL of the RealtyIQ API (e.g., `http://127.0.0.1:8000`) |
| `AUTH_TOKEN` | Yes | - | Token for API authentication |
| `SITE_ID` | No | `3` | Default site/domain ID |
| `USER_ID` | No | - | Default user ID for Tier 2 tools |
| `TLS_VERIFY` | No | `true` | Set to `false` to disable TLS verification (dev only) |

These are automatically loaded from `.env` when using `source dev-setup.sh`.

## Available Tools

### Core Tools (2)
Essential tools for listing properties and agents.

1. **`list_properties`** - Paginated property listing with search/filter
2. **`list_agents_summary`** - PII-safe agent listing

### Tier 1 - Property & Reference Data (6)
Tools requiring Token authentication only.

3. **`get_property_detail`** - Full property details
4. **`list_property_types`** - Property type reference data
5. **`list_asset_types`** - Asset type reference data
6. **`get_auction_types`** - Auction type reference data
7. **`get_site_detail`** - Site/domain configuration
8. **`property_count_summary`** - Count of properties matching filters

### Tier 2 - Auctions & Bids (7)
Tools requiring Token + OAuth2 authentication (user_id needed).

9. **`auction_dashboard`** - Auction-focused dashboard with filters
10. **`auction_bidders`** - List of registered bidders for an auction
11. **`auction_total_bids`** - Bid activity summary per bidder
12. **`bid_history`** - Full bid history for a property
13. **`auction_watchers`** - Count and list of auction watchers
14. **`admin_dashboard`** - Admin analytics and metrics
15. **`property_registration_graph`** - Property registration over time

### Utility Tools (1)

16. **`list_available_tools`** - List all available tools with descriptions

## Tool Documentation

For detailed documentation on each tool including parameters, examples, and API endpoints, see:
- **[tools.md](tools.md)** - Complete tool reference

## Usage Examples

### From an MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "list_properties",
                arguments={"page": 1, "page_size": 10}
            )
            print(f"Properties: {result.content}")

asyncio.run(main())
```

### Test with curl

```bash
# List properties
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_properties",
    "arguments": {
      "page": 1,
      "page_size": 10
    }
  }'

# Get property detail
curl -X POST http://localhost:8001/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_property_detail",
    "arguments": {
      "property_id": 12345
    }
  }'
```

## Architecture

```
┌─────────────────────┐
│   MCP Client        │
│  (AI Assistant)     │
└──────────┬──────────┘
           │ MCP Protocol
           │ (HTTP)
┌──────────▼──────────┐
│   MCP Server        │
│   (mcp_server.py)   │
│   Port 8001         │
└──────────┬──────────┘
           │
    ┌──────▼───────┐
    │   16 Tools   │
    └──────┬───────┘
           │ HTTP/Token Auth
┌──────────▼──────────┐
│   RealtyIQ API      │
│   (Django Backend)  │
└─────────────────────┘
```

## Development

### Adding New Tools

1. Create tool file in `tools/` directory:

```python
# tools/my_new_tool.py
from beeai_framework.tools import tool, StringToolOutput
from beeai_framework.tools.types import ToolRunOptions
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param1: str = Field(description="Parameter description")

@tool(description="Tool description")
async def my_new_tool(input: MyToolInput, options: ToolRunOptions) -> StringToolOutput:
    # Implementation
    result = f"Result for {input.param1}"
    return StringToolOutput(result)
```

2. Add to `tools/__init__.py`:

```python
from .my_new_tool import my_new_tool

__all__ = [
    # ... existing tools ...
    "my_new_tool",
]
```

3. Register in `mcp_server.py`:

```python
from tools import (
    # ... existing imports ...
    my_new_tool,
)

all_tools = [
    # ... existing tools ...
    my_new_tool,
]
```

4. Document in `docs/tools.md`

### Testing

```bash
# Test individual tools
cd tests
pytest test_list_properties.py -v

# Test all tools
pytest -v

# Test MCP server
python mcp_server.py
# In another terminal:
curl http://localhost:8001/health
```

## Troubleshooting

### Server Won't Start

**Problem**: `ModuleNotFoundError: No module named 'beeai_framework'`

**Solution**:
```bash
source dev-setup.sh
pip install -r requirements.txt
```

### Tools Return Authentication Errors

**Problem**: `401 Unauthorized`

**Solution**: Check environment variables:
```bash
echo $API_URL
echo $AUTH_TOKEN
# Make sure .env is loaded
source dev-setup.sh
```

### Connection Refused

**Problem**: Can't connect to port 8001

**Solution**:
1. Check if server is running: `ps aux | grep mcp_server`
2. Check port availability: `lsof -i :8001`
3. Try restarting the server

### Tools Return Empty Results

**Problem**: Tools return `[]` or empty responses

**Solution**:
1. Check `SITE_ID` environment variable matches your API data
2. Verify API backend is running and accessible
3. Test API endpoints directly with curl

## Production Deployment

### Using Docker

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV API_URL=https://your-api.com
ENV AUTH_TOKEN=your_token
ENV SITE_ID=3

EXPOSE 8001

CMD ["python", "mcp_server.py"]
```

```bash
# Build and run
docker build -t realtyiq-mcp-server .
docker run -p 8001:8001 --env-file .env realtyiq-mcp-server
```

### Using systemd

```ini
# /etc/systemd/system/realtyiq-mcp.service
[Unit]
Description=RealtyIQ MCP Server
After=network.target

[Service]
Type=simple
User=realtyiq
WorkingDirectory=/opt/realtyiq
EnvironmentFile=/opt/realtyiq/.env
ExecStart=/opt/realtyiq/venv/bin/python mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable realtyiq-mcp
sudo systemctl start realtyiq-mcp
sudo systemctl status realtyiq-mcp
```

## Performance

### Benchmarks

Typical response times (local development):
- `list_properties`: ~50-200ms
- `get_property_detail`: ~30-100ms
- `auction_dashboard`: ~100-300ms
- `list_available_tools`: ~5-10ms

### Optimization Tips

1. **Connection Pooling**: The server reuses connections to the API
2. **Caching**: Consider implementing Redis caching for frequently accessed data
3. **Rate Limiting**: Add rate limiting for production deployments
4. **Concurrent Requests**: The server handles concurrent requests efficiently

## Security

### Authentication

- All tools use Token authentication against the RealtyIQ API
- Tokens are passed via `Authorization: Token {AUTH_TOKEN}` header
- Never commit `.env` files with real tokens

### Best Practices

1. **Use HTTPS** in production (set `TLS_VERIFY=true`)
2. **Rotate tokens** regularly
3. **Limit permissions** - use read-only tokens when possible
4. **Monitor usage** - track API calls and tool usage
5. **Firewall** - restrict MCP server access to trusted clients

## Monitoring

### Health Check

```bash
# Check if server is running
curl http://localhost:8001/health

# Expected response: 200 OK
```

### Logs

The server outputs logs to stdout:
```
🚀 RealtyIQ MCP Server starting on port 8001
📊 Registered 16 tools
[2026-02-16 10:30:00] INFO: Tool called: list_properties
[2026-02-16 10:30:00] INFO: Response: 200 OK (150ms)
```

### Metrics

Track these metrics for production:
- Tool call counts
- Response times
- Error rates
- API token usage

## Related Documentation

- **[tools.md](tools.md)** - Complete tool reference with parameters and examples
- **[SPECS.md](SPECS.md)** - Overall project specifications
- **[API Documentation](../Api/README.md)** - Backend API reference

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [tools.md](tools.md) for tool-specific documentation
3. Check server logs for error messages
4. Verify environment variables are set correctly

---

**Version**: 1.0.0  
**Last Updated**: February 16, 2026  
**Maintainer**: RealtyIQ Team
