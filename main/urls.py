from django.conf.urls import url

from .views import HomeView, CreateBackJobView, ControlChartView, MonthlyBackJobPieChart, SimulateLineGraph

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^backjob/create/$', CreateBackJobView.as_view(), name='create_backjob'),
    url(r'^backjob/weekly-graph/$', ControlChartView.as_view(), name='weekly-graph'),
    url(r'^backjob/monthly-graph/$', MonthlyBackJobPieChart.as_view(), name='monthly-graph'),
    url(r'^backjob/simulate-graph/$', SimulateLineGraph.as_view(), name='simulate-line-graph'),
]