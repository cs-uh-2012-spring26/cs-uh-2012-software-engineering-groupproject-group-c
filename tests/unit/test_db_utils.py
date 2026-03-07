import pytest
from app.db.utils import serialize_oid, serialize_item, serialize_items
from app.db.constants import ID

def test_serialize_oid():
    """Test that any object passed is converted to a string."""
    assert serialize_oid(123) == "123"
    assert serialize_oid("abc") == "abc"

def test_serialize_item_valid():
    """Test serialization of a single dictionary item."""
    # We use the ID constant to ensure we are testing the right key
    sample_item = {ID: 1001, "name": "Yoga Class"}
    result = serialize_item(sample_item)
    
    assert result[ID] == "1001"
    assert result["name"] == "Yoga Class"

def test_serialize_item_none():
    """Test that passing None returns None safely."""
    assert serialize_item(None) is None

def test_serialize_items_list():
    """Test serialization of a list of items."""
    sample_list = [
        {ID: 1, "task": "A"},
        {ID: 2, "task": "B"}
    ]
    results = serialize_items(sample_list)
    
    assert len(results) == 2
    assert results[0][ID] == "1"
    assert results[1][ID] == "2"