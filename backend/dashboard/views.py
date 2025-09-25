from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from sensors.models import Reading, FanState, FanLog
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.db.models import Sum
from django.core.paginator import Paginator


@login_required(login_url='login')
def dashboard_view(request):
    
    readings_list = Reading.objects.all().order_by('-timestamp')
    paginator_readings = Paginator(readings_list, 10)
    page_number_readings = request.GET.get('page')
    page_obj_readings = paginator_readings.get_page(page_number_readings)

    fan_logs_list = FanLog.objects.all().order_by('-start_time')
    paginator_fan = Paginator(fan_logs_list, 10)
    page_number_fan = request.GET.get('page')
    page_obj_fan = paginator_fan.get_page(page_number_fan)

    try:
        fan_state = FanState.objects.get(id=1)
    except FanState.DoesNotExist:
        fan_state = None

    readings_json = json.dumps(list(readings_list.values()), cls=DjangoJSONEncoder)

    context = {
        'fan_state': fan_state,
        'readings_json': readings_json,
        'page_obj_readings': page_obj_readings,
        'page_obj_fan': page_obj_fan,
        'current_temperature': readings_list.first().temperature if readings_list.first() else 'N/A'
    }

    return render(request, 'dashboard/index.html', context)