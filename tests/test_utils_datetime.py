from datetime import datetime, timedelta

from migasfree.utils import time_horizon


class TestTimeHorizon:
    def test_correct_delay_excluding_weekends(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 5
        expected_date = date + timedelta(days=7)  # Expected date is 15th January 2024 (Monday)
        assert time_horizon(date, delay) == expected_date

    def test_delay_zero(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = 0
        assert time_horizon(date, delay) == date

    def test_delay_negative_one(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -1
        expected_date = date - timedelta(days=3)  # Expected date is 5th January 2024 (Friday)
        assert time_horizon(date, delay) == expected_date

    def test_delay_negative_365(self):
        date = datetime(2024, 1, 8)  # Monday
        delay = -365
        expected_date = date - timedelta(days=(365 + 146))  # Expected date is 15th August 2022 (Monday)
        assert time_horizon(date, delay) == expected_date
