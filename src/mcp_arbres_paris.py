"""
Paris Trees MCP Server
======================

A Model Context Protocol (MCP) server that provides tools to query and analyze 
the Paris trees dataset from OpenDataSoft's Open Data platform.

This server enables:
- Searching trees with various filters (species, height, location, remarkable status)
- Statistical aggregations by district, species, genus, etc.
- Geographic searches to find trees near specific coordinates
- Detailed species information with distribution analysis
- Discovery of remarkable heritage trees

API: OpenDataSoft Explore API v2.1
Dataset: https://opendata.paris.fr/explore/dataset/les-arbres/

Author: mfnunez
Repository: https://github.com/mfnunez/mcp-arbres-paris-open-data
"""

import os
from typing import Optional, Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Paris Trees")

# API Configuration
BASE_URL = "https://opendata.paris.fr/api/explore/v2.1"
DATASET_ID = "les-arbres"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


async def make_api_request(
    endpoint: str,
    params: Optional[dict] = None
) -> dict[str, Any]:
    """
    Make an asynchronous HTTP GET request to the OpenDataSoft API.
    
    Args:
        endpoint: API endpoint path (e.g., "/catalog/datasets/les-arbres/records")
        params: Optional dictionary of query parameters
        
    Returns:
        JSON response as a dictionary
        
    Raises:
        httpx.HTTPStatusError: If the request fails
    """
    url = f"{BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_dataset_info() -> str:
    """
    Get metadata and information about the Paris trees dataset.
    
    Returns details about:
    - Dataset title and description
    - Total number of records
    - Available fields with their types and labels
    
    This is useful for understanding the dataset structure and available fields
    before making more specific queries.
    
    Returns:
        Formatted string with dataset information
    """
    try:
        # Fetch dataset metadata from the catalog endpoint
        result = await make_api_request(f"/catalog/datasets/{DATASET_ID}")
        
        # Extract dataset and metadata information
        dataset = result.get("dataset", {})
        metas = dataset.get("metas", {}).get("default", {})
        
        # Extract info with safe defaults to prevent None formatting errors
        title = metas.get("title") or "N/A"
        description = metas.get("description") or "N/A"
        records_count = metas.get("records_count") or 0
        fields = dataset.get("fields", [])
        
        # Build a formatted list of the first 15 fields
        fields_text = '\n'.join(
            f"  - {f.get('name', 'N/A')} ({f.get('type', 'N/A')}): {f.get('label', 'N/A')}" 
            for f in fields[:15]
        )
        
        return f"""Paris Trees Dataset Information:
        
Title: {title}
Total Records: {records_count:,}

Description: {description}

Available Fields:
{fields_text}
... and more fields available.
"""
    except Exception as e:
        return f"Error fetching dataset info: {str(e)}"


@mcp.tool()
async def search_trees(
    where: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    select: Optional[str] = None,
    order_by: Optional[str] = None
) -> str:
    """
    Search and retrieve Paris trees data with filtering and pagination.
    
    This is the most versatile tool for querying the trees dataset. It supports:
    - Filtering by any field using SQL-like WHERE clauses
    - Selecting specific fields to return
    - Sorting results by any field
    - Pagination for large result sets
    
    Args:
        where: Filter query using ODSQL syntax 
               Examples: 
               - "arrondissement='PARIS 1ER ARR' AND hauteurenm > 20"
               - "libellefrancais='Platane'"
               - "remarquable='OUI'"
        limit: Number of records to return (max 100, default 20)
        select: Comma-separated fields to return 
                Example: "libellefrancais,genre,hauteurenm,adresse"
        offset: Pagination offset for retrieving more results (default 0)
        order_by: Field to sort by with optional direction
                  Examples: "hauteurenm DESC", "libellefrancais ASC"
    
    Common Field Names:
        - libellefrancais: French species name
        - genre: Genus
        - hauteurenm: Height in meters
        - circonferenceencm: Circumference in centimeters
        - arrondissement: District
        - adresse: Address
        - stadedeveloppement: Development stage
        - remarquable: Remarkable status ('OUI' or empty)
    
    Examples:
        - Find tall trees: where="hauteurenm > 25"
        - Find trees in specific district: where="arrondissement='PARIS 5E ARR'"
        - Find specific species: where="libellefrancais='Marronnier'"
        - Remarkable trees only: where="remarquable='OUI'"
        
    Returns:
        Formatted string with tree information including species, dimensions,
        location, and remarkable status when applicable
    """
    try:
        # Build query parameters
        params = {
            "limit": min(limit, MAX_LIMIT),
            "offset": offset
        }
        
        # Add optional parameters if provided
        if where:
            params["where"] = where
        if select:
            params["select"] = select
        if order_by:
            params["order_by"] = order_by
        
        # Make API request to records endpoint
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        total_count = result.get("total_count", 0)
        records = result.get("results", [])
        
        if not records:
            return "No trees found matching your criteria."
        
        output = [f"Found {total_count:,} trees total. Showing {len(records)} results (offset: {offset}):\n"]
        
        # Format each tree record
        for i, record in enumerate(records, 1):
            # IMPORTANT: In API v2.1, data is directly in the record object,
            # not in record["fields"] like in v1.x
            tree_info = [
                f"\n{i}. Tree Information:",
                f"   Species: {record.get('libellefrancais', 'Unknown')}",
                f"   Genus: {record.get('genre', 'N/A')}",
                f"   Height: {record.get('hauteurenm', 'N/A')} m",
                f"   Circumference: {record.get('circonferenceencm', 'N/A')} cm",
                f"   District: {record.get('arrondissement', 'N/A')}",
                f"   Address: {record.get('adresse', 'N/A')}",
                f"   Stage of Development: {record.get('stadedeveloppement', 'N/A')}",
            ]
            
            # Add remarkable status indicator if tree is heritage-listed
            remarquable = record.get('remarquable', '')
            if remarquable and remarquable.lower() == 'oui':
                tree_info.append(f"   🌟 Remarkable Tree: Yes (heritage tree)")
            
            # Add geographic coordinates if available
            if 'geo_point_2d' in record and record['geo_point_2d']:
                coords = record['geo_point_2d']
                if 'lat' in coords and 'lon' in coords:
                    tree_info.append(f"   Coordinates: {coords['lat']:.6f}, {coords['lon']:.6f}")
            
            output.append("\n".join(tree_info))
        
        # Add pagination hint if there are more results
        if total_count > offset + len(records):
            output.append(f"\n📄 Use offset={offset + limit} to see more results.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error searching trees: {str(e)}\nDebug info: {type(e).__name__}"


@mcp.tool()
async def get_tree_statistics(
    group_by: str,
    where: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Get aggregated statistics about Paris trees grouped by a specific field.
    
    This tool performs GROUP BY aggregations to count trees by category.
    Useful for understanding the distribution and composition of Paris's urban forest.
    
    IMPORTANT: In API v2.1, aggregations require a SELECT clause with an 
    aggregation function (count, sum, avg, etc.) along with the GROUP BY.
    
    Args:
        group_by: Field to group by. Common options:
                  - "arrondissement": Trees per district
                  - "libellefrancais": Trees per species
                  - "genre": Trees per genus
                  - "stadedeveloppement": Trees per development stage
        where: Optional filter to apply before aggregation
               Example: "hauteurenm > 20" to only count tall trees
        limit: Number of groups to return (default 20)
    
    Examples:
        - Trees per district: group_by="arrondissement"
        - Most common species: group_by="libellefrancais"
        - Trees by genus: group_by="genre"
        - Remarkable trees by species: group_by="libellefrancais", where="remarquable='OUI'"
        
    Returns:
        Formatted string with counts per group, sorted by count descending
    """
    try:
        # Build query parameters with required SELECT clause for v2.1 API
        params = {
            "select": f"{group_by}, count(*) as tree_count",
            "group_by": group_by,
            "limit": limit,
            "order_by": "tree_count DESC"
        }
        
        # Add optional WHERE filter
        if where:
            params["where"] = where
        
        # Make API request
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        records = result.get("results", [])
        
        if not records:
            return f"No statistics found for grouping by '{group_by}'."
        
        output = [f"Statistics grouped by '{group_by}':\n"]
        
        # Format each group with its count
        for i, record in enumerate(records, 1):
            group_value = record.get(group_by, "Unknown")
            count = record.get("tree_count", 0)
            output.append(f"{i:2d}. {group_value}: {count:,} trees")
        
        # Add total across displayed groups
        total = sum(r.get("tree_count", 0) for r in records)
        output.append(f"\nTotal in these groups: {total:,} trees")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error getting statistics: {str(e)}"


@mcp.tool()
async def find_trees_near_location(
    latitude: float,
    longitude: float,
    distance_meters: int = 500,
    limit: int = 20
) -> str:
    """
    Find trees near a specific geographic location in Paris.
    
    Uses the OpenDataSoft distance() function to perform geographic searches
    within a specified radius from a point.
    
    Args:
        latitude: Latitude coordinate in WGS84 (decimal degrees)
                  Example: 48.8566 for Paris center
        longitude: Longitude coordinate in WGS84 (decimal degrees)
                   Example: 2.3522 for Paris center
        distance_meters: Search radius in meters (default 500m)
        limit: Maximum number of trees to return (default 20)
    
    Famous Paris Locations:
        - Eiffel Tower: latitude=48.8584, longitude=2.2945
        - Notre-Dame: latitude=48.8530, longitude=2.3499
        - Arc de Triomphe: latitude=48.8738, longitude=2.2950
        - Louvre: latitude=48.8606, longitude=2.3376
        
    Returns:
        Formatted list of trees sorted by distance from the specified point,
        including species, height, address, and coordinates
    """
    try:
        # Build WHERE clause using OpenDataSoft's distance() function
        # Syntax: distance(geo_field, geom'POINT(lon lat)', radius)
        where_clause = f"distance(geo_point_2d, geom'POINT({longitude} {latitude})', {distance_meters}m)"
        
        params = {
            "where": where_clause,
            "limit": min(limit, MAX_LIMIT),
            # Order by distance (ascending = nearest first)
            "order_by": f"distance(geo_point_2d, geom'POINT({longitude} {latitude})') ASC"
        }
        
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        records = result.get("results", [])
        
        if not records:
            return f"No trees found within {distance_meters}m of coordinates ({latitude}, {longitude})."
        
        output = [f"Found {len(records)} trees within {distance_meters}m of ({latitude:.6f}, {longitude:.6f}):\n"]
        
        # Format each nearby tree
        for i, record in enumerate(records, 1):
            # Extract coordinates
            coords = record.get('geo_point_2d', {})
            lat = coords.get('lat', 'N/A')
            lon = coords.get('lon', 'N/A')
            
            # Add remarkable indicator if applicable
            remarquable_status = "🌟 (Remarkable)" if record.get('remarquable', '').lower() == 'oui' else ""
            
            output.append(f"""
{i}. {record.get('libellefrancais', 'Unknown')} {remarquable_status}
   Height: {record.get('hauteurenm', 'N/A')} m
   Address: {record.get('adresse', 'N/A')}
   District: {record.get('arrondissement', 'N/A')}
   Coordinates: {lat}, {lon}""")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error finding nearby trees: {str(e)}"


@mcp.tool()
async def find_remarkable_trees(
    limit: int = 20,
    arrondissement: Optional[str] = None
) -> str:
    """
    Find remarkable (heritage) trees in Paris.
    
    Remarkable trees are distinguished by their singularity, morphology, identity,
    or social role. They are part of Paris's natural, cultural, and landscape heritage.
    
    These trees have special protection status and are often exceptional specimens
    in terms of age, size, rarity, or historical significance.
    
    Args:
        limit: Maximum number of trees to return (default 20)
        arrondissement: Optional filter by district
                        Example: "PARIS 5E ARR", "BOIS DE BOULOGNE"
    
    Returns:
        List of remarkable trees sorted by height (tallest first),
        including detailed information about each tree's characteristics
        
    Examples:
        - Find all remarkable trees: (no parameters)
        - Find remarkable trees in 5th district: arrondissement="PARIS 5E ARR"
        - Find top 50 tallest remarkable trees: limit=50
    """
    try:
        # Build WHERE clause for remarkable trees
        where_clause = "remarquable='OUI'"
        if arrondissement:
            where_clause += f" AND arrondissement='{arrondissement}'"
        
        params = {
            "where": where_clause,
            "limit": min(limit, MAX_LIMIT),
            # Sort by height descending to show most impressive trees first
            "order_by": "hauteurenm DESC"
        }
        
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        total_count = result.get("total_count", 0)
        records = result.get("results", [])
        
        if not records:
            return "No remarkable trees found matching your criteria."
        
        output = [
            f"🌟 Found {total_count:,} remarkable trees in Paris",
            f"Showing {len(records)} results:\n"
        ]
        
        # Format each remarkable tree with full details
        for i, record in enumerate(records, 1):
            output.append(f"""
{i}. {record.get('libellefrancais', 'Unknown')} 🌟
   Height: {record.get('hauteurenm', 'N/A')} m
   Circumference: {record.get('circonferenceencm', 'N/A')} cm
   Address: {record.get('adresse', 'N/A')}
   District: {record.get('arrondissement', 'N/A')}
   Stage: {record.get('stadedeveloppement', 'N/A')}""")
            
            # Add coordinates if available
            coords = record.get('geo_point_2d', {})
            if coords:
                lat = coords.get('lat', 'N/A')
                lon = coords.get('lon', 'N/A')
                output.append(f"   Coordinates: {lat}, {lon}")
        
        # Add info about remaining trees
        if total_count > len(records):
            output.append(f"\n📄 {total_count - len(records)} more remarkable trees available.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error finding remarkable trees: {str(e)}"


@mcp.tool()
async def get_tree_species_info(species_name: str) -> str:
    """
    Get detailed information about a specific tree species in Paris.
    
    This tool provides comprehensive statistics about a species including:
    - Total count across Paris
    - Geographic distribution by district
    - Examples of the tallest specimens
    - Remarkable (heritage) trees of this species
    
    Args:
        species_name: French name of the species (case-sensitive)
                      Common species:
                      - "Platane" (Plane tree)
                      - "Marronnier" (Horse chestnut)
                      - "Tilleul" (Linden)
                      - "Erable" (Maple)
                      - "Sophora" (Pagoda tree)
                      - "Chêne" (Oak)
                      - "Sequoia" (Sequoia)
    
    Returns:
        Detailed species report including:
        - Total count
        - Distribution across districts (top 10)
        - Tallest 5 examples with locations
        - Indication of remarkable specimens
        
    Note: The species name must match exactly as recorded in the dataset.
          Check get_tree_statistics(group_by="libellefrancais") for available species.
    """
    try:
        # Build WHERE clause to filter by species
        where_clause = f"libellefrancais='{species_name}'"
        
        # First query: Get distribution statistics by district
        # IMPORTANT: Use SELECT with count() aggregation for v2.1 API
        stats_result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params={
                "where": where_clause,
                "select": f"arrondissement, count(*) as tree_count",
                "group_by": "arrondissement",
                "limit": 20,
                "order_by": "tree_count DESC"
            }
        )
        
        # Second query: Get tallest examples of this species
        examples_result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params={
                "where": where_clause,
                "limit": 5,
                "order_by": "hauteurenm DESC"
            }
        )
        
        stats = stats_result.get("results", [])
        examples = examples_result.get("results", [])
        
        # Check if species exists in dataset
        if not stats and not examples:
            return f"No trees found for species '{species_name}'. Please check the spelling."
        
        # Calculate total count across all districts
        total_count = sum(s.get("tree_count", 0) for s in stats)
        
        output = [f"Information about '{species_name}' in Paris:\n"]
        output.append(f"Total count: {total_count:,} trees\n")
        
        # Display district distribution
        if stats:
            output.append("Distribution by district:")
            for stat in stats[:10]:  # Show top 10 districts
                district = stat.get("arrondissement", "Unknown")
                count = stat.get("tree_count", 0)
                output.append(f"  - {district}: {count:,} trees")
        
        # Display tallest examples
        if examples:
            output.append(f"\nTallest examples:")
            for i, tree in enumerate(examples, 1):
                # Add star indicator for remarkable trees
                remarquable_indicator = " 🌟" if tree.get('remarquable', '').lower() == 'oui' else ""
                output.append(f"""
  {i}. Height: {tree.get('hauteurenm', 'N/A')} m{remarquable_indicator}
     Location: {tree.get('adresse', 'N/A')}
     District: {tree.get('arrondissement', 'N/A')}
     Circumference: {tree.get('circonferenceencm', 'N/A')} cm""")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error getting species info: {str(e)}"


# Entry point for running the MCP server
if __name__ == "__main__":
    mcp.run()