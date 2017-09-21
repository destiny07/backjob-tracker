import datetime
import random
import string

import time
import uuid

import os

import pytz


def random_string():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(20))

def random_boolean():
    return random.choice([True, False])

def strTimeProp(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def random_date():
    start_date = "2017/03/24 12:00 AM"
    end_date = "2017/09/20 11:59 PM"
    format = '%Y/%m/%d %I:%M %p'
    date1 = strTimeProp(start_date, end_date, format, random.random())
    res = datetime.datetime.strptime(date1, format)
    res1 = pytz.utc.localize(res)

    print('type', type(res))
    print(res)

    return res1


try:
    from django.core.wsgi import get_wsgi_application

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "graph_one.settings")

    application = get_wsgi_application()

    from main.models import JobOrder

    for i in range(0, 10):
        job_order = JobOrder()
        job_order.order_number = str(uuid.uuid1())
        job_order.customer_name = random_string()
        job_order.datetime_filed = random_date()
        job_order.attending_op = random_string()
        job_order.datetime_filed = random_date()
        job_order.is_job_reworked = random_boolean()
        job_order.post_is_job_reworked = random_boolean()

        job_order.save()

    random_date()
except AttributeError:
    pass