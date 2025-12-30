#!/usr/bin/env python3
import os
import time
import sys
import glob
import re
import json

MAPPING_FILE = "led_mapping_results.json"

def get_led_index(path):
    # Extracts index from path like ".../rgb:kbd_backlight_12"
    # base: rgb:kbd_backlight -> 0
    # base_1 -> 1
    filename = os.path.basename(path)
    match = re.search(r'rgb:kbd_backlight(?:_(\d+))?$', filename)
    if match:
        suffix = match.group(1)
        return int(suffix) if suffix else 0
    return -1

def find_led_paths():
    paths = glob.glob("/sys/class/leds/*:kbd_backlight*")
    # Sort by numeric index
    paths.sort(key=get_led_index)
    return paths

def set_led_color(led_path, r, g, b):
    intensity_file = os.path.join(led_path, "multi_intensity")
    brightness_file = os.path.join(led_path, "brightness")
    
    if os.path.exists(intensity_file):
        try:
            with open(intensity_file, 'w') as f:
                f.write(f"{r} {g} {b}")
            with open(brightness_file, 'w') as f:
                f.write("255") 
        except Exception as e:
            print(f"Error writing to {led_path}: {e}")

def turn_off_all(paths):
    for path in paths:
        set_led_color(path, 0, 0, 0)

def main():
    print("ITE 8291 Key Mapping Test Tool (Interactive)")
    print("--------------------------------------------")
    print("This tool will light up each LED one by one.")
    print("Please type the name of the key that lights up.")
    print("If NO key lights up, type 'no' or just press Enter.")
    print("If you want to exit and save, type 'exit'.")
    print("--------------------------------------------")
    
    if os.geteuid() != 0:
        print("Error: This script must be run as root (sudo).")
        sys.exit(1)

    led_paths = find_led_paths()
    if not led_paths:
        print("No keyboard backlight LEDs found.")
        sys.exit(1)

    print(f"Found {len(led_paths)} LED devices.")
    
    results = {}
    
    # Load existing results if any to resume? (Optional, kept simple for now)
    
    try:
        turn_off_all(led_paths)
        time.sleep(1)
        
        for i, path in enumerate(led_paths):
            index = get_led_index(path)
            led_name = os.path.basename(path)
            
            # Light up RED
            set_led_color(path, 255, 0, 0)
            
            print(f"\n[{i+1}/{len(led_paths)}] LED Index: {index} ({led_name}) is ON (RED).")
            key_name = input("Which key is this? (Enter='no', 'exit'=stop): ").strip()
            
            # Turn off
            set_led_color(path, 0, 0, 0)
            
            if key_name.lower() == 'exit':
                break
            
            if key_name and key_name.lower() != 'no':
                results[index] = key_name
                print(f"Saved: Index {index} -> {key_name}")
            else:
                print(f"Skipped Index {index}")

    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        turn_off_all(led_paths)
        
        # Save results
        if results:
            with open(MAPPING_FILE, 'w') as f:
                json.dump(results, f, indent=4)
            print(f"\nMapping results saved to {MAPPING_FILE}")
            print(json.dumps(results, indent=2))
        else:
            print("\nNo mapping results to save.")

if __name__ == "__main__":
    main()
