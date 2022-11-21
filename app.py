from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, session, url_for,make_response
from werkzeug.security import check_password_hash
import os
import uuid
import jwt
import json
import helper

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

db = helper.initializeOrderDb()
@app.before_request
def before_request_func():
    if not 'menus' in session:
        menus = []
        adminMenu = { 'admin': [
                            { 'index': 1, 'active' : False, 'url': url_for('customers'), 'title': 'Customers' },
                            { 'index': 2, 'active' : False, 'url': url_for('catalogs'), 'title': 'Catalogs' },
                            { 'index': 3, 'active' : False, 'url': url_for('orders'), 'title': 'Orders' }
        ]}
        menus.append(adminMenu)
        userMenu = { 'user':[
            { 'index': 1, 'active' : False, 'url': url_for('myOrder'), 'title': 'My Orders' },
            { 'index': 2, 'active' : False, 'url': url_for('aboutUs'), 'title': 'About Us' }
        ]}
        menus.append(userMenu)
        session['menus'] = menus

@app.route('/')
def index():
    menus = session['menus']
    if 'token' in session:
        auth = json.loads(session['token'])
        user = auth['user']

        return render_template('index.html', user = user, menus =menus)

    return render_template('index.html', menus =menus)    

@app.route('/customers')
def customers():
    menus = helper.getMenusItem('admin',1)
   
    user = None
    if 'token' in session:
        auth = json.loads(session['token'])
        user = auth['user']
       
    else:
        return redirect(url_for('adminLogin'))

    if user:
        customers = helper.getCustomers(db, user['branch'])
        return render_template('customerList.html', user = user, data = customers, menus =menus)

    app.logger.info('User %s visited to customers...', user['userName']) 
    session['redirectAfterAuth'] = request.url
    return redirect(url_for('adminLogin'))  

@app.route('/catalogs', defaults={'id': None},methods=['GET','POST'])
@app.route('/catalogs/<id>',methods=['GET','POST'])
def catalogs(id):
    menus = helper.getMenusItem('admin',2)

    user = None
    if request.method == 'GET':
        if 'token' in session:
            auth = json.loads(session['token'])
            user = auth['user']
        else:
            return redirect(url_for('adminLogin'))       

        catalogs = helper.getCatalogs(db)
        catalog = None
        if id:
          catalog = list(filter(lambda u: u['id'] == id, catalogs))[0]
 
        return render_template('catalog.html', user = user, data= catalogs, catalog = catalog, menus =menus)     
    else:
        item = request.form['catalogName']
        unitInstock =  int(request.form['unitsInstock'])
        unitPrice = float(request.form['unitPrice'])
        depositRate = 0.0
        if request.form['depositRate']:
            depositRate = float(request.form['depositRate'])

        rentOnly = 0
        buyOnly = 0
        cuttingOnly = 0
        if 'forRentOnly' in request.form and request.form['forRentOnly'] == 'on':
            rentOnly = 1

        if 'forPurchaseOnly' in request.form and request.form['forPurchaseOnly'] == 'on':
            buyOnly = 1

        if 'forCuttingOnly' in request.form and request.form['forCuttingOnly'] == 'on':    
            cuttingOnly = 1

        if id:
           status,error = helper.updateCatalog(db,id, item,unitPrice, depositRate,rentOnly,buyOnly,cuttingOnly)
        else:
           status,error =  helper.newCatalog(db,item, unitInstock,unitPrice, depositRate,rentOnly,buyOnly,cuttingOnly)

        if status == 200:
            db.commit()

        return redirect(url_for('catalogs'))

@app.route('/orders')
def orders():
    menus =helper.getMenusItem('admin',3)

    user = None
    if 'token' in session:
        auth = json.loads(session['token'])
        user = auth['user']
    else:
        return redirect(url_for('adminLogin'))    

    if user:
        orders = helper.getOrders(db, user['branch'])
        return render_template('orderList.html', user = user, data = orders, menus =menus)

    session['redirectAfterAuth'] = request.url
    return redirect(url_for('adminLogin'))    

@app.route('/<customerId>/order/<orderId>/')
def orderDetails(orderId, customerId):
    menus =helper.getMenusItem('admin',3)
    user = None
    if 'token' in session:
        auth = json.loads(session['token'])
        user = auth['user']
    else:
        return redirect(url_for('adminLogin'))  

    if user:
        order = helper.getOrder(db, orderId)
        details = helper.getOrderDetails(db,orderId)
        customer = helper.getCustomer(db,customerId)
        datas = {'customer': customer, 'order': order, 'items': details}
        return render_template('orderDetails.html', user = user, data = datas, menus =menus)  

@app.route('/myOrder')
def myOrder():
    menus = helper.getMenusItem('user',1)
    custId = str(uuid.uuid4())
    order = {
        'customer': {
            'id': custId,
            'firstName' : '',
            'lastName' : '',
            'institution': '',
            'major': '',
            'gender': '',
            'degree': '',
            'weight': '',
            'height': '',
            'mobileNo': '',
            'lineId' : ''
        },
        'items': helper.getCatalogsViewModel(db),
        'id': str(uuid.uuid4()),
        'customerId': custId,
        'orderLocation': '',
        'orderKind': '',
        'shipping': {
            'address': ''
        },
        'color': '',
        'status': 'open'
    }
    app.logger.info('Someone visited to my orders...') 
    return render_template('newOrder.html', order = order, menus =menus)

@app.route('/about')
def aboutUs():
    menus = helper.getMenusItem('user',2)
    return render_template('about.html', menus = menus)

@app.route('/login',methods=['GET','POST'])
def adminLogin():
    if request.method == "GET":
        users = helper.getUsers()
        session['auth'] = users
        return render_template('login.html', menus = helper.getMenusItem()) 
   
    username = request.form['username']
    password = request.form['password']
    if username and password:
        users = session['auth']
        session.pop('auth')

        user = list(filter(lambda u: u['userName'] == username, users))[0]
        if user['userName'] == username and check_password_hash(user['password'],password):
            token = jwt.encode(
                payload = {
                    'exp': datetime.utcnow() + timedelta(minutes = 90),
                    'iat': datetime.utcnow(),
                    'sub': user['id'],
                    'branch': user['branch']
                },
                key = app.config.get('SECRET_KEY'),
                algorithm = 'HS256'
            )
            app.logger.info('loged in: %s@%s', user['userName'], user['branch'])
            menus = helper.getMenusItem('admin')
            data = { 'id': user['id'], 'branch': user['branch'] }
            session['token'] = json.dumps({'token' : token , 'user': data})
            if 'redirectAfterAuth' in session:
                return  redirect(session['redirectAfterAuth'])       
            return redirect(url_for('index', user= data, menus = menus))  

    return redirect(url_for('adminLogin', menus = menus))  

@app.route('/logout')
def adminLogOut():
    app.logger.info('User loged out...')
    session.clear()
    return redirect(url_for('index'))    

@app.route('/catalog/<id>/delete', methods=['POST'])
def delete(id):
    status = 200
    erorr =''
    if id:
     status, error = helper.deleteCatalog(db,id)

    if status == 200:
        db.commit()
        return make_response(json.dumps({ 'redirect_url': url_for('catalogs')}),status)
        
    return make_response(json.dumps({ 'redirect_url': url_for('success', status=status)}),200)

@app.route('/submit/order', methods=['POST'])
def submitOrder():
    app.logger.info('User create new order...')
    status, error, orderRefNo = helper.makeOrder(db)
    return make_response(json.dumps({ 'redirect_url': url_for('success', orderRefNo=orderRefNo, status=status)}),200)

@app.route('/<location>/order/<orderId>/update/<status>',methods=['POST'] )
def updateOrderStatus(orderId,location,status):
    if 'token' in session:
        if orderId and location and status:
            status_code, error = helper.updateOrderStatus(db,orderId,location,status)
            if status_code == 200:
                 db.commit()
            return  make_response(json.dumps({}), 200)
        return  make_response(json.dumps({}), 400) 
    return  make_response(json.dumps({'error': 'unauthorized'}), 401)     

@app.route('/info/<int:status>', defaults={'orderRefNo': None})
@app.route('/info/<orderRefNo>/<int:status>')
def success(status,orderRefNo):
    menus = helper.getMenusItem('user',1)
    return render_template('success.html', orderRefNo=orderRefNo,status = status, menus=menus)     

def is_user_authen():
    token =  None
    if 'token' in session:
        auth = json.loads(session['token'])
        token = auth['token']
        user = auth['user']
        try:
            payload = jwt.decode(jwt=token, key= app.config.get('SECRET_KEY'),algorithms='HS256')
            return payload['sub'] == user['id'] and payload['branch'] == user['branch']

        except jwt.ExpiredSignatureError:
            session.pop('token')
            return redirect(url_for('adminLogin'))

        except jwt.InvalidTokenError:
            session.pop('token')
            return False
      
    return False

def notification():
    return helper.getOrderNotification(db)

app.jinja_env.globals.update(is_user_authen = is_user_authen)
app.jinja_env.globals.update(getInstitution = helper.getInstitution)
app.jinja_env.globals.update(getOrderKind = helper.getOrderKind)
app.jinja_env.globals.update(orderNotification = notification)

if __name__ == "__main__":
    app.run(host='host=somruthai.com', port=443, debug=True, ssl_context='adhoc')