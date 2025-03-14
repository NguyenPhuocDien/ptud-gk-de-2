from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your_secret_key'  # Cần thiết cho session và flash
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

# Mô hình User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), default='user')
    avatar_url = db.Column(db.String(200), default='default.png')
    tasks = db.relationship('Task', backref='user', lazy=True)

# Mô hình Category
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default='primary')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='category', lazy=True)
    user = db.relationship('User', backref='categories')

# Mô hình Task
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='đang thực hiện')
    created = db.Column(db.DateTime, default=datetime.utcnow)
    finished = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    priority = db.Column(db.String(20), default='trung bình')
    due_date = db.Column(db.DateTime, nullable=True)

# Tạo cơ sở dữ liệu
with app.app_context():
    db.create_all()

# Hàm kiểm tra đuôi file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Decorator kiểm tra đăng nhập
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator kiểm tra quyền admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Không cho phép đăng ký username "Admin"
        if username == "Admin":
            flash('Tên đăng nhập này không được phép sử dụng!', 'danger')
            return redirect(url_for('register'))
            
        # Kiểm tra username đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
            return redirect(url_for('register'))
        
        # Tạo user mới
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth.html', view_type='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            flash(f'Xin chào, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin!', 'danger')
    
    return render_template('auth.html', view_type='login')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user.role == 'admin':
        # Admin xem tất cả các task
        tasks = Task.query.all()
        users = User.query.all()
        categories = Category.query.all()
    else:
        # User chỉ xem task của mình
        tasks = Task.query.filter_by(user_id=user_id).all()
        categories = Category.query.filter_by(user_id=user_id).all()
        users = None
    
    return render_template('dashboard.html', tasks=tasks, users=users, categories=categories)

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    user = User.query.get(user_id)
    return render_template('user_management.html', view_type='profile', user=user)

@app.route('/upload_avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar():
    if request.method == 'POST':
        if 'avatar' not in request.files:
            flash('Không có file nào được chọn!', 'danger')
            return redirect(request.url)
        
        file = request.files['avatar']
        
        if file.filename == '':
            flash('Chưa chọn file!', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Thêm user_id vào tên file để tránh trùng lặp
            filename = f"{session['user_id']}_{filename}"
            
            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Cập nhật avatar cho user
            user = User.query.get(session['user_id'])
            user.avatar_url = filename
            db.session.commit()
            
            flash('Avatar đã được cập nhật thành công!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Loại file không được phép!', 'danger')
            
    user = User.query.get(session['user_id'])
    return render_template('upload_avatar.html', user=user)

@app.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        status = request.form.get('status', 'đang chờ')
        priority = request.form.get('priority', 'trung bình')
        category_id = request.form.get('category_id')
        due_date_str = request.form.get('due_date')
        
        # Xử lý due_date
        due_date = None
        if due_date_str and due_date_str.strip():
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        # Nếu là admin, có thể chọn user để gán task
        if session['role'] == 'admin' and 'user_id' in request.form:
            user_id = request.form['user_id']
        else:
            user_id = session['user_id']
        
        new_task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            user_id=user_id,
            category_id=category_id if category_id else None
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('Thêm công việc mới thành công!', 'success')
        return redirect(url_for('dashboard'))
    
    # Nếu là admin, lấy danh sách user để hiển thị trong form
    users = []
    if session['role'] == 'admin':
        users = User.query.all()
    
    # Lấy danh sách category của user
    categories = Category.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('task_management.html', view_type='add', users=users, categories=categories)

@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Kiểm tra quyền: admin có thể sửa tất cả, user chỉ sửa task của mình
    if session['role'] != 'admin' and task.user_id != session['user_id']:
        flash('Bạn không có quyền sửa công việc này!', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description', '')
        task.status = request.form['status']
        task.priority = request.form.get('priority', 'trung bình')
        category_id = request.form.get('category_id')
        task.category_id = category_id if category_id else None
        
        due_date_str = request.form.get('due_date')
        if due_date_str and due_date_str.strip():
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                pass
        else:
            task.due_date = None
        
        # Nếu status là "hoàn thành" và chưa có thời gian hoàn thành
        if task.status == 'hoàn thành' and not task.finished:
            task.finished = datetime.utcnow()
        # Nếu status không phải "hoàn thành", reset thời gian hoàn thành
        elif task.status != 'hoàn thành':
            task.finished = None
        
        # Nếu là admin, có thể thay đổi user
        if session['role'] == 'admin' and 'user_id' in request.form:
            task.user_id = request.form['user_id']
        
        db.session.commit()
        flash('Cập nhật công việc thành công!', 'success')
        return redirect(url_for('dashboard'))
    
    # Nếu là admin, lấy danh sách user để hiển thị trong form
    users = []
    if session['role'] == 'admin':
        users = User.query.all()
    
    # Lấy danh sách category của user
    categories = Category.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('task_management.html', view_type='edit', task=task, users=users, categories=categories, now=datetime.utcnow())

@app.route('/task/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Kiểm tra quyền: admin có thể xóa tất cả, user chỉ xóa task của mình
    if session['role'] != 'admin' and task.user_id != session['user_id']:
        flash('Bạn không có quyền xóa công việc này!', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Xóa công việc thành công!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('user_management.html', view_type='manage', users=users)

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        
        # Chỉ cập nhật mật khẩu nếu có nhập mới
        if request.form['password']:
            user.password = request.form['password']
        
        db.session.commit()
        flash('Cập nhật người dùng thành công!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('user_management.html', view_type='edit', user=user)

@app.route('/admin/user/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    # Không cho phép xóa chính mình
    if user_id == session['user_id']:
        flash('Không thể xóa tài khoản đang đăng nhập!', 'danger')
        return redirect(url_for('manage_users'))
    
    user = User.query.get_or_404(user_id)
    
    # Xóa tất cả task của user này
    Task.query.filter_by(user_id=user_id).delete()
    
    # Xóa user
    db.session.delete(user)
    db.session.commit()
    
    flash('Xóa người dùng thành công!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/categories')
@login_required
def list_categories():
    user_id = session['user_id']
    categories = Category.query.filter_by(user_id=user_id).all()
    return render_template('categories.html', categories=categories)

@app.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        color = request.form['color']
        user_id = session['user_id']
        
        new_category = Category(
            name=name,
            color=color,
            user_id=user_id
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash('Thêm danh mục mới thành công!', 'success')
        return redirect(url_for('list_categories'))
    
    return render_template('task_management.html', view_type='add_category')

@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Kiểm tra quyền: admin có thể sửa tất cả, user chỉ sửa category của mình
    if session['role'] != 'admin' and category.user_id != session['user_id']:
        flash('Bạn không có quyền sửa danh mục này!', 'danger')
        return redirect(url_for('list_categories'))
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.color = request.form['color']
        
        db.session.commit()
        flash('Cập nhật danh mục thành công!', 'success')
        return redirect(url_for('list_categories'))
    
    return render_template('task_management.html', view_type='edit_category', category=category)

@app.route('/category/delete/<int:category_id>')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Kiểm tra quyền: admin có thể xóa tất cả, user chỉ xóa category của mình
    if session['role'] != 'admin' and category.user_id != session['user_id']:
        flash('Bạn không có quyền xóa danh mục này!', 'danger')
        return redirect(url_for('list_categories'))
    
    # Cập nhật các task thuộc category này về null
    tasks = Task.query.filter_by(category_id=category_id).all()
    for task in tasks:
        task.category_id = None
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Xóa danh mục thành công!', 'success')
    return redirect(url_for('list_categories'))

if __name__ == '__main__':
    # Tạo thư mục uploads nếu chưa tồn tại
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Thêm tài khoản admin cố định
    with app.app_context():
        # Đảm bảo tất cả bảng được tạo
        db.create_all()
        
        # Kiểm tra xem đã có admin chưa
        admin = User.query.filter_by(username='Admin').first()
        if not admin:
            admin = User(username='Admin', password='Admin', role='admin')
            db.session.add(admin)
            db.session.commit()
        # Nếu đã có admin, đảm bảo password là "Admin"
        elif admin.password != 'Admin':
            admin.password = 'Admin'
            db.session.commit()
    
    app.run(debug=True)