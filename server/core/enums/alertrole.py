"""Enumeration for GW alert roles."""

from enum import StrEnum


class AlertRole(StrEnum):
    """Alert role — whether the alert is a real observation or a test."""

    observation = "observation"
    test = "test"
