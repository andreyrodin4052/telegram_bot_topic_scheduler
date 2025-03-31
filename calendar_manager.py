import json
from datetime import datetime, timedelta
import os
from collections import OrderedDict

class CalendarManager:
    def __init__(self, db_file='calendar_db.json'):
        """
        Initialize the CalendarManager with a database file.

        :param db_file: A string representing the path to the JSON database file.
        """
        self.db_file = db_file
        self.calendar_db = self._load_calendar_db()

    def _load_calendar_db(self):
        """
        Load the calendar database from a JSON file.
        If the file doesn't exist, return an empty OrderedDict.
        Dates are sorted in ascending order.
        """
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as file:
                # Load the database and convert string keys back to date objects
                db = json.load(file)
                # Sort dates in ascending order
                sorted_dates = sorted(
                    (datetime.strptime(date, '%Y-%m-%d').date() for date in db.keys()),
                    key=lambda x: x
                )
                # Create an OrderedDict with sorted dates
                calendar_db = OrderedDict()
                for date in sorted_dates:
                    calendar_db[date] = db[date.isoformat()]
                return calendar_db
        return OrderedDict()

    def _save_calendar_db(self):
        """
        Save the calendar database to a JSON file.
        Convert date objects to string keys for JSON serialization.
        """
        with open(self.db_file, 'w') as file:
            # Convert date objects to string keys
            db = {date.isoformat(): events for date, events in self.calendar_db.items()}
            json.dump(db, file, indent=4)

    def add_event(self, date, event):
        """
        Add an event (string) to the calendar database for a specific date.
        Prevents adding the same event to the same date more than once.
        Maintains the calendar_db in sorted order by date.

        :param date: A string representing the date in 'YYYY-MM-DD' format.
        :param event: A string representing the event to be added.
        :return: A string indicating the result of the operation.
        """
        try:
            # Convert the date string to a datetime object to ensure it's valid
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD'."

        # If the date is not in the database, create a new list for it
        if date_obj not in self.calendar_db:
            self.calendar_db[date_obj] = []

        # Check if the event already exists for the given date
        if event in self.calendar_db[date_obj]:
            return f"Event '{event}' already exists for {date}. Skipping."

        # Add the event to the list for the given date
        self.calendar_db[date_obj].append(event)

        # Re-sort the calendar_db to maintain ascending order
        self.calendar_db = OrderedDict(sorted(self.calendar_db.items(), key=lambda x: x[0]))

        # Save the updated database to file
        self._save_calendar_db()
        return f"Event added to {date}: {event}"

    def show_events(self, date):
        """
        Display all events for a specific date.

        :param date: A string representing the date in 'YYYY-MM-DD' format.
        :return: A tuple containing:
                 - A string listing the events for the given date.
                 - A boolean indicating whether there is at least one event on the given date.
        """
        try:
            # Convert the date string to a datetime object to ensure it's valid
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD'.", False

        # Check if the date exists in the database
        if date_obj in self.calendar_db:
            events = self.calendar_db[date_obj]
            if events:
                event_list = "\n".join([f"- {event}" for event in events])
                return f"All topics to remember on {date}:\n{event_list}", True
            else:
                return f"No events found for {date}.", False
        else:
            return f"No events found for {date}.", False

    def cut_events_before_date(self, cutoff_date):
        """
        Remove all events from the calendar database that are before the given date.

        :param cutoff_date: A string representing the cutoff date in 'YYYY-MM-DD' format.
        :return: A string indicating the result of the operation.
        """
        try:
            # Convert the cutoff date string to a datetime object to ensure it's valid
            cutoff_date_obj = datetime.strptime(cutoff_date, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use 'YYYY-MM-DD'."

        # Create a list of dates to remove
        dates_to_remove = [date for date in self.calendar_db.keys() if date < cutoff_date_obj]

        # Remove the dates from the database
        for date in dates_to_remove:
            del self.calendar_db[date]

        self._save_calendar_db()
        return f"Removed all events before {cutoff_date}."

    def add_multiple(self, event, exponent_base=2, start_date=None):
        """
        Add an event to multiple dates with an exponentially growing gap between dates.

        :param event: A string representing the event to be added.
        :param exponent_base: An integer representing the base for the exponential gap.
                              Defaults to 2.
        :param start_date: A string representing the start date in 'YYYY-MM-DD' format.
                           If not provided, the current date is used.
        :return: A string indicating the result of the operation.
        """
        if start_date is None:
            # Use the current date if no start date is provided
            start_date_obj = datetime.now().date()
        else:
            try:
                # Convert the start date string to a datetime object to ensure it's valid
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return "Invalid start date format. Please use 'YYYY-MM-DD'."

        # Calculate the end date (30 years from the start date)
        end_date_obj = start_date_obj + timedelta(days=365 * 30)

        # Initialize the gap
        gap = 1

        # Add the event to dates with exponentially growing gaps
        current_date_obj = start_date_obj
        output = []
        while current_date_obj <= end_date_obj:
            result = self.add_event(current_date_obj.isoformat(), event)
            output.append(result)
            # Increment the gap exponentially using the provided base
            current_date_obj += timedelta(days=gap)
            gap *= exponent_base

        return "\n".join(output)
