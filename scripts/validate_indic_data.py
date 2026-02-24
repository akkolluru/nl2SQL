import argparse
import json
import os
import sys

def validate_indic_data(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)
        
    print(f"Validating {file_path}...\n")
    
    total_lines = 0
    missing_hindi = 0
    missing_telugu = 0
    
    samples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                total_lines += 1
                record = json.loads(line)
                
                hin = record.get('question_hindi', '').strip()
                tel = record.get('question_telugu', '').strip()
                
                if not hin:
                    missing_hindi += 1
                if not tel:
                    missing_telugu += 1
                    
                if total_lines <= 5:
                    samples.append(record)
                    
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    print("=== STATISTICS ===")
    print(f"Total records          : {total_lines}")
    print(f"Missing Hindi trans    : {missing_hindi} ({(missing_hindi/max(total_lines,1))*100:.2f}%)")
    print(f"Missing Telugu trans   : {missing_telugu} ({(missing_telugu/max(total_lines,1))*100:.2f}%)")
    
    print("\n=== DATA SAMPLES (First 5) ===")
    for i, s in enumerate(samples):
        print(f"\nSample {i+1} [DB: {s.get('db_id')}]")
        print(f"  Gold SQL : {s.get('query')}")
        print(f"  English  : {s.get('question')}")
        print(f"  Hindi    : {s.get('question_hindi')}")
        print(f"  Telugu   : {s.get('question_telugu')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate generated Indic Spider JSONL data.")
    parser.add_argument("--file", type=str, default="data/processed/indic_spider_train.jsonl", help="Path to JSONL file")
    args = parser.parse_args()
    
    validate_indic_data(args.file)
