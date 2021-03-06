import hashlib
from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import HttpResponseRedirect
from StoreApp.models import *

from StoreApp.models import *
from BuyerApp.models import *

def loginValid(fun):
    def inner(request,*args,**kwargs):
        c_user = request.COOKIES.get("username")
        s_user = request.session.get("username")
        if c_user and s_user and c_user == s_user:
            return fun(request, *args, **kwargs)
        else:
            return HttpResponseRedirect("/StoreApp/login/")
    return inner


def set_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode())
    result = md5.hexdigest()
    return result


def register(request):
    """
    register注册
    返回注册页面
    进行注册数据保存
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username and password:
            seller = Seller()
            seller.username = username
            seller.password = set_password(password)
            seller.nickname = username
            seller.save()
            return HttpResponseRedirect("/StoreApp/login/")
    return render(request,"store/register.html")

def login(request):
    """
    登录功能，如果登录成功，跳转到首页
    如果失败，跳转到登录页
    """
    response = render(request,"store/login.html")
    response.set_cookie("login_from","login_page")
    if request.method =="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username and password:
            #校验用户名是否存在
            user = Seller.objects.filter(username = username).first()
            if user:
                web_password = set_password(password)
                #校验请求是否来源于登录页面
                cookies = request.COOKIES.get("login_from")
                #校验密码是否正确
                if user.password ==web_password and cookies == "login_page":
                    response = HttpResponseRedirect("/StoreApp/index/")
                    #检测是否登录
                    response.set_cookie("username",username)
                    request.session["username"] = username

                    response.set_cookie("user_id", user.id)  # cookie提供用户id 方便其他功能查询
                    #校验是否有店铺
                    store = Store.objects.filter(user_id=user.id).first() #在查询店铺是否存在
                    if store:
                        response.set_cookie("has_store",store.id)
                    else:
                        response.set_cookie("has_store","")
                    return response
    return response


@loginValid
def index(request):
    """
    添加检查账号是否有店铺的逻辑
    """
    #查询当前用户是谁

    return render(request,"store/index.html")

@loginValid
def register_store(request):
    type_list = StoreType.objects.all()
    if request.method == "POST":
        post_data = request.POST  #接受post数据
        store_name = post_data.get("store_name")
        store_description = post_data.get("store_description")
        store_phone = post_data.get("store_phone")
        store_money = post_data.get("store_money")
        store_address = post_data.get("store_address")

        user_id = int(request.COOKIES.get("user_id"))  #通过cookie来得到user_id
        type_lists = post_data.getlist("type")         #通过request.post来得到类型，但是是一个列表
        store_logo = request.FILES.get("store_logo")   #通过request.FILES得到
        #保存非多对多数据
        store = Store()
        store.store_name = store_name
        store.store_description = store_description
        store.store_phone = store_phone
        store.store_money = store_money
        store.store_address = store_address
        store.user_id = user_id
        store.store_logo = store_logo
        store.save()    #保存。生成了数据库中的一条数据

        #在生成的数据当中添加多对多字段
        for i in type_lists:   #循环type列表，得到类型id
            store_type = StoreType.objects.get(id = i)  #查询类型数据
            store.type.add(store_type)   #添加到类型字段，多对多的映射
        store.save()           #保存
        response = HttpResponseRedirect("/StoreApp/index/")
        response.set_cookie("has_store",store.id)
        return response
    return render(request,"store/register_store.html",locals())

@loginValid
def add_goods(request):
    #负责添加商品
    goods_type_list = GoodsType.objects.all()
    if request.method =="POST":
        #获取post请求
        goods_name = request.POST.get("goods_name")
        goods_price = request.POST.get("goods_price")
        goods_number = request.POST.get("goods_number")
        goods_description = request.POST.get("goods_description")
        goods_date = request.POST.get("goods_date")
        goods_safeDate = request.POST.get("goods_safeDate")

        goods_type = request.POST.get("goods_type")

        goods_store = request.POST.get("goods_store")
        goods_image = request.FILES.get("goods_image")
        #开始保存数据
        goods = Goods()
        goods.goods_name = goods_name
        goods.goods_price = goods_price
        goods.goods_number = goods_number
        goods.goods_description = goods_description
        goods.goods_date = goods_date
        goods.goods_safeDate = goods_safeDate
        goods.goods_image = goods_image

        goods.goods_type = GoodsType.objects.get(id = int(goods_type))
        goods.store_id = Store.objects.get(id = int(goods_store))
        goods.save()
        #保存多对多数据
        return HttpResponseRedirect("/StoreApp/list_goods/up/")
    return render(request,"store/add_goods.html",locals())


@loginValid
def list_goods(request,state):
    """
    商品的列表页
    state 商品状态
        up 在售
        down下架
    """
    #获取两个关键字
    if state == "up":
        state_num = 1
    else:
        state_num = 0
    keywords = request.GET.get("keywords","") #查询关键词
    page_num = request.GET.get("page",1) #页码
    #查询店铺
    store_id = request.COOKIES.get("has_store")
    store = Store.objects.get(id=int(store_id))
    if keywords: #判断关键词是否存在
        goods_list = store.goods_set.filter(goods_name__contains=keywords,goods_under=state_num)#完成了模糊查询
    else: #如果关键词不存在，查询所有
        goods_list = store.goods_set.filter(goods_under=state_num)
    #分页，每页3条
    paginator = Paginator(goods_list,3)
    page = paginator.page(int(page_num))
    page_range = paginator.page_range
    #返回分页数据
    return render(request,"store/goods_list.html",{"page":page,"page_range":page_range,"keywords":keywords,"state":state})


@loginValid
def goods(request,goods_id):
    goods_data = Goods.objects.filter(id = goods_id).first()
    return render(request,"store/goods.html",locals())

@loginValid
def update_goods(request,goods_id):
    goods_data = Goods.objects.filter(id=goods_id).first()
    if request.method =="POST":
        #获取post请求
        goods_date = request.POST.get("goods_date")
        goods_safeDate = request.POST.get("goods_safeDate")
        goods_image = request.FILES.get("goods_image")
        goods_name = request.POST.get("goods_name")
        goods_price = request.POST.get("goods_price")
        goods_number = request.POST.get("goods_number")
        goods_description = request.POST.get("goods_description")

        #开始修改数据
        goods = Goods.objects.get(id=int(goods_id))   #获取当前商品
        goods.goods_name = goods_name
        goods.goods_price = goods_price
        goods.goods_number = goods_number
        goods.goods_description = goods_description
        goods.goods_date = goods_date
        goods.goods_safeDate = goods_safeDate
        if goods_image:   #如果有上传图片再发起修改
            goods.goods_image = goods_image
        goods.save()
        return HttpResponseRedirect("/StoreAapp/goods/%s/"%goods_id)
        #保存多对多数据
    return render(request,"store/update_goods.html",locals())


@loginValid
def list_goods_type(request):
    goods_type_list = GoodsType.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        picture = request.FILES.get("picture")

        goods_type = GoodsType()
        goods_type.name = name
        goods_type.description = description
        goods_type.picture = picture
        goods_type.save()
    return render(request,"store/goods_type_list.html",locals())


@loginValid
def delete_goods_type(request):
    id = int(request.GET.get("id"))
    goods = GoodsType.objects.get(id = id)
    goods.delete()
    return HttpResponseRedirect("/Store/list_goods_type/")


def base(request):
    return render(request,"store/base.html")


# def CookieTest(request):
    #查询拥有指定商品的所有

# Create your views here.


def CookieTest(request):
    #查询拥有指定商品的所有数据
    goods = Goods.objects.get(id = 1)
    store_list = goods.store_id.all()
    store_list = goods.store_id.filter()
    store_list = goods.store_id.get()
    #查询指定店铺拥有的所有商品
    store = Store.objects.get(id = 17)
    #goods_set 是多对多表的名称的小写，固定写法
    store.goods_set.get()
    store.goods_set.filter()
    store.goods_set.all()

    response = render(request,"store/Test.html",locals())
    response.set_cookie("valid","")
    return response


def set_goods(request,state):
    if state == "up":
        state_num = 1
    else:
        state_num = 0
    id = request.GET.get("id")
    referer = request.META.get("HTTP_REFERER")
    if id:
        goods = Goods.objects.filter(id=id).first()
        if state =="delete":
            goods.delete()
        else:
            goods.goods_under = state_num
            goods.save()
    return HttpResponseRedirect(referer)


def order_list(request):
    store_id = request.COOKIES.get("has_store")
    order_list = OrderDetail.objects.filter(order_id__order_status=2,goods_store=store_id)
    return render(request,"store/order_list.html",locals())

def logout(request):
    response = HttpResponseRedirect("/Store/login/")
    for key in request.COOKIES:#获取当前所有cookie
        response.delete_cookie(key)
    return response


