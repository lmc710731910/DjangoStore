from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect

from BuyerApp.models import *
from StoreApp.views import set_password
from StoreApp.models import *

def loginValid(fun):
    def inner(request,*args,**kwargs):
        c_user = request.COOKIES.get("username")
        s_user = request.session.get("username")
        if c_user and s_user and c_user == s_user:
            return fun(request, *args, **kwargs)
        else:
            return HttpResponseRedirect("/BuyerApp/login/")
    return inner


def base(request):
    return render(request,"buyer/base.html")


def register(request):
    if request.method =="POST":
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        email = request.POST.get("email")

        buyer = Buyer()
        buyer.username = username
        buyer.password = set_password(password)
        buyer.email = email
        buyer.save()
        return HttpResponseRedirect("/BuyerApp/login/")
    return render(request,"buyer/register.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        if username and password:
            user = Buyer.objects.filter(username=username).first()
            if user:
                web_password = set_password(password)
                if user.password == web_password:
                    response = HttpResponseRedirect("/BuyerApp/index/")
                    #校验的登录
                    response.set_cookie("username",user.username)
                    request.session["username"]=user.username
                    #方便其他查询，弄个id
                    response.set_cookie("user_id",user.id)
                    return response
    return render(request,"buyer/login.html")

@loginValid
def index(request):
    goods_type_list = GoodsType.objects.all()
    return render(request,"buyer/index.html",locals())


def logout(request):
    response = HttpResponseRedirect("/BuyerApp/login")
    for key in request.COOKIES:
        response.delete_cookie(key)
    del request.session["username"]
    return response

# Create your views here.
