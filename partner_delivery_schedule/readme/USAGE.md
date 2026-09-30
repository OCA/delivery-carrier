To use this module you need to:

1.  Go to *Contacts \> Create* or *Sales \> Orders \> Customers \>
    Create*.
2.  Go to *Sales and Purchases* tab.
3.  Create new delivery hours for this partner in *Delivery Schedule*
    field.

You can set deliveries schedule directly in *Sales \> Configuration \>
Delivery Schedule*

To configure the search horizon for the next reachable departure:

1.  Go to *Settings \> General Settings*.
2.  In the *Delivery Schedule* section, set **Delivery Departure Horizon**
    to the number of days ahead to look for an available slot
    (default: 8 days). This setting is per company.

To find the next departure for a partner:

```python
schedule, departure = partner.get_next_schedule()
```

Or on a ``delivery.schedule`` recordset:

```python
schedule, departure = schedules.get_next_schedule(
    from_date=fields.Datetime.now(),
    tz="Europe/Paris",
)
```
