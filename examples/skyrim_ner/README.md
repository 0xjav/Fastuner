# Skyrim NER Dataset for GliNER-2

Fine-tune GliNER-2 to recognize Skyrim-specific entities!

## Entity Types

- **CHARACTER**: NPCs, named characters
- **LOCATION**: Cities, dungeons, regions
- **FACTION**: Guilds, groups (Companions, Dark Brotherhood)
- **RACE**: Races (Nord, Khajiit, Argonian)
- **ITEM**: Weapons, armor, artifacts (Daedric artifacts, etc.)
- **CREATURE**: Dragons, monsters (Alduin, draugr)
- **DEITY**: Gods, Daedric Princes (Talos, Azura)
- **EVENT**: Historical events (Dragon War, Great Collapse)

## Dataset Format

For GliNER-2, each sample should be:

```jsonl
{"input_text": "Ulfric Stormcloak leads the rebellion in Windhelm against the Imperial Legion.", "target_text": "CHARACTER: Ulfric Stormcloak | LOCATION: Windhelm | FACTION: Imperial Legion"}
```

This teaches the model to extract Skyrim entities from any text!
