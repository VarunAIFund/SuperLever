#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge ChatGPT Standardized Locations Script

This script takes the results from ChatGPT standardization and merges them back
into the main standardized_batch_locations.json file, replacing FAILED entries
with ChatGPT's standardized results.
"""

import json
from pathlib import Path
from collections import Counter


class LocationMerger:
    def __init__(self):
        self.merged_count = 0
        self.skipped_count = 0
        self.unknown_count = 0
        self.missing_count = 0
    
    def merge_chatgpt_results(self, main_file='standardized_batch_locations.json',
                            chatgpt_file='chatgpt_standardized_locations.json',
                            backup_file='standardized_batch_locations_backup.json'):
        """Merge ChatGPT results into the main standardized locations file."""
        
        # Check that both input files exist
        main_path = Path(main_file)
        chatgpt_path = Path(chatgpt_file)
        
        if not main_path.exists():
            print(f"❌ Error: {main_file} not found!")
            return False
            
        if not chatgpt_path.exists():
            print(f"❌ Error: {chatgpt_file} not found!")
            return False
        
        print("🔄 Merging ChatGPT standardized locations into main file...")
        print(f"Main file: {main_file}")
        print(f"ChatGPT file: {chatgpt_file}")
        print()
        
        # Load both files
        print("📖 Loading files...")
        with open(main_path, 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        
        with open(chatgpt_path, 'r', encoding='utf-8') as f:
            chatgpt_data = json.load(f)
        
        print(f"Main file entries: {len(main_data)}")
        print(f"ChatGPT results: {len(chatgpt_data)}")
        
        # Count original FAILED entries
        original_failed = sum(1 for status in main_data.values() if status == "FAILED")
        original_successful = len(main_data) - original_failed
        print(f"Original FAILED entries: {original_failed}")
        print(f"Original successful entries: {original_successful}")
        print(f"Total original entries: {len(main_data)}")
        
        # Create backup of original file
        print(f"💾 Creating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        # Replace FAILED location keys with ChatGPT standardized names
        print("\n🔀 Replacing FAILED location keys with ChatGPT standardized names...")
        print("-" * 60)
        
        updated_main_data = {}
        
        # Process each entry in the main data
        for original_location, value in main_data.items():
            if value == "FAILED":
                # This is a FAILED entry - check if ChatGPT has a replacement
                if original_location in chatgpt_data:
                    chatgpt_result = chatgpt_data[original_location]
                    
                    if chatgpt_result in ["UNKNOWN", "MISSING_FROM_RESPONSE", "FAILED"]:
                        # Keep original key with FAILED value
                        updated_main_data[original_location] = "FAILED"
                        if chatgpt_result == "UNKNOWN":
                            self.unknown_count += 1
                            print(f"  ❓ KEEPING ORIGINAL (ChatGPT: UNKNOWN): {original_location}")
                        elif chatgpt_result == "MISSING_FROM_RESPONSE":
                            self.missing_count += 1
                            print(f"  ⚠️  KEEPING ORIGINAL (Missing): {original_location}")
                        elif chatgpt_result == "FAILED":
                            self.skipped_count += 1
                            print(f"  ❌ KEEPING ORIGINAL (ChatGPT also failed): {original_location}")
                        else:
                            self.skipped_count += 1
                            print(f"  ❌ KEEPING ORIGINAL (ChatGPT failed): {original_location}")
                    else:
                        # Replace key with ChatGPT's standardized name, keep "FAILED" as value
                        if chatgpt_result in updated_main_data:
                            # Duplicate key! Keep original to avoid losing data
                            updated_main_data[original_location] = "FAILED"
                            print(f"  ⚠️  DUPLICATE KEY DETECTED: {original_location}")
                            print(f"      ChatGPT wanted: {chatgpt_result} (already exists)")
                            print(f"      KEEPING ORIGINAL to avoid data loss")
                        else:
                            updated_main_data[chatgpt_result] = "FAILED"
                            self.merged_count += 1
                            print(f"  ✅ REPLACED KEY: {original_location}")
                            print(f"      NEW KEY: {chatgpt_result} → FAILED")
                else:
                    # FAILED entry not in ChatGPT results - keep as is
                    updated_main_data[original_location] = "FAILED"
                    print(f"  ⚠️  KEEPING ORIGINAL (not in ChatGPT): {original_location}")
            else:
                # Not a FAILED entry - keep as is
                updated_main_data[original_location] = value
        
        # Replace main_data with updated version
        main_data = updated_main_data
        
        # Save the merged results
        print(f"\n💾 Saving results with updated keys to: {main_file}")
        with open(main_path, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        # Update the text file too
        text_file = main_file.replace('.json', '.txt')
        print(f"📄 Updating text file: {text_file}")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("Original Location → Standardized Location\n")
            f.write("=" * 50 + "\n\n")
            
            for original, standardized in main_data.items():
                if standardized != "FAILED":
                    f.write(f"{original} → {standardized}\n")
                else:
                    f.write(f"{original} → FAILED\n")
        
        # Count final entries
        final_failed = sum(1 for status in main_data.values() if status == "FAILED")
        final_successful = len(main_data) - final_failed
        
        print(f"\n📊 Final counts:")
        print(f"Final entries total: {len(main_data)}")
        print(f"Final successful entries: {final_successful}")  
        print(f"Final FAILED entries: {final_failed}")
        
        # Check if we lost any entries
        entries_lost = len(main_data) - (original_failed + original_successful)
        if entries_lost != 0:
            print(f"⚠️  WARNING: {abs(entries_lost)} entries {'lost' if entries_lost < 0 else 'gained'} during merge!")
        
        # Print summary
        self._print_summary(original_failed, final_failed)
        
        return True
    
    def _print_summary(self, original_failed, final_failed):
        """Print summary of merge operation."""
        print(f"\n{'='*60}")
        print("MERGE SUMMARY")
        print(f"{'='*60}")
        print(f"Original FAILED entries: {original_failed}")
        print(f"Successfully merged from ChatGPT: {self.merged_count}")
        print(f"Kept as FAILED (ChatGPT: UNKNOWN): {self.unknown_count}")
        print(f"Kept as FAILED (Missing from ChatGPT): {self.missing_count}")
        print(f"Kept as FAILED (ChatGPT also failed): {self.skipped_count}")
        print(f"Final FAILED entries: {final_failed}")
        
        improvement = original_failed - final_failed
        improvement_percent = (improvement / original_failed * 100) if original_failed > 0 else 0
        
        print(f"\n📈 Improvement:")
        print(f"Reduced FAILED entries by: {improvement}")
        print(f"Improvement rate: {improvement_percent:.1f}%")
        
        if final_failed > 0:
            print(f"\n⚠️  {final_failed} locations still marked as FAILED")
            print("These are likely genuinely problematic or ambiguous locations")
        else:
            print(f"\n🎉 All locations have been successfully standardized!")
        
        print(f"\n📁 Files updated:")
        print(f"  - standardized_batch_locations.json (main file)")
        print(f"  - standardized_batch_locations.txt (text version)")
        print(f"  - standardized_batch_locations_backup.json (backup created)")


def main():
    """Main function to merge ChatGPT results."""
    
    print("ChatGPT Results Merger")
    print("=" * 30)
    print("This script merges ChatGPT standardized locations back into the main file")
    print("Replaces FAILED entries with successful ChatGPT standardizations")
    print()
    
    # Get user confirmation
    response = input("🔄 Merge ChatGPT results into standardized_batch_locations.json? (y/n): ").lower().strip()
    
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled by user")
        return
    
    print()
    
    # Initialize merger
    merger = LocationMerger()
    
    # Perform the merge
    try:
        success = merger.merge_chatgpt_results()
        
        if success:
            print("\n✅ Merge operation completed successfully!")
            print("Review the summary above to see the results.")
            print("\n💡 Next step: Run retry_failed_locations.py to get coordinates!")
        else:
            print("\n❌ Merge operation failed!")
            
    except Exception as e:
        print(f"\n❌ Error during merge: {e}")
        print("The original file should be safe (backup was created)")


if __name__ == "__main__":
    main()