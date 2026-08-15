class TimeService:

    def time_to_minutes(self, time_string: str) -> int:
        """
        Convert a clock time such as '12:07' into minutes
        since the start of the day.
        """
        hours, minutes = map(
            int,
            time_string.split(":")
        )

        return hours * 60 + minutes


    def minutes_to_time(self, total_minutes: int) -> str:
        """
        Convert minutes into an HH:MM clock-time string.

        This method is mainly for display. Route calculations should
        keep the original total-minute value so that trips crossing
        midnight can still be handled correctly.
        """

        # Remove complete days because HH:MM represents only clock time.
        total_minutes = total_minutes % (24 * 60)

        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f"{hours:02d}:{minutes:02d}"