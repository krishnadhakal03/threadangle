import bcrypt
password = "password123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(f"Hashed: {hashed}")
check = bcrypt.checkpw(password.encode('utf-8'), hashed)
print(f"Check: {check}")
