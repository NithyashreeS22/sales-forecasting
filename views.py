from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from random import randint
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
import io
import os
import urllib, base64
from django.conf import settings

data=pd.read_excel('./files/sales_info.xlsx',index_col='Date')
products=pd.read_excel('./files/products.xlsx')
forecast_df=pd.read_csv('./files/sales_forecasted.csv')
products=data['Product'].unique()
sales_data=dict()
sales_data=dict()
for c in products:
    sales_data[c]=data[data['Product']==c][['Qty']]

sales_data1=dict()
for product in sales_data:
    sales_data1[product]=sales_data[product].values
    sales_data1[product] = sales_data1[product].astype('float32')

cols=list(sales_data.keys())

import numpy as np
timestep = 30
Xtrain=dict()
Xtest=dict()
Ytrain=dict()
Ytest=dict()
for product in sales_data:
    X=[]
    Y=[]
    for i in range(len(sales_data1[product])- (timestep)):
        X.append(sales_data1[product][i:i+timestep])
        Y.append(sales_data1[product][i+timestep])


    X=np.asanyarray(X)
    Y=np.asanyarray(Y)


    k = 4600
    Xtrain[product] = X[:k,:,:]
    Xtest[product] = X[k:,:,:]    
    Ytrain[product] = Y[:k]    
    Ytest[product]= Y[k:]  

from keras.models import load_model
model=dict()
for product in sales_data:
    fname='./files/'+product+'.h5'
    model[product]=load_model(fname)

import pickle
f=open('./files/scaler.dat','rb')
scaler=pickle.load(f)
f=open('./files/Xin.dat','rb')
Xin=pickle.load(f)
timestep = 30
future=30

def insert_end(Xin,new_input):
    #print ('Before: \n', Xin , new_input )
    for i in range(timestep-1):
        Xin[:,i,:] = Xin[:,i+1,:]
    Xin[:,timestep-1,:] = new_input
    #print ('After :\n', Xin)
    return Xin

def productDemandByDuration(duration,products):
    a=dict()
    f=dict()
    l=len(sales_data[c])
    if products is None:
        products=sales_data.keys()
    for product in products:
        a[product]=sales_data[product][l-duration:][['Qty']].sum().values[0]
        f[product]=forecast_df[forecast_df['Product']==product][:duration]['Forecasted'].sum()
    df=pd.DataFrame(columns=['product','actual','forecasted'])
    df['Product']=a.keys()
    df['Actual']=a.values()
    df['Forecasted']=f.values()
    fig, ax = plt.subplots()
    plt.tight_layout()
    df.plot.barh(x = 'Product', y = ['Actual', 'Forecasted'], ax = ax)
    plt.rcParams["figure.figsize"] = [10, len(products)*.8]
    plt.xlabel("Quantity")
    plt.ylabel("Product")
    plt.title("Next "+str(duration)+" Days Demand vs Last "+str(duration)+ " Actual Sales")
    for p in ax.patches: 
        ax.annotate(p.get_width(), (p.get_width()*1.02,p.get_y()+.08))
    image_name = 'sample_plot.png'
    print(settings.STATIC_ROOT)
    image_path = os.path.join(settings.BASE_DIR, 'app', 'static',  'images', image_name)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    # Save the plot as a PNG file
    plt.savefig(image_path,dpi=300, bbox_inches='tight')

    return image_name

def forecastDemandByDuration(duration,products):
    a=dict()
    f=dict()
    l=len(sales_data[c])
    if products is None:
        products=sales_data.keys()
    for product in products:
        f[product]=forecast_df[forecast_df['Product']==product][:duration]['Forecasted'].sum()

    
    return f

def forecastDemandBySeason(duration,products):
    a=dict()
    f=dict()
    l=len(sales_data[c])
    if products is None:
        products=sales_data.keys()
    if duration=='Spring':
        for product in products:
            f[product]=int(forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='03') |
                                 (forecast_df['Date'].str.split('-').str[1]=='04'))]['Forecasted'].sum()*1.02)
    elif duration=='Summer':
        for product in products:
            f[product]=forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='05') |
                                 (forecast_df['Date'].str.split('-').str[1]=='06'))]['Forecasted'].sum()
    elif duration=='Monsoon':
        for product in products:
            f[product]=forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='07') |
                                 (forecast_df['Date'].str.split('-').str[1]=='08')|
                                 (forecast_df['Date'].str.split('-').str[1]=='09'))]['Forecasted'].sum()
    elif duration=='Autumn':
        for product in products:
            f[product]=int(forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='10') |
                                 (forecast_df['Date'].str.split('-').str[1]=='11'))]['Forecasted'].sum()*1.03)
    elif duration=='Winter':
        for product in products:
            f[product]=forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='12') |
                                 (forecast_df['Date'].str.split('-').str[1]=='01')|
                                 (forecast_df['Date'].str.split('-').str[1]=='01'))]['Forecasted'].sum()
    elif duration=='Spring':
        for product in products:
            f[product]=int(forecast_df[(forecast_df['Product']==product) 
                               &((forecast_df['Date'].str.split('-').str[1]=='03') |
                                 (forecast_df['Date'].str.split('-').str[1]=='04'))]['Forecasted'].sum()*1.04)

    
    return f

def homePage(request):
    return render(request,'home.html')

def registerPage(request):
    form=UserCreationForm()
    if request.method=='POST':
        form=UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    return render(request,'register.html',{'form':form})

def loginPage(request):
    if request.method=='POST':
        uname=request.POST['uname']
        pwd=request.POST['pwd']
        user=authenticate(request,username=uname,password=pwd)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,"Invalid User Name / Password")
    return render(request,'login.html')

def logoutPage(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def forecastPage(request):
    if request.method=='POST':
        product=request.POST['product']
        duration=request.POST['duration']
        imgpath={'week':'next_week.png','month':'next_month.png','quarter':'next_quarter.png','year':'next_year.png'}
        filepath={'week':'./files/all_products_next_week.pkl',
                  'month':'./files/all_products_next_month.pkl',
                  'quarter':'./files/all_products_next_quarter.pkl',
                  'year':'./files/all_products_next_year.pkl'}
        if product=='All Products':
            f=open(filepath[duration],'rb')
            data=pickle.load(f)
            sales=0
            for key in data:
                sales=round(sales+sum(data[key]['Forecasted']),0)
            path=imgpath[duration]
        else:
            f=open(filepath[duration],'rb')
            data=pickle.load(f)
            sales=0
            f=open(filepath[duration],'rb')
            sales=round(sales+sum(data[product]['Forecasted']),0)
            path=imgpath[duration]
        return render(request,'forecast.html',{'path':path,'duration':duration,'product':product,'sales':sales})
    return render(request,'forecast.html')

@login_required(login_url='login')
def compareDemand(request):
    if request.method=='POST':
        category=request.POST['category']
        if category!='all':
            products=request.POST.getlist('product')
        else:
            products=None
        duration=int(request.POST['duration'])
        image_name = productDemandByDuration(duration,products)  
        return render(request, 'compareDemands.html', {'image_name': image_name})
    return render(request, 'compareDemands.html')

@login_required(login_url='login')
def forecastDemand(request):
    if request.method=='POST':
        category=request.POST['category']
        if category!='all':
            products=request.POST.getlist('product')
        else:
            products=None
        duration=int(request.POST['duration'])
        forecasted = forecastDemandByDuration(duration,products)  
        return render(request, 'product_demand.html', {'forecasted': forecasted,'duration':duration})
    return render(request, 'product_demand.html')

@login_required(login_url='login')
def seasonalDemand(request):
    if request.method=='POST':
        category=request.POST['category']
        if category!='all':
            products=request.POST.getlist('product')
        else:
            products=None
        duration=request.POST['duration']
        forecasted = forecastDemandBySeason(duration,products)  
        return render(request, 'seasonalDemand.html', {'forecasted': forecasted,'duration':duration})
    return render(request, 'seasonalDemand.html')