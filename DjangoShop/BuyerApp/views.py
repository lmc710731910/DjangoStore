import time
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect
from django.db.models import Sum

from alipay import AliPay

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
    """
    前台首页
    """
    result_list = [] #定义一个容器用来存放结果
    goods_type_list = GoodsType.objects.all() #查询所有的类型
    for goods_type in goods_type_list: #循环类型
        goods_list = goods_type.goods_set.values()[:4] #查询前4条
        if goods_list: #如果类型对应的值
            goodsType = {
                "id": goods_type.id,
                "name": goods_type.name,
                "description": goods_type.description,
                "picture": goods_type.picture,
                "goods_list": goods_list
            } #构建输出结果
             #查询类型当中有数据的数据
            result_list.append(goodsType) #有数据的类型放入result_list
    return render(request,"buyer/index.html",locals())


@loginValid
def goods_list(request):
    """
    前台列表页
    :param reuqest:
    :return:
    """
    goodsList = []
    type_id = request.GET.get("type_id")
    #获取类型
    goods_type = GoodsType.objects.filter(id = type_id).first()
    if goods_type:
        #查询所有上架的产品
        goodsList = goods_type.goods_set.filter(goods_under=1)
    return render(request,"buyer/goods_list.html",locals())


def logout(request):
    response = HttpResponseRedirect("/BuyerApp/login")
    for key in request.COOKIES:
        response.delete_cookie(key)
    del request.session["username"]
    return response


def pay_order(request):
    money = request.GET.get("money")
    order_id = request.GET.get("order_id")

    alipay_public_key_string = """-----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvDLACgfW7LL0fImgia0Pr7mEXmGJWxxy15RSvCuy2O4Qq+eAdBKw1yMOaHTeBTrWNDv6iBk+EyNuSs2CdMFwdHXF3GCmyLTm+SXXrDY016DaHFSQJPKplh0UrkcI8GvriWpCdbOSPBuoSgBShugyP9hz2ua05+ilJ9eBolrYVLNWDByPrsnbXXuHmIc8QdYj3NYq20e790feJgJaTCt1lthoh5T7DShGiEDC33cRGHzDo4YV4LKg5Azy+xbc8EdMI972U4rnWpzc5pulG7YMHnjJZmad3Z7hiegWFoAkUd+wClfwvj3HS6vTLgkzFapHmVCLocuL/L6eIZbZPjQ8yQIDAQAB
    -----END PUBLIC KEY-----"""

    app_private_key_string = """-----BEGIN RSA PRIVATE KEY-----
    MIIEowIBAAKCAQEAvDLACgfW7LL0fImgia0Pr7mEXmGJWxxy15RSvCuy2O4Qq+eAdBKw1yMOaHTeBTrWNDv6iBk+EyNuSs2CdMFwdHXF3GCmyLTm+SXXrDY016DaHFSQJPKplh0UrkcI8GvriWpCdbOSPBuoSgBShugyP9hz2ua05+ilJ9eBolrYVLNWDByPrsnbXXuHmIc8QdYj3NYq20e790feJgJaTCt1lthoh5T7DShGiEDC33cRGHzDo4YV4LKg5Azy+xbc8EdMI972U4rnWpzc5pulG7YMHnjJZmad3Z7hiegWFoAkUd+wClfwvj3HS6vTLgkzFapHmVCLocuL/L6eIZbZPjQ8yQIDAQABAoIBAFft7kPBfe2BfzFgrB0nOpkDuJDQSXjERfPrXOyGDj3EnQ10UFPrF6ysuGKdl84hu0sUau2Dvbj7aOCSPE2Iw53mGNfqYIKN4wytXaMcgHvur3llGSPqLMnyNGNo1Qhfo+DEQOD1UXG8Cljo5aYafr/NxfOUrxlbXS7MRckxYLnRc1T11pLLTFviu+RfIHnEJfPLhWsOUE/IHtUNxwDTWf02McTFYKLVZaJt0gFQrXTfEWLYF907mcewQMWrlEMa40n4vr/Hm91XCfdACQXslTfmg4jZu1hvW9E/nXSAOMz5SjEJtWOf5mYtTN3YE+ij1Yj3eA6mgjmEhI+szcpPh3ECgYEA3tPdWdp/Ba069xreCkRoF895ZJvQLdLBvXdo4yaHO/twrJxEEJYP8jWk4p22tKcR5URlZaBL5tlN4ssFZyaezHhkasPWt9Wis7xu7YkzHb0RQZALexd3/WlxV50y9duEs31X/mYH/GpbtDAt6G0HwPF2N5+EFSwcynCuI5IVsKsCgYEA2DciL7Q9MoflIqQG/lkF1/Mho3JNJ+Rx8K7C93n2iUL7hg1vK1df9WpKX63H3Mf+spz7vuNem8hhSZeJERIicT/C11ZDjiclxnUrNbu7dKWYZPZiDoX8t+lBaiGzzgFKTkwn/Xg8qigDJSby/Mye7fOw/CwG6dKMgcGNRDXbUFsCgYEAueSiG13u7jtwn8moR4R+Gq8ZpNdgO3pB6uB9flMcKuw/OaE8H2Ixd21NW0kbrWZbxZrjxH6QE8xh77xTi5RqkkY17+Plc4QksjGXkU8Od9bNWJblHRGdJqoaxm78nqM998ev6yoPq4LHcnFnOyoKd+p5JzpKpKcidbi/bilnMvUCgYB1j7TE32mO+hj6dtlenqTwwEAAEPwmvq29Qii8StJj28nLH67ckAua8woxb9oGD7BLCdRP/GzKo29ShlR+ta+IiDS2xS7CMkL132t5MfRA/nEYJGc4ol3A2dE5lc2gK09ttzbfOOszUcI0BzODhPa9Rw1qb73qkRLY0pavCeGPlQKBgDlhWpx14brUiybP5+YrzY4EYmOZ+QhzwOVZiPz6eFZANnkNfmVN6gpEs/CaIzArGeIpn0MH6Qnk8DZcuPDyb9Yxj1evK3K5GrentiSUERV+/fVs0TpJhAGetEeZXWMjyfbfqiC9w3Ixg4eDoDBAyifQloMEifWLLEzknsf2VpWU
    -----END RSA PRIVATE KEY-----"""

    #实例化支付应用
    alipay = AliPay(
        appid="2016101000652507",
        app_notify_url=None,
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2"
    )

    # 发起支付请求
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id,  # 订单号
        total_amount=str(money),  # 支付金额
        subject="SKⅡ官方旗舰店",  # 交易主题
        return_url="http://127.0.0.1:8000/BuyerApp/pay_result/",
        notify_url="http://127.0.0.1:8000/BuyerApp/pay_result/"
    )

    order = Order.objects.get(order_id=order_id)
    order.order_status=2
    order.save()

    return HttpResponseRedirect("https://openapi.alipaydev.com/gateway.do?" + order_string)


def goods_detail(request):
    goods_id = request.GET.get("goods_id")
    if goods_id:
        goods = Goods.objects.filter(id=goods_id).first()
        if goods:
            return render(request,"buyer/goods_detail.html",locals())
    return HttpResponse("没有您指定的商品")

def setOrderId(user_id,goods_id,store_id):
    '''
    设置订单编号
    时间+ 用户id + 商品id + 商店id +
    '''
    strtime = time.strftime("%Y%m%d%H%M%S",time.localtime())
    return strtime + str(user_id) + str(goods_id) + str(store_id)


def place_order(request):
    if request.method == "POST":
        #post数据
        count = int(request.POST.get("count"))
        goods_id = request.POST.get("goods_id")
        #cookie的数据
        user_id = request.COOKIES.get("user_id")
        #数据库的数据
        goods = Goods.objects.get(id = goods_id)
        store_id = goods.store_id.id #获取商品对应的商店的id
        price = goods.goods_price
        #保存订单
        order = Order()
        order.order_id = setOrderId(str(user_id),str(goods_id),str(store_id))
        order.goods_count = count
        order.order_user = Buyer.objects.get(id = user_id)
        order.order_price = count*price
        order.order_status=1
        order.save()
        #订单详情
        order_detail = OrderDetail()
        order_detail.order_id = order
        order_detail.goods_id = goods_id
        order_detail.goods_name = goods.goods_name
        order_detail.goods_price = goods.goods_price
        order_detail.goods_number = count
        order_detail.goods_total = count*goods.goods_price
        order_detail.goods_store = store_id
        order_detail.goods_image = goods.goods_image
        order_detail.save()

        detail = [order_detail]
        return render(request,"buyer/place_order.html",locals())
    else:
        order_id = request.GET.get("order_id")
        if order_id:
            order = Order.objects.get(id = order_id)
            detail = order.orderdetail_set.all()
            return render(request,"buyer/place_order.html", locals())
        else:
            return HttpResponse("非法请求")

def pay_result(request):

    return render(request,"buyer/pay_result.html",locals())



def cart(request):
    user_id = request.COOKIES.get("user_id")
    goods_list = Cart.objects.filter(user_id=user_id)
    if request.method =="POST":
        post_data = request.POST
        cart_data = []  #收集前端传递过来的商品
        for k,v in post_data.items():
            if k.startswith("goods_"):
                cart_data.append(Cart.objects.get(id = int(v)))
        goods_count = len(cart_data) #提交过来的数据的总的数量
        goods_total = sum([int(i.goods_total) for i in cart_data])#订单的总价

        #修改使用聚类查询，返回指定商品的总价
        #1、查询到所有的商品
        # cart_data = [] #收集前端传递过来的商品id
        # for k,v in post_data.items():
        #     if k.startswith("goods_"):
        #         cart_data.append(int(v))
        # #2、使用in 方法进行范围的划定，然后使用Sum方法进行计算
        # cart_goods = Cart.objects.filter(id__in=cart_data).aggregate(Sum("goods_total")) #获取到总价
        # print(cart_goods)

        #保存订单
        order = Order()
        order.order_id = setOrderId(user_id,goods_count,"2")
        #订单当中有多个商品或者多个店铺，使用goods_count来代替商品id，用“2”代替店铺id
        order.goods_count = goods_count
        order.order_user = Buyer.objects.get(id=user_id)
        order.order_price = goods_total
        order.order_status = 1
        order.save()

        #保存订单详情
        #这里的detail是购物车里的实例数据，不是商品的实例
        print(cart_data)
        for detail in cart_data:
            order_detail = OrderDetail()
            order_detail.order_id = order  #order是一条订单数据
            order_detail.goods_id = detail.goods_id
            order_detail.goods_name = detail.goods_name
            order_detail.goods_price = detail.goods_price
            order_detail.goods_number = detail.goods_number
            order_detail.goods_total = detail.goods_total
            order_detail.goods_store = detail.goods_store
            order_detail.goods_image = detail.goods_picture
            order_detail.save()
        #order是一条订单支付页！！！
        url = "/BuyerApp/place_order/?order_id=%s"%order.id
        return HttpResponseRedirect(url)
    return render(request,"buyer/cart.html",locals())

def add_cart(request):
    result = {"state":"error","data":""}
    if request.method =="POST":
        #request请求得到
        count = int(request.POST.get("count"))
        goods_id = request.POST.get("goods_id")
        #数据库查询得到
        goods = Goods.objects.get(id = int(goods_id))
        #cookies数据
        user_id = request.COOKIES.get("user_id")

        cart = Cart()
        cart.goods_name = goods.goods_name
        cart.goods_price = goods.goods_price
        cart.goods_total = goods.goods_price*count
        cart.goods_number = count
        cart.goods_picture = goods.goods_image
        cart.goods_id = goods.id
        cart.goods_store = goods.store_id.id
        cart.user_id = user_id
        cart.save()
        result["state"] = "success"
        result["data"] = "商品添加成功"
    else:
        result["error"] = "请求错误"
    return JsonResponse(result)

# def



# Create your views here.
