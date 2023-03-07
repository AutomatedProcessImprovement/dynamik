"""
This module contains the definitions for reading the logs later used by the drift detection algorithm.
A specific implementation for parsing CSV files from apromore is included.
All log parsers are expected to return an iterator, which will be used later by the detection algorithm.
"""
from __future__ import annotations

import collections.abc
import logging
import typing
from dataclasses import dataclass

from expert.model import Event


@dataclass
class Mapping:
    """Defines the mapping between a dictionary-like object and Event attributes."""

    start: str
    """The attribute from the log file containing the event start timestamp"""
    end: str
    """The attribute from the log file containing the event finish timestamp"""
    case: str
    """The attribute from the log file containing the case ID"""
    activity: str
    """The attribute from the log file containing the activity name"""
    resource: str | None = None
    """The attribute from the log file containing the resource name"""
    enablement: str | None = None
    """The attribute from the log file containing the event enablement timestamp"""

    def dict_to_event(self: Mapping, source: dict[str, typing.Any] | collections.abc.Mapping[str, typing.Any]) -> Event:
        """
        Create an `expert.model.Event` instance from a source *dictionary-like* object applying the current mapping.

        Parameters
        ----------
        * `source`: *a dictionary-like object with the attributes of the event*

        Returns
        -------
        * the `expert.model.Event` instance resulting from applying this mapping to the *dictionary-like* source
        """
        instance = Event(
            case=source[self.case],
            activity=source[self.activity],
            start=source[self.start],
            end=source[self.end],
            resource=source[self.resource] if self.resource is not None else None,
            enabled=source[self.enablement] if self.enablement is not None else None,
        )

        logging.debug('transforming %(source)r to %(instance)r', {'source': source, 'instance': instance})

        return instance
