import sqlite3 as sl
from flask import session,request
import datetime
import calendar
import json
import uuid
import random
import string
import app
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def initializeOrderDb():
    db = sl.connect('order.db', check_same_thread=False)
    with db:
        # db.execute(""" DROP TABLE IF EXISTS Customers """)
        # db.execute(""" DROP TABLE IF EXISTS Order_Details """)
        # db.execute(""" DROP TABLE IF EXISTS Orders """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Customers (
                id TEXT NOT NULL PRIMARY KEY,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                firstName TEXT NOT NULL,
                lastName TEXT NOT NULL,
                gender TEXT NOT NULL,
                institution TEXT NOT NULL,
                major TEXT NOT NULL,
                degree TEXT NOT NULL,
                weight INTEGER DEFAULT 0 NOT NULL,
                height INTEGER DEFAULT 0 NOT NULL,
                mobileNo TEXT NOT NULL,
                lineId TEXT NOT NULL
            );
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS Catalogs (
                id TEXT NOT NULL PRIMARY KEY,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                item TEXT NOT NULL,
                unitInStock INTEGER DEFAULT 0 NOT NULL,
                unitPrice REAL DEFAULT 0 NOT NULL,
                depositRate REAL DEFAULT 0.3,
                rentOnly INTEGER DEFAULT 0,
                purchaseOnly INTEGER DEFAULT 0,
                cuttingOnly INTEGER DEFAULT 0

            );
        """)
    
        db.execute("""
            CREATE TABLE IF NOT EXISTS Orders (
                id TEXT NOT NULL PRIMARY KEY,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                customerId TEXT NOT NULL,
                orderLocation TEXT NOT NULL,
                method TEXT NOT NULL,
                shipAddress TEXT NOT NULL,
                color TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open' ,
                dueDate TEXT,
                orderRefNo TEXT NOT NULL
            );
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS Order_Details (
                id TEXT NOT NULL PRIMARY KEY,
                orderId TEXT NOT NULL,
                catalogId TEXT NOT NULL,
                item TEXT NOT NULL,
                qty INTEGER DEFAULT 0 NOT NULL,
                status TEXT DEFAULT 'open',
                orderKind TEXT NOT NULL,
                depositAmount REAL DEFAULT 0.0,
                totalAmount REAL DEFAULT 0.0
            );
        """)
    return db

# Read data
def getCatalogs(db):
    query = "SELECT * FROM Catalogs"
    return getDatas(db,query)  

def getCustomers(db, location):
    query = f"SELECT c.* From Customers c"

    if location and location != 'All':
        query = f"SELECT c.* From Orders o Left Join Customers c ON o.customerId = c.id and o.orderLocation = '{location}'"

    return getDatas(db,query)  

def getCustomer(db, id):
    query = f"SELECT c.* From Customers c Where c.id = '{id}'"
    cursor = db.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    return toDict(cursor,row)

def getOrders(db, location, orderRefNo = None):
    query = "SELECT o.*, c.id as customerId ,c.firstName || ' ' || c.lastName as customerName from Orders o  Left join Customers c ON o.customerId = c.id"
    if location != 'All':
        query = f"SELECT o.*, c.id as customerId ,c.firstName || ' ' || c.lastName as customerName from Orders o  Left join Customers c ON o.customerId = c.id Where o.orderLocation = '{location}'"
    
    if orderRefNo:
        if location == 'All':
            query = f"SELECT o.*, c.id as customerId ,c.firstName || ' ' || c.lastName as customerName from Orders o  Left join Customers c ON o.customerId = c.id Where o.orderRefNo = '{orderRefNo}'"
        else:
            query = f"SELECT o.*, c.id as customerId ,c.firstName || ' ' || c.lastName as customerName from Orders o  Left join Customers c ON o.customerId = c.id Where o.orderRefNo = '{orderRefNo}' and o.orderLocation = '{location}'"

    orders = getDatas(db,query)  
    # for order in orders:
    #     items = getOrderDetails(db,order['id'])
    #     order['items'] = items
    
    return orders 
    
def getOrder(db, id):
    query = f"SELECT * From Orders Where id = '{id}'"
    cursor = db.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    return toDict(cursor,row)

def getOrderDetails(db, orderId):
    query = "SELECT * from Order_Details"
    if orderId:
        query = f"SELECT * from Order_Details Where orderId = '{orderId}'"
    return getDatas(db,query)  

def getDatas(db, query):
    datas = []
    try:
        with db: 
            cursor = db.cursor()    
            datas = cursor.execute(query)
    except sl.Error as error:
        print(error)

    return toResultList(cursor,datas)  

def getCatalogsViewModel(db):  
    query = "SELECT * FROM Catalogs where unitInStock > 0"
    catalogs = getDatas(db,query)

    if catalogs:
        for catalog in catalogs:
          catalog['addedToCart'] = False

    return catalogs

def getOrderNotification(db):
    query = f"SELECT * From Orders Where status = 'open'"
    cursor = db.cursor()
    rows = cursor.execute(query)
    orders = toResultList(cursor,rows)
    count = len(orders)
    return count

def getUsers():
    return [
            {
                'id': str(uuid.uuid4()),
                'branch' : 'All',
                'userName' : 'admin',
                'password' : generate_password_hash('@dM!n!$tRaT0RAll')
            },
            {
                'id': str(uuid.uuid4()),
                'branch' : 'Bangkhen',
                'userName' : 'admin_Bkn',
                'password' : generate_password_hash('@dM!n!$tRaT0RBkn')
            },
            {
                'id': str(uuid.uuid4()),
                'branch' : 'LatKrabang',
                'userName' : 'admin_Lkg',
                'password' : generate_password_hash('@dM!n!$tRaT0RLkg')
            },
            {
                'id': str(uuid.uuid4()),
                'branch' : 'Minburi',
                'userName' : 'admin_Mbi',
                'password' : generate_password_hash('@dM!n!$tRaT0RMbi')
            }
        ]


#Insert data
def makeOrder(db):
    #Customer informations.
    customerId = request.form['customer_id']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    gender = request.form['gender']
    institution = request.form['institution']
    if 'opt_institution' in request.form:
        institution = request.form['opt_institution']

    major = request.form['major']
    degree = request.form['degree']
    weight = int(request.form['weight'])
    height = int(request.form['height'])
    mobileNo = request.form['mobileNo']
    lineId = request.form['lineId']

    #Save customer data..
    saveCust_Status,saveCust_error = newCustomer(db,customerId,firstName,lastName,gender,institution,major,degree,weight,height,mobileNo,lineId)

    #Order informations.
    orderId = request.form['order_id']
    orderLocation = request.form['orderLocate']
    color = request.form['color']

    method = request.form['shipMethod']
    address = ''
    if 'address' in request.form:
        address = request.form['address']

    order_status = request.form['order_status']
    #Save order information.
    orderRefNo = ''
    saveOrder_Status,saveOrder_error,orderRefNo = newOrder(db,orderId,customerId,orderLocation,method,address,color,order_status)

    #Order details
    orderKind = ''
    orderItems = json.loads(request.form['orderItems'])
    for item in orderItems:
        orderDetailId =  str(uuid.uuid4())
        catalogId = item['id']
        catalogDesc = item['item']
        orderKind = item['orderKind']
        qty = item['qty']  
        unitsInStock = item['unitsInStock'] - qty   
        depositAmount = (item['depositRate'] * item['unitPrice']) * qty   
        if orderKind == 'rent':
            totalAmount = (item['unitPrice'] * qty) + depositAmount
        else:
            totalAmount = item['unitPrice'] * qty   

        #update catalogs unit in stock = unit in stock - qty 
        try:
            with db:
                cursor = db.cursor()
                cursor.execute(f"UPDATE Catalogs SET unitInStock = {unitsInStock} Where id = '{catalogId}'" )
        except sl.Error as error:
            db.rollback()
            app.logger.error('failed to update Units In Stock in Catalogs: %s Line#231', error)

        detail_status,savedDetailerror = newOrderDetails(db, orderDetailId, orderId, catalogId ,catalogDesc, qty,depositAmount,totalAmount,order_status,orderKind)

    if saveCust_Status == 200 and saveOrder_Status == 200 and detail_status == 200:
        db.commit()
        return 200,saveOrder_error,orderRefNo 
    return 400 ,'An errors occurred while system making an order...'    

def newCatalog(db, item, unitInStock, unitPrice, depositRate, rentOnly, purchaseOnly, cuttingOnly):
    error_message = ''
    status = 200
    query = "INSERT INTO  Catalogs(id,item, unitInStock, unitPrice, depositRate, rentOnly, purchaseOnly, cuttingOnly) VALUES (?,?,?,?,?,?,?,?)"
    try:
        with db:
            cursor = db.cursor()
            cursor.execute(query, (str(uuid.uuid4()),item, unitInStock, unitPrice, depositRate, rentOnly, purchaseOnly, cuttingOnly))
    except sl.Error as error:
        db.rollback()
        status = 400
        error_message = error
        app.logger.error('failed to adding new catalog: %s Line#251', error)
    return status, error_message    

def newCustomer(db,id,firstName,lastName,gender,institution,major,degree,weight,height,mobileNo,lineId):
    error_message = ''
    status = 200
    try:
        with db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Customers (id,firstName,lastName,gender,institution,major,degree,weight,height,mobileNo,lineId) values (?,?,?,?,?,?,?,?,?,?,?)", (id,firstName,lastName,gender,institution,major,degree,weight,height,mobileNo,lineId))
    except sl.Error as error:
        db.rollback()
        status = 400
        error_message = error
        app.logger.error('failed to adding new customer: %s Line#266', error)

    return status, error_message

def newOrder(db,id, customerId,orderLocation,method,shipAddress,color,order_status):
    error_message = ''
    status = 200
    orderRefNo = generateOrderRefNo(db)
    dueDate =  datetime.utcnow() + timedelta(weeks=  3)
    
    try:
        with db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Orders (id,customerId,orderLocation,method,shipAddress,color,status, dueDate,orderRefNo) values (?,?,?,?,?,?,?,?,?)", (id, customerId,orderLocation,method,shipAddress,color,order_status,dueDate.strftime('%Y-%m-%d %H:%M:%S'),orderRefNo))
    except sl.Error as error:
        db.rollback()
        status = 400
        error_message = error
        app.logger.error('failed to adding new order: %s Line#285', error)

    return status, error_message, orderRefNo

def newOrderDetails(db,id,orderId, catalogId ,item,qty,depositAmount,totalAmount,status,orderKind):
    error_message = ''
    status_code = 200
    try:
        with db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Order_Details (id, orderId, catalogId ,item, qty, depositAmount, totalAmount, status, orderKind) values (?,?,?,?,?,?,?,?,?)", (id,orderId,catalogId,item,qty,depositAmount,totalAmount,status,orderKind))
    except sl.Error as error:
        db.rollback()
        status_code = 400
        error_message = error
        app.logger.error('failed to adding new order details: %s Line#302', error)

    return status_code, error_message


#Update data
def updateOrderStatus(db, orderId, location ,status):
    status_code = 200
    error_message =None
    order = getOrders(db,location,orderId)[0]
    if order['status'] != status:
        query = f"Update Orders SET status = '{status}' Where id = '{orderId}'"
        try:
            with db:
                cursor = db.cursor()
                cursor.execute(query)
        except sl.Error as error:
            db.rollback()
            status_code = 400
            error_message = error
            print(f'an error occoured while updating order status...  {error}')
    return status_code, error_message        

def updateCatalog(db, id,item, unitPrice, depositRate, rentOnly, purchaseOnly, cuttingOnly):
    error_message = ''
    status = 200
    query = f"UPDATE Catalogs SET item = '{item}',unitPrice ={unitPrice},depositRate = {depositRate},rentOnly ={rentOnly}, purchaseOnly ={purchaseOnly},cuttingOnly ={cuttingOnly}  Where id = '{id}'"
    try:
        with db:
            cursor = db.cursor()
            cursor.execute(query)
    except sl.Error as error:
        db.rollback()
        status = 400
        error_message = error_message
        app.logger.error('failed to updating new catalog: %s Line#338', error)

    return status, error_message  


#Delete data
def deleteCatalog(db,id):
    query = f"Delete from Catalogs Where id = '{id}'"
    error_message = ''
    status = 200
    try:
        with db:
            cursor = db.cursor()
            cursor.execute(query)
    except sl.Error as error:
        db.rollback()
        status = 400
        error_message = error
        app.logger.error('failed to delete new catalog: %s Line#357', error)

    return status, error_message


#Utilities
def getMenusItem(key = None, id = None):
    menus = [{ 'admin' : [] },  { 'user': []}]

    if 'menus' in session and key and id:
        index = 0
        if key == 'user':
            index = 1
        menus = session['menus']

        activeMenu = list(filter(lambda u: u['active'] == True, menus[index][key]))
        if activeMenu:
            activeMenu[0]['active'] = False

        menu =list(filter(lambda u: u['index'] == id, menus[index][key]))[0]
        menu['active'] = True

    return menus   

def generateOrderRefNo(db):
    refNo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    query = f"SELECT orderRefNo From Orders Where orderRefNo = '{refNo}'"
    cursor = db.cursor()
    cursor.execute(query)
    row = cursor.fetchone()
    if row is None:
        return refNo
    else:
        generateOrderRefNo(db)    

def toDict(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def toResultList(cursor, rows):
    results = []
    if rows:
        for row in rows:
            data = toDict(cursor,row)  

            if 'timestamp' in data:
                timestamp = datetime.strptime(data['timestamp'] ,'%Y-%m-%d %H:%M:%S')
                timestamp = datetime.fromtimestamp(calendar.timegm(timestamp.timetuple()))
                data['timestamp'] = timestamp

            if 'institution' in data:
                data['institution'] = getInstitution(data['institution'])
                      

            results.append(data)
        return results

def getInstitution(s):
    if s:
        if s == 'spu':
            return 'ม.ศรีปทุม (SPU)'
        if s == 'ku':
            return 'ม.เกษตรศาสตร์ (KU)'  
        if s == 'kmu':
            return 'ม.เทคโนโลยีพระจอมเกล้า KMU (พระนครเหนือ, ลาดกระบัง, ธนบุรี)'   
        if s == 'buu':
            return 'ม.บูรพา (BUU)'
        if s == 'bu':
            return 'ม.กรุงเทพ (BU)'
        if s == 'hcu':
            return 'ม.หัวเฉียวเฉลิมพระเกียรติ (HCU)'
        if s == 'bsu':
            return 'ม.กรุงเทพสุวรรณภูมิ (BSU)'
        if s == 'rsu':
            return 'ม.รังสิต (RSU)'
        if s == 'utcc':
            return 'ม.หอการค้าไทย (UTCC)'    

def getOrderKind(kind):
    if kind == 'rent':
        return "ซื้อ"
    if kind == 'buy':
        return "ตัด/ซื้อ" 
    if kind == "cutting":
        return "ตัด" 