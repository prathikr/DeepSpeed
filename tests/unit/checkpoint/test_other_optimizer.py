import deepspeed
from deepspeed.ops.op_builder import FusedLambBuilder

from tests.unit.common import DistributedTest
from tests.unit.simple_model import *

from tests.unit.checkpoint.common import checkpoint_correctness_verification

import pytest


class TestOtherOptimizerCheckpoint(DistributedTest):
    world_size = 2

    @pytest.mark.skipif(not deepspeed.ops.__compatible_ops__[FusedLambBuilder.NAME],
                        reason="lamb is not compatible")
    def test_checkpoint_unfused_optimizer(self, tmpdir):
        config_dict = {
            "train_batch_size": 2,
            "steps_per_print": 1,
            "optimizer": {
                "type": "Lamb",
                "params": {
                    "lr": 0.00015
                }
            },
            "gradient_clipping": 1.0,
            "fp16": {
                "enabled": True
            },
            "scheduler": {
                "type": "OneCycle",
                "params": {
                    "cycle_first_step_size": 1000,
                    "cycle_first_stair_count": 500,
                    "cycle_second_step_size": 1000,
                    "cycle_second_stair_count": 500,
                    "decay_step_size": 1000,
                    "cycle_min_lr": 0.0001,
                    "cycle_max_lr": 0.0010,
                    "decay_lr_rate": 0.001,
                    "cycle_min_mom": 0.85,
                    "cycle_max_mom": 0.99,
                    "decay_mom_rate": 0.0
                }
            }
        }

        args = args_from_dict(tmpdir, config_dict)
        hidden_dim = 10
        models = [SimpleModel(hidden_dim, empty_grad=False) for _ in range(2)]

        # Load & verify optimizer states
        checkpoint_correctness_verification(config_dict,
                                            models=models,
                                            hidden_dim=hidden_dim,
                                            tmpdir=tmpdir,
                                            load_optimizer_states=True)

        # Ignore optimizer states
        checkpoint_correctness_verification(config_dict,
                                            models=models,
                                            hidden_dim=hidden_dim,
                                            tmpdir=tmpdir,
                                            load_optimizer_states=False)

    def test_checkpoint_fused_optimizer(self, tmpdir):
        config_dict = {
            "train_batch_size": 2,
            "steps_per_print": 1,
            "optimizer": {
                "type": "Adam",
                "params": {
                    "lr": 0.00015,
                    "betas": [0.8,
                              0.999],
                    "eps": 1e-8,
                    "weight_decay": 3e-7
                }
            },
            "fp16": {
                "enabled": True
            }
        }

        args = args_from_dict(tmpdir, config_dict)
        hidden_dim = 10
        models = [SimpleModel(hidden_dim, empty_grad=False) for _ in range(2)]

        # Load & verify optimizer states
        checkpoint_correctness_verification(config_dict,
                                            models=models,
                                            hidden_dim=hidden_dim,
                                            tmpdir=tmpdir,
                                            load_optimizer_states=True)

        # Ignore optimizer states
        checkpoint_correctness_verification(config_dict,
                                            models=models,
                                            hidden_dim=hidden_dim,
                                            tmpdir=tmpdir,
                                            load_optimizer_states=False)

    def test_checkpoint_fp32_optimizer(self, tmpdir):
        config_dict = {
            "train_batch_size": 2,
            "steps_per_print": 1,
            "optimizer": {
                "type": "Adam",
                "params": {
                    "lr": 0.00015,
                    "betas": [0.8,
                              0.999],
                    "eps": 1e-8,
                    "weight_decay": 3e-7
                }
            },
            "fp16": {
                "enabled": False
            }
        }

        args = args_from_dict(tmpdir, config_dict)
        hidden_dim = 10
        models = [SimpleModel(hidden_dim, empty_grad=False) for _ in range(2)]
        checkpoint_correctness_verification(config_dict,
                                            models=models,
                                            hidden_dim=hidden_dim,
                                            tmpdir=tmpdir,
                                            fp16=False)
