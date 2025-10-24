# test_mcp.py
import asyncio
import sys
sys.path.insert(0, 'src')

from mcp_arbres_paris import (
    get_dataset_info,
    search_trees,
    get_tree_statistics,
    find_trees_near_location,
    get_tree_species_info
)

async def test_all_functions():
    print("=" * 60)
    print("Testing MCP Arbres Paris Server")
    print("=" * 60)
    
    # Test 1: Get dataset info
    print("\n1. Testing get_dataset_info...")
    result = await get_dataset_info()
    print(result[:500] + "...\n")
    
    # Test 2: Search trees
    print("\n2. Testing search_trees (trees taller than 30m)...")
    result = await search_trees(where="hauteur > 30", limit=5)
    print(result[:800] + "...\n")
    
    # Test 3: Get statistics
    print("\n3. Testing get_tree_statistics (by arrondissement)...")
    result = await get_tree_statistics(group_by="arrondissement", limit=10)
    print(result[:600] + "...\n")
    
    # Test 4: Find trees near location (Notre-Dame)
    print("\n4. Testing find_trees_near_location (near Notre-Dame)...")
    result = await find_trees_near_location(
        latitude=48.8530,
        longitude=2.3499,
        distance_meters=200,
        limit=5
    )
    print(result[:600] + "...\n")
    
    # Test 5: Get species info
    print("\n5. Testing get_tree_species_info (Platane)...")
    result = await get_tree_species_info(species_name="Platane")
    print(result[:600] + "...\n")
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_functions())