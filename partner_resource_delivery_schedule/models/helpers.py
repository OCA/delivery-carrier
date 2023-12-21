# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime

from odoo import fields, models

from odoo.addons.resource.models.resource import datetime_to_string, make_aware


def get_next_available_date(
    date_from: datetime,
    date_to: datetime,
    resources: models.Model = None,
    calendars: models.Model = None,
) -> datetime:
    """Get next available date of the given resource between the given dates
    and substracting the unavailable calendars and resources

    :param date_from: Date from which to start searching
    :type date_from: datetime.datetime
    :param date_to: Date to which to stop searching
    :type date_to: datetime.datetime
    :param resources: Resources to match the next available date
    :type resources: resource.resource
    :param calendars: Calendars to match the next available date
    :type calendars: resource.calendar
    :return: Next available date
    :rtype: datetime.datetime or None
    """
    if not resources and not calendars:
        return

    aware_date_from, dummy = make_aware(date_from)
    aware_date_to, dummy = make_aware(date_to)

    intervals_list = []
    if resources:
        resource_intervals, _cwi = resources._get_valid_work_intervals(
            aware_date_from,
            aware_date_to,
        )
        intervals_list.extend(list(resource_intervals.values()))

    if calendars:
        for calendar in calendars:
            calendar_intervals = calendar._work_intervals_batch(
                aware_date_from,
                aware_date_to,
                compute_leaves=True,
            )
            for cal_interval in calendar_intervals.values():
                intervals_list.append(cal_interval)

    if not intervals_list:
        return

    availability_interval = intervals_list[0]
    for intervals in intervals_list[1:]:
        availability_interval = availability_interval & intervals

    for ds, _de, _r in availability_interval:
        return fields.Datetime.from_string(datetime_to_string(ds))
