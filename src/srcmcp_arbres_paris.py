# src/mcp_arbres_paris.py
import os
from typing import Optional, Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Paris Trees")

# Base configuration
BASE_URL = "https://opendata.paris.fr/api/explore/v2.1"
DATASET_ID = "les-arbres"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

async def make_api_request(
    endpoint: str,
    params: Optional[dict] = None
) -> dict[str, Any]:
    """Make async request to OpenDataSoft API."""
    url = f"{BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_dataset_info() -> str:
    """
    Get metadata and information about the Paris trees dataset.
    Returns details about available fields, number of records, and dataset description.
    """
    try:
        result = await make_api_request(f"/catalog/datasets/{DATASET_ID}")
        
        dataset = result.get("dataset", {})
        info = {
            "dataset_id": dataset.get("dataset_id"),
            "title": dataset.get("metas", {}).get("default", {}).get("title"),
            "description": dataset.get("metas", {}).get("default", {}).get("description"),
            "records_count": dataset.get("metas", {}).get("default", {}).get("records_count"),
            "fields": [
                {
                    "name": field.get("name"),
                    "label": field.get("label"),
                    "type": field.get("type"),
                    "description": field.get("description")
                }
                for field in dataset.get("fields", [])
            ]
        }
        
        return f"""Paris Trees Dataset Information:
        
Title: {info['title']}
Total Records: {info['records_count']:,}

Description: {info['description']}

Available Fields:
{chr(10).join(f"  - {f['name']} ({f['type']}): {f.get('label', 'N/A')}" for f in info['fields'][:15])}
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
    
    Args:
        where: Filter query (e.g., "arrondissement='PARIS 1ER ARR' AND hauteur > 20")
        limit: Number of records to return (max 100, default 20)
        select: Comma-separated fields to return (e.g., "libellefrancais,genre,hauteur,adresse")
        offset: Pagination offset for retrieving more results
        order_by: Field to sort by (e.g., "hauteur DESC")
    
    Examples:
        - Find tall trees: where="hauteur > 25"
        - Find trees in specific district: where="arrondissement='PARIS 5E ARR'"
        - Find specific species: where="libellefrancais='Marronnier'"
    """
    try:
        params = {
            "limit": min(limit, MAX_LIMIT),
            "offset": offset
        }
        
        if where:
            params["where"] = where
        if select:
            params["select"] = select
        if order_by:
            params["order_by"] = order_by
        
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        total_count = result.get("total_count", 0)
        records = result.get("results", [])
        
        if not records:
            return "No trees found matching your criteria."
        
        output = [f"Found {total_count:,} trees total. Showing {len(records)} results (offset: {offset}):\n"]
        
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            tree_info = [
                f"\n{i}. Tree Information:",
                f"   Species: {fields.get('libellefrancais', 'Unknown')}",
                f"   Genus: {fields.get('genre', 'N/A')}",
                f"   Height: {fields.get('hauteur', 'N/A')} m",
                f"   Circumference: {fields.get('circonference', 'N/A')} cm",
                f"   District: {fields.get('arrondissement', 'N/A')}",
                f"   Address: {fields.get('adresse', 'N/A')}",
                f"   Stage of Development: {fields.get('stadedeveloppement', 'N/A')}",
            ]
            
            if 'geom' in fields and fields['geom']:
                coords = fields['geom'].get('geometry', {}).get('coordinates', [])
                if coords:
                    tree_info.append(f"   Coordinates: {coords[1]:.6f}, {coords[0]:.6f}")
            
            output.append("\n".join(tree_info))
        
        if total_count > offset + len(records):
            output.append(f"\n📄 Use offset={offset + limit} to see more results.")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error searching trees: {str(e)}"


@mcp.tool()
async def get_tree_statistics(
    group_by: str,
    where: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Get aggregated statistics about Paris trees grouped by a specific field.
    
    Args:
        group_by: Field to group by (e.g., "arrondissement", "libellefrancais", "genre", "stadedeveloppement")
        where: Optional filter to apply before aggregation
        limit: Number of groups to return (default 20)
    
    Examples:
        - Trees per district: group_by="arrondissement"
        - Most common species: group_by="libellefrancais"
        - Trees by genus: group_by="genre"
    """
    try:
        params = {
            "group_by": group_by,
            "limit": limit,
            "order_by": "count DESC"
        }
        
        if where:
            params["where"] = where
        
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        records = result.get("results", [])
        
        if not records:
            return f"No statistics found for grouping by '{group_by}'."
        
        output = [f"Statistics grouped by '{group_by}':\n"]
        
        for i, record in enumerate(records, 1):
            group_value = record.get(group_by, "Unknown")
            count = record.get("count", 0)
            output.append(f"{i:2d}. {group_value}: {count:,} trees")
        
        total = sum(r.get("count", 0) for r in records)
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
    Find trees near a specific location in Paris.
    
    Args:
        latitude: Latitude coordinate (e.g., 48.8566 for Paris center)
        longitude: Longitude coordinate (e.g., 2.3522 for Paris center)
        distance_meters: Search radius in meters (default 500m)
        limit: Maximum number of trees to return
    
    Example:
        - Find trees near Eiffel Tower: latitude=48.8584, longitude=2.2945
        - Find trees near Notre-Dame: latitude=48.8530, longitude=2.3499
    """
    try:
        # OpenDataSoft uses distance function in where clause
        where_clause = f"distance(geom, geom'POINT({longitude} {latitude})', {distance_meters}m)"
        
        params = {
            "where": where_clause,
            "limit": min(limit, MAX_LIMIT),
            "order_by": f"distance(geom, geom'POINT({longitude} {latitude})') ASC"
        }
        
        result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params=params
        )
        
        records = result.get("results", [])
        
        if not records:
            return f"No trees found within {distance_meters}m of coordinates ({latitude}, {longitude})."
        
        output = [f"Found {len(records)} trees within {distance_meters}m of ({latitude:.6f}, {longitude:.6f}):\n"]
        
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            tree_coords = fields.get('geom', {}).get('geometry', {}).get('coordinates', [None, None])
            
            output.append(f"""
{i}. {fields.get('libellefrancais', 'Unknown')}
   Height: {fields.get('hauteur', 'N/A')} m
   Address: {fields.get('adresse', 'N/A')}
   District: {fields.get('arrondissement', 'N/A')}
   Coordinates: {tree_coords[1]:.6f}, {tree_coords[0]:.6f}""")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error finding nearby trees: {str(e)}"


@mcp.tool()
async def get_tree_species_info(species_name: str) -> str:
    """
    Get detailed information about a specific tree species in Paris.
    
    Args:
        species_name: French name of the species (e.g., "Marronnier", "Platane", "Tilleul")
    
    Returns information about all trees of that species including count, locations, and characteristics.
    """
    try:
        # First, get count and basic stats
        where_clause = f"libellefrancais='{species_name}'"
        
        stats_result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params={
                "where": where_clause,
                "group_by": "arrondissement",
                "limit": 20,
                "order_by": "count DESC"
            }
        )
        
        # Then get some example trees
        examples_result = await make_api_request(
            f"/catalog/datasets/{DATASET_ID}/records",
            params={
                "where": where_clause,
                "limit": 5,
                "order_by": "hauteur DESC"
            }
        )
        
        stats = stats_result.get("results", [])
        examples = examples_result.get("results", [])
        
        if not stats and not examples:
            return f"No trees found for species '{species_name}'. Please check the spelling."
        
        total_count = sum(s.get("count", 0) for s in stats)
        
        output = [f"Information about '{species_name}' in Paris:\n"]
        output.append(f"Total count: {total_count:,} trees\n")
        
        if stats:
            output.append("Distribution by district:")
            for stat in stats[:10]:
                district = stat.get("arrondissement", "Unknown")
                count = stat.get("count", 0)
                output.append(f"  - {district}: {count:,} trees")
        
        if examples:
            output.append(f"\nTallest examples:")
            for i, tree in enumerate(examples, 1):
                fields = tree.get("fields", {})
                output.append(f"""
  {i}. Height: {fields.get('hauteur', 'N/A')} m
     Location: {fields.get('adresse', 'N/A')}
     District: {fields.get('arrondissement', 'N/A')}
     Circumference: {fields.get('circonference', 'N/A')} cm""")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error getting species info: {str(e)}"


if __name__ == "__main__":
    mcp.run()