import sys
import os
import time
import threading
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import psutil
import torch
import builtins

# Override print to automatically flush output for real-time console updates
def print(*args, **kwargs):
    kwargs['flush'] = True
    builtins.print(*args, **kwargs)

from app.database.engine import SessionLocal
from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule
from app.services.classification_service import get_classification_service

class ResourceMonitor:
    def __init__(self, interval=0.05):
        self.interval = interval
        self.process = psutil.Process(os.getpid())
        self.cpu_usages = []
        self.ram_usages = []
        self.running = False
        self.monitor_thread = None

    def start(self):
        self.cpu_usages = []
        self.ram_usages = []
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor(self):
        # We need a small sleep to let the CPU percentage measurement stabilize
        self.process.cpu_percent(interval=None)
        while self.running:
            try:
                # get CPU percent for this process relative to all cores
                cpu = self.process.cpu_percent(interval=None)
                ram = self.process.memory_info().rss / (1024 * 1024) # MB
                self.cpu_usages.append(cpu)
                self.ram_usages.append(ram)
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        # Calculate stats
        avg_cpu = sum(self.cpu_usages) / len(self.cpu_usages) if self.cpu_usages else 0.0
        peak_cpu = max(self.cpu_usages) if self.cpu_usages else 0.0
        avg_ram = sum(self.ram_usages) / len(self.ram_usages) if self.ram_usages else 0.0
        peak_ram = max(self.ram_usages) if self.ram_usages else 0.0
        return avg_cpu, peak_cpu, avg_ram, peak_ram

def main():
    print("=" * 80)
    print("Morpheus Local Llama-3.2-3B Benchmark Runner")
    print("=" * 80)

    # Check environment & resources
    cpu_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)
    total_sys_ram = psutil.virtual_memory().total / (1024 * 1024 * 1024) # GB
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"System Configuration:")
    print(f"  CPU Cores: {physical_cores} Physical / {cpu_cores} Logical")
    print(f"  System RAM: {total_sys_ram:.2f} GB")
    print(f"  Torch Device: {device.upper()}")
    if device == "cuda":
        print(f"  GPU Name: {torch.cuda.get_device_name(0)}")
    print("-" * 80)

    # Initial RAM usage
    initial_process = psutil.Process(os.getpid())
    base_ram = initial_process.memory_info().rss / (1024 * 1024) # MB
    print(f"Initial Process RAM: {base_ram:.2f} MB")

    db = SessionLocal()
    blocks = [b.name for b in db.query(ScheduleBlock).all()]
    rules = [r.name for r in db.query(Rule).all()]
    db.close()

    print(f"Database Context:")
    print(f"  Schedule Blocks count: {len(blocks)} ({', '.join(blocks[:3])}...)")
    print(f"  Rules count: {len(rules)} ({', '.join(rules[:3])}...)")
    print("-" * 80)

    # Get service
    classifier = get_classification_service()

    # Measure loading model time and RAM delta
    print("Loading local Llama-3.2-3B model into memory...")
    monitor = ResourceMonitor()
    monitor.start()
    
    load_start = time.time()
    classifier._load_model_lazy()
    load_time = time.time() - load_start
    
    avg_cpu_load, peak_cpu_load, avg_ram_load, peak_ram_load = monitor.stop()
    loaded_ram = initial_process.memory_info().rss / (1024 * 1024) # MB
    ram_delta = loaded_ram - base_ram
    
    print(f"Model Loaded Successfully!")
    print(f"  Load Time: {load_time:.2f} seconds")
    print(f"  RAM Usage After Load: {loaded_ram:.2f} MB (Delta: +{ram_delta:.2f} MB)")
    print(f"  Peak CPU usage during load: {peak_cpu_load:.2f}%")
    print("-" * 80)

    # 5 test prompts of different lengths/types
    test_prompts = [
        {
            "id": 1,
            "type": "Short (Schedule only)",
            "log": "I did Jogging at 6 AM."
        },
        {
            "id": 2,
            "type": "Short-Medium (Rule violation)",
            "log": "I was lazy today. Did not exercise and played computer games at home."
        },
        {
            "id": 3,
            "type": "Medium (Mixed Standard)",
            "log": "Followed Sleep Schedule and Morning Routine. Did Morning Study. Jogging was partial."
        },
        {
            "id": 4,
            "type": "Long (Descriptive daily log)",
            "log": "Today was a busy day. I woke up at 7 AM and completed my Morning Routine. After that, I traveled to the office and did some deep work. I had lunch with coworkers. In the evening, I went for a run (Jogging) for about 30 minutes, which complies with Exercise Mandatory. At night, I spent 2 hours on Night Study. I did not play any games and followed all my rules."
        },
        {
            "id": 5,
            "type": "Long (Complex mixed violations)",
            "log": "I woke up super late at 10 AM, completely failing Follow Sleep Schedule. As a result, Morning Routine was missed and Morning Study Must Not Be Wasted was violated. I felt lazy and did not do any Exercise Mandatory today. The only good thing was that I followed No Games At Home and did deep work in the afternoon. At night I did about 1 hour of Night Study."
        }
    ]

    results = []

    for item in test_prompts:
        p_id = item["id"]
        p_type = item["type"]
        raw_log = item["log"]
        
        print(f"Running Prompt {p_id} ({p_type})...")
        print(f"Log: \"{raw_log}\"")

        # Build prompt context to measure sizes
        prompt_text = classifier._build_prompt(raw_log, blocks, rules)
        inputs = classifier._tokenizer(prompt_text, return_tensors="pt")
        input_tokens = inputs.input_ids.shape[1]
        
        monitor = ResourceMonitor()
        monitor.start()
        
        inf_start = time.time()
        
        # We run tokenizer, model generate with TextStreamer, and json parsing
        device_inputs = inputs.to(classifier._device)
        from transformers import TextStreamer
        streamer = TextStreamer(classifier._tokenizer, skip_prompt=True)
        
        print("\n--- Model Output (Streaming) ---")
        with torch.no_grad():
            outputs = classifier._model.generate(
                **device_inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=False,
                streamer=streamer
            )
        print("--------------------------------\n")
        
        generated_text = classifier._tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        inf_time = time.time() - inf_start
        
        avg_cpu, peak_cpu, avg_ram, peak_ram = monitor.stop()
        
        # Token sizes
        total_tokens = len(outputs[0])
        output_tokens = total_tokens - input_tokens
        tok_per_sec = output_tokens / inf_time if inf_time > 0 else 0
        
        # JSON parsing
        json_valid = False
        parsed_entries = []
        try:
            parsed_entries = classifier._parse_llama_json(generated_text)
            json_valid = True
        except Exception as je:
            print(f"  JSON Parsing failed: {je}")
            
        print(f"  Completed in {inf_time:.2f}s | Speed: {tok_per_sec:.2f} tok/s | Input Tok: {input_tokens} | Output Tok: {output_tokens}")
        print(f"  Peak RAM: {peak_ram:.2f} MB | Peak CPU: {peak_cpu:.2f}% (logical core usage)")
        print(f"  JSON Parsed: {'SUCCESS' if json_valid else 'FAILED'} (Got {len(parsed_entries)} entries)")
        print("-" * 80)
        
        results.append({
            "id": p_id,
            "type": p_type,
            "log": raw_log,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency": inf_time,
            "speed": tok_per_sec,
            "avg_cpu": avg_cpu,
            "peak_cpu": peak_cpu,
            "peak_ram": peak_ram,
            "avg_ram": avg_ram,
            "json_valid": json_valid,
            "raw_output": generated_text,
            "parsed_count": len(parsed_entries)
        })

    # Generate report file
    report_path = Path("benchmark_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Morpheus Local Llama-3.2-3B Benchmark Report\n\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## System Information\n")
        f.write(f"- **CPU**: {physical_cores} Physical / {cpu_cores} Logical Cores\n")
        f.write(f"- **Total RAM**: {total_sys_ram:.2f} GB\n")
        f.write(f"- **Inference Device**: {device.upper()}\n")
        if device == "cuda":
            f.write(f"  - **GPU**: {torch.cuda.get_device_name(0)}\n")
        f.write(f"- **Model Path**: `local_models/Llama-3.2-3B`\n\n")
        
        f.write("## Initialization Metrics\n")
        f.write(f"- **Baseline RAM (Process Start)**: {base_ram:.2f} MB\n")
        f.write(f"- **Model Loading Time**: {load_time:.2f} seconds\n")
        f.write(f"- **RAM After Model Loaded**: {loaded_ram:.2f} MB (Delta: +{ram_delta:.2f} MB)\n")
        f.write(f"- **Peak CPU Usage during Model Load**: {peak_cpu_load:.2f}%\n\n")
        
        f.write("## Inference Performance Metrics\n\n")
        f.write("| ID | Type | Log Length (chars) | Input Tokens | Output Tokens | Latency (s) | Speed (tok/s) | Peak RAM (MB) | Peak CPU (%) | JSON Status |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            status_str = "🟢 Success" if r["json_valid"] else "🔴 Failed"
            f.write(f"| {r['id']} | {r['type']} | {len(r['log'])} | {r['input_tokens']} | {r['output_tokens']} | {r['latency']:.2f}s | {r['speed']:.2f} | {r['peak_ram']:.2f} | {r['peak_cpu']:.2f}% | {status_str} |\n")
        f.write("\n")
        
        f.write("## Detailed Prompts & Outputs\n\n")
        for r in results:
            f.write(f"### Prompt {r['id']}: {r['type']}\n")
            f.write(f"**Log Input**:\n> {r['log']}\n\n")
            f.write("**Raw Generated Model Output**:\n```json\n" + r["raw_output"] + "\n```\n\n")
            f.write(f"- **JSON Validated**: {r['json_valid']}\n")
            f.write(f"- **Parsed Structured Entries**: {r['parsed_count']}\n")
            f.write(f"- **Performance**: {r['latency']:.2f}s ({r['speed']:.2f} tokens/sec)\n")
            f.write(f"- **Peak CPU Usage**: {r['peak_cpu']:.2f}% | Peak Process RAM: {r['peak_ram']:.2f} MB\n\n")
            f.write("---\n\n")
            
        f.write("## Feasibility Analysis\n")
        # Compute averages
        avg_latency = sum(r["latency"] for r in results) / len(results)
        avg_speed = sum(r["speed"] for r in results) / len(results)
        max_peak_ram = max(r["peak_ram"] for r in results)
        
        f.write(f"- **Average Inference Latency**: {avg_latency:.2f} seconds\n")
        f.write(f"- **Average Generation Speed**: {avg_speed:.2f} tokens/second\n")
        f.write(f"- **Peak RAM Footprint (Model + Inference)**: {max_peak_ram:.2f} MB\n\n")
        
        f.write("### Recommendation\n")
        if avg_latency > 5.0:
            f.write("> [!WARNING]\n")
            f.write(f"> **Not Feasible for Real-Time UI Requests.** An average response time of {avg_latency:.2f}s is too high for a standard web app request-response cycle. It will freeze page loads and block the server thread pool.\n")
        else:
            f.write("> [!NOTE]\n")
            f.write("> **Feasible but resource-intensive.** The latency is within acceptable limits, but CPU and memory footprints must be monitored closely.\n")
            
    print(f"SUCCESS: Detailed benchmark report generated at '{report_path.resolve()}'")

if __name__ == "__main__":
    main()
