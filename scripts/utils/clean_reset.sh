#!/bin/bash
echo "🧹 Cleaning up corrupted training data and old models..."

# Delete only small/empty CSVs? No, better to be safe and delete all to avoid mixing good/bad data
# But asking user to re-do video is annoying if video works.
# Let's check size before deleting.

cd datasets
for f in *_training_data.csv; do
    if [ -f "$f" ]; then
        size=$(wc -c <"$f")
        if [ $size -lt 500 ]; then
            echo "🗑️  Deleting empty/corrupt file: $f ($size bytes)"
            rm "$f"
        else
            echo "✅ Keeping valid file: $f ($size bytes)"
        fi
    fi
done
cd ..

echo "✨ Cleanup complete. Ready for re-training."
