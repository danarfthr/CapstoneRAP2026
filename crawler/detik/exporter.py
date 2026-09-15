import csv
import json
from typing import Iterator, Dict
from config import config, logger

def stream_cache_records() -> Iterator[Dict]:
    """
    Generator that reads the JSONL cache file line by line.
    This prevents memory overflow (Out of Memory errors) even if the 
    cache file grows to several gigabytes.
    """
    if not config.cache_file.exists():
        logger.error(f"Cache file {config.cache_file} does not exist. Run crawler first.")
        return

    with open(config.cache_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"Skipping corrupted JSON on line {line_num} during export.")

def export_to_csv():
    """
    Converts the flat JSONL records into a proper CSV file.
    Automatically escapes quotes and newlines in the article body.
    """
    # The keys must match the dictionary output from parser.py
    headers = ["url", "title", "date", "tags", "body"]
    
    logger.info(f"Starting CSV export to {config.final_csv}...")
    
    # newline="" is required by Python's csv module to prevent blank lines between rows on Windows
    with open(config.final_csv, "w", encoding="utf-8", newline="") as f_csv:
        # quoting=csv.QUOTE_ALL replicates the escapeCsvValue function from convert_to_csv.ts
        writer = csv.DictWriter(f_csv, fieldnames=headers, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        count = 0
        for record in stream_cache_records():
            # Convert the list of tags into a single string separated by " | " 
            # exactly as it was done in the TypeScript pipeline
            raw_tags = record.get("tags", [])
            formatted_tags = " | ".join(raw_tags) if isinstance(raw_tags, list) else ""
            
            writer.writerow({
                "url": record.get("url", ""),
                "title": record.get("title", ""),
                "date": record.get("date", ""),
                "tags": formatted_tags,
                "body": record.get("body", "")
            })
            count += 1
            
    logger.info(f"CSV export complete. Saved {count} rows.")
    return count

def export_to_json_array():
    """
    Converts the line-delimited JSONL cache into a standard JSON Array file
    so it can be easily imported into visualization tools or pandas.
    """
    logger.info(f"Starting JSON Array export to {config.final_json}...")
    
    with open(config.final_json, "w", encoding="utf-8") as f_json:
        f_json.write("[\n")
        
        first = True
        for record in stream_cache_records():
            if not first:
                f_json.write(",\n")
            # ensure_ascii=False preserves Indonesian text accurately
            f_json.write(json.dumps(record, ensure_ascii=False, indent=4))
            first = False
            
        f_json.write("\n]")
        
    logger.info("JSON Array export complete.")

def run_export():
    """Main function to trigger all exports."""
    if not config.cache_file.exists():
        return
        
    total_records = export_to_csv()
    if total_records > 0:
        export_to_json_array()
        logger.info(f"Pipeline finished! Final datasets available in: {config.output_dir.absolute()}")

if __name__ == "__main__":
    run_export()