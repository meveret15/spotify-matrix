# Simple test file
from platformdirs import user_cache_dir
print("Successfully imported platformdirs")
cache_dir = user_cache_dir("test", "test")
print(f"Cache directory: {cache_dir}") 