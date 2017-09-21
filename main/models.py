from django.db import models

class JobOrder(models.Model):
    order_number = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    datetime_filed = models.DateTimeField()
    attending_op = models.CharField(max_length=100)
    is_job_reworked = models.BooleanField(default=False)
    post_is_job_reworked = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.order_number)
