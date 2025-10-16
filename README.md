# clever-document-assistant-ru

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Documents AI assistant for visual question answering 

## Project Organization

```
clever-document-assistant-ru/
├── LICENSE
├── Makefile
├── README.md
├── requirements.txt
├── setup.cfg
├── pyproject.toml
│
├── docs/
│   └── index.md
│
├── models/
│   ├── pre_trained/
│   │   ├── florence_2_large/
│   │   │   ├── config.json
│   │   │   ├── preprocessor_config.json
│   │   │   ├── ...
│   │   │   ├── tokenizer_config.json
│   │   │   └── README.md
│   │   └── qwen2_5_vl_32B_Instruct/
│   │       ├── config.json
│   │       ├── tokenizer_config.json
│   │       ├── ...
│   │       ├── special_tokens_map.json
│   │       └── README.md
│   └── fine_tuned/
│       ├── florence_2_large/
│       │   ├── adapter_config.json
│       │   ├── ...
│       │   ├── training_args.json
│       │   └── README.md
│       └── qwen2_5_vl_32B_Instruct/
│           ├── adapter_config.json
│           ├── ...
│           ├── training_args.json
│           └── README.md
│
├── notebooks/
│   ├── qwen2_5_vl_32B_Instruct/
│   │   ├── data_processing/
│   │   │   └── 1.0-data-consolidation.ipynb
│   │   ├── training/
│   │   │   ├── 2.0-qwen-qlora-sft.ipynb
│   │   │   └── 2.1-qwen-qlora-grpo.ipynb
│   │   └── inference/
│   │       ├── 3.0-qwen-evaluation-vqa.ipynb
│   │       └── 3.1-qwen-evaluation-llm.ipynb
│   ├── florence_2_large/
│   │   ├── data_processing/
│   │   │   └── 4.0-data-syntesis.ipynb
│   │   ├── training/
│   │   │   └── 5.0-florence-finetuning.ipynb
│   │   └── inference/
│   │       ├── 6.0-florence-evaluation-test.ipynb
│   │       └── 6.1-florence-evaluation-wer-cer.ipynb
│   └── florence_2_vl/
│       └──  data_processing/
│           └── 7.0-data-syntesis.ipynb
│
├── references/
│   ├── papers/
│   │   ├── document_ai_comparative_study_layout_analysis.pdf
│   │   ├── enhancing_document_understanding_contrastive_learning.pdf
│   │   ├── florence_2_unified_vision_tasks.pdf
│   │   ├── florence_vl_depth_breadth_fusion.pdf
│   │   └── layoutlmv3_pretraining_document_ai.pdf
│   └── datasets/
│
├── reports/
│   └── figures/
│
└── clever_document_assistant_ru/
    ├── __init__.py
    └── bot/
        ├── telegram_bot.py
        └── inference_model.py
```

--------

