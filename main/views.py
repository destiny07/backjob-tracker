import calendar
import datetime

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from .models import JobOrder


class HomeView(TemplateView):
    template_name = 'home.html'


class CreateBackJobView(View):

    def get(self, request):
        return TemplateResponse(request, 'create.backjob.html', {})

    def post(self, request, *args, **kwargs):
        order_number = request.POST.get('order_number', '')
        customer_name = request.POST.get('customer_name', '')
        datetime_filed = request.POST.get('datetime_filed', '')
        attending_op = request.POST.get('attending_op', '')
        is_job_reworked = request.POST.get('is_job_reworked', False)
        post_is_job_reworked = request.POST.get('post_is_job_reworked', False)

        try:
            back_job = JobOrder()

            back_job.order_number = order_number
            back_job.customer_name = customer_name
            back_job.datetime_filed = datetime.datetime.strptime(datetime_filed, "%Y-%m-%dT%H:%M")
            back_job.attending_op = attending_op
            back_job.is_job_reworked = is_job_reworked
            back_job.post_is_job_reworked = post_is_job_reworked

            back_job.save()
        except ValidationError:
            pass

        return HttpResponse(order_number)


class ControlChartView(TemplateView):
    template_name = 'line.graph.html'

    def get_context_data(self, **kwargs):
        context = super(ControlChartView, self).get_context_data(**kwargs)

        try:
            if self.request.GET:
                date_arg = self.request.GET['date']
                date = datetime.datetime.strptime(date_arg, '%Y-%m-%d')
            else:
                date = timezone.now()
        except KeyError:
            date = timezone.now()

        start_date = self.get_start_date(date)
        end_date = self.get_end_date(date)

        context['start_date'] = start_date
        context['end_date'] = end_date
        context['data'] = self.generate_data(start_date, end_date)

        return context

    def generate_data(self, start_date, end_date):
        curr_start_date = start_date

        week_no = 1
        previous_y = 0

        data = []

        while curr_start_date < end_date:
            curr_end_date = curr_start_date + datetime.timedelta(days=6)
            weekly_backjobs = self.get_back_job(curr_start_date, curr_end_date)

            if weekly_backjobs:
                proportion_of_backjob = self.calculate_weekly_score(weekly_backjobs)
                previous_y = proportion_of_backjob
            else:
                proportion_of_backjob = previous_y

            data.append({'x': week_no, 'y': proportion_of_backjob})
            week_no += 1
            curr_start_date += datetime.timedelta(days=7)

        return data

    def get_start_date(self, date):
        weekday = date.weekday()
        first_weekday_date = date - datetime.timedelta(days=weekday)

        # get date six months ago
        start_date = first_weekday_date - datetime.timedelta(6 * 365 / 12)

        return start_date

    def get_end_date(self, date):
        weekday = date.weekday()
        first_weekday_date = date - datetime.timedelta(days=weekday)
        end_date = first_weekday_date + datetime.timedelta(days=6)

        return end_date

    def calculate_weekly_score(self, weekly_backjobs):
        num_of_yes = 0
        num_of_no = 0

        for backjob in weekly_backjobs:
            if backjob.is_job_reworked:
                num_of_yes += 1
            else:
                num_of_no += 1

        try:
            proportion_of_backjob = num_of_yes / (num_of_yes + num_of_no)
        except ZeroDivisionError:
            proportion_of_backjob = 0

        return proportion_of_backjob

    def get_back_job(self, start_date, end_date):
        return JobOrder.objects.filter(datetime_filed__range=[start_date, end_date])

    def get_date_range(self, date):
        return (date - datetime.timedelta(6*365/12))


class MonthlyBackJobPieChart(TemplateView):
    template_name = 'pie.chart.html'

    def get_context_data(self, **kwargs):
        context = super(MonthlyBackJobPieChart, self).get_context_data(**kwargs)

        try:
            if self.request.GET:
                year = self.request.GET['year']
                month = self.request.GET['month']
            else:
                year = datetime.datetime.today().year
                month = datetime.datetime.today().month
        except KeyError:
            year = datetime.datetime.today().year
            month = datetime.datetime.today().month

        data = self.generate_data(int(year), int(month))

        context['year'] = year
        context['month'] = month
        context['backjob_score'] = data['backjob']
        context['non_backjob_score'] = data['non_backjob']

        return context

    def generate_data(self, year, month):
        date = datetime.datetime(year, month, 1)
        weekday = date.weekday()
        start_date = date - datetime.timedelta(days=weekday)

        month_last_day = calendar.monthrange(year, month)
        month_last_date = datetime.datetime(year, month, month_last_day[1])
        weekday_month_last_date = month_last_date.weekday()
        weekday_difference = 6 - weekday_month_last_date
        end_date = month_last_date + datetime.timedelta(days=weekday_difference)

        backjob_list = self.get_backjob(start_date, end_date)
        backjob_count = 0

        for backjob in backjob_list:
            if backjob.is_job_reworked:
                backjob_count += 1

        non_backjob_count = backjob_list.count() - backjob_count

        return {'backjob': backjob_count, 'non_backjob': non_backjob_count}

    def get_backjob(self, start_date, end_date):
        return JobOrder.objects.filter(datetime_filed__range=[start_date, end_date])
