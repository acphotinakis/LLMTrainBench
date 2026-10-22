import torch

def get_device():
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using Apple Silicon GPU Acceleration (MPS)")
    else:
        device = torch.device("cpu")
        print("MPS not available, falling back to CPU")
    return device
print(get_device())