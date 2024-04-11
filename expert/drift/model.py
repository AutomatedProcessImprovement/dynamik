"""This module contains the definition of the model used for drift detection in the cycle time of a process."""

from __future__ import annotations

import enum
import typing
from dataclasses import dataclass
from datetime import datetime, timedelta

import scipy
from anytree import NodeMixin

from expert.process_model import Event
from expert.utils.logger import LOGGER
from expert.utils.model import Pair
from expert.utils.pm.batching import discover_batches
from expert.utils.pm.processing import decompose_processing_times
from expert.utils.pm.waiting import decompose_waiting_times
from expert.utils.timer import profile


class DriftCause(NodeMixin):
    """TODO docs"""

    def __init__(
            self: typing.Self,
            what: str,
            how: Pair,
            data: Pair,
            parent: DriftCause | None = None,
            children: DriftCause | None = None,
    ) -> None:
        super().__init__()
        self.what = what
        self.how = how
        self.data = data
        self.parent = parent
        if children:
            self.children = children


class DriftLevel(enum.Enum):
    """The drift level. Can be no drift, drift warning or confirmed drift."""

    NONE = 0
    WARNING = 1
    CONFIRMED = 2


@dataclass
class Drift:
    """The drift, with its level and the data that lead to the detection"""

    level: DriftLevel
    reference_model: Model | None = None
    running_model: Model | None = None
    first_warning: Drift | None = None

    @profile()
    def __post_init__(self: typing.Self) -> None:
        # if the drift has been confirmed, compute the features
        if self.level == DriftLevel.CONFIRMED:
            # compute the batches
            discover_batches(self.reference_model.data)
            discover_batches(self.running_model.data)
            # decompose processing times
            decompose_processing_times(self.reference_model.data)
            decompose_processing_times(self.running_model.data)
            # decompose waiting times
            decompose_waiting_times(self.reference_model.data)
            decompose_waiting_times(self.running_model.data)


NO_DRIFT: Drift = Drift(level=DriftLevel.NONE)


class Model:
    """TODO docs"""

    # The date and time when the model starts
    start: datetime
    # The date and time when the model ends
    end: datetime
    # The collection of events used as the model
    data: typing.MutableSequence[Event]

    def __init__(self: typing.Self, start: datetime, length: timedelta) -> None:
        self.start = start
        self.end = start + length
        self.data = []

    @property
    def empty(self: typing.Self) -> bool:
        """TODO docs"""
        return len(self.data) == 0

    def prune(self: typing.Self) -> None:
        """TODO docs"""
        LOGGER.debug("pruning model")
        # Remove all events that are out of the overlapping region from the running model
        self.data = [event for event in self.data if event.start > self.start and event.end < self.end]

    def add(self: typing.Self, event: Event) -> None:
        """TODO docs"""
        self.data.append(event)

    def statistically_equals(self: typing.Self, other: Model, *, significance: float = 0.05) -> bool:
        """TODO docs"""
        if len(list(self.data)) > 0 and len(list(other.data)) > 0:
            result = scipy.stats.kstest(
                [event.cycle_time.total_seconds() for event in self.data],
                [event.cycle_time.total_seconds() for event in other.data],
            )

            LOGGER.verbose("test(reference != running) p-value: %.4f", result.pvalue)

            return result.pvalue >= significance

        return True

    def envelopes(self: typing.Self, event: Event) -> bool:
        """TODO docs"""
        return self.start < event.enabled < event.end < self.end

    def update_timeframe(self: typing.Self, start: datetime, length: timedelta) -> None:
        """TODO docs"""
        self.start = start
        self.end = start + length
        # Delete outdated events from the model
        LOGGER.debug("pruning model (timeframe %s - %s)", self.start, self.end)
        self.prune()

    def completed(self: typing.Self, instant: datetime) -> bool:
        """TODO docs"""
        return instant > self.end

    def __repr__(self: typing.Self) -> str:
        return f"""Model(timeframe=({self.start} - {self.end}), events={len(self.data)})"""
