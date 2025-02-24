import numpy as np
import deepspeed
import pytest
from deepspeed.runtime.progressive_layer_drop import ProgressiveLayerDrop

from tests.unit.common import DistributedTest
from tests.unit.simple_model import SimpleModel, PLD_SimpleModel, random_dataloader


@pytest.mark.parametrize('theta', [0, 0.1, 0.9, 1.0])
def test_pld_schedule(tmpdir, theta):
    gamma = 0.001

    pld_scheduler = ProgressiveLayerDrop(theta, gamma)
    for i in range(10):
        pld_scheduler.update_state(i)
        expected_theta = (1. - theta) * np.exp(-gamma * i) + theta
        actual_theta = pld_scheduler.get_theta()
        assert expected_theta == actual_theta


@pytest.mark.parametrize('theta', [0, 0.1, 0.9, 1.0])
class TestPLDModel(DistributedTest):
    world_size = 1

    def test_pld_model(self, theta):
        gamma = 0.001
        config_dict = {
            "train_batch_size": 1,
            "steps_per_print": 1,
            "optimizer": {
                "type": 'Adam',
                "params": {
                    "lr": 0.0001
                }
            },
            "fp16": {
                "enabled": True
            },
            "progressive_layer_drop": {
                "enabled": True,
                "theta": theta,
                "gamma": gamma
            }
        }
        hidden_dim = 10

        model = PLD_SimpleModel(hidden_dim, empty_grad=False)
        model, _, _, _ = deepspeed.initialize(config=config_dict,
                                              model=model,
                                              model_parameters=model.parameters())

        data_loader = random_dataloader(model=model,
                                        total_samples=50,
                                        hidden_dim=hidden_dim,
                                        device=model.device)

        for i, batch in enumerate(data_loader):
            loss = model(batch[0], batch[1])
            model.backward(loss)
            model.step()

            expected_theta = (1. - theta) * np.exp(-gamma * i) + theta
            actual_theta = model.get_pld_theta()
            assert expected_theta == actual_theta


class TestNonPLDModel(DistributedTest):
    world_size = 1

    def test_non_pld_model(self):
        gamma = 0.001
        theta = 0.5
        config_dict = {
            "train_batch_size": 1,
            "steps_per_print": 1,
            "optimizer": {
                "type": 'Adam',
                "params": {
                    "lr": 0.0001
                }
            },
            "fp16": {
                "enabled": True
            },
            "progressive_layer_drop": {
                "enabled": True,
                "theta": theta,
                "gamma": gamma
            }
        }
        hidden_dim = 10

        model = SimpleModel(hidden_dim, empty_grad=False)
        model, _, _, _ = deepspeed.initialize(config=config_dict,
                                              model=model,
                                              model_parameters=model.parameters())

        data_loader = random_dataloader(model=model,
                                        total_samples=1,
                                        hidden_dim=hidden_dim,
                                        device=model.device)

        for i, batch in enumerate(data_loader):
            with pytest.raises(TypeError):
                loss = model(batch[0], batch[1])
