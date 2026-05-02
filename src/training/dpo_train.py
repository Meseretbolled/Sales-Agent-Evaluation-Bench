import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from trl import DPOTrainer, DPOConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
TRAIN_FILE = "preferences_train.jsonl"
DEV_FILE = "preferences_dev.jsonl"
OUTPUT_DIR = "/content/drive/MyDrive/tenacious-bench-lora-v0.1" if os.path.exists("/content/drive") else "./outputs"

def train():
    # 1. Load Dataset
    print(f"Loading datasets from {TRAIN_FILE} and {DEV_FILE}...")
    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "test": DEV_FILE})

    # 2. BitsAndBytes Config for Colab T4
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load Model and Tokenizer
    print(f"Loading model: {MODEL_ID}...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    # 4. LoRA Config
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 5. DPO Config
    dpo_config = DPOConfig(
        output_dir=OUTPUT_DIR,
        beta=0.1,  # Standard DPO temperature
        learning_rate=5e-5,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        max_prompt_length=512,
        max_length=1024,
        num_train_epochs=3,
        logging_steps=10,
        eval_steps=50,
        evaluation_strategy="steps",
        save_strategy="steps",
        save_total_limit=3,
        bf16=True if torch.cuda.is_bf16_supported() else False,
        fp16=False if torch.cuda.is_bf16_supported() else True,
        remove_unused_columns=False,
        report_to="none",
    )

    # 6. Initialize Trainer
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # DPOTrainer will handle reference model if passed None
        args=dpo_config,
        beta=0.1,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        peft_config=peft_config,
    )

    # 7. Start Training
    print("Starting DPO training...")
    trainer.train()

    # 8. Save final LoRA Adapter
    print(f"Saving final adapter to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    train()
