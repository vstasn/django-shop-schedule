# Api methods

# Open API
# User
/api/user/register/
- Register new user

/api/user/login/
- Login and get AuthToken

# Shop
/api/shop/<pk:int>/schedule
- Get shop schedule

/api/shop/<pk:int>/is_working
- Check if shop is working now

# Should auth before using these methods
/api/shop
- Create new shop with owner=request.user

/api/shop/<pk:int>/update_schedule
- Update shop schedule

/api/shop/<pk:int>/close
- Close shop (can set a few days)