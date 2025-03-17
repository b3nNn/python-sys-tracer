import requests
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from tracer.tracer import Tracer, Config, load_config

# Read the configuration file
config_file = 'transformers_config.json'
config = None
try:
    config = load_config(config_file)
    print(f"Version: {config.version}")
    for f in config.filters:
        print(f"Filter: {f.name}, Files: {f.files}, Modules: {f.modules}")
except FileNotFoundError:
    print(f"Error: Configuration file '{config_file}' not found.")

with Tracer("audit.jsonl", config):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Load model and processor
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Florence-2-large-ft", torch_dtype=torch_dtype, trust_remote_code=True
    ).to(device)
    processor = AutoProcessor.from_pretrained(
        "microsoft/Florence-2-large-ft", trust_remote_code=True
    )

    prompt = "<OD>"

    # Fetch and open image
    url = "https://github.com/b3nNn/florence2.cpp/blob/develop/puma.png?raw=true"
    image = Image.open(requests.get(url, stream=True).raw)

    # Process inputs (traces processor.__call__)
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)

    # Generate output (traces model.generate)
    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        do_sample=False,
        num_beams=3
    )

    # Decode generated IDs (traces processor.batch_decode)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    # Post-process generation (traces processor.post_process_generation)
    parsed_answer = processor.post_process_generation(
        generated_text, task="<OD>", image_size=(image.width, image.height)
    )

    print(parsed_answer)