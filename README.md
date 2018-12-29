# Api methods

[![CircleCI](https://circleci.com/gh/vstasn/django-shop-schedule.svg?style=svg)](https://circleci.com/gh/vstasn/django-shop-schedule)

## API/User

Register new user
  - /api/user/register/

Login and get AuthToken
  - /api/user/login/

## API/Shop

Get shop schedule
  - /api/shop/<pk:int>/schedule

Check if shop is working now
  - /api/shop/<pk:int>/is_working

## Should auth before using these methods

Create new shop with owner=request.user
  - /api/shop

Update shop schedule
  - /api/shop/<pk:int>/update_schedule

Close shop (can set a few days)
  - /api/shop/<pk:int>/close