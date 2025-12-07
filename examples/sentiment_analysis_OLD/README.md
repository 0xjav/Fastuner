# Sentiment Analysis Example

This dataset contains 100 samples for fine-tuning a sentiment classification model.

## Dataset Details

- **Task Type**: Classification
- **Classes**: 3 (positive, negative, neutral)
- **Samples**: 100 (balanced distribution)
- **Format**: JSONL with `input_text` and `target_text`

## Example Usage

```bash
# Upload the dataset
fastuner datasets upload examples/sentiment_analysis/sentiment.jsonl \
  --name "sentiment_v1" \
  --task-type classification

# Start fine-tuning
fastuner finetune start \
  --model-id distilbert-base-uncased \
  --dataset-id ds_xxx \
  --adapter-name sentiment_adapter \
  --method lora

# Deploy the adapter
fastuner deployments create --adapter-id adp_xxx

# Run inference
fastuner inference run \
  --model-id distilbert-base-uncased \
  --adapter sentiment_adapter \
  --input "This product is amazing!"
```

## Dataset Schema

Each line contains:
- `input_text`: Customer review or feedback text
- `target_text`: Sentiment label (positive/negative/neutral)

Example:
```json
{"input_text": "This product exceeded all my expectations! Absolutely love it.", "target_text": "positive"}
```

## Model Recommendations

- **Fast/Cheap**: `distilbert-base-uncased`
- **Better Quality**: `roberta-base`
- **Best Quality**: `bert-large-uncased`

## Expected Results

After fine-tuning, the model should be able to classify sentiment with ~85-90% accuracy on similar product review text.
