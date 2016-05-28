# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.hashers import make_password
from MyApp.qrCode import generate_qrcode
from MyApp.handle import *
from forms import *

# 输出日志信息
logger = logging.getLogger('MyApp.views')


def index(request):
    try:
        if not request.user.is_authenticated():
            return redirect('login.html')

    except Exception as e:
        logger.error(e)
    return render(request, 'index.html', locals())


# 注册
def do_register(request):
    try:
        if request.method == 'POST':
            registerForm = RegisterForm(request.POST)
            # 注册
            if registerForm.is_valid():
                user = User.objects.create(
                    username=registerForm.cleaned_data["username"],
                    email=registerForm.cleaned_data["email"],
                    password=make_password(registerForm.cleaned_data["password"]),
                )
                user.save()

                # 登录
                user.backend = 'django.contrib.auth.backends.ModelBackend'  # 指定默认的登录验证方式
                login(request, user)
                return redirect('index')
        else:
            registerForm = RegisterForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'register.html', locals())


# 登陆
def do_login(request):
    try:
        if request.method == 'POST':
            loginForm = LoginForm(request.POST)
            if loginForm.is_valid():
                # 登录
                username = loginForm.cleaned_data["username"]
                password = loginForm.cleaned_data["password"]
                user = authenticate(username=username, password=password)
                if user is not None:
                    user.backend = 'django.contrib.auth.backends.ModelBackend'  # 指定默认的登录验证方式
                    login(request, user)
                    return redirect('index.html')
            else:
                return render(request, 'login.html', {
                    "loginForm": loginForm,
                    "loginFailed": "账户或密码错误",
                })
        else:
            loginForm = LoginForm()
    except Exception as e:
        logger.error(e)
    return render(request, 'login.html', locals())


# 注销
def do_logout(request):
    try:
        logout(request)
    except Exception as e:
        logger.error(e)
    return redirect('login.html')


# 添加模型
def add_model(request):
    try:
        if request.user.is_authenticated():
            if request.method == 'POST':
                uploadForm = UploadForm(request.POST, request.FILES)
                if uploadForm.is_valid():
                    bundle = Bundle.objects.create(id_user=request.user,
                                                   name=uploadForm.cleaned_data["modelName"],
                                                   model=uploadForm.cleaned_data["model"],
                                                   note=uploadForm.cleaned_data["note"],
                                                   )
                    api = api_url_maker(str(bundle.id))  # 自定义的方法
                    generate_qrcode(api, str(bundle.QRCode)[8:])  # 去除路径只保留文件名
                    bundle.imageTarget = bundle.QRCode
                    config_info_json_data = ar_config_info_handle(bundle.imageTarget, bundle.model)
                    bundle.config_info = config_info_json_data
                    bundle.save()
                    return redirect('view-model.html?bundle_id=' + str(bundle.id))
            else:
                uploadForm = UploadForm()
        else:
            return redirect('login.html')
    except Exception as e:
        logger.error(e)
    return render(request, 'add-model.html', locals())


# 删除模型
def delete_model(request):
    try:
        if request.user.is_authenticated():
            bundle_id = request.GET.get('bundle_id')
            if bundle_id is not None and Bundle.objects.filter(id=bundle_id):
                model = Bundle.objects.get(id=bundle_id)
                comments = Bundle.objects.get(id=bundle_id).comment_set.all()
                Scans = Bundle.objects.get(id=bundle_id).scan_set.all()
                model.model.delete(save=True)
                model.QRCode.delete(save=True)
                model.imageTarget.delete(save=True)
                Scans.delete()
                comments.delete()
                model.delete()
            else:
                return redirect('login.html')
    except Exception as e:
        logger.error(e)
    return redirect('models.html')


# 展示模型列表
def models(request):
    try:
        if request.user.is_authenticated():
            models_list = User.objects.get(
                username=request.user
            ).bundle_set.all()
        else:
            return redirect('login.html')
    except Exception as e:
        logger.error(e)
    return render(request, 'models.html', locals())


def view_model(request):
    try:
        if request.user.is_authenticated():
            bundle_id = request.GET.get('bundle_id')
            if bundle_id is not None and Bundle.objects.filter(id=bundle_id):
                model = Bundle.objects.get(id=bundle_id)
                qrCodePath = model.QRCode.url
                imageTargetPath = model.imageTarget.url
            else:
                redirect('404.html')
        else:
            redirect('login.html')
    except Exception as e:
        logger.error(e)
    return render(request, 'view-model.html', locals())


# 用户账户
def my_account(request):
    return render(request, 'my-account.html', locals())


# 编辑账户
def edit_profile(request):
    return render(request, 'edit-profile.html', locals())


# 帮助页面
def help_page(request):
    return render(request, 'help.html', locals())


# AR模型api
def ar_config_info_api(request):
    try:
        bundle_id = request.GET.get('bundle_id')
        if bundle_id is not None and Bundle.objects.filter(id=bundle_id):
            bundle = Bundle.objects.get(id=bundle_id)
            config_info = bundle.config_info
            return HttpResponse(config_info)
    except Exception as e:
        logger.error(e)
    return HttpResponse('error')
