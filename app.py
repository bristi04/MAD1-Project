from flask import Flask , render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from jinja2 import Template
from datetime import datetime
from functools import wraps

app=Flask(__name__)
app.config['SECRET_KEY']='12312421'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///project.sqlite3'
db=SQLAlchemy(app)
api=Api(app)

#Models
class User(db.Model):
    __tablename__ = "user"
    id= db.Column(db.Integer(), primary_key = True,autoincrement= True)
    username=db.Column(db.String, nullable=False, unique=True)
    password=db.Column(db.String, nullable=False)
    email=db.Column(db.String, nullable=False)
    user_request=db.relationship("BookRequest", backref="user", cascade='all, delete-orphan')
    user_orders=db.relationship("Orders", backref="user", cascade='all, delete-orphan')

class Librarian(db.Model):
    __tablename__ = "librarian"
    id= db.Column(db.Integer, primary_key = True)
    adminname=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)
    email=db.Column(db.String, nullable=False)
   
class Book(db.Model):
    __tablename__ = "book"
    book_id= db.Column(db.Integer, primary_key = True)
    book_name=db.Column(db.String, nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey("categories.category_id"))
    author_name=db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    request=db.relationship("BookRequest", backref="book", cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__="categories"
    category_id=db.Column(db.Integer, primary_key = True)
    category_name=db.Column(db.String, nullable=False, unique=True)
    description=db.Column(db.String, nullable=False)
    date_created = db.Column(db.String, nullable=False)
    section=db.relationship("Book",backref="category", cascade='all, delete-orphan')

class BookRequest(db.Model):
    __tablename__="book_request"
    request_id=db.Column(db.Integer, primary_key = True, autoincrement= True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"))
    username=db.Column(db.String, nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey("categories.category_id"))
    book_id=db.Column(db.Integer, db.ForeignKey("book.book_id"))
    book_name=db.Column(db.String, nullable=False)
    author_name=db.Column(db.String, nullable=False)
    price=db.Column(db.Integer, nullable=False)
    status=db.Column(db.String, nullable=False)
    date_of_issue=db.Column(db.String, nullable= False)
    date_of_return=db.Column(db.String, nullable=False)
    user_return_date=db.Column(db.String)
    feedback=db.Column(db.String)
    
class Orders(db.Model):
     __tablename__="orders"
     order_id=db.Column(db.Integer, primary_key = True, autoincrement= True)
     user_id=db.Column(db.Integer, db.ForeignKey("user.id"))
     username=db.Column(db.String, nullable=False)
     book_id=db.Column(db.Integer, db.ForeignKey("book.book_id"))
     book_name=db.Column(db.String, nullable=False)
     category_id=db.Column(db.Integer, db.ForeignKey("categories.category_id"))
     author_name=db.Column(db.String, nullable=False)
     price=db.Column(db.Integer, db.ForeignKey("book.price"))
     payment=db.Column(db.String, nullable=False)
     date_of_issue=db.Column(db.String, nullable=False)
     
with app.app_context():
    db.create_all()    

#CurrentDate
current_datetime = datetime.now()



#decorater for auth_required
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        if 'admin_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login_as_user')) 
    return inner

#First User/Librarian Interface
@app.route("/project")
def home_page():
    return render_template("index.html")

#User Requirements
  
@app.route("/login_as_user", methods=['GET','POST'])
def login_user():
    if request.method == "POST":
        username=request.form.get('username')
        password=request.form.get('password')
        
        user=User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(f'/user/{user.id}')
        else:
            flash('Incorrect username or password! Please check again')
    return render_template("login_user.html")

@app.route('/user/<int:user_id>', methods=['GET','POST'])
def user_login(user_id):
    user=User.query.get(user_id)
    if 'user_id' in session:
        flash('Logged in successfully!')
        return render_template("user_dashboard.html", username=user.username)


@app.route("/signup",methods=['GET','POST'])
def register():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')
        this_user=User.query.filter_by(username=username).first()
        if this_user:
            flash('user already exists!')
        else:
           new_user=User(username=username, password=password, email=email)
           db.session.add(new_user)
           db.session.commit()
           flash('signed up successfully!')
           return redirect('/login_as_user')
    
    return render_template("signup.html")

        
@app.route('/profile', methods=['GET','POST'])
@auth_required
def profile():
        user=User.query.get(session['user_id'])
        if request.method=="POST":
           username=request.form.get('username')
           oldpassword=request.form.get('oldpassword')
           password=request.form.get('newpassword')
           email=request.form.get('email')
           if not username or not password or not email:
               flash('Please fill out all the required fleilds!')
               return redirect(url_for('profile'))
           if oldpassword != user.password:
               flash('Incorrect password')
               return redirect(url_for('profile'))
           user.username=username
           user.password=password
           user.email=email
           db.session.commit()
           flash('profile updated successfully! login again')
           return redirect('/login_as_user')
        return render_template('profile_user.html', user=user )

@app.route('/bookcart', methods=["GET","POST"])
def book_cart():
    users=User.query.get(session['user_id'])
    categories=Category.query.all()
    requested_books = [req.book_id for req in users.user_request]
    ordered_books=[order.book_id for order in users.user_orders]
    parameter=request.args.get('parameter')
    query=request.args.get('query')
    parameters={
        'cname':'Category',
        'bname':'Book',
        'aname':'Author Name',
        'price':'Max Price'
    }
    if parameter=='cname':
        categories=Category.query.filter(Category.category_name.ilike(f'%{query}%')).all()
        return render_template('bookcart.html',categories=categories, parameters=parameters, query=query)
    elif parameter=='bname':
        return render_template('bookcart.html',categories=categories, param=parameter, bname=query, parameters=parameters, query=query)
    elif parameter=='aname':
        return render_template('bookcart.html',categories=categories, param=parameter, aname=query, parameters=parameters, query=query)
    elif parameter=='price':
        query=int(query)
        return render_template('bookcart.html', users=users,categories=categories, param=parameter, price=query, parameters=parameters, query=query)
    return render_template('bookcart.html',categories=categories, users=users, parameters=parameters,query=query, requested_books=requested_books, ordered_books=ordered_books)


@app.route('/request/<int:book_id>/', methods=['GET','POST'])
def request_book(book_id):
         user=User.query.get(session['user_id'])
         existing_request_count = BookRequest.query.filter_by(user_id=user.id).count()
         if existing_request_count >= 5:
            flash('You have reached the maximum limit of book requests.')
            return redirect('/bookcart')
         book=Book.query.get(book_id)
         book_name=book.book_name
         author_name=book.author_name
         price=book.price
         status='requested'
         book.date_of_issue='to be notified'
         book.date_of_return='to be notified'
         new_req=BookRequest(user_id=session['user_id'], username=user.username, book_id=book_id,book_name=book_name,category_id=book.category_id, author_name=author_name, price=price,status=status, date_of_issue=book.date_of_issue, date_of_return=book.date_of_return)
         db.session.add(new_req)
         db.session.commit()
         flash('Book requested successfully!')
         return redirect('/bookcart')
     
@app.route('/mybooks')
@auth_required
def mybooks():
    myreq=BookRequest.query.filter_by(user_id=session['user_id'])
    return render_template('mybooks.html', myreq=myreq)

@app.route('/cancel_request/<int:request_id>', methods=['GET','POST'] )
def cancel_request(request_id):
    req=BookRequest.query.get(request_id)
    if request.method=="POST":
        db.session.delete(req)
        db.session.commit()
        flash('request cancelled!')
        return redirect('/mybooks')
    return render_template('cancel_request.html', req=req)

@app.route("/access_ebook/<int:request_id>",  methods=['GET','POST'])
def ebook_access(request_id):
    req=BookRequest.query.get(request_id)
    return render_template('ebook_access.html',req=req)

@app.route("/return/<int:request_id>", methods=['GET','POST'])
def return_book(request_id):
    req=BookRequest.query.get(request_id)
    if request.method=="POST":
        req.status="returned"
        req.feedback=request.form.get('feedback')
        req.user_return_date=current_datetime
        db.session.commit()
        flash('book returned successfully!')
        return redirect('/mybooks')
    return render_template('returnbook.html', req=req, current_datetime=datetime.now())
    
@app.route('/buy/<int:book_id>/', methods=['GET','POST'])
def order_book(book_id):
    user=User.query.get(session['user_id'])
    book=Book.query.get(book_id)
    book_name=book.book_name
    author_name=book.author_name
    price=book.price
    payment='payment pending'
    new_order=Orders(user_id=session['user_id'], username=user.username, book_id=book_id,book_name=book_name,category_id=book.category_id, author_name=author_name, price=price,payment=payment)
    db.session.add(new_order)
    db.session.commit()
    flash('Book added successfully!')
    return redirect('/bookcart')

@app.route('/myorders')
@auth_required
def myorders():
    myorder=Orders.query.filter_by(user_id=session['user_id'])
    return render_template('myorders.html', myorder=myorder)

@app.route('/cancel_order/<int:order_id>',methods=['GET','POST'])
def cancel_order(order_id):
    order=Orders.query.get(order_id)
    if request.method=="POST":
        db.session.delete(order)
        db.session.commit()
        flash('order cancelled')
        return redirect('/myorders')
    return render_template('cancel_order.html',order=order)

@app.route('/pay/<int:order_id>',methods=['GET','POST'])
def pay_order(order_id):
    order=Orders.query.get(order_id)
    if request.method=="POST":
      order.payment="paid"
      db.session.commit()
      flash('payment successful')
    return render_template('/pay_and_download.html', order=order, username=order.username)

@app.route('/access_order/<int:order_id>',methods=['GET','POST'])
def access_book(order_id):
    order=Orders.query.get(order_id)
    return render_template('/access_order.html', order=order, username=order.username)
    

#Admin Requirements

@app.route("/login_as_admin",methods=['GET','POST'])
def login_admin():
    if request.method == "POST":
        adminname=request.form.get('adminname')
        password=request.form.get('password')
        
        admin=Librarian.query.filter_by(adminname=adminname).first()
        if admin and admin.password == password:
            session['admin_id'] = admin.id
            flash('Logged in successfully!')
            return render_template("librarian_dashboard.html",adminname=adminname)
        else:
            flash('Incorrect username or password! Please try again')
            return redirect('/login_as_admin')
    return render_template("login_admin.html")

@app.route('/profile_admin', methods=['GET','POST'])
@auth_required
def admin_profile():
        admin=Librarian.query.get(session['admin_id'])
        if request.method=="POST":
           adminname=request.form.get('adminname')
           oldpassword=request.form.get('oldpassword')
           password=request.form.get('newpassword')
           email=request.form.get('email')
           if not adminname or not password or not email:
               return redirect(url_for('profile_admin'))
           if oldpassword != admin.password :
               return redirect(url_for('admin_profile'))
           admin.adminname=adminname
           admin.password=password
           admin.email=email
           db.session.commit()
           flash('profile updated successfully! Login again')
           return redirect('/login_as_admin')
        return render_template('profile_admin.html', admin=admin )

@app.route('/addsection', methods=['GET','POST'])
def addsection():
    if request.method=="POST":
        cname=request.form.get('cname')
        description=request.form.get('description')
        date=request.form.get('date')
        new_section=Category.query.filter_by(category_name=cname).first()
        if new_section:
            flash('This section already exists!')
        else:
           new_section=Category(category_name=cname, description=description,date_created=date)
           db.session.add(new_section)
           db.session.commit()
           flash('Section added successfully!')
           return redirect('/allsection')
    return render_template('addsection.html')

@app.route('/admin_requests', methods=['GET','POST'])
def admin_requests():
    req=BookRequest.query.all()
    current_datetime = datetime.now()
    for request in req:
        if request.date_of_return != 'to be notified' and request.date_of_return !='none':
           return_date = datetime.strptime(request.date_of_return, '%Y-%m-%d %H:%M:%S')
           if return_date <= current_datetime:
             db.session.delete(request)
             db.session.commit()
             flash(f'The request for book {request.book_name} automatically revoked from the user {request.username}!')
    remaining_requests=BookRequest.query.all()
    return render_template('admin_author.html', req=remaining_requests)

@app.route('/admin_orders',  methods=['GET','POST'])
def admin_orders():
    order=Orders.query.all()
    return render_template('admin_order.html', order=order)
    
@app.route('/allsection')
def all_section():
    categories=Category.query.all()
    parameter=request.args.get('parameter')
    query=request.args.get('query')
    parameters={
        'cname':'Category',
    }
    if parameter=='cname':
        categories=Category.query.filter(Category.category_name.ilike(f'%{query}%')).all()
        return render_template('allsection.html',categories=categories, parameters=parameters, query=query)
    return render_template('allsection.html',categories=categories,  parameters=parameters,query=query)

@app.route('/addbooks/<int:category_id>/', methods=['GET','POST'])
def addbooks(category_id):
    if request.method=="POST":
        book_name=request.form.get('book_name')
        author_name=request.form.get('author_name')
        price=request.form.get('price')
        new_book=Book.query.filter_by(book_name=book_name).first()
        if new_book:
            flash('This book already exists!')
        else:
           price=float(price)
           new_book=Book(book_name=book_name,category_id=category_id,author_name=author_name,price=price)
           db.session.add(new_book)
           db.session.commit()
           flash('Book added successfully!')
           return redirect('/allsection')
    return render_template('addbooks.html', category_id=category_id)

@app.route('/showsection/<int:category_id>/', methods=['GET','POST'])
def showsection(category_id):
    categories=Category.query.filter_by(category_id=category_id)
    book=Book.query.filter_by(category_id=category_id)
    parameter=request.args.get('parameter')
    query=request.args.get('query')
    parameters={
        'bname':'Book Name',
    }
    if parameter=='bname':
        book=Book.query.filter(Book.book_name.ilike(f'%{query}%')).all()
        return render_template('showsection.html',book=book, categories=categories, parameters=parameters, query=query)
    return render_template('showsection.html',parameters=parameters, query=query, categories=categories, book=book)

#Edit a book
@app.route('/updatebook/<int:category_id>/<int:book_id>/', methods=['GET','POST'])
def update_book(category_id, book_id):
    categories=Category.query.get(category_id)
    book=Book.query.get(book_id)
    if request.method=="POST":
       book_name=request.form.get('book_name')
       author_name=request.form.get('author_name')
       price=request.form.get('price')
       book.book_name=book_name
       book.category_id=category_id
       book.author_name=author_name
       book.price=price
       db.session.commit()
       flash('Book updated successfully!')
       return redirect('/allsection')
    return render_template('updatebook.html', book=book, categories=categories)

#Edit a section
@app.route('/updatesection/<int:category_id>/', methods=["GET","POST"])
def update_section(category_id):
    categories=Category.query.get(category_id)
    if request.method=="POST":
        categories.category_name=request.form.get('cname')
        categories.description=request.form.get('description')
        categories.data_of_creation=request.form.get('doc')
        db.session.commit()
        flash('Section updated successfully!')
        return redirect('/allsection')
    return render_template('updatesection.html',categories=categories)
        

@app.route('/deletebook/<int:category_id>/<int:book_id>/', methods=['GET','POST'])
def delete_book(category_id, book_id):
    categories=Category.query.get(category_id)
    book=Book.query.get(book_id)
    if request.method=="POST":
        db.session.delete(book)
        db.session.commit()  
        flash('Book Deleted successfully!') 
        return redirect('/allsection')  
    return render_template('deletebook.html', book=book, categories=categories)


@app.route('/deletesection/<int:category_id>/', methods=['GET','POST'])
def delete_section(category_id):
    category=Category.query.get(category_id)
    if request.method=="POST":
        db.session.delete(category)
        db.session.commit()
        flash('Section Deleted successfully!') 
        return redirect('/allsection')  
    return render_template('deletesection.html', category=category)

@app.route('/grantbook/<int:request_id>', methods=['GET','POST'])
def grant_book(request_id):
    req=BookRequest.query.get(request_id)
    if request.method=="POST":
        date_of_issue=request.form.get('doi')
        date_of_return=request.form.get('dor')
        req.date_of_issue=date_of_issue
        req.date_of_return=date_of_return
        req.status="granted"
        db.session.commit()
        flash('Book granted to the user!')
        return redirect('/admin_requests')
    return render_template('grantbook.html',req=req)

@app.route('/grantorder/<int:order_id>', methods=['GET','POST'])
def grant_order(order_id):
    order=Orders.query.get(order_id)
    if request.method=="POST":
      order.date_of_issue=datetime.now()
      order.payment="pay now"
      db.session.commit()
      flash('user is notified to make the payment')
      return redirect('/admin_orders')
    return render_template('grantorder.html', order=order, current_datetime=current_datetime)

@app.route('/reject/<int:request_id>', methods=['GET','POST'])
def reject_book(request_id):
    req=BookRequest.query.get(request_id)
    #req.date_of_issue="none"
    #req.date_of_return="none"
    req.status="request rejected"
    flash('request rejected successfully')
    db.session.commit()
    return redirect('/admin_requests')

@app.route('/revoke/<int:request_id>', methods=['GET','POST'])
def revoke_book(request_id):
    req=BookRequest.query.get(request_id)
    return_date=datetime.strptime(req.date_of_return, '%Y-%m-%d %H:%M:%S')
    current_datetime = datetime.now()
    if request.method=="POST":
        db.session.delete(req)
        db.session.commit()
        flash('book revoked from the user!')
        return redirect('/admin_requests') 
    else:
        return render_template('revoke.html', req=req, current_datetime=current_datetime)
    
@app.route('/admin_stats')
def admin_statistics():
    categories=Category.query.all()
    category_names=[category.category_name for category in categories]
    category_sizes=[len(category.section) for category in categories]
    return render_template('chart_admin.html', categories=categories, category_names=category_names,category_sizes=category_sizes)    
    
    
if __name__=="__main__":
    app.run(debug=True)