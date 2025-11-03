from typing import List, Any

def chunk_list(data: list, size: int) -> List[List[Any]]:
    """
    Splits a list into chunks of a specified size. 
    Used for batching API requests to comply with rate limits.
    """
    return [data[i:i + size] for i in range(0, len(data), size)]