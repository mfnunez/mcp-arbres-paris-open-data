# MCP Arbres Paris Open Data

An MCP (Model Context Protocol) server that provides access to Paris trees data from the Open Data Paris API.

## Overview

This MCP server allows Claude Desktop (or any MCP client) to query and analyze data about all the trees in Paris, including species, locations, heights, and more.

## Features

- 🌳 **Dataset Information**: Get metadata about the Paris trees dataset
- 🔍 **Advanced Search**: Search trees with complex filters
- 📊 **Statistics**: Aggregate data by species, district, or other attributes
- 📍 **Location-based Search**: Find trees near specific coordinates
- 🌿 **Species Information**: Get detailed info about specific tree species

## Installation

### Prerequisites

- Python 3.10 or higher
- Claude Desktop application

### Setup

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/mcp-arbres-paris-open-data.git
cd mcp-arbres-paris-open-data
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Available Tools

1. **get_dataset_info**: Get metadata about the Paris trees dataset
2. **search_trees**: Search trees with filters and pagination
3. **get_tree_statistics**: Get aggregated statistics grouped by fields
4. **find_trees_near_location**: Find trees near specific coordinates
5. **get_tree_species_info**: Get detailed information about a species

### Example Queries

Ask Claude:
- "How many trees are there in Paris?"
- "Find all oak trees (Chêne) in the 5th arrondissement"
- "What are the tallest trees in Paris?"
- "Find trees near the Eiffel Tower"
- "Show me statistics about tree species in Paris"

## Configuration for Claude Desktop

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "paris-trees": {
      "command": "python",
      "args": [
        "C:/path/to/mcp-arbres-paris-open-data/src/mcp_arbres_paris.py"
      ]
    }
  }
}
```

## Data Source

Data is provided by [Open Data Paris](https://opendata.paris.fr/) through their OpenDataSoft API.

Dataset: [Les Arbres](https://opendata.paris.fr/explore/dataset/les-arbres/)

## API Reference

This server uses the OpenDataSoft Explore API v2.1:
- [API Documentation](https://help.opendatasoft.com/apis/ods-explore-v2/)
- [Console](https://opendata.paris.fr/api/explore/v2.1/console)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
```

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db