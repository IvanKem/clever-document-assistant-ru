---
# Model Card for florence-2-large-ft

This model is a fine-tuned version of [microsoft/Florence-2-large](https://huggingface.co/microsoft/Florence-2-large) for document understanding and visual question answering tasks.

## Model Description

Florence-2-large is a powerful vision foundation model that has been fine-tuned using full parameter fine-tuning (not LoRA) on custom training loops for enhanced document AI capabilities.

## Quick Start

```python
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

# Load model and processor
model_name = "your-username/florence-2-large-ft"
processor = AutoProcessor.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Prepare inputs for document understanding
prompt = "<OD>What is the total amount on this invoice?</OD>"
inputs = processor(images=document_image, text=prompt, return_tensors="pt").to(model.device)

# Generate response
generated_ids = model.generate(
    **inputs,
    max_new_tokens=256,
    do_sample=True,
    temperature=0.7
)

generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
print(generated_text)
```
