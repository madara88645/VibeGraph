from datetime import date

from app.services.trial_meter import TrialMeter


def test_trial_meter_tracks_each_identity_without_going_below_zero():
    meter = TrialMeter(free_calls=2, global_daily_cap=10)

    assert meter.remaining("visitor-a") == 2
    assert meter.consume("visitor-a") == 1
    assert meter.consume("visitor-a") == 0
    assert meter.consume("visitor-a") == 0
    assert meter.remaining("visitor-b") == 2


def test_trial_meter_global_cap_blocks_every_identity():
    meter = TrialMeter(free_calls=5, global_daily_cap=2)

    assert meter.consume("visitor-a") == 4
    assert meter.consume("visitor-b") == 0
    assert meter.is_global_exhausted() is True
    assert meter.remaining("visitor-a") == 0
    assert meter.remaining("visitor-c") == 0


def test_trial_meter_resets_identity_and_global_counts_on_day_rollover():
    current_day = [date(2026, 6, 24)]
    meter = TrialMeter(
        free_calls=2,
        global_daily_cap=2,
        today=lambda: current_day[0],
    )

    assert meter.consume("visitor-a") == 1
    assert meter.consume("visitor-a") == 0
    assert meter.is_global_exhausted() is True

    current_day[0] = date(2026, 6, 25)

    assert meter.is_global_exhausted() is False
    assert meter.remaining("visitor-a") == 2
