from typing import Tuple
from torchvision.models.resnet import resnet50
import torch
from ptflops.flops_counter import get_model_complexity_info

from nni.compression.pytorch.utils.counter import count_flops_params
from nni.compression.pytorch.speedup import ModelSpeedup
from nni.algorithms.compression.pytorch.pruning import L1FilterPruner

from alfred.dl.torch.common import device
import time


model = resnet50(pretrained=True).to(device)
torch.save(model.state_dict(), 'origin.pth')
# print(model)

config_list = [{
    'sparsity': 0.8,
    'op_types': ['Conv2d']
}]

input_size = [1, 3, 640, 640]
dummy_input = torch.randn(input_size).to(device)

tic = time.time()
a = model(dummy_input)
print('first time: ', time.time() - tic)

flops, params, _ = count_flops_params(model, dummy_input, verbose=True)
print(f"Model FLOPs {flops/1e6:.2f}M, Params {params/1e6:.2f}M")



pruner = L1FilterPruner(model, config_list)
pruner.compress()

flops, params, _ = count_flops_params(model, dummy_input, verbose=True)
print(f"Model FLOPs {flops/1e6:.2f}M, Params {params/1e6:.2f}M")

pruned_model_path = 'l1_pruned.pth'
pruned_model_mask_path = 'l1_pruned_mask.pth'

pruner.export_model(model_path=pruned_model_path, mask_path=pruned_model_mask_path)


model = resnet50(pretrained=True).to(device)
m_speedup = ModelSpeedup(model, dummy_input, masks_file=pruned_model_mask_path)
m_speedup.speedup_model()


tic = time.time()
a = model(dummy_input)
print('second time: ', time.time() - tic)


# print(model)
torch.save(model.state_dict(), 'l1_speedup_model2.pth')

flops, params, _ = count_flops_params(model, dummy_input, verbose=True)
print(f"Model FLOPs {flops/1e6:.2f}M, Params {params/1e6:.2f}M")