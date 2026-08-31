import requests
from src.config.config_loader import config


def image_read(image: str) -> str:
    endpoint = config("AZURE_OPENAI_ENDPOINT")
    api_key = config("AZURE_OPENAI_API_KEY")
    deployment_name = config("DEPLOYMENT_NAME")
    api_version = config("API_version")

    url = f"{endpoint}openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"

    headers = {"Content-Type": "application/json", "api-key": api_key}

    data = {
        "messages": [
            {
                "role": "system",
                "content": "List only: question numbers and key points. Max 150 tokens.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image,
                            "detail": "low",  # 85 tokens vs 765
                        },
                    }
                ],
            },
        ],
        "max_tokens": 150,
        "temperature": 0,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return "[Image error]"
