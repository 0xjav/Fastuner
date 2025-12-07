# Instruction Tuning Example

This dataset contains 100 instruction-response pairs for fine-tuning causal language models (Llama, Qwen, etc.).

## Dataset Details

- **Task Type**: Text Generation / Instruction Following
- **Samples**: 100 diverse instructions with detailed responses
- **Format**: JSONL with `input_text` (instruction) and `target_text` (response)
- **Domains**: Programming, science, writing, business, general knowledge

## Example Usage

```bash
# Upload the dataset
fastuner datasets upload examples/instruction_tuning/instructions.jsonl \
  --name "instructions_v1" \
  --task-type text_generation

# Start fine-tuning
fastuner finetune start \
  --model-id Qwen/Qwen2.5-0.5B-Instruct \
  --dataset-id ds_xxx \
  --adapter-name instruction_adapter \
  --method lora

# Deploy the adapter
fastuner deployments create --adapter-id adp_xxx

# Run inference
fastuner inference run \
  --model-id Qwen/Qwen2.5-0.5B-Instruct \
  --adapter instruction_adapter \
  --input "Explain machine learning in simple terms."
```

## Dataset Schema

Each line contains:
- `input_text`: The instruction or question
- `target_text`: The detailed response

Example:
```json
{"input_text": "Explain what photosynthesis is in simple terms.", "target_text": "Photosynthesis is the process where plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar. It's essentially how plants make their own food using sunlight."}
```

## Model Recommendations

- **Smallest/Fastest**: `Qwen/Qwen2.5-0.5B-Instruct` (~500MB)
- **Good Balance**: `Qwen/Qwen2.5-1.5B-Instruct` (~1.5GB)
- **Better Quality**: `meta-llama/Llama-3.2-1B-Instruct` (~1GB)
- **High Quality**: `Qwen/Qwen2.5-3B-Instruct` (~3GB)

## Training Tips

1. **Learning Rate**: Start with `2e-4` for LoRA fine-tuning
2. **Epochs**: 3-5 epochs usually sufficient for this dataset size
3. **LoRA Rank**: `r=16` or `r=32` works well
4. **Target Modules**: The script auto-detects `q_proj, k_proj, v_proj, o_proj`
5. **Batch Size**: 4 with gradient accumulation for effective batch of 16

## Expected Results

After fine-tuning, the model should:
- Follow instructions more accurately
- Generate more detailed and structured responses
- Better understand the format of instruction-response pairs
- Maintain general knowledge while adapting to your response style

## Data Format

The training script formats data as:
```
<instruction>

<response><eos_token>
```

This teaches the model to generate responses when given instructions.

## Next Steps

1. Fine-tune with this dataset
2. Test the adapter with various instructions
3. Add your own domain-specific instruction-response pairs
4. Iterate and improve based on results

## Notes

- This is a demonstration dataset - for production, use 1000+ examples
- Consider adding domain-specific data for specialized use cases
- QLoRA (4-bit quantization) can be used for larger models on smaller GPUs
