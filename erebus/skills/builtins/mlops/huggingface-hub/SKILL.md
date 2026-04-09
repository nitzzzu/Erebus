---
name: huggingface-hub
description: Interact with Hugging Face Hub — download/upload models and datasets, manage repos, deploy endpoints, query datasets.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["mlops", "huggingface", "models", "datasets", "deployment"]
required_environment_variables:
  - name: HF_TOKEN
    prompt: "Enter your Hugging Face token"
---

# Hugging Face Hub

Use this skill to interact with the Hugging Face Hub.

## When to Use

- User wants to find or download models
- User needs to upload a model or dataset
- User wants to deploy an inference endpoint
- User needs to query datasets with SQL

## CLI Usage

```bash
pip install huggingface_hub[cli]

# Login
huggingface-cli login --token $HF_TOKEN

# Download model
huggingface-cli download meta-llama/Llama-3-8B

# Upload model
huggingface-cli upload my-model ./model_dir

# Search models
huggingface-cli search models "text-generation" --sort downloads

# Dataset info
huggingface-cli dataset-info username/dataset-name
```

## Python API

```python
from huggingface_hub import HfApi

api = HfApi()
models = api.list_models(search="llama", sort="downloads")
```

## Process

1. **Identify**: What HF Hub operation is needed?
2. **Authenticate**: Ensure HF token is configured
3. **Execute**: Run the appropriate command
4. **Verify**: Confirm success
5. **Report**: Show results (model card, download path, etc.)
