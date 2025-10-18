---
base_model: microsoft/Florence-2-large
library_name: transformers
model_name: florence-2-vl-large
tags:
- base_model:microsoft/Florence-2-large
- vision-language
- document-ai
- visual-question-answering
- transformers
license: other
pipeline_tag: visual-question-answering
---

# Model Card for florence-2-vl-large

This model is a fine-tuned version of [microsoft/Florence-2-large](https://huggingface.co/microsoft/Florence-2-large) for document understanding and visual question answering tasks.

## Quick start

```python
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

model_name = "your-username/florence-2-vl-large"
processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    trust_remote_code=True
).to("cuda")

# Document question answering
prompt = "<MORE>What information is in this document?</MORE>"
inputs = processor(text=prompt, images=document_image, return_tensors="pt").to("cuda")

generated_ids = model.generate(
    **inputs,
    max_new_tokens=256,
    do_sample=False,
    num_beams=3
)

generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
parsed_answer = processor.post_process_generation(generated_text, task="<MORE>")
print(parsed_answer)
