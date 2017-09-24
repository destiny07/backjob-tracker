import calendar
import datetime

import math
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

        # weekly_stat = self.get_weekly_job_stat(start_date, end_date)
        # backjob_list = weekly_stat['backjob_list']
        # total_job_list = weekly_stat['total_job_list']

        backjob_list = [2, 3, 1, 3, 6, 6, 20]
        total_job_list = [31, 25, 38, 28, 21, 25, 50]

        dataset = self.generate_graph_data(backjob_list, total_job_list)
        ucl = self.generate_graph_upper_control_limit(backjob_list, total_job_list)
        cl = self.generate_graph_center_line(backjob_list, total_job_list)

        context['start_date'] = start_date
        context['end_date'] = end_date
        context['dataset'] = dataset
        context['ucl'] = ucl['dataset']
        context['ucl_value'] = ucl['ucl_value']
        context['cl'] = cl['dataset']
        context['cl_value'] = cl['cl_value']

        return context

    def generate_graph_data(self, backjob_list, total_job_list):
        dataset = []

        # center_line = self.calculate_pbar(backjob_list, total_job_list)
        # upper_control_limit = self.calculate_ucl(center_line, total_job_list[-1])

        for i in range(0, len(total_job_list)):
            pbar = self.calculate_pbar(backjob_list[i], total_job_list[i])

            dataset.append({'x': i, 'y': pbar})

        return dataset

    def generate_graph_upper_control_limit(self, backjob_list, total_job_list):
        pbar = self.calculate_pbar(backjob_list, total_job_list)
        ucl = self.calculate_ucl(pbar, total_job_list[-1])
        upper_control_limit_dataset = []

        for i in range(0, len(total_job_list)):
            upper_control_limit_dataset.append({'x': i, 'y': ucl})

        return {'dataset': upper_control_limit_dataset, 'ucl_value': ucl}

    def generate_graph_center_line(self, backjob_list, total_job_list):
        center_line = self.calculate_pbar(backjob_list, total_job_list)
        center_line_dataset = []

        for i in range(0, len(total_job_list)):
            center_line_dataset.append({'x': i, 'y': center_line})

        return {'dataset': center_line_dataset, 'cl_value': center_line}

    def calculate_ucl(self, pbar, total_job_count):
        ucl = 0

        try:
            ucl = pbar + (3 * math.sqrt((pbar*(1-pbar))/total_job_count))
        except ZeroDivisionError as e:
            print(e)

        return ucl

    def calculate_pbar(self, backjob, total_job):
        pbar = 0

        if type(backjob) is list and type(total_job) is list:
            backjob_count = 0
            total_job_count = 0

            for job in backjob:
                backjob_count += job

            for job in total_job:
                total_job_count += job
        else:
            backjob_count = backjob
            total_job_count = total_job

        try:
            pbar = backjob_count / total_job_count
        except ZeroDivisionError as e:
            print(e)

        return pbar

    def get_weekly_job_stat(self, start_date, end_date):
        curr_start_date = start_date
        backjob_list = []
        total_job_list = []

        while curr_start_date < end_date:
            curr_end_date = curr_start_date + datetime.timedelta(days=6)
            backjob_count = self.get_total_backjob(curr_start_date, curr_end_date)
            total_job_count = self.get_total_job(curr_start_date, curr_end_date)

            backjob_list.append(backjob_count)
            total_job_list.append(total_job_count)

            curr_start_date += datetime.timedelta(days=6)

        return {'backjob_list': backjob_list, 'total_job_list': total_job_list}

    def get_total_backjob(self, start_date, end_date):
        total_job = JobOrder.objects.filter(datetime_filed__range=[start_date, end_date])
        backjob_count = 0

        for job in total_job:
            if job.is_job_reworked:
                backjob_count += 1

        return backjob_count

    def get_total_job(self, start_date, end_date):
        return JobOrder.objects.filter(datetime_filed__range=[start_date, end_date]).count()

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
        context['month'] = calendar.month_name[int(month)]
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

        job_count = self.get_total_job(start_date, end_date)
        backjob_count = self.get_total_backjob(start_date, end_date)

        non_backjob_count = job_count - backjob_count

        return {'backjob': backjob_count, 'non_backjob': non_backjob_count}

    def get_total_backjob(self, start_date, end_date):
        total_job_list = JobOrder.objects.filter(datetime_filed__range=[start_date, end_date])
        backjob_count = 0

        for backjob in total_job_list:
            if backjob.is_job_reworked:
                backjob_count += 1

        return backjob_count

    def get_total_job(self, start_date, end_date):
        return JobOrder.objects.filter(datetime_filed__range=[start_date, end_date]).count()
