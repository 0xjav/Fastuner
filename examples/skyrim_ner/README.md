# Skyrim Named Entity Recognition (NER)

Fine-tune a language model to recognize and extract Skyrim-specific entities!

## Entity Types

- **CHARACTER**: NPCs, named characters (Dragonborn, Ulfric Stormcloak)
- **LOCATION**: Cities, dungeons, regions (Whiterun, Skyrim, Throat of the World)
- **FACTION**: Guilds, groups (Companions, Dark Brotherhood, Thieves Guild)
- **RACE**: Races (Nord, Khajiit, Argonian)
- **ITEM**: Weapons, armor, artifacts (steel armor, Auriel's Bow)
- **CREATURE**: Dragons, monsters (Alduin, Paarthurnax, draugr)
- **DEITY**: Gods, Daedric Princes (Talos, Azura, Molag Bal)
- **EVENT**: Historical events (Dragon War, Dragon Crisis)

## Dataset Details

- **Task Type**: Text Generation (Entity Extraction)
- **Samples**: 100 examples covering major Skyrim lore
- **Format**: Input text → Entity annotations

## Example Usage

```bash
# Upload the dataset
fastuner datasets upload examples/skyrim_ner/skyrim_entities.jsonl \
  --name "skyrim_ner_v1" \
  --task-type text_generation

# Start fine-tuning
fastuner finetune start \
  --model-id Qwen/Qwen2.5-0.5B-Instruct \
  --dataset-id ds_xxx \
  --adapter-name skyrim_ner_adapter \
  --method lora

# Run inference
fastuner inference run \
  --model-id Qwen/Qwen2.5-0.5B-Instruct \
  --adapter skyrim_ner_adapter \
  --input "Paarthurnax taught the Dragonborn the Fire Breath shout at High Hrothgar."
```

## Dataset Format

Each sample contains:
- `input_text`: A sentence about Skyrim lore
- `target_text`: Extracted entities in format `TYPE: entity1, entity2 | TYPE: entity3`

Example:
```json
{"input_text": "The Dragonborn arrived in Whiterun to warn Jarl Balgruuf about the dragon attack on Helgen.", "target_text": "CHARACTER: Dragonborn, Jarl Balgruuf | LOCATION: Whiterun, Helgen | CREATURE: dragon"}
```

## Expected Results

After fine-tuning, the model should:
- Extract character names, locations, and other entities from Skyrim text
- Recognize domain-specific terms (Thu'um, Draugr, etc.)
- Categorize entities into the correct types
- Handle complex sentences with multiple entity types

## Model Recommendations

- **Fast**: `Qwen/Qwen2.5-0.5B-Instruct`
- **Better**: `Qwen/Qwen2.5-1.5B-Instruct`
- **Best**: `meta-llama/Llama-3.2-3B-Instruct`

## Use Cases

- **Game Wiki Parsing**: Extract structured data from lore descriptions
- **Quest Tracking**: Identify characters, locations, and items in quest text
- **Lore Analysis**: Build knowledge graphs from Elder Scrolls text
- **Mod Development**: Auto-tag entities in custom content
