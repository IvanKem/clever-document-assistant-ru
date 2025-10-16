---
base_model: unsloth/qwen2.5-vl-32b-instruct-bnb-4bit
library_name: peft
model_name: qwen2.5-vl-32b-ft
tags:
- base_model:adapter:unsloth/qwen2.5-vl-32b-instruct-bnb-4bit
- lora
- sft
- transformers
- trl
- unsloth
licence: license
pipeline_tag: text-generation
---

# Model Card for qwen2.5-vl-32b-ft

This model is a fine-tuned version of [unsloth/qwen2.5-vl-32b-instruct-bnb-4bit](https://huggingface.co/unsloth/qwen2.5-vl-32b-instruct-bnb-4bit).
It has been trained using [TRL](https://github.com/huggingface/trl).

## Model Repository

**Full model weights and configuration available at:**  
**[IvanKem/Qwen2.5-VL-32-unsloth-4bit-ft](https://huggingface.co/IvanKem/Qwen2.5-VL-32-unsloth-4bit-ft)**

## Quick start

```python
from transformers import pipeline

question = "If you had a time machine, but could only go to the past or the future once and never return, which would you choose and why?"
generator = pipeline("text-generation", model="IvanKem/Qwen2.5-VL-32-unsloth-4bit-ft", device="cuda")
output = generator([{"role": "user", "content": question}], max_new_tokens=128, return_full_text=False)[0]
print(output["generated_text"])
```

## Training procedure

 


This model was trained with SFT.

### Framework versions

- PEFT 0.17.1
- TRL: 0.23.0
- Transformers: 4.56.2
- Pytorch: 2.8.0
- Datasets: 4.2.0
- Tokenizers: 0.22.1

## Citations



Cite TRL as:
    
```bibtex
@misc{vonwerra2022trl,
	title        = {{TRL: Transformer Reinforcement Learning}},
	author       = {Leandro von Werra and Younes Belkada and Lewis Tunstall and Edward Beeching and Tristan Thrush and Nathan Lambert and Shengyi Huang and Kashif Rasul and Quentin Gallou{\'e}dec},
	year         = 2020,
	journal      = {GitHub repository},
	publisher    = {GitHub},
	howpublished = {\url{https://github.com/huggingface/trl}}
}
```
