import datetime

def delta_months(start,end = None):
    if not end: end= datetime.datetime.now()
    if not start: return None
    m = 12 * (end.year - start.year)
    m += end.month - start.month
    return m
