# ptud-gk-de-2
Ứng dụng quản lý công việc với các chức năng quản lý công việc, kiểm tra tiến độ, thời gian tạo task, thời gian hoàn thành với 2 tác nhân admin và user, phân loại công việc và cho người dùng sử dụng avatar cá nhân.

Tên: Nguyễn Phước Điền
Mssv: 21002595  
Github: NPD.iuh@gmail.com

Dự án này là một ứng dụng quản lý công việc giúp người dùng tổ chức nhiệm vụ hiệu quả. Ứng dụng cho phép:  
- Quản lý nhiệm vụ với trạng thái, thời gian tạo, và thời gian hoàn thành.  
- Hỗ trợ hai vai trò: Admin (quản lý toàn bộ) và User (quản lý nhiệm vụ cá nhân).  
- Ứng dụng được xây dựng bằng công nghệ Python, Flask, HTML, CSS, JS, SQLite.

 ## Hướng dẫn cài đặt
 ### 1. Clone repository:
  git clone [https://github.com/<your-username>/ptud-gk-de-2.git](https://github.com/NguyenPhuocDien/ptud-gk-de-2.git)
  cd ptud-gk-de-2
### 2. Tạo và kích hoạt môi trường ảo:
  python -m venv venv
  venv\Scripts\activate
### 3. Chạy cơ sở dữ liệu SQLite
flask db init
flask db migrate -m 
flask db upgrade
