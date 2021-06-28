from django.shortcuts import render, HttpResponse
import random
from utils.tencent.sms import send_sms_single
from django.conf import settings
from django import forms
from app01 import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import redis
from django.http import JsonResponse
import re

conn = redis.Redis(host='localhost', port=6379, decode_responses=True)


class RegisterModelForm(forms.ModelForm):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput())

    confirm_password = forms.CharField(
        label='重复密码',
        widget=forms.PasswordInput())
    code = forms.CharField(
        label='验证码',
        widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)

    def clean(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        password = self.cleaned_data.get('password')
        phone = self.cleaned_data.get('mobile_phone')
        code = self.cleaned_data.get('code')
        print(code, conn.get(phone))
        if code != conn.get(phone):
            raise ValidationError('验证码有误')
        if password != confirm_password:
            raise ValidationError('两次密码不一致')
        return self.cleaned_data


def register(request):
    form = RegisterModelForm()
    if request.method == 'POST':
        form = RegisterModelForm(request.POST)
        if form.is_valid():
            return HttpResponse("注册成功")
    return render(request, 'app01/register.html', {'form': form})


def send_sms(request):
    """ 发送短信
        ?tpl=login  -> 548762
        ?tpl=register -> 548760
    """
    tpl = request.GET.get('tpl')
    phone_number = request.GET.get('phone')
    template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    if not template_id:
        return HttpResponse('模板不存在')
    if not re.match(r'^(1[3|4|5|6|7|8|9])\d{9}$', phone_number):
        return JsonResponse({'status': -1, 'msg': '手机号码有误！'})

    code = random.randrange(1000, 9999)
    # res = send_sms_single('17866553115', template_id, [code, 5])
    print(code)
    conn.set(phone_number, code, ex=60)
    res = {
        'result': 0
    }
    if res['result'] == 0:
        return JsonResponse({'status': 0})
    else:
        return JsonResponse({'status': -1, 'msg': '手机号码有误！'})
