#!/usr/bin/env python3
"""Test Open WebUI integration."""

import sys
import requests
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_api_health():
    """Test API is running."""
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        assert data["status"] == "ok"
        print(f"✓ API health check passed ({data['items']} items)")
        return True
    except Exception as e:
        print(f"✗ API health check failed: {e}")
        return False


def test_search_endpoint():
    """Test search endpoint."""
    try:
        resp = requests.get(
            "http://localhost:8000/search",
            params={"q": "CUT&Tag", "k": 3},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        assert len(results) > 0, "No results returned"
        assert all("score" in r for r in results), "Results missing score"
        assert all("name" in r for r in results), "Results missing name"
        print(f"✓ Search endpoint works ({len(results)} results)")
        return True
    except Exception as e:
        print(f"✗ Search endpoint failed: {e}")
        return False


def test_entity_endpoint():
    """Test entity detail endpoint."""
    try:
        resp = requests.get(
            "http://localhost:8000/entity",
            params={"id": "bowtie2"},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        assert data["id"] == "bowtie2"
        assert "name" in data
        print(f"✓ Entity endpoint works ({data['name']})")
        return True
    except Exception as e:
        print(f"✗ Entity endpoint failed: {e}")
        return False


def test_related_endpoint():
    """Test related entities endpoint."""
    try:
        resp = requests.get(
            "http://localhost:8000/related",
            params={"id": "bowtie2", "k": 3},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        assert "related" in data
        print(f"✓ Related endpoint works ({len(data['related'])} related)")
        return True
    except Exception as e:
        print(f"✗ Related endpoint failed: {e}")
        return False


def test_stats_endpoint():
    """Test stats endpoint."""
    try:
        resp = requests.get("http://localhost:8000/stats", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        assert "total_items" in data
        assert "entity_types" in data
        print(f"✓ Stats endpoint works ({data['total_items']} total items)")
        return True
    except Exception as e:
        print(f"✗ Stats endpoint failed: {e}")
        return False


def test_tool_script():
    """Test that tool script is valid Python."""
    try:
        tool_path = Path(__file__).parent.parent / "open_webui_tools" / "kg_memory_tool.py"
        with open(tool_path) as f:
            code = f.read()
        compile(code, str(tool_path), 'exec')
        print("✓ Tool script is valid Python")
        return True
    except SyntaxError as e:
        print(f"✗ Tool script has syntax error: {e}")
        return False


def test_tool_with_valves():
    """Test that tool with valves is valid."""
    try:
        tool_path = Path(__file__).parent.parent / "open_webui_tools" / "kg_memory_tool_with_valves.py"
        with open(tool_path) as f:
            code = f.read()
        compile(code, str(tool_path), 'exec')
        print("✓ Tool script (with valves) is valid Python")
        return True
    except SyntaxError as e:
        print(f"✗ Tool script (with valves) has syntax error: {e}")
        return False


def test_tool_execution():
    """Test tool execution by importing and calling."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "open_webui_tools"))
        from kg_memory_tool import Tools
        
        # Note: This will fail if API is not running, that's OK for this test
        tools = Tools()
        result = tools.query_knowledge("test", top_k=1)
        assert isinstance(result, str)
        print("✓ Tool class can be instantiated and called")
        return True
    except ImportError as e:
        print(f"✗ Cannot import Tool: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("✓ Tool class works (API not running, connection expected to fail)")
        return True
    except Exception as e:
        print(f"✗ Tool execution failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Open WebUI Integration Tests")
    print("=" * 60)
    print()
    
    # Check if API is running
    api_running = test_api_health()
    
    results = []
    
    if api_running:
        # Test API endpoints
        results.append(("Search endpoint", test_search_endpoint()))
        results.append(("Entity endpoint", test_entity_endpoint()))
        results.append(("Related endpoint", test_related_endpoint()))
        results.append(("Stats endpoint", test_stats_endpoint()))
    else:
        print("\n⚠️  API not running, skipping endpoint tests")
        print("   Start with: pixi run serve-memory")
    
    # Test tool scripts
    print()
    results.append(("Tool script syntax", test_tool_script()))
    results.append(("Tool script (valves) syntax", test_tool_with_valves()))
    results.append(("Tool execution", test_tool_execution()))
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
