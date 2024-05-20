from django.db import models

class cam1_model1(models.Model):
    item_code = models.CharField(max_length=255, null=True, blank=True)
    weight = models.CharField(max_length=255, null=True, blank=True) 
    confidence_all = models.IntegerField(null=True, blank=True)
    label_name = models.CharField(max_length=255,null=True, blank=True)
    join_detect = models.BooleanField(default=False,null=True, blank=True) 
    OK = models.BooleanField(default=False,null=True, blank=True) 
    NG = models.BooleanField(default=False,null=True, blank=True) 
    num_labels = models.IntegerField(null=True, blank=True)
    width_min = models.IntegerField(null=True, blank=True)
    width_max = models.IntegerField(null=True, blank=True)
    height_min = models.IntegerField(null=True, blank=True)
    height_max = models.IntegerField(null=True, blank=True)
    PLC_value = models.IntegerField(null=True, blank=True)
    cmpnt_conf = models.IntegerField(null=True, blank=True)

  

