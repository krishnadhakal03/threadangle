import os
import requests

RUNWAYML_API_KEY = os.getenv("RUNWAYML_API_KEY")

# Example prompt and parameters
data = {
    "prompt": "A cinematic cityscape at sunset, trending on artstation",
    "num_frames": 24,
    "seed": 42,
    "motion": "cinematic"
}

headers = {
    "Authorization": f"Bearer {RUNWAYML_API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.runwayml.com/v1/generate/video",
    json=data,
    headers=headers
)

if response.status_code == 200:
    with open("runwayml_sample.mp4", "wb") as f:
        f.write(response.content)
    print("Video saved as runwayml_sample.mp4")
else:
    print(f"Error: {response.status_code}", response.text)
