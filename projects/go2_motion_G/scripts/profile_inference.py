import time
import torch
import numpy as np

# Load model
policy_path = "/home/user/unitree-workspace/git/community/wty-yy/go2_moe_cts/policy.pt"
print(f"Loading {policy_path}")
model = torch.jit.load(policy_path, map_location="cpu")
model.eval()

# Warmup
obs_tensor = torch.zeros((1, 45), dtype=torch.float32)
with torch.inference_mode():
    for _ in range(10):
        model(obs_tensor)

print("Starting benchmark...")
times = []
with torch.inference_mode():
    for _ in range(100):
        start = time.perf_counter()
        model(obs_tensor)
        times.append(time.perf_counter() - start)

avg_ms = np.mean(times) * 1000
max_ms = np.max(times) * 1000
min_ms = np.min(times) * 1000
print(f"Avg: {avg_ms:.2f} ms")
print(f"Max: {max_ms:.2f} ms")
print(f"Min: {min_ms:.2f} ms")
