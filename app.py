import re
from typing_extensions import Self
from flask import Flask, request, template_rendered
from flask import url_for, redirect, flash
from flask import render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, product
import random, string
from sqlalchemy import null
import cx_Oracle

## Oracle 連線
cx_Oracle.init_oracle_client(lib_dir="./instantclient_21_3") # init Oracle instant client 位置
connection = cx_Oracle.connect('Group6', 'group066', cx_Oracle.makedsn('140.117.69.58', 1521, 'orcl')) # 連線資訊
cursor = connection.cursor()

## Flask-Login : 確保未登入者不能使用系統
app = Flask(__name__)
app.secret_key = 'Your Key'  
login_manager = LoginManager(app)
login_manager.login_view = 'login' # 假如沒有登入的話，要登入會導入 login 這個頁面

class User(UserMixin):
    
    pass

@login_manager.user_loader
def user_loader(userid):  
    user = User()
    user.id = userid
    cursor.prepare('SELECT IDENTITY, NAME FROM MEMBER WHERE MID = :id ')
    cursor.execute(None, {'id':userid})
    data = cursor.fetchone()
    user.role = data[0]
    user.name = data[1]
    return user 

# 主畫面
@app.route('/')
def index():
    return render_template('index.html')

# 登入頁面
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        account = request.form['account']
        password = request.form['password']

        # 查詢看看有沒有這個資料
        # sql = 'SELECT ACCOUNT, PASSWORD, MID, IDENTITY, NAME FROM MEMBER WHERE ACCOUNT = \'' + account + '\''
        # cursor.execute(sql)
        cursor.prepare('SELECT ACCOUNT, PASSWORD, MID, IDENTITY, NAME FROM MEMBER WHERE ACCOUNT = :id ')
        cursor.execute(None, {'id': account})

        data = cursor.fetchall() # 抓去這個帳號的資料

        # 但是可能他輸入的是沒有的，所以下面我們 try 看看抓不抓得到
        try:
            DB_password = data[0][1] # true password
            user_id = data[0][2] # user_id
            identity = data[0][3] # user or manager

        # 抓不到的話 flash message '沒有此帳號' 給頁面
        except:
            flash('*沒有此帳號')
            return redirect(url_for('login'))

        if( DB_password == password ):
            user = User()
            user.id = user_id
            login_user(user)

            if( identity == 'user'):
                return redirect(url_for('viedostore'))
            else:
                return redirect(url_for('manager'))
        
        # 假如密碼不符合 則會 flash message '密碼錯誤' 給頁面
        else:
            flash('*密碼錯誤，請再試一次')
            return redirect(url_for('login'))

    
    return render_template('login.html')

# 註冊頁面
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_name = request.form['username']
        user_account = request.form['account']
        user_password = request.form['password']
        user_identity = request.form['identity']
        
        # 抓取所有的會員帳號，因為下面要比對是否已經有這個帳號
        check_account =""" SELECT ACCOUNT FROM MEMBER """
        cursor.execute(check_account)
        exist_account = cursor.fetchall()
        account_list = []
        for i in exist_account:
            account_list.append(i[0])

        if(user_account in account_list):
            # 如果已經有這個帳號，就會給一個 flash message : 上面會顯示已經有這個帳號了
            flash('Falid!')
            return redirect(url_for('register'))
        else:
            # 在 SQL 裡有設定 member id 是 auto increment 所以第一個值給：null
            # 可參考的設定連結：https://www.abu.tw/2008/06/oracle-autoincrement.html
            cursor.prepare('INSERT INTO MEMBER VALUES (null, :name, :account, :password, :identity)')
            cursor.execute(None, {'name': user_name, 'account':user_account, 'password':user_password, 'identity':user_identity })
            connection.commit()
            return redirect(url_for('login'))

    return render_template('register.html')

# viedo內部
@app.route('/bookstore', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def viedostore():

    # 以防管理者誤闖
    if request.method == 'GET':
        if( current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager'))

    # 查看書本的詳細資料（假如有收到 pid 的 request）
    if 'pid' in request.args:
        pid = request.args['pid']

        # 查詢這本書的詳細資訊
        cursor.prepare('SELECT * FROM PRODUCT WHERE PID = :id ')
        cursor.execute(None, {'id': pid})

        data = cursor.fetchone() 
        pname = data[1]
        price = data[2]
        category = data[3]

        product = {
            '商品編號': pid,
            '商品名稱': pname,
            '單價': price,
            '類別': category
        }

        # 把抓到的資料用 json 格式傳給 projuct.html 
        return render_template('product.html', data = product)

    # 沒有收到 pid 的 request 的話，代表只是要看所有的書
    sql = 'SELECT * FROM PRODUCT'
    cursor.execute(sql)
    viedo_row = cursor.fetchall()
    viedo_data = []
    for i in viedo_row:
        viedo = {
            '商品編號': i[0],
            '商品名稱': i[1]
        }
        viedo_data.append(viedo)

    # 抓取所有書的資料 用一個 List 包 Json 格式，在 html 裡可以用 for loop 呼叫
    return render_template('viedostore.html', viedo_data=viedo_data, user=current_user.name)

@app.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('viedostore'))

    if 'delete' in request.values: #要刪除

        pid = request.values.get('delete')

        # 看看 RECORD 裡面有沒有需要這筆產品的資料
        cursor.prepare('SELECT * FROM RECORD WHERE PID=:pid')
        cursor.execute(None, {'pid':pid})
        data = cursor.fetchone() #可以抓一筆就好了，假如有的話就不能刪除
        
        if(data != None):
            flash('faild')
        else:
            cursor.prepare('DELETE FROM PRODUCT WHERE PID = :id ')
            cursor.execute(None, {'id': pid})
            connection.commit() # 把這個刪掉

    elif 'edit' in request.values: #要修改
            pid = request.values.get('edit')
            return redirect(url_for('edit', pid=pid))

    # viedo_data = viedo()
    viedo_data = []

    return render_template('manager.html', viedo_data=viedo_data, user=current_user.name)

def viedo():
    sql = 'SELECT * FROM VIDEO'
    cursor.execute(sql)
    viedo_row = cursor.fetchall()
    viedo_data = []
    for i in viedo_row:
        viedo = {
            '商品編號': i[0],
            '商品名稱': i[1],
            '商品售價': i[2],
            '商品類別': i[3]
        }
        viedo_data.append(viedo)
    return viedo_data

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():

    # 以防使用者使用管理員功能
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('viedostore'))

    if request.method == 'POST':
        pid = request.values.get('pid')
        new_name = request.values.get('name')
        new_price = request.values.get('price')
        new_category = request.values.get('category')
        cursor.prepare('UPDATE PRODUCT SET PNAME=:name, PRICE=:price, CATEGORY=:category WHERE PID=:pid')
        cursor.execute(None, {'name':new_name, 'price':new_price,'category':new_category, 'pid':pid})
        connection.commit()
        
        return redirect(url_for('manager'))

    else:
        product = show_info()
        return render_template('edit.html', data=product)

def show_info():
    video_id = request.args['VIDEO_ID']
    cursor.prepare('SELECT * FROM PRODUCT WHERE PID = :id ')
    cursor.execute(None, {'id': video_id})

    data = cursor.fetchone() #password
    video_id = data[1]
    title = data[2]
    publish_time = data[3]

    product = {
        '影片編號': video_id,
        '影片標題': title,
        '上架日期': publish_time,
    }
    return viedo

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():

    if request.method == 'POST':
    
        cursor.prepare('SELECT * FROM PRODUCT WHERE PID=:pid')
        data = ""

        while ( data != None): #裡面沒有才跳出回圈

            number = str(random.randrange( 10000, 99999))
            en = random.choice(string.ascii_letters)
            pid = en + number #隨機編號
            cursor.execute(None, {'pid':pid})
            data = cursor.fetchone()

        name = request.values.get('name')
        price = request.values.get('price')
        category = request.values.get('category')

        if ( len(name) < 1 or len(price) < 1): #使用者沒有輸入
            return redirect(url_for('manager'))

        cursor.prepare('INSERT INTO PRODUCT VALUES (:pid, :name, :price, :category)')
        cursor.execute(None, {'pid': pid, 'name':name, 'price':price, 'category':category })
        connection.commit()

        return redirect(url_for('manager'))

    return render_template('add.html')

    user_id = current_user.id #找到現在使用者是誰
    cursor.prepare('SELECT * FROM CART WHERE MID = :id ')
    cursor.execute(None, {'id': user_id})
    data = cursor.fetchone()
    
    tno = data[2] # 使用者有購物車了，購物車的交易編號是什麼

    cursor.prepare('SELECT * FROM RECORD WHERE TNO = :id')
    cursor.execute(None, {'id': tno})
    product_row = cursor.fetchall()
    product_data = []

    for i in product_row:
        cursor.prepare('SELECT PNAME FROM PRODUCT WHERE PID = :id')
        cursor.execute(None, {'id': i[1]})
        price = cursor.fetchone()[0] 
        product = {
            '商品編號': i[1],
            '商品名稱': price,
            '商品價格': i[3],
            '數量': i[2]
        }
        product_data.append(product)
    
    cursor.prepare('SELECT SUM(TOTAL) FROM RECORD WHERE TNO = :id')
    cursor.execute(None, {'id': tno})
    total = cursor.fetchone()[0]

    return render_template('order.html', data=product_data, total=total)

@app.route('/dashboard')
@login_required
def dashboard():
    revenue = []
    dataa = []
    for i in range(1,13):
        cursor.prepare('SELECT EXTRACT(MONTH FROM ORDERTIME), SUM(PRICE) FROM ORDER_LIST WHERE EXTRACT(MONTH FROM ORDERTIME)=:mon GROUP BY EXTRACT(MONTH FROM ORDERTIME)')
        cursor.execute(None, {"mon": i})
        
        row = cursor.fetchall()
        if cursor.rowcount == 0:
            revenue.append(0)
        else:
            for j in row:
                revenue.append(j[1])
                
        cursor.prepare('SELECT EXTRACT(MONTH FROM ORDERTIME), COUNT(OID) FROM ORDER_LIST WHERE EXTRACT(MONTH FROM ORDERTIME)=:mon GROUP BY EXTRACT(MONTH FROM ORDERTIME)')
        cursor.execute(None, {"mon": i})
        
        row = cursor.fetchall()
        if cursor.rowcount == 0:
            dataa.append(0)
        else:
            for k in row:
                dataa.append(k[1])
        
    cursor.prepare('SELECT SUM(TOTAL), CATEGORY FROM(SELECT * FROM PRODUCT,RECORD WHERE PRODUCT.PID = RECORD.PID) GROUP BY CATEGORY')
    cursor.execute(None)
    row = cursor.fetchall()
    datab = []
    for i in row:
        temp = {
            'value': i[0],
            'name': i[1]
        }
        datab.append(temp)
    
    cursor.prepare('SELECT SUM(PRICE), COUNT(*), MEMBER.MID, MEMBER.NAME FROM ORDER_LIST, MEMBER WHERE ORDER_LIST.MID = MEMBER.MID AND MEMBER.IDENTITY = :identity AND ROWNUM<=5 GROUP BY MEMBER.MID, MEMBER.NAME ORDER BY SUM(PRICE) DESC')
    cursor.execute(None, {'identity':'user'})
    row = cursor.fetchall()
    datac = []
    counter = 0
    nameList = []
    countList = []
    for i in row:
        counter = counter + 1
        datac.append(i[0])
    for j in row:
        nameList.append(j[3])
    for k in row:
        countList.append(k[1])
    
    counter = counter - 1
        
    return render_template('dashboard.html', counter = counter, revenue = revenue, dataa = dataa, datab = datab, datac = datac, nameList = nameList, countList = countList)

@app.route('/logout')  
def logout():

    logout_user()  
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True #easy to debug
    app.secret_key = "Your Key"
    app.run(host="0.0.0.0", port=5000)