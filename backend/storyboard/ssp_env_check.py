import os, json

keys = {
  'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY')),
  'ENABLE_ANTHROPIC_PLANNER': os.getenv('ENABLE_ANTHROPIC_PLANNER'),
  'PEXELS_API_KEY': bool(os.getenv('PEXELS_API_KEY') or os.getenv('PEXELS_KEY')),
  'PIXABAY_API_KEY': bool(os.getenv('PIXABAY_API_KEY') or os.getenv('PIXABAY_KEY')),
  'PLAYWRIGHT_SANDBOX_PROFILE': bool(os.getenv('PLAYWRIGHT_SANDBOX_PROFILE')),
}

print(json.dumps(keys))
