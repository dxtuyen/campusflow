"""The UI's session lifecycle; this is not durable database storage."""

import streamlit as st

from application.models import ComparisonRun, Dataset, PolicyExperiment, ScheduleConfig
from application.sample_data import load_sample


def use_dataset(dataset: Dataset) -> None:
    st.session_state.dataset = dataset
    for key in ("run", "what_if", "import_errors"):
        st.session_state.pop(key, None)


def initialize_state() -> None:
    if "dataset" not in st.session_state:
        use_dataset(load_sample())
    # Preserve browser sessions opened before the refactor from positional tuples.
    run = st.session_state.get("run")
    if isinstance(run, tuple) and len(run) == 4:
        st.session_state.run = ComparisonRun(*run)
    experiment = st.session_state.get("what_if")
    if isinstance(experiment, tuple) and len(experiment) == 4:
        dataset, config, penalties, results = experiment
        st.session_state.what_if = PolicyExperiment(
            dataset, config, tuple(penalties), tuple(results)
        )


def save_run(run: ComparisonRun) -> None:
    st.session_state.run = run
    st.session_state.view_algorithm = (
        "CP-SAT" if run.cp_sat.complete or not run.greedy.complete else "Greedy"
    )


def current_run(dataset: Dataset, config: ScheduleConfig) -> ComparisonRun | None:
    run = st.session_state.get("run")
    return (
        run if isinstance(run, ComparisonRun) and run.matches(dataset, config) else None
    )


def save_experiment(experiment: PolicyExperiment) -> None:
    st.session_state.what_if = experiment


def current_experiment(
    dataset: Dataset, config: ScheduleConfig, penalties: tuple[int, ...]
) -> PolicyExperiment | None:
    experiment = st.session_state.get("what_if")
    return (
        experiment
        if isinstance(experiment, PolicyExperiment)
        and experiment.matches(dataset, config, penalties)
        else None
    )
