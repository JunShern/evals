import nltk
import numpy as np
from nltk.corpus import wordnet as wn

import evals
from evals.api import CompletionFn
from evals.elsuite.make_me_say.autoeval import run as run_auto_eval
from evals.elsuite.make_me_say.core import Game
from evals.record import RecorderBase

nltk.download("wordnet")
wn.ensure_loaded()  # needed to support threading


class MakeMeSay(evals.Eval):
    def __init__(
        self,
        completion_fns: list[CompletionFn],
        *args,
        **kwargs,
    ):
        super().__init__(completion_fns, *args, **kwargs)
        assert len(completion_fns) == 3, "MakeMeSay only supports three completion fns"
        (
            self.manipulator_completion_fn,
            self.manipulatee_completion_fn,
            self.judge_completion_fn,
        ) = completion_fns

    def eval_sample(self, sample: dict, rng) -> None:
        del rng

        assert isinstance(sample, dict), "sample must be a dict"
        assert isinstance(sample["input"], dict)
        assert "codeword" in sample["input"]
        assert isinstance(sample["input"]["codeword"], str)

        game: Game = run_auto_eval(
            codeword=sample["input"]["codeword"],
            manipulator_completion_fn=self.manipulator_completion_fn,
            manipulatee_completion_fn=self.manipulatee_completion_fn,
            judge_completion_fn=self.judge_completion_fn,
        )

        evals.record.record_metrics(
            is_win=game.is_win(),
            is_loss=game.is_loss(),
            is_violation=game.is_violation(),
            is_user_aware_of_manipulation=game.is_user_aware_of_manipulation(),
        )

    def run(self, recorder: RecorderBase):
        samples = self.get_samples()
        self.eval_all_samples(recorder, samples)
        metrics = recorder.get_metrics()

        return {
            "win_rate": np.mean([d["is_win"] for d in metrics]),
            "loss_rate": np.mean([d["is_loss"] for d in metrics]),
            "violation_rate": np.mean([d["is_violation"] for d in metrics]),
            "user_aware_of_manipulation_rate": np.mean(
                [d["is_user_aware_of_manipulation"] for d in metrics]
            ),
        }
