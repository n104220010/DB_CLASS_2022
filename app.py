import re
from typing_extensions import Self
from flask import Flask, request, template_rendered
from flask import url_for, redirect, flash
import logging
from flask import render_template

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, product
import random, string
from sqlalchemy import null
import cx_Oracle

## Oracle 連線
#cx_Oracle.init_oracle_client(lib_dir="C:\\Users\\sharo\\Documents\\GitHub\\_DB_CLASS_2022\\instantclient_21_3") # init Oracle instant client 位置
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
    print(userid)
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
                return redirect(url_for('videostore'))
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

# video內部
@app.route('/videostore', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def videostore():
    #video_id = request.args['pid']
    #video_id = request.form['pid']
    # 以防管理者誤闖
    if request.method == 'GET':
        if( current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager'))

    # 查看書本的詳細資料（假如有收到 pid 的 request）
    if 'pid' in request.args:
        #video_id = request.args['pid']
        video_id = request.form['pid']

        # 查詢VIDEO的詳細資訊
        cursor.prepare('SELECT * FROM VIDEO WHERE video_id = :video_id ')
        cursor.execute(None, {'video_id': video_id})

        data = cursor.fetchone() 
        video_id = data[0]
        title = data[1]
        publish_time = data[2]

        product = {
            '影片編號': video_id,
            '影片標題': title,
            '上架日期': publish_time
        }

        # 把抓到的資料用 json 格式傳給 projuct.html 
        return render_template('product.html', data = product)

    # 沒有收到 pid 的 request 的話，代表只是要看所有的書
    sql = 'SELECT * FROM video'
    cursor.execute(sql)
    video_row = cursor.fetchall()
    video_data = []
    for i in video_row:
        video = {
            '影片編號': i[0],
            '影片標題': i[1]
        }
        video_data.append(video)
    print(video_data)
    # 抓取所有書的資料 用一個 List 包 Json 格式，在 html 裡可以用 for loop 呼叫
    return render_template('bookstore.html', video_data=video_data, user=current_user.name)

@app.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    #print("before video")
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('videostore'))

    if 'delete' in request.values: #要刪除

        pid = request.values.get('delete')

        # 看看 RECORD 裡面有沒有需要這筆產品的資料
        cursor.prepare('SELECT * FROM DAILY_PERFORMANCE WHERE VIDEO_ID=:pid')
        cursor.execute(None, {'pid':pid})
        data = cursor.fetchone() #可以抓一筆就好了，假如有的話就不能刪除
        
        if(data != None):
            flash('faild')
        else:
            cursor.prepare('DELETE FROM VIDEO WHERE VIDEO_ID = :pid ')
            cursor.execute(None, {'pid': pid})
            connection.commit() # 把這個刪掉

    elif 'edit' in request.values: #要修改
            pid = request.values.get('edit')
            return redirect(url_for('edit', pid=pid))
    video_data = video()
    #print(video_data)
    #video_data = []

    return render_template('manager.html', video_data=video_data, user=current_user.name)

def video():
    sql = 'SELECT * FROM VIDEO'
    app.logger.info(sql)
    cursor.execute(sql)
    video_row = cursor.fetchall()
    video_data = []
    for i in video_row:
        app.logger.info(i)
        video = {
            '影片編號': i[0],
            '影片標題': i[1],
            '上架日期': i[2]
        }
        video_data.append(video)
    return video_data

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():

    # 以防使用者使用管理員功能
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('videostore'))

    if request.method == 'POST':
        video_id = request.values.get('video_id')
        new_title = request.values.get('title')
        new_publish_time = request.values.get('publish_time')
        cursor.prepare('UPDATE VIDEO SET TITLE=:new_title, PUBLISH_TIME=:new_publish_time WHERE VIDEO_ID=:video_id')
        cursor.execute(None, {'new_title':new_title, 'new_publish_time':new_publish_time, 'video_id':video_id})
        connection.commit()
        
        return redirect(url_for('manager'))

    else:
        product = show_info()
        return render_template('edit.html', data=product)

def show_info():
    video_id = request.args['pid']
    #print(video_id)
    cursor.prepare('SELECT * FROM VIDEO WHERE VIDEO_ID = :video_id ')
    cursor.execute(None, {'video_id': video_id})

    data = cursor.fetchone() #password
    video_id = data[0]
    title = data[1]
    publish_time = data[2]

    product = {
        '影片編號': video_id,
        '影片標題': title,
        '上架日期': publish_time,
    }
    return product

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():

    if request.method == 'POST':
    
        cursor.prepare('SELECT * FROM VIDEO WHERE VIDEO_ID=:pid')
        data = ""

        while ( data != None): #裡面沒有才跳出回圈

            number = str(random.randrange( 10000, 99999))
            en = random.choice(string.ascii_letters)
            pid = en + number #隨機編號
            cursor.execute(None, {'pid':pid})
            data = cursor.fetchone()

        title = request.values.get('title')
        publish_time = request.values.get('publish_time')
        
        if ( len(title) < 1 or len(publish_time) < 1): #使用者沒有輸入
            return redirect(url_for('manager'))

        cursor.prepare('INSERT INTO VIDEO (video_id, title, publish_time) VALUES (:pid, :title, :publish_time)')
        cursor.execute(None, {'pid': pid, 'title':title, 'publish_time':publish_time })
        connection.commit()

        return redirect(url_for('manager'))

    return render_template('add.html')

@app.route('/dashboard')
@login_required
def dashboard():
    revenue = []
    dataa = []
    for i in range(1,13):
        pDate="2021/{:02d}".format(i)
        print(pDate)
        cursor.prepare('SELECT SUM(VIDEO_LIKES_ADDED) FROM DAILY_PERFORMANCE WHERE substr(PERFORMANCE_DATE,1,7)=:pDate')
        cursor.execute(None, {"pDate": pDate})
        
        row = cursor.fetchall()
        if cursor.rowcount == 0:
            revenue.append(0)
        else:
            for j in row:
                revenue.append(j[0])
    """                   
        cursor.prepare('SELECT TO_DATE(TO_DATE(PERFORMANCE_DATE,''YYYY/MM/DD''),''MM''), SUM(VIDEO_LIKES_ADDED) FROM DAILY_PERFORMANCE WHERE TO_DATE(TO_DATE(PERFORMANCE_DATE,''YYYY/MM/DD''),''MM'')=:mon GROUP BY TO_DATE(TO_DATE(PERFORMANCE_DATE,''YYYY/MM/DD''),''MM'')')
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
    """
    #counter = counter - 1
    counter = 12
    print(revenue)    
    datab = []
    datac = []
    nameList = []
    countList = []
    return render_template('dashboard.html', counter = counter, revenue = revenue, dataa = dataa, datab = datab, datac = datac, nameList = nameList, countList = countList)

@app.route('/logout')  
def logout():

    logout_user()  
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True #easy to debug
    #handler = logging.FileHandler('c://flask.log', encoding='UTF-8')
    #handler.setLevel(logging.DEBUG) # 設定日誌記錄最低級別為DEBUG，低於DEBUG級別的日誌記錄會被忽略，不設定setLevel()則預設為NOTSET級別。
    #logging_format = logging.Formatter(
    #    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    #handler.setFormatter(logging_format)
    #app.logger.addHandler(handler)
    app.secret_key = "Your Key"
    app.run(host="0.0.0.0", port=5001)